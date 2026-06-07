"""One-call smoke test for a paid model, routed through the cost guard (Phase 0.4).

Makes a single tiny chat completion, reads real token usage from the response, and
records the cost in data/processed/_spend.json. Keys come from env vars ONLY (named in
pricing.yaml per model); nothing is hard-coded. If the key is missing the test skips
cleanly with instructions (expected before keys are provisioned).

Currently implements the OpenAI-compatible chat API (covers DeepSeek and an OpenAI/GPT
anchor). Gemini and Anthropic use different wire formats — their adapters land in Phase
3.4; this smoke test will say so rather than guess.

  python -m experiments.harness.paid_smoke deepseek-chat
  python -m experiments.harness.paid_smoke gpt-5.1
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

from experiments.harness.cost_guard import CostGuard, load_pricing
from experiments.harness.env import load_env

SMOKE_PROMPT = "Reply with exactly the word: pong."


def _openai_compatible_call(cfg: dict, api_key: str, model: str) -> dict:
    payload: dict = {
        "model": model,
        "messages": [{"role": "user", "content": SMOKE_PROMPT}],
    }
    # GPT-5.x reasoning models: new token param, no custom temperature, and an explicit
    # reasoning_effort. DeepSeek (and older OpenAI) take the classic params.
    if cfg.get("provider") == "openai":
        payload["max_completion_tokens"] = 256  # room for any reasoning tokens
        rp = cfg.get("reasoning_param")
        rv = cfg.get("reasoning_values", {})
        if rp and "off" in rv:
            payload[rp] = rv["off"]  # cheapest: reasoning OFF for the smoke
    else:
        payload["max_tokens"] = 16
        payload["temperature"] = 0.0
    base_url = cfg["base_url"]
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def smoke(model: str) -> int:
    load_env()  # pull keys from .env if not already in the environment
    pricing = load_pricing()
    cfg = pricing.get("models", {}).get(model)
    if cfg is None:
        print(f"Unknown model '{model}'. Known: {', '.join(sorted(pricing['models']))}")
        return 1

    env_key = cfg["env_key"]
    api_key = os.environ.get(env_key)
    if not api_key:
        print(f"[skip] {env_key} not set — cannot smoke-test '{model}'.")
        print(f"       Provide it via env only, e.g.:  export {env_key}=...")
        print( "       (never commit keys). Re-run this once the key is exported.")
        return 0  # expected pre-key; not a failure

    api = cfg.get("api")
    if api != "openai_compatible":
        print(f"[skip] '{model}' uses the '{api}' API; its adapter lands in Phase 3.4.")
        print( "       The 0.4 smoke test currently supports openai_compatible providers"
               " (DeepSeek, OpenAI).")
        return 0

    print(f"Smoke-testing {model} via {cfg['base_url']} ...")
    try:
        resp = _openai_compatible_call(cfg, api_key, model)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:300]
        print(f"[fail] HTTP {e.code} {e.reason}: {body}")
        return 1
    except (urllib.error.URLError, OSError) as e:
        print(f"[fail] {e}")
        return 1

    usage = resp.get("usage", {})
    in_tok = usage.get("prompt_tokens", 0)
    out_tok = usage.get("completion_tokens", 0)
    text = (resp.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()

    guard = CostGuard(pricing=pricing)
    cost = guard.record(model, in_tok, out_tok, meta={"smoke": True})
    print(f"  reply   : {text[:60]!r}")
    print(f"  tokens  : {in_tok} in + {out_tok} out")
    print(f"  cost    : €{cost:.6f}  (recorded)")
    print(f"  remaining budget: €{guard.remaining_eur():.4f}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Paid one-call smoke test (Phase 0.4)")
    p.add_argument("model", help="model key from experiments/configs/pricing.yaml")
    args = p.parse_args(argv)
    return smoke(args.model)


if __name__ == "__main__":
    raise SystemExit(main())

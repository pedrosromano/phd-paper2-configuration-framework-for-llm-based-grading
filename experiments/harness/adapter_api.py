"""Paid API grading adapter (Phase 3.4) -- DeepInfra (open roster) + OpenAI (anchor).

grade(item, config, guard) -> GradeResult, same interface as the Ollama adapter, routed
through the cost guard (every call records real token cost; refuses if the provider's
ceiling is already spent). Reasoning toggle per provider, from pricing.yaml:
  - openai (GPT-5.1): reasoning_effort = none|high; max_completion_tokens; no temperature.
  - deepinfra (Qwen3.5 / DeepSeek-V4 / GLM-5.1): chat_template_kwargs.enable_thinking = false|true.

  python -m experiments.harness.adapter_api    # smoke test all roster models, off vs on
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from experiments.harness import prompts
from experiments.harness.cost_guard import BudgetExceeded, CostGuard, load_pricing
from experiments.harness.env import load_env
from experiments.harness.grading import GradeResult
from experiments.harness.parser import parse_output


class _Transient(Exception):
    pass


@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=30),
       retry=retry_if_exception_type(_Transient), reraise=True)
def _chat(base_url: str, key: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code in (429, 500, 502, 503, 504):
            raise _Transient(f"HTTP {e.code}") from e
        raise
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        raise _Transient(str(e)) from e


def _build_payload(mcfg: dict, prompt: str, reasoning: str) -> dict:
    rv = mcfg.get("reasoning_values", {})
    payload = {"model": mcfg["model_id"], "messages": [{"role": "user", "content": prompt}]}
    if mcfg.get("provider") == "openai":
        payload["max_completion_tokens"] = 4096
        rp = mcfg.get("reasoning_param")           # reasoning_effort
        if rp and reasoning in rv:
            payload[rp] = rv[reasoning]            # none | high
    else:                                          # deepinfra (OpenAI-compatible) + others
        payload["max_tokens"] = 4096
        payload["temperature"] = 0.0
        rp = mcfg.get("reasoning_param")           # enable_thinking
        if rp and reasoning in rv:
            payload["chat_template_kwargs"] = {rp: rv[reasoning]}   # {"enable_thinking": bool}
    return payload


def grade(item, config, guard: CostGuard | None = None) -> GradeResult:
    load_env()
    pricing = (guard.pricing if guard else load_pricing())
    mcfg = dict(pricing["models"][config.model])
    mcfg.setdefault("model_id", config.model)      # anchor (gpt-5.1) uses its key as the API model name
    provider = mcfg.get("provider", "unknown")
    key = os.environ.get(mcfg["env_key"])

    def err(msg: str) -> GradeResult:
        return GradeResult(score=None, parse_ok=False, raw="", tokens_in=0, tokens_out=0,
                           latency_s=0.0, model=config.model, reasoning=config.reasoning,
                           config_hash=config.config_hash, error=msg)

    if not key:
        return err(f"{mcfg['env_key']} not set")
    if guard is not None and guard.remaining_for(provider) <= 0:
        return err(f"budget exhausted for provider {provider}")

    prompt = prompts.render(config, item)
    payload = _build_payload(mcfg, prompt, config.reasoning)
    t0 = time.perf_counter()
    try:
        resp = _chat(mcfg["base_url"], key, payload)
    except urllib.error.HTTPError as e:
        return err(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:160]}")
    except _Transient as e:
        return err(f"transient (retries exhausted): {str(e)[:120]}")
    latency = round(time.perf_counter() - t0, 3)

    msg = resp.get("choices", [{}])[0].get("message", {})
    raw = (msg.get("content") or "").strip()
    usage = resp.get("usage", {})
    tin, tout = int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0))
    if guard is not None:
        guard.record(config.model, tin, tout, meta={"config_hash": config.config_hash,
                                                     "reasoning": config.reasoning})
    parsed, ok = parse_output(raw, config.scope, config.decomposition)
    return GradeResult(score=parsed["score"], per_criterion=parsed["per_criterion"],
                       answers=parsed["answers"], parse_ok=ok, raw=raw,
                       tokens_in=tin, tokens_out=tout, latency_s=latency,
                       model=config.model, reasoning=config.reasoning,
                       config_hash=config.config_hash)


def _smoke() -> int:
    import pandas as pd
    from pathlib import Path
    from experiments.configs.config import Config
    df = pd.read_parquet(Path(__file__).resolve().parents[2] / "data" / "processed" / "corpus.parquet")
    item = df[df.dataset == "mohler"].iloc[0]
    guard = CostGuard()
    print(f"gold={item.gold_score}/{item.gold_scale_max}\n")
    for model in ["deepseek-v4-flash", "qwen3.5", "glm-5.1", "gpt-5.1"]:
        for reasoning in ("off", "on"):
            cfg = Config("mohler", "short_answer", model, reasoning=reasoning,
                         context_level="with_guidance")
            r = grade(item, cfg, guard)
            print(f"  {model:18} [{reasoning:3}] score={str(r.score):>5} ok={r.parse_ok!s:5} "
                  f"tok={r.tokens_in:>4}+{r.tokens_out:<5} {r.latency_s:>5}s err={r.error}")
    print(f"\nDeepInfra spent: €{guard.spent_for('deepinfra'):.4f} / €{guard.ceiling_for('deepinfra'):.0f}  |  "
          f"OpenAI spent: €{guard.spent_for('openai'):.4f} / €{guard.ceiling_for('openai'):.0f}")
    print("GLM clean-OFF check: compare glm-5.1 off vs on output tokens above "
          "(off should be MUCH smaller if reasoning truly disabled).")
    return 0


if __name__ == "__main__":
    raise SystemExit(_smoke())

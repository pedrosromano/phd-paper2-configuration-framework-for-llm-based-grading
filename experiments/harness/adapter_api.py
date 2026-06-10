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
import threading
import time
import urllib.error
import urllib.request

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_random_exponential

from experiments.harness import prompts
from experiments.harness.cost_guard import BudgetExceeded, CostGuard, load_pricing
from experiments.harness.env import load_env
from experiments.harness.grading import GradeResult
from experiments.harness.parser import parse_output


class _Transient(Exception):
    pass


# Transient-retry counters (for tuning concurrency: watch the 429 rate per step).
_RETRY = {"429": 0, "5xx": 0, "net": 0}
_RETRY_LOCK = threading.Lock()


def _bump(kind: str) -> None:
    with _RETRY_LOCK:
        _RETRY[kind] += 1


def retry_stats() -> dict:
    with _RETRY_LOCK:
        return dict(_RETRY)


# Jittered exponential backoff: random spread (0..2^n, capped 30s) so workers that hit a
# 429 together do NOT retreat in lockstep -> avoids a synchronized retry storm at high
# concurrency. Retries only on transient server/network errors (429 + 5xx gateway + net);
# 4xx like 400/401/403/404 re-raise immediately (not retried).
@retry(stop=stop_after_attempt(4), wait=wait_random_exponential(multiplier=1, max=30),
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
        if e.code == 429:
            _bump("429")
            raise _Transient("HTTP 429") from e
        if e.code in (500, 502, 503, 504):
            _bump("5xx")
            raise _Transient(f"HTTP {e.code}") from e
        raise
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        _bump("net")
        raise _Transient(str(e)) from e


def _build_payload(mcfg: dict, prompt: str, config) -> dict:
    """Single-turn payload (one user message)."""
    return _build_payload_msgs(mcfg, [{"role": "user", "content": prompt}], config)


def _build_payload_msgs(mcfg: dict, messages: list, config) -> dict:
    """Build the request from a messages list (supports multi-turn shared conversations).
    Sampling settings come from the Config (so they match config_hash exactly): max_tokens,
    temperature, top_p, seed. The reasoning toggle maps per provider."""
    reasoning = config.reasoning
    rv = mcfg.get("reasoning_values", {})
    payload = {"model": mcfg["model_id"], "messages": messages}
    if config.seed is not None:
        payload["seed"] = config.seed
    if mcfg.get("provider") == "openai":
        # GPT-5.1 reasoning tier: only max_completion_tokens + reasoning_effort; it rejects
        # temperature/top_p, so we deliberately omit them (config_hash still records them).
        payload["max_completion_tokens"] = config.max_tokens
        rp = mcfg.get("reasoning_param")           # reasoning_effort
        if rp and reasoning in rv:
            payload[rp] = rv[reasoning]            # none | high
    else:                                          # deepinfra (OpenAI-compatible) + others
        payload["max_tokens"] = config.max_tokens
        payload["temperature"] = config.temperature
        payload["top_p"] = config.top_p
        rp = mcfg.get("reasoning_param")           # enable_thinking
        if rp and reasoning in rv:
            payload["chat_template_kwargs"] = {rp: rv[reasoning]}   # {"enable_thinking": bool}
    return payload


def _reasoning_tokens(usage: dict) -> int | None:
    """Thinking-token count if the backend exposes it (OpenAI nests it under
    completion_tokens_details; some OpenAI-compatible backends put it at top level)."""
    details = usage.get("completion_tokens_details") or {}
    rt = details.get("reasoning_tokens")
    if rt is None:
        rt = usage.get("reasoning_tokens")
    return int(rt) if rt is not None else None


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
    payload = _build_payload(mcfg, prompt, config)
    t0 = time.perf_counter()
    try:
        resp = _chat(mcfg["base_url"], key, payload)
    except urllib.error.HTTPError as e:
        return err(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:160]}")
    except _Transient as e:
        return err(f"transient (retries exhausted): {str(e)[:120]}")
    latency = round(time.perf_counter() - t0, 3)

    choice = resp.get("choices", [{}])[0]
    raw = (choice.get("message", {}).get("content") or "").strip()
    finish = choice.get("finish_reason")
    usage = resp.get("usage", {})
    tin, tout = int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0))
    rtok = _reasoning_tokens(usage)
    cost = None
    if guard is not None:
        cost = round(guard.record(config.model, tin, tout,
                                  meta={"config_hash": config.config_hash,
                                        "reasoning": config.reasoning}), 6)
    parsed, ok = parse_output(raw, config.scope, config.decomposition)
    return GradeResult(score=parsed["score"], per_criterion=parsed["per_criterion"],
                       answers=parsed["answers"], parse_ok=ok, raw=raw,
                       tokens_in=tin, tokens_out=tout, latency_s=latency,
                       model=config.model, reasoning=config.reasoning,
                       config_hash=config.config_hash, reasoning_tokens=rtok,
                       finish_reason=finish, cost_eur=cost)


def grade_whole_exam(items, config, guard: CostGuard | None = None):
    """Grade ALL questions of one submission in a SINGLE call (scope=whole_exam). Returns
    (per_question, meta): per_question is [{item, score, parse_ok}] mapped back by question_id;
    meta carries the shared call's prompt/raw/tokens/cost/latency/finish_reason. The same call
    covers N questions -> the runner writes N rows tagged with call_group (the submission) so
    cost is counted once per group, while each question keeps its own score for agreement."""
    load_env()
    pricing = (guard.pricing if guard else load_pricing())
    mcfg = dict(pricing["models"][config.model])
    mcfg.setdefault("model_id", config.model)
    provider = mcfg.get("provider", "unknown")
    key = os.environ.get(mcfg["env_key"])
    prompt = prompts.render_whole_exam(config, items)

    def fail(msg):
        per = [{"item": it, "score": None, "parse_ok": False} for it in items]
        return per, {"prompt": prompt, "raw": "", "tokens_in": 0, "tokens_out": 0,
                     "reasoning_tokens": None, "latency_s": 0.0, "finish_reason": None,
                     "cost_eur": None, "error": msg}

    if not key:
        return fail(f"{mcfg['env_key']} not set")
    if guard is not None and guard.remaining_for(provider) <= 0:
        return fail(f"budget exhausted for provider {provider}")
    payload = _build_payload(mcfg, prompt, config)
    t0 = time.perf_counter()
    try:
        resp = _chat(mcfg["base_url"], key, payload)
    except urllib.error.HTTPError as e:
        return fail(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:160]}")
    except _Transient as e:
        return fail(f"transient (retries exhausted): {str(e)[:120]}")
    latency = round(time.perf_counter() - t0, 3)
    choice = resp.get("choices", [{}])[0]
    raw = (choice.get("message", {}).get("content") or "").strip()
    usage = resp.get("usage", {})
    tin, tout = int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0))
    cost = round(guard.record(config.model, tin, tout,
                              meta={"config_hash": config.config_hash, "whole_exam": True}), 6) \
        if guard is not None else None
    parsed, _ = parse_output(raw, "whole_exam", config.decomposition)
    answers = parsed.get("answers") or []
    key_field = "total" if config.decomposition == "criterion" else "score"
    by_qid = {}
    for a in answers:
        if isinstance(a, dict) and a.get("question_id") is not None:
            by_qid[str(a["question_id"])] = a.get(key_field, a.get("score"))
    per = []
    for it in items:
        sc = by_qid.get(str(it["question_id"]))
        per.append({"item": it, "score": _num_or_none(sc), "parse_ok": sc is not None})
    return per, {"prompt": prompt, "raw": raw, "tokens_in": tin, "tokens_out": tout,
                 "reasoning_tokens": _reasoning_tokens(usage), "latency_s": latency,
                 "finish_reason": choice.get("finish_reason"), "cost_eur": cost, "error": None}


def _num_or_none(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def grade_conversation(items, config, guard: CostGuard | None = None):
    """Grade `items` IN THE GIVEN ORDER inside ONE shared conversation: each turn's request
    carries the full prior history (questions + the model's own earlier grades), so position /
    anchoring can act (Phase 4.9 shared condition). Sequential by construction. Returns a list
    [{item, score, parse_ok, position, ...per-turn metrics, prompt}] -- one per item, in order."""
    load_env()
    pricing = (guard.pricing if guard else load_pricing())
    mcfg = dict(pricing["models"][config.model]); mcfg.setdefault("model_id", config.model)
    provider = mcfg.get("provider", "unknown")
    key = os.environ.get(mcfg["env_key"])
    out, messages = [], []
    for pos, it in enumerate(items):
        user = prompts.render_turn(config, it, first=(pos == 0))
        rec = {"item": it, "position": pos, "prompt": user, "score": None, "parse_ok": False,
               "tokens_in": 0, "tokens_out": 0, "reasoning_tokens": None, "latency_s": 0.0,
               "finish_reason": None, "cost_eur": None, "error": None, "raw": ""}
        if not key:
            rec["error"] = f"{mcfg['env_key']} not set"; out.append(rec); continue
        messages.append({"role": "user", "content": user})
        payload = _build_payload_msgs(mcfg, messages, config)
        t0 = time.perf_counter()
        try:
            resp = _chat(mcfg["base_url"], key, payload)
        except urllib.error.HTTPError as e:
            rec["error"] = f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:120]}"
        except _Transient as e:
            rec["error"] = f"transient (retries exhausted): {str(e)[:100]}"
        if rec["error"]:
            messages.append({"role": "assistant", "content": "{}"})   # keep the turn structure
            out.append(rec); continue
        rec["latency_s"] = round(time.perf_counter() - t0, 3)
        choice = resp.get("choices", [{}])[0]
        raw = (choice.get("message", {}).get("content") or "").strip()
        usage = resp.get("usage", {})
        tin, tout = int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0))
        if guard is not None:
            rec["cost_eur"] = round(guard.record(config.model, tin, tout,
                                    meta={"config_hash": config.config_hash, "conversation": True}), 6)
        parsed, ok = parse_output(raw, config.scope, config.decomposition)
        rec.update({"raw": raw, "tokens_in": tin, "tokens_out": tout,
                    "reasoning_tokens": _reasoning_tokens(usage),
                    "finish_reason": choice.get("finish_reason"),
                    "score": parsed["score"], "parse_ok": ok})
        messages.append({"role": "assistant", "content": raw})
        out.append(rec)
    return out


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

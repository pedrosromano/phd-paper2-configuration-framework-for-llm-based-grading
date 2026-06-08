"""Local Ollama grading adapter (Phase 3.3).

grade(item, config) -> GradeResult{score, per_criterion?, raw, tokens, latency, parse_ok}.
For local-convenience models / smoke tests; the roster runs on DeepInfra (Phase 3.4).

Reasoning toggle per family: thinking models (qwen3*, deepseek-r1, glm) take Ollama's
`think` param; for Qwen we also append `/no_think` when OFF (its think=False can leak,
seen in Phase 2.2). Non-thinking models (gemma3) ignore the toggle. Retries via tenacity.

  python -m experiments.harness.adapter_ollama         # smoke test on a real item
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from experiments.harness import prompts
from experiments.harness.grading import GradeResult
from experiments.harness.parser import parse_output

OLLAMA = "http://localhost:11434"
_THINKING_FAMILIES = ("qwen3", "qwen2.5", "deepseek-r1", "glm")


def _is_thinking(model: str) -> bool:
    m = model.lower()
    return any(f in m for f in _THINKING_FAMILIES)


@retry(stop=stop_after_attempt(4),
       wait=wait_exponential(multiplier=1, min=2, max=20),
       retry=retry_if_exception_type((urllib.error.URLError, TimeoutError, ConnectionError)),
       reraise=True)
def _call(model: str, prompt: str, think: bool, config) -> dict:
    options = {"temperature": config.temperature, "top_p": config.top_p,
               "num_predict": config.max_tokens}
    if config.seed is not None:
        options["seed"] = config.seed
    payload = {
        "model": model, "prompt": prompt, "stream": False,
        "think": think,                       # ignored by non-thinking models
        "options": options,
    }
    req = urllib.request.Request(f"{OLLAMA}/api/generate",
                                 data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read().decode("utf-8"))


def grade(item, config) -> GradeResult:
    """Grade one item with a local Ollama model (question-by-question scope)."""
    prompt = prompts.render(config, item)
    think = config.reasoning == "on"
    if config.model.lower().startswith("qwen") and not think:
        prompt += "\n/no_think"
    t0 = time.perf_counter()
    try:
        resp = _call(config.model, prompt, think, config)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ConnectionError) as e:
        return GradeResult(score=None, parse_ok=False, raw="", tokens_in=0, tokens_out=0,
                           latency_s=round(time.perf_counter() - t0, 3), model=config.model,
                           reasoning=config.reasoning, config_hash=config.config_hash,
                           error=f"{type(e).__name__}: {str(e)[:120]}")
    latency = round(time.perf_counter() - t0, 3)
    raw = resp.get("response", "") or ""
    parsed, ok = parse_output(raw, config.scope, config.decomposition)
    return GradeResult(
        score=parsed["score"], per_criterion=parsed["per_criterion"], answers=parsed["answers"],
        parse_ok=ok, raw=raw,
        tokens_in=int(resp.get("prompt_eval_count", 0)),
        tokens_out=int(resp.get("eval_count", 0)),
        latency_s=latency, model=config.model, reasoning=config.reasoning,
        config_hash=config.config_hash,
        finish_reason=resp.get("done_reason"),   # "stop" (natural) | "length" (token cap)
    )


def _smoke() -> int:
    import pandas as pd
    from pathlib import Path
    from experiments.configs.config import Config
    corpus = Path(__file__).resolve().parents[2] / "data" / "processed" / "corpus.parquet"
    df = pd.read_parquet(corpus)
    item = df[df.dataset == "mohler"].iloc[0]
    for reasoning in ("off", "on"):
        cfg = Config("mohler", "short_answer", "qwen3:30b", reasoning=reasoning,
                     context_level="with_guidance")
        r = grade(item, cfg)
        print(f"[reasoning={reasoning}] score={r.score} parse_ok={r.parse_ok} "
              f"gold={item.gold_score}/{item.gold_scale_max} "
              f"tok={r.tokens_in}+{r.tokens_out} {r.latency_s}s err={r.error}")
        print(f"   raw: {r.raw.strip()[:120]!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_smoke())

"""Verify the logged config ACTUALLY matches what was requested (not just internally
self-consistent). Catches the class the integrity audit cannot: a logged reasoning=on whose
payload sent enable_thinking=false, a row labelled qwen whose request hit deepseek, a
with_guidance row whose prompt carried no rubric, or a threading cross.

Three independent checks:
  1) STATIC payload audit (no API) -- the config->payload mapping is ONE function used by
     every call, so verifying it for all roster x {off,on} verifies it for every row:
     payload.model == pricing model_id, and the reasoning toggle == the requested value.
  2) LIVE routing probe -- send one real call per (model, reasoning) and confirm the API's
     own "model" field is the requested model and that ON spends far more tokens than OFF
     (the toggle actually took effect end-to-end).
  3) BEHAVIOURAL scan of runs.jsonl -- per-(model,reasoning) token behaviour and the stored
     prompt text must agree with the labels (no mislabelled cells / no thread crossing).

  python -m experiments.run.verify_request_mapping            # static + behavioural (no API)
  python -m experiments.run.verify_request_mapping --live     # also the live routing probe
"""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from pathlib import Path

import pandas as pd

from experiments.configs.config import Config
from experiments.harness import adapter_api
from experiments.harness.cost_guard import load_pricing
from experiments.harness.env import load_env

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS = REPO_ROOT / "data" / "processed" / "runs" / "runs.jsonl"
ROSTER = ["qwen3.5", "deepseek-v4-flash", "glm-5.1", "gpt-5.1"]
_R = []


def ck(name, ok, detail=""):
    _R.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}{('  -> ' + str(detail)) if detail else ''}")


def static_payload_audit(pricing):
    print("1) STATIC payload audit (config -> request, all roster x {off,on}):")
    for model in ROSTER:
        mcfg = dict(pricing["models"][model])
        mcfg.setdefault("model_id", model)
        rv = mcfg.get("reasoning_values", {})
        for reasoning in ("off", "on"):
            cfg = Config("mohler", "short_answer", model, reasoning=reasoning,
                         context_level="with_guidance")
            p = adapter_api._build_payload(mcfg, "PROMPT", cfg)
            # (a) the payload routes to the requested model id
            ck(f"{model:18} [{reasoning}] payload.model == {mcfg['model_id']}",
               p["model"] == mcfg["model_id"], p["model"])
            # (b) the reasoning toggle carries the requested value
            if mcfg.get("provider") == "openai":
                got = p.get(mcfg["reasoning_param"])            # reasoning_effort
                want = rv.get(reasoning)
            else:
                got = p.get("chat_template_kwargs", {}).get(mcfg["reasoning_param"])  # enable_thinking
                want = rv.get(reasoning)
            ck(f"{model:18} [{reasoning}] toggle {mcfg['reasoning_param']} == {want!r}",
               got == want, got)


def live_probe(pricing):
    print("\n2) LIVE routing probe (request -> served model + toggle effect):")
    load_env()
    import pandas as pd
    df = pd.read_parquet(REPO_ROOT / "data" / "processed" / "corpus.parquet")
    item = df[df.dataset == "mohler"].iloc[0]
    for model in ROSTER:
        mcfg = dict(pricing["models"][model]); mcfg.setdefault("model_id", model)
        key = os.environ.get(mcfg["env_key"])
        if not key:
            ck(f"{model} live", False, f"{mcfg['env_key']} not set"); continue
        toks = {}
        for reasoning in ("off", "on"):
            cfg = Config("mohler", "short_answer", model, reasoning=reasoning,
                         context_level="with_guidance")
            from experiments.harness import prompts
            payload = adapter_api._build_payload(mcfg, prompts.render(cfg, item), cfg)
            try:
                resp = adapter_api._chat(mcfg["base_url"], key, payload)
            except Exception as e:
                ck(f"{model:18} [{reasoning}] live call", False, str(e)[:60]); continue
            served = str(resp.get("model", ""))
            want = mcfg["model_id"]
            ok = served == want or served.startswith(want) or want.split("/")[-1].lower() in served.lower()
            ck(f"{model:18} [{reasoning}] served model == requested", ok, f"served={served!r} want={want!r}")
            toks[reasoning] = int(resp.get("usage", {}).get("completion_tokens", 0))
        if "off" in toks and "on" in toks:
            ck(f"{model:18} ON spends >> OFF tokens (toggle real)", toks["on"] > toks["off"] * 1.5, toks)


def behavioural_scan():
    print("\n3) BEHAVIOURAL scan of runs.jsonl (labels vs reality):")
    rows = []
    for l in RUNS.read_text().splitlines():
        if l.strip():
            try:
                rows.append(json.loads(l))
            except json.JSONDecodeError:
                pass
    df = pd.DataFrame(rows)
    ok_rows = df[df.parse_ok & df.error.isna()]
    # (a) OFF cells must be cheap (no hidden reasoning); ON cells must be expensive.
    by = defaultdict(list)
    for r in ok_rows.itertuples():
        by[(r.model, r.reasoning)].append(int(r.completion_tokens or 0))
    print("   completion-token profile by (model, reasoning) [should split off<<on]:")
    for (m, rsn) in sorted(by):
        v = pd.Series(by[(m, rsn)])
        print(f"     {m:18} {rsn:3}  n={len(v):>6}  median={v.median():.0f}  p95={v.quantile(.95):.0f}")
    # flag OFF rows that behaved like ON (toggle silently on?) and vice-versa
    off_hi = ok_rows[(ok_rows.reasoning == "off") & (ok_rows.completion_tokens > 800)]
    on_lo = ok_rows[(ok_rows.reasoning == "on") &
                    (pd.to_numeric(ok_rows.completion_tokens) < 20) &
                    (ok_rows.finish_reason == "stop")]
    ck("no OFF row behaves like ON (>800 out tok)", len(off_hi) == 0, f"{len(off_hi)} suspced")
    ck("no ON row behaves like OFF (<20 out tok, clean stop)", len(on_lo) == 0, f"{len(on_lo)} suspect")
    # (b) the stored prompt must match the context_level label (grounding present iff with_guidance)
    import re
    GRND = re.compile(r"RUBRIC|REFERENCE ANSWER|reference answer|rubric", re.I)
    wg = ok_rows[ok_rows.context_level == "with_guidance"]
    none = ok_rows[ok_rows.context_level == "none"]
    wg_missing = sum(0 if (isinstance(p, str) and GRND.search(p)) else 1 for p in wg.prompt.head(3000))
    none_has = sum(1 if (isinstance(p, str) and GRND.search(p)) else 0 for p in none.prompt.head(3000))
    ck("with_guidance prompts contain grounding (sample 3000)", wg_missing == 0, f"{wg_missing} missing")
    ck("none prompts contain NO grounding (sample 3000)", none_has == 0, f"{none_has} unexpected")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="also send real probe calls")
    args = ap.parse_args(argv)
    pricing = load_pricing()
    static_payload_audit(pricing)
    if args.live:
        live_probe(pricing)
    behavioural_scan()
    ok = all(_R)
    print(f"\n{'='*60}\nREQUEST-MAPPING: {'ALL PASS' if ok else 'FAILURES'} "
          f"({sum(_R)}/{len(_R)})\n{'='*60}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

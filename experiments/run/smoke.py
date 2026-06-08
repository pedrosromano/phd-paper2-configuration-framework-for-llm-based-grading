"""End-to-end harness smoke test (Phase 3.7).

Runs the FULL pipeline -- config (3.1) -> prompt (3.2) -> adapter (3.3/3.4) -> parser
(3.5) -> cache+log (3.6) -- over a tiny matrix and prints the run rows + a pi
extractable-rate readout. Default: 5 items x 1 cheap LOCAL model x reasoning {off,on}
x k=2 = 20 runs. Fix anything rough here before scaling (Phase 4).

  python -m experiments.run.smoke                 # local qwen3:30b on Mohler
  python -m experiments.run.smoke --model deepseek-v4-flash   # DeepInfra path
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from experiments.configs.config import LOCAL_MODELS, Config
from experiments.harness import adapter_api, adapter_ollama, store
from experiments.harness.cost_guard import CostGuard
from experiments.harness.parser import compute_pi

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS = REPO_ROOT / "data" / "processed" / "corpus.parquet"
SMOKE_RUNS = REPO_ROOT / "data" / "processed" / "runs" / "smoke.jsonl"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="qwen3:30b")
    p.add_argument("--dataset", default="mohler")
    p.add_argument("--domain", default="short_answer")
    p.add_argument("--n", type=int, default=5)
    p.add_argument("--k", type=int, default=2)
    p.add_argument("--fresh", action="store_true", help="ignore/overwrite the smoke cache")
    args = p.parse_args(argv)

    df = pd.read_parquet(CORPUS)
    items = [r for _, r in df[(df.dataset == args.dataset) &
                              (df.domain == args.domain)].head(args.n).iterrows()]
    if args.fresh and SMOKE_RUNS.exists():
        SMOKE_RUNS.unlink()
    st = store.RunStore(SMOKE_RUNS)
    guard = CostGuard()
    is_local = args.model in LOCAL_MODELS
    grade_fn = ((lambda i, c: adapter_ollama.grade(i, c)) if is_local
                else (lambda i, c: adapter_api.grade(i, c, guard)))

    print(f"Smoke: {len(items)} items x {args.model} ({'local' if is_local else 'DeepInfra/anchor'}) "
          f"x reasoning{{off,on}} x k={args.k}  = {len(items)*2*args.k} runs\n")
    rows, n_calls = [], 0
    for reasoning in ("off", "on"):
        for ri in range(args.k):
            for it in items:
                cfg = Config(args.dataset, args.domain, args.model, reasoning=reasoning,
                             context_level="with_guidance", k=args.k, run_index=ri)
                row, cached = store.run_one(it, cfg, grade_fn, st)
                rows.append(row)
                n_calls += (0 if cached else 1)
                tag = "cache" if cached else "call "
                print(f"  [{tag}] {row['item_id']:18} r={reasoning:3} ri={ri} "
                      f"score={str(row['score']):>5} ok={row['parse_ok']!s:5} "
                      f"tok={row['tokens_in']}+{row['tokens_out']} {row['latency_s']}s"
                      + (f" ERR={row['error']}" if row['error'] else ""))

    print(f"\n--- readout ({n_calls} live calls, {len(rows)-n_calls} cached) ---")
    rdf = pd.DataFrame(rows)
    for reasoning, g in rdf.groupby("reasoning"):
        pi = compute_pi(g["parse_ok"])
        scored = g[g["parse_ok"]]
        print(f"  reasoning={reasoning}: pi={pi}  (parse_ok {int(g.parse_ok.sum())}/{len(g)}) | "
              f"mean_out_tok={int(g.tokens_out.mean())} | mean_latency={g.latency_s.mean():.1f}s"
              + (f" | mean_score={scored.score.mean():.2f}" if len(scored) else ""))
    err = rdf[rdf.error.notna()]
    if len(err):
        print(f"  errors: {len(err)} -> {err.error.value_counts().head(3).to_dict()}")
    print(f"\nstore: {len(st)} rows at {SMOKE_RUNS.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

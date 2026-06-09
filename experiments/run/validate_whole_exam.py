"""Phase 4.7 validation gate: confirm whole-exam grading reliably extracts ONE score per
question from a multi-question response, BEFORE running the full scope arm.

Grades a few real PT-CS code submissions whole-exam (qwen3.5, off, with_guidance, holistic),
maps the answers back by question_id, and prints per-question parsed score vs gold + a
coverage check (did every question get a score, with the right question_id?). No rows written.

  python -m experiments.run.validate_whole_exam --n 3
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from experiments.configs.config import Config
from experiments.harness import adapter_api
from experiments.harness.cost_guard import CostGuard

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS = REPO_ROOT / "data" / "processed" / "corpus.parquet"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3, help="number of submissions to validate")
    args = ap.parse_args(argv)

    df = pd.read_parquet(CORPUS)
    pt = df[(df.dataset == "ptcs") & (df.domain == "code") & (df.submission_id.notna())]
    subs = list(pt.submission_id.drop_duplicates())[: args.n]
    cfg = Config("ptcs", "code", "qwen3.5", reasoning="off",
                 context_level="with_guidance", scope="whole_exam", decomposition="holistic")
    guard = CostGuard()
    print(f"Whole-exam validation: {len(subs)} PT-CS submissions x qwen3.5 (off, with_guidance, holistic)\n")

    tot_q, tot_ok = 0, 0
    for sid in subs:
        items = [r for _, r in pt[pt.submission_id == sid].iterrows()]
        per, meta = adapter_api.grade_whole_exam(items, cfg, guard)
        n_ok = sum(p["parse_ok"] for p in per)
        tot_q += len(per); tot_ok += n_ok
        print(f"=== submission {sid}: {len(items)} questions | parsed {n_ok}/{len(items)} | "
              f"{meta['tokens_in']}+{meta['tokens_out']} tok | {meta['latency_s']}s"
              + (f" | ERR={meta['error']}" if meta['error'] else "") + " ===")
        for p in per:
            it = p["item"]
            g = it.get("gold_score")
            print(f"   q={str(it['question_id']):>6}  pred={str(p['score']):>5}/"
                  f"{_fmt(it.get('gold_scale_max'))}   gold={_fmt(g)}   "
                  f"{'OK' if p['parse_ok'] else 'NO SCORE'}")
        if meta["error"] is None and n_ok < len(items):
            print(f"   raw (first 200): {meta['raw'][:200]!r}")
        print()

    print(f"COVERAGE: {tot_ok}/{tot_q} questions got a score "
          f"({100*tot_ok/max(tot_q,1):.0f}%).  Spend: DeepInfra €{guard.spent_for('deepinfra'):.4f}")
    print("If coverage is ~100% and question_ids line up, the whole-exam path is reliable -> run the arm.")
    return 0


def _fmt(x):
    try:
        f = float(x)
        return str(int(f)) if f == int(f) else f"{f:.2f}"
    except (TypeError, ValueError):
        return str(x)


if __name__ == "__main__":
    raise SystemExit(main())

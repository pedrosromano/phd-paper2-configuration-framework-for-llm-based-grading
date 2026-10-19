"""Re-grade error rows in place (transient failures the cache would otherwise treat as done).

The cache keys on (item_id, config_hash, run_index), so an error row counts as "done" and a
plain relaunch will NOT retry it. This finds error rows, re-grades each with the SAME config
(rebuilt from the row's own fields), and REPLACES the row -> recovers transient timeouts/429s
without disturbing any good cell. Atomic rewrite + backup. Refuses while a run is live.

  python -m experiments.run.regrade_errors            # dry-run (list error rows)
  python -m experiments.run.regrade_errors --apply
  python -m experiments.run.regrade_errors --store verification.jsonl --corpus corpus_verification.parquet \
         --workers 8 --apply                       # another store and corpus, several calls at a time
"""

from __future__ import annotations

import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from experiments.configs.config import Config
from experiments.harness import adapter_api, prompts, store
from experiments.harness.cost_guard import CostGuard

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS = REPO_ROOT / "data" / "processed" / "runs" / "runs.jsonl"
BACKUP = REPO_ROOT / "data" / "processed" / "_archive" / "runs_before_regrade.jsonl.bak"
CORPUS = REPO_ROOT / "data" / "processed" / "corpus.parquet"


def _cfg_from_row(r: dict) -> Config:
    return Config(dataset=r["dataset"], domain=r["domain"], model=r["model"],
                  reasoning=r["reasoning"], context_level=r["context_level"],
                  scope=r["scope"], decomposition=r["decomposition"],
                  conversation_state=r.get("conversation_state", "none"),
                  instruction=r.get("instruction") or "standard",
                  k=int(r.get("k", 5)), temperature=r["temperature"], top_p=r["top_p"],
                  max_tokens=r["max_tokens"], seed=r["seed"], run_index=r["run_index"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--store", default=RUNS.name, help="run store in data/processed/runs (default runs.jsonl)")
    ap.add_argument("--corpus", default=CORPUS.name, help="corpus in data/processed (default corpus.parquet)")
    ap.add_argument("--workers", type=int, default=1, help="calls at a time")
    args = ap.parse_args(argv)
    runs, corpus_path = RUNS.parent / args.store, CORPUS.parent / args.corpus
    backup = BACKUP.with_name(f"{runs.stem}_before_regrade.jsonl.bak")
    if subprocess.run(["pgrep", "-f", "experiments.run.matrix run"], capture_output=True).returncode == 0:
        print("REFUSED: a matrix run is live. Wait for it to finish.")
        return 1

    rows = [json.loads(l) for l in runs.read_text().splitlines() if l.strip()]
    err_idx = [i for i, r in enumerate(rows) if r.get("error")]
    print(f"{len(rows):,} rows | {len(err_idx)} error rows")
    for i in err_idx:
        r = rows[i]
        print(f"  {r['item_id']:18} {r['model']:18} r={r['reasoning']} mt={r['max_tokens']} "
              f"ri={r['run_index']}  err={str(r['error'])[:50]}")
    if not err_idx:
        return 0
    if not args.apply:
        print(f"\nDRY-RUN: pass --apply to re-grade these and replace them in {runs.name}.")
        return 0

    corpus = pd.read_parquet(corpus_path)
    by_id = {r["item_id"]: r for _, r in corpus.iterrows()}
    guard = CostGuard()
    backup.parent.mkdir(parents=True, exist_ok=True)
    backup.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")

    def regrade(i):
        r = rows[i]
        item = by_id[r["item_id"]]
        cfg = _cfg_from_row(r)
        assert cfg.config_hash == r["config_hash"], f"config rebuilt differently for {r['item_id']}"
        res = adapter_api.grade(item, cfg, guard)
        print(f"  re-graded {r['item_id']}: parse_ok={res.parse_ok} err={res.error} tok={res.tokens_out} "
              f"{'OK' if res.error is None and res.parse_ok else 'STILL FAILING'}", flush=True)
        return i, store.build_run_row(item, cfg, res, prompts.render(cfg, item)), res.error is None and res.parse_ok

    fixed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for i, row, ok in ex.map(regrade, err_idx):
            rows[i] = row
            fixed += ok

    tmp = runs.with_suffix(".jsonl.tmp")
    tmp.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    tmp.replace(runs)
    print(f"\nrewrote {runs.name}: {fixed}/{len(err_idx)} recovered. Backup at {backup.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

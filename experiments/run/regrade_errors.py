"""Re-grade error rows in place (transient failures the cache would otherwise treat as done).

The cache keys on (item_id, config_hash, run_index), so an error row counts as "done" and a
plain relaunch will NOT retry it. This finds error rows, re-grades each with the SAME config
(rebuilt from the row's own fields), and REPLACES the row -> recovers transient timeouts/429s
without disturbing any good cell. Atomic rewrite + backup. Refuses while a run is live.

  python -m experiments.run.regrade_errors            # dry-run (list error rows)
  python -m experiments.run.regrade_errors --apply
"""

from __future__ import annotations

import argparse
import json
import subprocess
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
                  k=int(r.get("k", 5)), temperature=r["temperature"], top_p=r["top_p"],
                  max_tokens=r["max_tokens"], seed=r["seed"], run_index=r["run_index"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)
    if subprocess.run(["pgrep", "-f", "experiments.run.matrix run"], capture_output=True).returncode == 0:
        print("REFUSED: a matrix run is live. Wait for it to finish.")
        return 1

    rows = [json.loads(l) for l in RUNS.read_text().splitlines() if l.strip()]
    err_idx = [i for i, r in enumerate(rows) if r.get("error")]
    print(f"{len(rows):,} rows | {len(err_idx)} error rows")
    for i in err_idx:
        r = rows[i]
        print(f"  {r['item_id']:18} {r['model']:18} r={r['reasoning']} mt={r['max_tokens']} "
              f"ri={r['run_index']}  err={str(r['error'])[:50]}")
    if not err_idx:
        return 0
    if not args.apply:
        print("\nDRY-RUN: pass --apply to re-grade these and replace them in runs.jsonl.")
        return 0

    corpus = pd.read_parquet(CORPUS)
    by_id = {r["item_id"]: r for _, r in corpus.iterrows()}
    guard = CostGuard()
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    BACKUP.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")

    fixed = 0
    for i in err_idx:
        r = rows[i]
        item = by_id[r["item_id"]]
        cfg = _cfg_from_row(r)
        res = adapter_api.grade(item, cfg, guard)
        rows[i] = store.build_run_row(item, cfg, res, prompts.render(cfg, item))
        ok = res.error is None and res.parse_ok
        fixed += ok
        print(f"  re-graded {r['item_id']}: parse_ok={res.parse_ok} err={res.error} "
              f"tok={res.tokens_out} {'OK' if ok else 'STILL FAILING'}")

    tmp = RUNS.with_suffix(".jsonl.tmp")
    tmp.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    tmp.replace(RUNS)
    print(f"\nrewrote runs.jsonl: {fixed}/{len(err_idx)} recovered. Backup at {BACKUP.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

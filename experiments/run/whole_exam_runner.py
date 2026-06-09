"""Phase 4.7 scope arm -- whole-exam side (PT-CS only). Grades each sampled submission in ONE
call and writes one row PER QUESTION (scope=whole_exam, call_group=submission). The q-by-q
side of the scope contrast is already in the store (the qwen3.5-off baseline cells), so only
the whole-exam side runs here. Resumable (per-question cache), cost-guarded, concurrent over
submissions.

  python -m experiments.run.whole_exam_runner            # run the arm
  python -m experiments.run.whole_exam_runner --limit 2  # tiny validation of the writer
"""

from __future__ import annotations

import argparse
import json
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace
from pathlib import Path

import pandas as pd
import yaml

from experiments.configs.config import Config
from experiments.harness import adapter_api, store
from experiments.harness.cost_guard import CostGuard
from experiments.harness.grading import GradeResult

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS = REPO_ROOT / "data" / "processed" / "corpus.parquet"
MATRIX = REPO_ROOT / "experiments" / "configs" / "matrix.yaml"
RUNS_FILE = REPO_ROOT / "data" / "processed" / "runs" / "runs.jsonl"
SEED = 20260609


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--limit", type=int, default=None, help="cap submissions (writer validation)")
    args = ap.parse_args(argv)

    spec = yaml.safe_load(MATRIX.read_text())
    n_subs = int(spec["sampling"]["whole_exam_submissions"])
    k = int(next(a for a in spec["arms"] if a["name"] == "scope_arm").get("k", 5))
    corpus = pd.read_parquet(CORPUS)
    pt = corpus[(corpus.dataset == "ptcs") & (corpus.domain == "code") & (corpus.submission_id.notna())]
    submap = {sid: [r for _, r in g.iterrows()] for sid, g in pt.groupby("submission_id")}
    subs = sorted(submap)
    random.Random(SEED).shuffle(subs)
    subs = subs[: (args.limit or n_subs)]

    cfg0 = Config("ptcs", "code", "qwen3.5", reasoning="off", context_level="with_guidance",
                  scope="whole_exam", decomposition="holistic", k=k)
    st = store.RunStore(RUNS_FILE)
    guard = CostGuard()
    chash = cfg0.config_hash
    tasks = [(sid, ri) for sid in subs for ri in range(k)]
    # skip a (submission, rep) only if EVERY question already has its row
    todo = [(sid, ri) for sid, ri in tasks
            if not all(st.has(it["item_id"], chash, ri) for it in submap[sid])]
    print(f"scope arm (whole-exam): {len(subs)} submissions x k={k} = {len(tasks)} calls | "
          f"{len(tasks)-len(todo)} cached | {len(todo)} to run @ {args.concurrency}x")

    lock = threading.Lock()
    done = {"calls": 0, "q": 0, "ok": 0}

    def work(sid, ri):
        items = submap[sid]
        cfg = replace(cfg0, run_index=ri)
        per, meta = adapter_api.grade_whole_exam(items, cfg, guard)
        with lock:
            for p in per:
                res = GradeResult(score=p["score"], parse_ok=p["parse_ok"], raw=meta["raw"],
                                  tokens_in=meta["tokens_in"], tokens_out=meta["tokens_out"],
                                  latency_s=meta["latency_s"], model=cfg.model, reasoning=cfg.reasoning,
                                  config_hash=cfg.config_hash, reasoning_tokens=meta["reasoning_tokens"],
                                  finish_reason=meta["finish_reason"], cost_eur=meta["cost_eur"],
                                  error=meta["error"])
                st.append(store.build_run_row(p["item"], cfg, res, meta["prompt"], call_group=str(sid)))
                done["q"] += 1
                done["ok"] += int(bool(p["parse_ok"]))
            done["calls"] += 1
            if done["calls"] % 50 == 0:
                print(f"  ... {done['calls']}/{len(todo)} calls | {done['q']} q rows | "
                      f"pi={done['ok']/max(done['q'],1):.3f} | DeepInfra €{guard.spent_for('deepinfra'):.2f}",
                      flush=True)

    if todo:
        with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
            futs = [ex.submit(work, sid, ri) for sid, ri in todo]
            for f in as_completed(futs):
                f.result()
    print(f"DONE. {done['calls']} calls, {done['q']} question-rows, "
          f"pi={done['ok']/max(done['q'],1):.3f} | DeepInfra €{guard.spent_for('deepinfra'):.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

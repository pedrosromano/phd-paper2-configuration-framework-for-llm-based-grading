"""Phase 4.9 conversation-state sub-study (PT-CS code). Standalone study (CLAUDE.md §6).

Per (model, submission, k): three passes --
  * clean        : each question graded independently (no history) -- the reference.
  * shared/natural: ONE conversation, questions in ascending question_id order.
  * shared/inverse: ONE conversation, questions in descending order.
The same question thus appears at a DIFFERENT position in natural vs inverse shared runs ->
isolates the position/anchoring effect cleanly (fixed orders, user 2026-06-09). Two models:
qwen3.5 (RQ1 continuity) and glm-5.1 (better code discrimination -> the order effect is more
likely detectable if it exists; qwen's 0-collapse may mask it -- §11).

SEQUENTIAL within a session (the conversation is inherently ordered); PARALLEL only across
sessions. Writes to its OWN conversation.jsonl (key includes order_id, so shared/natural and
shared/inverse don't collide). Resumable, cost-guarded.

  python -m experiments.run.conversation_runner --limit 1   # validation (1 submission)
  python -m experiments.run.conversation_runner             # full sub-study
"""

from __future__ import annotations

import argparse
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace
from pathlib import Path

import pandas as pd
import yaml

from experiments.configs.config import Config
from experiments.harness import adapter_api, prompts, store
from experiments.harness.cost_guard import CostGuard
from experiments.harness.grading import GradeResult

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS = REPO_ROOT / "data" / "processed" / "corpus.parquet"
MATRIX = REPO_ROOT / "experiments" / "configs" / "matrix.yaml"
CONV_FILE = REPO_ROOT / "data" / "processed" / "runs" / "conversation.jsonl"
MODELS = ["qwen3.5", "glm-5.1"]
PASSES = [("clean", "natural"), ("shared", "natural"), ("shared", "inverse")]
SEED = 20260609


def _qkey(it):
    try:
        return int(it["question_id"])
    except (TypeError, ValueError):
        return str(it["question_id"])


def _res_from(rec, cfg):
    return GradeResult(score=rec["score"], parse_ok=rec["parse_ok"], raw=rec["raw"],
                       tokens_in=rec["tokens_in"], tokens_out=rec["tokens_out"],
                       latency_s=rec["latency_s"], model=cfg.model, reasoning=cfg.reasoning,
                       config_hash=cfg.config_hash, reasoning_tokens=rec["reasoning_tokens"],
                       finish_reason=rec["finish_reason"], cost_eur=rec["cost_eur"], error=rec["error"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--limit", type=int, default=None, help="cap submissions (validation)")
    args = ap.parse_args(argv)

    spec = yaml.safe_load(MATRIX.read_text())
    n_subs = int(spec["sampling"]["conversation_submissions"])
    k = int(next(a for a in spec["arms"] if a["name"] == "conversation_substudy").get("k", 3))
    corpus = pd.read_parquet(CORPUS)
    pt = corpus[(corpus.dataset == "ptcs") & (corpus.domain == "code") & (corpus.submission_id.notna())]
    submap = {sid: sorted([r for _, r in g.iterrows()], key=_qkey) for sid, g in pt.groupby("submission_id")}
    import random
    subs = sorted(submap)
    random.Random(SEED).shuffle(subs)
    subs = subs[: (args.limit or n_subs)]

    seen: set = set()
    if CONV_FILE.exists():
        for l in CONV_FILE.read_text().splitlines():
            if l.strip():
                try:
                    r = json.loads(l)
                    seen.add((r["item_id"], r["config_hash"], r["run_index"], r.get("order_id")))
                except json.JSONDecodeError:
                    pass
    guard = CostGuard()
    lock = threading.Lock()
    CONV_FILE.parent.mkdir(parents=True, exist_ok=True)
    fh = CONV_FILE.open("a", encoding="utf-8")
    done = {"sessions": 0, "rows": 0, "ok": 0}

    # one work unit = one session (model, submission, k, conversation_state, order)
    units = [(m, sid, ri, cs, od) for m in MODELS for sid in subs
             for ri in range(k) for (cs, od) in PASSES]

    def write(row):
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        done["rows"] += 1
        done["ok"] += int(bool(row["parse_ok"]))

    def run_session(m, sid, ri, cstate, order):
        items = submap[sid]
        if order == "inverse":
            items = list(reversed(items))
        cfg = Config("ptcs", "code", m, reasoning="off", context_level="with_guidance",
                     scope="question_by_question", decomposition="holistic",
                     conversation_state=cstate, k=k, run_index=ri)
        sess = f"{m}|{sid}|{cstate}|{order}|k{ri}"
        if all((str(it["item_id"]), cfg.config_hash, ri, order) in seen for it in items):
            return
        rows = []
        if cstate == "clean":
            for pos, it in enumerate(items):
                res = adapter_api.grade(it, cfg, guard)
                rows.append(store.build_run_row(it, cfg, res, prompts.render(cfg, it),
                            session_id=sess, order_id=order, order_index=pos))
        else:
            for rec in adapter_api.grade_conversation(items, cfg, guard):
                rows.append(store.build_run_row(rec["item"], cfg, _res_from(rec, cfg), rec["prompt"],
                            session_id=sess, order_id=order, order_index=rec["position"]))
        with lock:
            for row in rows:
                write(row)
            done["sessions"] += 1
            if done["sessions"] % 30 == 0:
                print(f"  ... {done['sessions']}/{len(units)} sessions | {done['rows']} rows | "
                      f"pi={done['ok']/max(done['rows'],1):.3f} | DeepInfra €{guard.spent_for('deepinfra'):.2f}",
                      flush=True)

    print(f"conversation sub-study: {len(MODELS)} models x {len(subs)} subs x k={k} x "
          f"{len(PASSES)} passes = {len(units)} sessions @ {args.concurrency}x\n")
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = [ex.submit(run_session, *u) for u in units]
        for f in as_completed(futs):
            f.result()
    fh.close()
    print(f"DONE. {done['sessions']} sessions run, {done['rows']} rows, "
          f"pi={done['ok']/max(done['rows'],1):.3f} | DeepInfra €{guard.spent_for('deepinfra'):.2f} | -> {CONV_FILE.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

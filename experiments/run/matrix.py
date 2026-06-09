"""Phase 4 matrix runner + cost estimator (`make run ARGS=...`).

  python -m experiments.run.matrix estimate      # 4.1: print per-arm and total € -- NO calls
  python -m experiments.run.matrix estimate --arm reasoning_arm
  python -m experiments.run.matrix run --arm baseline   # 4.2+: execute (cost-guarded, resumable)

`estimate` expands the pruned matrix (experiments/configs/matrix.yaml), multiplies each
config cell by its sampled item count and per-call token assumptions, and reports the €
per arm (DeepInfra + OpenAI separately) plus the DEDUPED grand total -- cells shared
between arms run once via the (config_hash, run_index) cache, so the deduped figure is the
real spend. It makes NO API calls; it is the pre-flight the user confirms before any run.
"""

from __future__ import annotations

import argparse
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

from experiments.configs.config import expand_arm
from experiments.harness import adapter_api, prompts, store
from experiments.harness.cost_guard import CostGuard

REPO_ROOT = Path(__file__).resolve().parents[2]
MATRIX = REPO_ROOT / "experiments" / "configs" / "matrix.yaml"
CORPUS = REPO_ROOT / "data" / "processed" / "corpus.parquet"
RUNS_FILE = REPO_ROOT / "data" / "processed" / "runs" / "runs.jsonl"
REPORT_FILE = REPO_ROOT / "data" / "processed" / "runs" / "_run_report.md"

# The 6 core arms run unattended overnight; whole-exam (scope) + conversation need extra
# harness wiring + an open §11 decision, so they are NOT in the core set (run later).
CORE_ARMS = ["baseline", "nonreasoning_main", "reasoning_arm",
             "context_arm", "decomposition_arm", "anchor_reduced"]
# Automated 4.4 gate: run these first, checkpoint health, only then the expensive rest.
GATE_PHASE1 = ["baseline", "nonreasoning_main"]
GATE_PHASE2 = ["reasoning_arm", "context_arm", "decomposition_arm", "anchor_reduced"]
GATE_MIN_PI = 0.85            # abort the expensive arms if parse-rate falls below this
DEFAULT_SEED = 20260609      # deterministic item sampling (stable across resume)


# --------------------------------------------------------------------------- sampling model
class Sampler:
    """Turns a Config into (n_items, input_tok, output_tok) using matrix.yaml + corpus counts."""

    def __init__(self, spec: dict, corpus: pd.DataFrame):
        self.s = spec["sampling"]
        self.tok = spec["tokens"]
        self.spec_latency = spec["latency_s"]
        self.avail = corpus.groupby(["dataset", "domain"]).size().to_dict()
        ptcs = corpus[corpus.dataset == "ptcs"]
        self.n_submissions = ptcs.submission_id.nunique()
        # code items contained in the first N PT-CS submissions (for the conversation sub-study)
        code = ptcs[ptcs.domain == "code"]
        subs = sorted(code.submission_id.dropna().unique())[: self.s["conversation_submissions"]]
        self.conv_items = int(code[code.submission_id.isin(subs)].shape[0])

    def n_items(self, c, item_cap: int | None = None) -> int:
        if c.conversation_state in ("clean", "shared"):
            n = self.conv_items * self.s["conversation_orders"]
        elif c.scope == "whole_exam":
            n = min(self.s["whole_exam_submissions"], self.n_submissions)
        else:
            avail = self.avail.get((c.dataset, c.domain), 0)
            n = min(self.s["question_by_question"].get(f"{c.dataset}:{c.domain}", 0), avail)
            if c.reasoning == "on":
                n = min(n, self.s["reasoning_on_subsample"])
        return min(n, item_cap) if item_cap else n

    def latency_s(self, c) -> float:
        lat = self.spec_latency
        if c.scope == "whole_exam":
            return lat["whole_exam_on" if c.reasoning == "on" else "whole_exam_off"]
        return lat["on" if c.reasoning == "on" else "off"]

    def tokens(self, c) -> tuple[int, int]:
        key = f"{c.domain}|{c.scope}|{c.decomposition}|{c.reasoning}"
        tin, tout = self.tok[key]
        if c.conversation_state == "shared":          # accumulating history inflates input
            tin = int(tin * self.s.get("conversation_shared_input_factor", 4))
        return tin, tout


# --------------------------------------------------------------------------- estimation
def estimate(arm_filter: str | None = None) -> int:
    spec = yaml.safe_load(MATRIX.read_text())
    corpus = pd.read_parquet(CORPUS)
    sampler = Sampler(spec, corpus)
    guard = CostGuard()

    concurrency = int(spec.get("concurrency", 8))
    seen: set[tuple[str, int]] = set()                 # (config_hash, run_index) -> dedup global spend
    totals = {"deepinfra": {"calls": 0, "eur": 0.0, "sec": 0.0},
              "openai": {"calls": 0, "eur": 0.0, "sec": 0.0}}
    print(f"{'arm':<22} {'provider':<10} {'cells':>6} {'calls':>9} {'est €':>9} {'wall':>8}")
    print("-" * 70)

    for arm in spec["arms"]:
        if arm_filter and arm["name"] != arm_filter:
            continue
        cap = arm.get("item_cap")
        configs = expand_arm(arm)
        per_prov: dict[str, dict] = {}
        for c in configs:
            prov = guard.provider_of(c.model)
            n = sampler.n_items(c, cap)
            tin, tout = sampler.tokens(c)
            eur = guard.cost_eur(c.model, tin * n, tout * n)
            sec = n * sampler.latency_s(c)
            p = per_prov.setdefault(prov, {"cells": 0, "calls": 0, "eur": 0.0, "sec": 0.0})
            p["cells"] += 1; p["calls"] += n; p["eur"] += eur; p["sec"] += sec
            key = (c.config_hash, c.run_index)
            if key not in seen:                        # count toward real spend once
                seen.add(key)
                t = totals.setdefault(prov, {"calls": 0, "eur": 0.0, "sec": 0.0})
                t["calls"] += n; t["eur"] += eur; t["sec"] += sec
        for prov, p in sorted(per_prov.items()):
            print(f"{arm['name']:<22} {prov:<10} {p['cells']:>6} {p['calls']:>9,} {p['eur']:>8.2f} "
                  f"{_hms(p['sec'] / concurrency):>8}")

    print("-" * 70)
    print(f"DEDUPED GRAND TOTAL (real spend; shared cells run once via cache; wall @ {concurrency}x parallel):")
    for prov in ("deepinfra", "openai"):
        t = totals.get(prov, {"calls": 0, "eur": 0.0, "sec": 0.0})
        ceil = guard.ceiling_for(prov)
        spent = guard.spent_for(prov)
        proj = spent + t["eur"]
        flag = "  <-- OVER CEILING" if proj > ceil else ""
        print(f"  {prov:<10} {t['calls']:>9,} calls  €{t['eur']:>7.2f}  ~{_hms(t['sec'] / concurrency):>8}  "
              f"(spent €{spent:.2f}; projected €{proj:.2f} / €{ceil:.0f}){flag}")
    print("\nNO calls were made. Confirm these arms/N before `run`.")
    return 0


def _hms(sec: float) -> str:
    h, rem = divmod(int(sec), 3600)
    m, s = divmod(rem, 60)
    return f"{h}h{m:02d}m" if h else f"{m}m{s:02d}s"


# --------------------------------------------------------------------------- run (4.2+)
def _log(msg: str) -> None:
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {msg}", flush=True)


def _arm_tasks(arm: dict, sampler: Sampler, by_id: dict, seed: int, order_cache: dict) -> list[tuple]:
    """Expand one arm into (item_row, config) tasks. Items are a deterministic seeded sample
    per (dataset,domain); the ON/anchor caps take a PREFIX of the same order, so the sampled
    sets nest (anchor60 ⊂ on175 ⊂ offN) -> reasoning/anchor contrasts are properly paired.
    Whole-exam / conversation configs are skipped (not core)."""
    cap = arm.get("item_cap")
    tasks = []
    for c in expand_arm(arm):
        if c.scope == "whole_exam" or c.conversation_state in ("clean", "shared"):
            continue
        key = (c.dataset, c.domain)
        if key not in order_cache:
            ids = [i for i in by_id if by_id[i]["dataset"] == c.dataset and by_id[i]["domain"] == c.domain]
            random.Random(f"{seed}:{c.dataset}:{c.domain}").shuffle(ids)
            order_cache[key] = ids
        n = sampler.n_items(c, cap)
        for iid in order_cache[key][:n]:
            tasks.append((by_id[iid], c))
    return tasks


def _execute(tasks: list[tuple], st: store.RunStore, guard: CostGuard, concurrency: int) -> list[dict]:
    """Grade all uncached tasks concurrently; append rows under a lock. Errors come back as
    rows (adapter returns an error GradeResult, never raises) so π/counts stay correct."""
    # dedup within this run + drop already-cached cells (resume-safe)
    seen, todo = set(), []
    for it, c in tasks:
        k = (str(it["item_id"]), c.config_hash, c.run_index)
        if k in seen or st.has(it["item_id"], c.config_hash, c.run_index):
            continue
        seen.add(k)
        todo.append((it, c))
    total, cached = len(tasks), len(tasks) - len(todo)
    _log(f"  {total:,} cells | {cached:,} cached/skip | {len(todo):,} to run @ {concurrency}x")
    lock = threading.Lock()
    done = {"n": 0, "ok": 0}
    rows: list[dict] = []

    def work(it, c):
        res = adapter_api.grade(it, c, guard)
        row = store.build_run_row(it, c, res, prompts.render(c, it))
        with lock:
            st.append(row)
            done["n"] += 1
            done["ok"] += int(bool(row["parse_ok"]))
            if done["n"] % 250 == 0:
                pi = done["ok"] / done["n"]
                _log(f"  ... {done['n']:,}/{len(todo):,}  π={pi:.3f}  "
                     f"DeepInfra €{guard.spent_for('deepinfra'):.2f} | OpenAI €{guard.spent_for('openai'):.2f}")
        return row

    if todo:
        with ThreadPoolExecutor(max_workers=concurrency) as ex:
            futs = [ex.submit(work, it, c) for it, c in todo]
            for f in as_completed(futs):
                rows.append(f.result())
    return rows


def _gate_ok(st: store.RunStore, tasks: list[tuple]) -> tuple[bool, dict]:
    """Automated 4.4 gate over phase-1 tasks (cached + fresh): healthy parse-rate and
    non-degenerate scores before committing to the expensive arms."""
    rws = [st.get(it["item_id"], c.config_hash, c.run_index) for it, c in tasks]
    rws = [r for r in rws if r is not None]
    n = len(rws)
    if not n:
        return False, {"note": "no phase-1 rows"}
    pi = sum(bool(r["parse_ok"]) for r in rws) / n
    scores = [r["score"] for r in rws if r["parse_ok"] and r["score"] is not None]
    degenerate = len(set(scores)) <= 1
    ok = pi >= GATE_MIN_PI and len(scores) / n >= GATE_MIN_PI and not degenerate
    return ok, {"n": n, "pi": round(pi, 4), "scored_frac": round(len(scores) / n, 4),
                "distinct_scores": len(set(scores)), "degenerate": degenerate}


def _preflight(spec, sampler, guard) -> bool:
    """Refuse to start if a provider's projected spend would breach its ceiling."""
    prov_eur = {}
    for arm in spec["arms"]:
        if arm["name"] not in CORE_ARMS:
            continue
        cap = arm.get("item_cap")
        for c in expand_arm(arm):
            if c.scope == "whole_exam" or c.conversation_state in ("clean", "shared"):
                continue
            prov = guard.provider_of(c.model)
            n = sampler.n_items(c, cap)
            tin, tout = sampler.tokens(c)
            prov_eur[prov] = prov_eur.get(prov, 0.0) + guard.cost_eur(c.model, tin * n, tout * n)
    ok = True
    for prov, eur in sorted(prov_eur.items()):
        proj = guard.spent_for(prov) + eur
        ceil = guard.ceiling_for(prov)
        flag = "" if proj <= ceil else "  <-- OVER CEILING, refusing"
        _log(f"  preflight {prov}: ~€{eur:.2f}, projected €{proj:.2f} / €{ceil:.0f}{flag}")
        ok = ok and proj <= ceil
    return ok


def _report(arm_rows: dict, gate: dict, guard: CostGuard, aborted: bool, t0: float) -> str:
    lines = [f"# Phase 4 run report ({datetime.now(timezone.utc).isoformat(timespec='seconds')})", ""]
    lines.append(f"- wall time: {_hms(time.time() - t0)}")
    lines.append(f"- spend: DeepInfra €{guard.spent_for('deepinfra'):.2f} / €{guard.ceiling_for('deepinfra'):.0f}"
                 f"  |  OpenAI €{guard.spent_for('openai'):.2f} / €{guard.ceiling_for('openai'):.0f}")
    lines.append(f"- automated 4.4 gate: {gate}")
    if aborted:
        lines.append("- **ABORTED at the gate — expensive arms (phase 2) did NOT run.**")
    lines += ["", "| arm | cells | π | mean_score | n_errors |", "|---|---:|---:|---:|---:|"]
    for arm, rws in arm_rows.items():
        if not rws:
            lines.append(f"| {arm} | 0 | - | - | - |")
            continue
        n = len(rws)
        pi = sum(bool(r["parse_ok"]) for r in rws) / n
        sc = [r["score"] for r in rws if r["parse_ok"] and r["score"] is not None]
        ms = round(sum(sc) / len(sc), 3) if sc else None
        ne = sum(1 for r in rws if r["error"])
        lines.append(f"| {arm} | {n:,} | {pi:.3f} | {ms} | {ne} |")
    return "\n".join(lines)


def run(arm_filter: str | None, concurrency: int = 16, seed: int = DEFAULT_SEED,
        limit: int | None = None) -> int:
    spec = yaml.safe_load(MATRIX.read_text())
    corpus = pd.read_parquet(CORPUS)
    sampler = Sampler(spec, corpus)
    guard = CostGuard()
    st = store.RunStore(RUNS_FILE)
    by_id = {r["item_id"]: r for _, r in corpus.iterrows()}
    arm_by_name = {a["name"]: a for a in spec["arms"]}
    order_cache: dict = {}
    t0 = time.time()

    _log(f"Phase 4 run | seed={seed} | concurrency={concurrency} | store={RUNS_FILE.name}")
    if not _preflight(spec, sampler, guard):
        _log("REFUSED: a provider would breach its ceiling. Adjust matrix.yaml and retry.")
        return 1

    phase1 = arm_filter and [arm_filter] or GATE_PHASE1
    phase2 = [] if arm_filter else GATE_PHASE2
    if arm_filter and arm_filter not in CORE_ARMS:
        _log(f"REFUSED: '{arm_filter}' is not a core arm ({CORE_ARMS}).")
        return 1

    arm_rows: dict = {}
    p1_tasks_all: list[tuple] = []
    for name in phase1:
        _log(f"ARM {name} (phase 1)")
        tasks = _arm_tasks(arm_by_name[name], sampler, by_id, seed, order_cache)
        if limit:
            tasks = tasks[:limit]
        _execute(tasks, st, guard, concurrency)
        p1_tasks_all += tasks
        arm_rows[name] = [st.get(it["item_id"], c.config_hash, c.run_index) for it, c in tasks]

    gate_ok, gate = (True, {"skipped": "single-arm run"})
    if phase2:
        gate_ok, gate = _gate_ok(st, p1_tasks_all)
        _log(f"AUTOMATED 4.4 GATE: {'PASS' if gate_ok else 'FAIL'} {gate}")
        if not gate_ok:
            REPORT_FILE.write_text(_report(arm_rows, gate, guard, aborted=True, t0=t0))
            _log(f"Gate FAILED -> stopped before expensive arms. Report: {REPORT_FILE.name}")
            return 2
        for name in phase2:
            _log(f"ARM {name} (phase 2)")
            tasks = _arm_tasks(arm_by_name[name], sampler, by_id, seed, order_cache)
            if limit:
                tasks = tasks[:limit]
            _execute(tasks, st, guard, concurrency)
            arm_rows[name] = [st.get(it["item_id"], c.config_hash, c.run_index) for it, c in tasks]

    REPORT_FILE.write_text(_report(arm_rows, gate, guard, aborted=False, t0=t0))
    _log(f"DONE in {_hms(time.time() - t0)}. Report: {REPORT_FILE.name}")
    _log(f"Spend: DeepInfra €{guard.spent_for('deepinfra'):.2f} | OpenAI €{guard.spent_for('openai'):.2f}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["estimate", "run"], nargs="?", default="estimate")
    ap.add_argument("--arm", default=None, help="limit to one arm by name")
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--limit", type=int, default=None, help="cap tasks/arm (runner validation only)")
    args = ap.parse_args(argv)
    if args.cmd == "estimate":
        return estimate(args.arm)
    return run(args.arm, args.concurrency, args.seed, args.limit)


if __name__ == "__main__":
    raise SystemExit(main())

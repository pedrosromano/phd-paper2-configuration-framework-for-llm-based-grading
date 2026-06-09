"""Completeness + cost audit of a Phase 4 run (READ-ONLY; safe while a run is live).

Answers "did every expected cell actually get its runs, or are there holes?" by
reconstructing the EXACT expected (item_id, config_hash, run_index) set the runner
schedules -- same matrix, same seeded sampling, same caps -- and diffing it against the
rows in runs.jsonl. Reports, in gate-4.4 order (baseline+non-reasoning first, then the
expensive arms): expected vs obtained per cell, error rows with cause, real € vs estimate
per arm, and latency outliers. Nothing is written; no model is called.

  python -m experiments.run.audit
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from experiments.configs.config import expand_arm
from experiments.harness.cost_guard import CostGuard
from experiments.run.matrix import (CORE_ARMS, CORPUS, DEFAULT_SEED, GATE_PHASE1,
                                     GATE_PHASE2, MATRIX, RUNS_FILE, Sampler, _arm_tasks)

import yaml


def _expected(spec, sampler, by_id, seed):
    """{config_hash: {info, run_indices, item_ids}} for every core-arm cell, plus the
    arm each cell first appears in (gate order) and per-key (item,hash,ri) expectation."""
    order_cache: dict = {}
    cells: dict = {}
    keys: set = set()
    arm_of: dict = {}
    for name in GATE_PHASE1 + GATE_PHASE2:
        arm = next(a for a in spec["arms"] if a["name"] == name)
        for it, c in _arm_tasks(arm, sampler, by_id, seed, order_cache):
            ch = c.config_hash
            arm_of.setdefault(ch, name)
            cell = cells.setdefault(ch, {"info": _info(c), "n_items": set(), "ris": set()})
            cell["n_items"].add(str(it["item_id"]))
            cell["ris"].add(c.run_index)
            keys.add((str(it["item_id"]), ch, c.run_index))
    return cells, keys, arm_of


def _info(c) -> str:
    return (f"{c.dataset}:{c.domain} {c.model} r={c.reasoning} ctx={c.context_level} "
            f"{c.scope}/{c.decomposition}")


def main(argv=None) -> int:
    spec = yaml.safe_load(MATRIX.read_text())
    corpus = pd.read_parquet(CORPUS)
    sampler = Sampler(spec, corpus)
    by_id = {r["item_id"]: r for _, r in corpus.iterrows()}
    cells, exp_keys, arm_of = _expected(spec, sampler, by_id, DEFAULT_SEED)

    rows = []
    if RUNS_FILE.exists():
        for l in RUNS_FILE.read_text().splitlines():
            if not l.strip():
                continue
            try:                                  # tolerate a partial trailing line (live append)
                rows.append(json.loads(l))
            except json.JSONDecodeError:
                pass
    df = pd.DataFrame(rows)
    obt_keys, ok_keys, err_rows = set(), set(), []
    if len(df):
        for r in rows:
            k = (str(r["item_id"]), r["config_hash"], r["run_index"])
            obt_keys.add(k)
            if r.get("parse_ok"):
                ok_keys.add(k)
            if r.get("error"):
                err_rows.append(r)

    # only audit keys we EXPECT from the core matrix (ignore stray smoke/other rows)
    exp_obt = exp_keys & obt_keys
    missing = exp_keys - obt_keys
    print(f"COMPLETENESS AUDIT  (expected core cells, gate-4.4 order)\n")
    print(f"  expected (item,cell,run): {len(exp_keys):,}")
    print(f"  obtained:                 {len(exp_obt):,}")
    print(f"  parse_ok:                 {len(exp_keys & ok_keys):,}")
    print(f"  MISSING (no row at all):  {len(missing):,}")
    print(f"  error rows (logged):      {sum(1 for r in err_rows if (str(r['item_id']),r['config_hash'],r['run_index']) in exp_keys):,}\n")

    # per-arm breakdown in gate order
    print(f"  {'arm':<22} {'cells':>6} {'expected':>9} {'obtained':>9} {'ok':>9} {'missing':>8}")
    by_arm: dict = {}
    for ch, cell in cells.items():
        a = arm_of[ch]
        exp_n = len(cell["n_items"]) * len(cell["ris"])
        ob = sum(1 for iid in cell["n_items"] for ri in cell["ris"] if (iid, ch, ri) in obt_keys)
        okn = sum(1 for iid in cell["n_items"] for ri in cell["ris"] if (iid, ch, ri) in ok_keys)
        d = by_arm.setdefault(a, {"cells": 0, "exp": 0, "obt": 0, "ok": 0})
        d["cells"] += 1; d["exp"] += exp_n; d["obt"] += ob; d["ok"] += okn
    for name in GATE_PHASE1 + GATE_PHASE2:
        d = by_arm.get(name)
        if not d:
            print(f"  {name:<22} {'(not started)':>34}")
            continue
        miss = d["exp"] - d["obt"]
        flag = "  <-- INCOMPLETE" if miss else ""
        print(f"  {name:<22} {d['cells']:>6} {d['exp']:>9,} {d['obt']:>9,} {d['ok']:>9,} {miss:>8,}{flag}")

    # error causes
    if err_rows:
        ce = pd.Series([str(r["error"])[:45] for r in err_rows]).value_counts()
        print("\n  ERROR-ROW causes:")
        for cause, n in ce.head(10).items():
            print(f"    {n:>5}  {cause}")

    # real € per arm vs estimate-providers, latency outliers
    if len(df):
        df["cost"] = pd.to_numeric(df.get("cost_eur"), errors="coerce")
        lat = pd.to_numeric(df["latency_s"], errors="coerce")
        q1, q3 = lat.quantile(0.25), lat.quantile(0.75)
        thr = max(120.0, q3 + 3 * (q3 - q1))
        out = df[lat > thr]
        print(f"\n  real spend: DeepInfra €{df[df.provider=='deepinfra']['cost'].sum():.2f}  "
              f"OpenAI €{df[df.provider=='openai']['cost'].sum():.2f}")
        print(f"  latency: median={lat.median():.2f}s p95={lat.quantile(0.95):.2f}s "
              f"max={lat.max():.2f}s | infra outliers (>{thr:.0f}s): {len(out)}")
        if len(out):
            print("    " + ", ".join(f"{r.item_id}({r.latency_s:.0f}s)" for r in out.head(8).itertuples()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

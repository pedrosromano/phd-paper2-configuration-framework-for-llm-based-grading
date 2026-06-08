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
from pathlib import Path

import pandas as pd
import yaml

from experiments.configs.config import expand_arm
from experiments.harness.cost_guard import CostGuard

REPO_ROOT = Path(__file__).resolve().parents[2]
MATRIX = REPO_ROOT / "experiments" / "configs" / "matrix.yaml"
CORPUS = REPO_ROOT / "data" / "processed" / "corpus.parquet"


# --------------------------------------------------------------------------- sampling model
class Sampler:
    """Turns a Config into (n_items, input_tok, output_tok) using matrix.yaml + corpus counts."""

    def __init__(self, spec: dict, corpus: pd.DataFrame):
        self.s = spec["sampling"]
        self.tok = spec["tokens"]
        self.avail = corpus.groupby(["dataset", "domain"]).size().to_dict()
        ptcs = corpus[corpus.dataset == "ptcs"]
        self.n_submissions = ptcs.submission_id.nunique()
        # code items contained in the first N PT-CS submissions (for the conversation sub-study)
        code = ptcs[ptcs.domain == "code"]
        subs = sorted(code.submission_id.dropna().unique())[: self.s["conversation_submissions"]]
        self.conv_items = int(code[code.submission_id.isin(subs)].shape[0])

    def n_items(self, c) -> int:
        if c.conversation_state in ("clean", "shared"):
            return self.conv_items * self.s["conversation_orders"]
        if c.scope == "whole_exam":
            return min(self.s["whole_exam_submissions"], self.n_submissions)
        avail = self.avail.get((c.dataset, c.domain), 0)
        n = min(self.s["question_by_question"].get(f"{c.dataset}:{c.domain}", 0), avail)
        if c.reasoning == "on":
            n = min(n, self.s["reasoning_on_subsample"])
        return n

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

    seen: set[tuple[str, int]] = set()                 # (config_hash, run_index) -> dedup global spend
    totals = {"deepinfra": {"calls": 0, "eur": 0.0}, "openai": {"calls": 0, "eur": 0.0}}
    print(f"{'arm':<22} {'provider':<10} {'cells':>6} {'calls':>9} {'est €':>9}")
    print("-" * 62)

    for arm in spec["arms"]:
        if arm_filter and arm["name"] != arm_filter:
            continue
        configs = expand_arm(arm)
        per_prov: dict[str, dict] = {}
        for c in configs:
            prov = guard.provider_of(c.model)
            n = sampler.n_items(c)
            tin, tout = sampler.tokens(c)
            eur = guard.cost_eur(c.model, tin * n, tout * n)
            p = per_prov.setdefault(prov, {"cells": 0, "calls": 0, "eur": 0.0})
            p["cells"] += 1
            p["calls"] += n
            p["eur"] += eur
            key = (c.config_hash, c.run_index)
            if key not in seen:                        # count toward real spend once
                seen.add(key)
                totals.setdefault(prov, {"calls": 0, "eur": 0.0})
                totals[prov]["calls"] += n
                totals[prov]["eur"] += eur
        for prov, p in sorted(per_prov.items()):
            print(f"{arm['name']:<22} {prov:<10} {p['cells']:>6} {p['calls']:>9,} {p['eur']:>8.2f}")

    print("-" * 62)
    print("DEDUPED GRAND TOTAL (real spend; shared cells run once via cache):")
    for prov in ("deepinfra", "openai"):
        t = totals.get(prov, {"calls": 0, "eur": 0.0})
        ceil = guard.ceiling_for(prov)
        spent = guard.spent_for(prov)
        proj = spent + t["eur"]
        flag = "  <-- OVER CEILING" if proj > ceil else ""
        print(f"  {prov:<10} {t['calls']:>9,} calls  €{t['eur']:>7.2f}   "
              f"(already spent €{spent:.2f}; projected €{proj:.2f} / €{ceil:.0f}){flag}")
    print("\nNO calls were made. Confirm these arms/N before `run`.")
    return 0


# --------------------------------------------------------------------------- run (4.2+)
def run(arm_filter: str | None) -> int:
    print("[run] guarded execution is wired at Phase 4.2 (after the 4.1 estimate is confirmed).")
    print("      Re-run `estimate` and get sign-off first.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["estimate", "run"], nargs="?", default="estimate")
    ap.add_argument("--arm", default=None, help="limit to one arm by name")
    args = ap.parse_args(argv)
    return estimate(args.arm) if args.cmd == "estimate" else run(args.arm)


if __name__ == "__main__":
    raise SystemExit(main())

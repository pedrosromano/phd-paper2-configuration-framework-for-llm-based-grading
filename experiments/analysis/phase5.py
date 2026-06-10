"""Phase 5 analysis foundation -- the §5.0 conventions + 5.1 aggregate (PHASES.md).

Everything downstream (5.2-5.8) builds on the transforms here, so the corrections from the
Phase-4 full-data review live in ONE place: clamp [0,max], normalise (never pool raw scales),
K=5 QWK binning on the normalised score, SemEval fixed-0.5 threshold + per-split + AUROC,
whole-exam cost dedupe by call_group, and the mandatory pairing subsets (reasoning 175 /
scope 252 / anchor 60).

  python -m experiments.analysis.phase5            # print the 5.1 aggregate + convention checks
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS = REPO_ROOT / "data" / "processed" / "runs" / "runs.jsonl"
CONV = REPO_ROOT / "data" / "processed" / "runs" / "conversation.jsonl"

CELL = ["dataset", "domain", "model", "reasoning", "context_level", "scope", "decomposition"]
QWK_K = 5                       # a-priori bins (0..5, Mohler-aligned); sensitivity over {4,5,6} in 5.2


# --------------------------------------------------------------------------- load + §5.0 prep
def _read(path: Path) -> pd.DataFrame:
    rows = []
    for l in path.read_text().splitlines():
        if l.strip():
            try:
                rows.append(json.loads(l))
            except json.JSONDecodeError:
                pass
    return pd.DataFrame(rows)


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the §5.0 score conventions: clamp to [0, gold_scale_max], then normalise to 0–1.
    Adds pred (clamped), pred_norm, gold_norm. Leaves unparsed rows NaN (never coerced)."""
    d = df.copy()
    sc = pd.to_numeric(d["score"], errors="coerce")
    mx = pd.to_numeric(d["gold_scale_max"], errors="coerce")
    d["mx"] = mx
    d["pred"] = sc.clip(lower=0).clip(upper=mx)            # clamp [0, max]
    d["pred_norm"] = d["pred"] / mx
    d["gold_norm"] = pd.to_numeric(d["gold_score"], errors="coerce") / mx
    d["n_clamped_low"] = (sc < -1e-9).fillna(False)        # how many were negative (penalty criteria)
    return d


def load_main() -> pd.DataFrame:
    return prepare(_read(RUNS))


def load_conversation() -> pd.DataFrame:
    return prepare(_read(CONV))


def to_ordinal(norm: pd.Series, k: int = QWK_K) -> pd.Series:
    return (pd.to_numeric(norm, errors="coerce") * k).round().clip(0, k)


# --------------------------------------------------------------------------- §5.0 cost dedupe
def dedupe_call_groups(df: pd.DataFrame) -> pd.DataFrame:
    """For cost/token aggregates: whole-exam rows share ONE call (cost repeats on each
    question-row), so collapse each (call_group, config_hash, run_index) to a single row.
    Non-whole-exam rows (call_group null) are kept as-is (each is its own call)."""
    we = df[df["scope"] == "whole_exam"]
    rest = df[df["scope"] != "whole_exam"]
    we1 = we.drop_duplicates(["call_group", "config_hash", "run_index"])
    return pd.concat([rest, we1], ignore_index=True)


# --------------------------------------------------------------------------- §5.0 pairing subsets
def reasoning_paired(df: pd.DataFrame) -> pd.DataFrame:
    """Restrict each reasoning OFF/ON contrast to the items that have an ON cell (the 175
    sample) -- pairing OFF↔ON on the same items, never OFF-full-N (RQ1)."""
    keys = ["dataset", "domain", "model", "context_level", "scope", "decomposition"]
    on_items = (df[df["reasoning"] == "on"].groupby(keys)["item_id"].agg(set).rename("on_set"))
    out = df.merge(on_items, left_on=keys, right_index=True, how="left")
    return out[out.apply(lambda r: isinstance(r["on_set"], set) and r["item_id"] in r["on_set"], axis=1)]


def scope_paired(df: pd.DataFrame) -> pd.DataFrame:
    """Restrict the scope contrast to the 252 questions that have a whole-exam cell, on both
    sides (whole_exam and question_by_question), same model/etc. (RQ3)."""
    we_items = set(df[df["scope"] == "whole_exam"]["item_id"])
    code = df[(df["dataset"] == "ptcs") & (df["domain"] == "code") & df["item_id"].isin(we_items)]
    return code[code["scope"].isin(["whole_exam", "question_by_question"])]


def anchor_paired(df: pd.DataFrame) -> pd.DataFrame:
    """Restrict each dataset to the 60 items the GPT-5.1 anchor graded, so RQ4 compares the
    anchor to the open models on the SAME items (not 60 vs 2273)."""
    keep = []
    for ds, g in df.groupby("dataset"):
        a_items = set(g[g["model"] == "gpt-5.1"]["item_id"])
        if a_items:
            keep.append(g[g["item_id"].isin(a_items)])
    return pd.concat(keep, ignore_index=True) if keep else df.iloc[:0]


# --------------------------------------------------------------------------- 5.1 aggregate
def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    """Per-cell records: N, π, mean/median normalised score, deduped cost/tokens, error/trunc
    counts, and the non-random Qwen-ON truncation flag."""
    cost_src = dedupe_call_groups(df)
    cost = cost_src.assign(ce=pd.to_numeric(cost_src["cost_eur"], errors="coerce"),
                           ct=pd.to_numeric(cost_src["completion_tokens"], errors="coerce")) \
        .groupby(CELL).agg(calls=("item_id", "size"), cost_eur=("ce", "sum"),
                           mean_completion_tok=("ct", "mean")).reset_index()
    g = df.groupby(CELL)
    agg = g.agg(
        n_rows=("item_id", "size"), n_items=("item_id", "nunique"),
        pi=("parse_ok", "mean"),
        n_trunc=("finish_reason", lambda s: (s == "length").sum()),
        n_err=("error", lambda s: s.notna().sum()),
        mean_norm=("pred_norm", "mean"), median_norm=("pred_norm", "median"),
        frac0=("pred_norm", lambda s: (s < 1e-9).mean()),
    ).reset_index()
    out = agg.merge(cost, on=CELL, how="left")
    out["trunc_excluded_nonrandom"] = (out["n_trunc"] > 0)   # flag (all Qwen-ON; longest traces)
    return out


def main() -> int:
    df = load_main()
    print(f"main store: {len(df):,} rows  | conversation: {len(load_conversation()):,} rows\n")
    print("=== §5.0 convention checks ===")
    print(f"  clamped negatives -> 0: {int(df['n_clamped_low'].sum())} rows "
          f"(pred min now {df['pred'].min():.2f}, max-over-scale rows {int((df['pred']>df['mx']+1e-9).sum())})")
    cg = dedupe_call_groups(df)
    we = df[df.scope == 'whole_exam']
    print(f"  whole-exam cost dedupe: {len(we):,} rows -> {len(cg[cg.scope=='whole_exam']):,} calls")
    rp = reasoning_paired(df)
    print(f"  reasoning-paired subset: {len(rp):,} rows "
          f"(ON items/cell e.g. {rp[rp.reasoning=='on'].groupby(['dataset','domain','model']).item_id.nunique().head(3).to_dict()})")
    print(f"  scope-paired (252): {scope_paired(df).item_id.nunique()} items | "
          f"anchor-paired (60/ds): {anchor_paired(df).groupby('dataset').item_id.nunique().to_dict()}")

    print("\n=== 5.1 AGGREGATE (per cell; cost deduped) ===")
    agg = aggregate(df)
    with pd.option_context("display.width", 200, "display.max_rows", 80, "display.max_columns", None):
        show = agg[CELL + ["n_items", "pi", "frac0", "mean_norm", "median_norm",
                           "calls", "cost_eur", "n_trunc"]].round(3)
        print(show.to_string(index=False))
    agg.to_parquet(REPO_ROOT / "data" / "processed" / "_phase5_aggregate.parquet")
    print(f"\n{len(agg)} cells. π<0.97 cells: {int((agg.pi<0.97).sum())} "
          f"(all Qwen-ON truncation). Saved _phase5_aggregate.parquet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

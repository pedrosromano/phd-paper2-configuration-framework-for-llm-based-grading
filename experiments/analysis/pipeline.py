"""Phase 5 pipeline: load run rows -> aggregate (5.1) -> per-slice metrics (5.2-5.5).

A "slice" is one (dataset, model, reasoning, context_level, scope, decomposition,
conversation_state) cell -- i.e. one config_hash -- pooling its k repetitions. Metrics are
computed per dataset only (never across incompatible scales). This is the real Phase 5
engine; on the smoke set it doubles as the end-to-end schema check.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from experiments.analysis import metrics as M

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS_FILE = REPO_ROOT / "data" / "processed" / "runs" / "runs.jsonl"

# columns that identify a config cell (besides item_id / run_index)
CELL_COLS = ["dataset", "domain", "model", "model_id", "provider", "reasoning",
             "context_level", "scope", "decomposition", "conversation_state", "config_hash"]


def load_runs(path: Path = RUNS_FILE) -> pd.DataFrame:
    rows = [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- 5.1 aggregate
def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    """Per-cell record: mean score, pi (parse rate), mean tokens/latency/cost (5.1)."""
    if df.empty:
        return df
    d = df.copy()
    d["cost_eur_num"] = pd.to_numeric(d.get("cost_eur"), errors="coerce")
    g = d.groupby(CELL_COLS, dropna=False)
    agg = g.agg(
        n_runs=("run_index", "size"),
        n_items=("item_id", "nunique"),
        pi=("parse_ok", "mean"),
        mean_score=("score", "mean"),
        mean_prompt_tok=("prompt_tokens", "mean"),
        mean_completion_tok=("completion_tokens", "mean"),
        mean_latency_s=("latency_s", "mean"),
        total_cost_eur=("cost_eur_num", "sum"),
        n_errors=("error", lambda s: s.notna().sum()),
    ).reset_index()
    return agg


# --------------------------------------------------------------------------- run everything
def analyse(df: pd.DataFrame) -> dict:
    """Run 5.1-5.5 over a run-row frame, grouped per dataset/cell. Returns a dict of
    DataFrames keyed by Phase substep. Robust to tiny data (smoke)."""
    res: dict[str, pd.DataFrame] = {}
    if df.empty:
        return {"error": "no run rows"}
    res["5.1_aggregate"] = aggregate(df)

    agr_rows, con_rows, cost_rows = [], [], []
    for keys, slc in df.groupby(CELL_COLS, dropna=False):
        tag = dict(zip(CELL_COLS, keys))
        agr_rows.append({**tag, **M.agreement(slc)})
        con_rows.append({**tag, **M.consistency(slc)})
        cost_rows.append({**tag, **M.cost_summary(slc)})
    res["5.2_agreement"] = pd.DataFrame(agr_rows)
    res["5.3_consistency"] = pd.DataFrame(con_rows)
    res["5.4_cost"] = pd.DataFrame(cost_rows)

    # 5.4/5.5: per (dataset, model, ...) reasoning contrasts (pool over reasoning)
    contrast_cols = [c for c in CELL_COLS if c not in ("reasoning", "config_hash")]
    prem_rows, test_rows = [], []
    for keys, slc in df.groupby(contrast_cols, dropna=False):
        tag = dict(zip(contrast_cols, keys))
        prem_rows.append({**tag, **M.reasoning_premium(slc)})
        test_rows.append({**tag, **M.reasoning_effect_test(slc)})
    res["5.4_reasoning_premium"] = pd.DataFrame(prem_rows)
    res["5.5_reasoning_test"] = pd.DataFrame(test_rows)
    return res

"""Analysis metrics (Phase 5.2-5.5), as pure functions over run rows.

Every function declares the run-row FIELDS it consumes in its `consumes` attribute
(set just below it). experiments/analysis/coverage.py reads those declarations to build
the schema-coverage matrix mechanically -- so "does the logged schema support Phase 5?"
is answered by the code, not by hand. Each metric is per-dataset (never pooled across
incompatible scales) and degrades gracefully (returns NaN with a reason) when N is too
small, so it runs even on the 20-row smoke set.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import cohen_kappa_score, f1_score, accuracy_score


def _consumes(*fields):
    def deco(fn):
        fn.consumes = tuple(fields)
        return fn
    return deco


# --------------------------------------------------------------------------- helpers
def normalised(df: pd.DataFrame) -> pd.DataFrame:
    """Add pred_norm, gold_norm in [0,1] (score / gold_scale_max). Rows without a
    parseable score or a gold are left NaN -- never coerced (CLAUDE.md §8)."""
    out = df.copy()
    smax = pd.to_numeric(out["gold_scale_max"], errors="coerce")
    out["pred_norm"] = pd.to_numeric(out["score"], errors="coerce") / smax
    out["gold_norm"] = pd.to_numeric(out["gold_score"], errors="coerce") / smax
    return out


def to_ordinal(norm: pd.Series, n_bins: int) -> pd.Series:
    """Bin a normalised [0,1] score into ordinal levels 0..n_bins (QWK input).
    n_bins is recorded in the results so the binning choice is explicit (§11)."""
    return (pd.to_numeric(norm, errors="coerce") * n_bins).round().clip(0, n_bins)


# --------------------------------------------------------------------------- 5.2 agreement
@_consumes("score", "gold_score", "gold_scale_max")
def agreement(df: pd.DataFrame, n_bins: int = 5) -> dict:
    """QWK / Cohen's kappa / Spearman / Pearson / MAE / RMSE on one (dataset,...) slice,
    using only rows that parsed AND have a gold. pi-excluded rows do not silently become 0."""
    d = normalised(df)
    d = d[d["pred_norm"].notna() & d["gold_norm"].notna()]
    n = len(d)
    base = {"n_scored": n, "n_bins": n_bins}
    if n < 2:
        return {**base, "qwk": np.nan, "cohen_kappa": np.nan, "spearman": np.nan,
                "pearson": np.nan, "mae": np.nan, "rmse": np.nan, "note": "n<2"}
    p, g = d["pred_norm"].to_numpy(), d["gold_norm"].to_numpy()
    po, go = to_ordinal(d["pred_norm"], n_bins).astype(int), to_ordinal(d["gold_norm"], n_bins).astype(int)
    labels = list(range(n_bins + 1))
    qwk = cohen_kappa_score(go, po, weights="quadratic", labels=labels)
    kappa = cohen_kappa_score(go, po, labels=labels)
    sr = stats.spearmanr(p, g).statistic if np.ptp(p) and np.ptp(g) else np.nan
    pr = stats.pearsonr(p, g).statistic if np.ptp(p) and np.ptp(g) else np.nan
    mae = float(np.mean(np.abs(p - g)))
    rmse = float(np.sqrt(np.mean((p - g) ** 2)))
    return {**base, "qwk": _f(qwk), "cohen_kappa": _f(kappa), "spearman": _f(sr),
            "pearson": _f(pr), "mae": mae, "rmse": rmse}


@_consumes("score", "label_3way", "label_2way", "label_5way")
def classification(df: pd.DataFrame, label_col: str) -> dict:
    """Accuracy + macro-F1 for SemEval label tasks. Needs a predicted-label column
    derived upstream; here we report support so the wiring is verified even pre-derivation."""
    if label_col not in df.columns or df[label_col].isna().all():
        return {"note": f"no {label_col} in slice", "n": 0}
    return {"n_labelled": int(df[label_col].notna().sum()), "label_col": label_col}


# --------------------------------------------------------------------------- 5.3 consistency
@_consumes("score", "item_id", "config_hash", "run_index")
def consistency(df: pd.DataFrame) -> dict:
    """Within-cell spread across the k repetitions (SD per item, averaged) + ICC(2,1).
    Ground-truth-free (CLAUDE.md §6.2)."""
    d = normalised(df)
    d = d[d["pred_norm"].notna()]
    if d.empty:
        return {"mean_within_item_sd": np.nan, "icc": np.nan, "note": "no parsed scores"}
    per_item = d.groupby("item_id")["pred_norm"].agg(["std", "count"])
    mean_sd = float(per_item["std"].dropna().mean()) if per_item["std"].notna().any() else np.nan
    icc = _icc21(d.pivot_table(index="item_id", columns="run_index", values="pred_norm"))
    return {"mean_within_item_sd": _f(mean_sd), "icc": _f(icc),
            "n_items": int(d["item_id"].nunique()),
            "k_observed": int(d.groupby("item_id")["run_index"].nunique().max())}


def _icc21(mat: pd.DataFrame) -> float:
    """ICC(2,1) two-way random, single measure. Rows=items, cols=repetitions."""
    m = mat.dropna(axis=0, how="any").to_numpy(dtype=float)
    n, k = m.shape
    if n < 2 or k < 2:
        return np.nan
    grand = m.mean()
    ms_r = k * ((m.mean(axis=1) - grand) ** 2).sum() / (n - 1)          # between items
    ms_c = n * ((m.mean(axis=0) - grand) ** 2).sum() / (k - 1)          # between reps
    ss_e = ((m - m.mean(axis=1, keepdims=True) - m.mean(axis=0, keepdims=True) + grand) ** 2).sum()
    ms_e = ss_e / ((n - 1) * (k - 1))
    denom = ms_r + (k - 1) * ms_e + k * (ms_c - ms_e) / n
    return float((ms_r - ms_e) / denom) if denom else np.nan


# --------------------------------------------------------------------------- 5.4 cost
@_consumes("prompt_tokens", "completion_tokens", "reasoning_tokens", "cost_eur",
           "latency_s", "provider")
def cost_summary(df: pd.DataFrame) -> dict:
    """Per-slice operational cost. € for paid providers; tokens/latency for local
    (CLAUDE.md §6.2 -- don't conflate the two cost metrics). Latency reports MEDIAN
    alongside mean and flags infrastructure outliers (network stalls are not a model
    property -- §6.4): a call is an outlier if latency > median + 3*IQR."""
    g = df
    lat = pd.to_numeric(g["latency_s"], errors="coerce").dropna()
    q1, q3 = (lat.quantile(0.25), lat.quantile(0.75)) if len(lat) >= 4 else (None, None)
    out = {
        "n_calls": int(len(g)),
        "mean_prompt_tok": _f(g["prompt_tokens"].mean()),
        "mean_completion_tok": _f(g["completion_tokens"].mean()),
        # DeepInfra folds thinking into completion_tokens (null reasoning_tokens); only the
        # GPT-5.1 anchor itemises it -> the two are NOT comparable per-token (§6.4).
        "mean_reasoning_tok": _f(pd.to_numeric(g["reasoning_tokens"], errors="coerce").mean()),
        "mean_latency_s": _f(lat.mean()),
        "median_latency_s": _f(lat.median()),
        "n_latency_outliers": _infra_outliers(lat, q1, q3),
        "is_local": bool((g["provider"] == "ollama").all()),
    }
    cost = pd.to_numeric(g["cost_eur"], errors="coerce")
    out["total_cost_eur"] = _f(cost.sum()) if cost.notna().any() else None
    out["mean_cost_eur"] = _f(cost.mean()) if cost.notna().any() else None
    return out


def _infra_outliers(lat: pd.Series, q1, q3) -> int:
    """Count calls whose latency is an infrastructure outlier (> Q3 + 3*IQR). These are
    network/queue stalls, not model latency -- reported separately so 5.4 isn't skewed."""
    if q1 is None or q3 is None:
        return 0
    iqr = q3 - q1
    return int((lat > q3 + 3 * iqr).sum()) if iqr > 0 else 0


@_consumes("completion_tokens", "reasoning", "cost_eur")
def reasoning_premium(df: pd.DataFrame) -> dict:
    """The headline reasoning premium: ON vs OFF ratio on output tokens (always available)
    and on € (paid only). States WHICH metric (CLAUDE.md §6.2)."""
    by = df.groupby("reasoning")
    tok = by["completion_tokens"].mean()
    res = {"mean_out_tok": {k: _f(v) for k, v in tok.items()}}
    if {"off", "on"} <= set(tok.index) and tok.get("off", 0):
        res["output_token_premium_x"] = _f(tok["on"] / tok["off"])
    cost = df.assign(c=pd.to_numeric(df["cost_eur"], errors="coerce")).groupby("reasoning")["c"].mean()
    if cost.notna().any() and {"off", "on"} <= set(cost.index) and cost.get("off", 0):
        res["cost_premium_x"] = _f(cost["on"] / cost["off"])
    return res


# --------------------------------------------------------------------------- 5.5 stats
@_consumes("score", "gold_score", "gold_scale_max", "item_id", "reasoning")
def reasoning_effect_test(df: pd.DataFrame) -> dict:
    """Paired reasoning on/off test on per-item accuracy (|pred-gold|, lower=better),
    pairing by item_id (mean over k). Reports effect size (Cohen's dz) + 95% CI, not just p
    (CLAUDE.md §6.4). Underpowered on small N -- the function says so rather than over-reading."""
    d = normalised(df)
    d = d[d["pred_norm"].notna() & d["gold_norm"].notna()].copy()
    d["abs_err"] = (d["pred_norm"] - d["gold_norm"]).abs()
    piv = d.pivot_table(index="item_id", columns="reasoning", values="abs_err", aggfunc="mean")
    if not {"off", "on"} <= set(piv.columns):
        return {"note": "need both reasoning off & on", "n_pairs": 0}
    piv = piv.dropna(subset=["off", "on"])
    n = len(piv)
    if n < 2:
        return {"note": "n<2 pairs", "n_pairs": n}
    diff = (piv["on"] - piv["off"]).to_numpy()      # negative => reasoning improves accuracy
    md, sd = float(diff.mean()), float(diff.std(ddof=1))
    dz = md / sd if sd else np.nan
    t = stats.ttest_rel(piv["on"], piv["off"])
    half = 1.96 * sd / np.sqrt(n) if sd else np.nan
    return {"n_pairs": n, "mean_diff_abs_err": md, "ci95": [_f(md - half), _f(md + half)],
            "cohen_dz": _f(dz), "t": _f(t.statistic), "p": _f(t.pvalue),
            "note": "negative mean_diff => reasoning ON lowers error"}


# --------------------------------------------------------------------------- util
def _f(x):
    try:
        f = float(x)
        return None if np.isnan(f) else round(f, 6)
    except (TypeError, ValueError):
        return None


# the metric functions whose `consumes` the coverage matrix scans
METRIC_FUNCS = [agreement, classification, consistency, cost_summary,
                reasoning_premium, reasoning_effect_test]

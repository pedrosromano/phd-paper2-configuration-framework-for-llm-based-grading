"""Figure 6.3 -- cost-vs-agreement scatter (the headline trade-off).

One point per config cell: x = cost proxy (mean € for paid, else mean completion tokens
for local -- the two are NOT conflated, CLAUDE.md §6.2), y = agreement (QWK). Marker by
reasoning on/off. Exports .pdf + .pgf into article/figures. Importable as plot(df, out_dir).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["pgf.texsystem"] = "pdflatex"   # IEEEtran toolchain (§9), not xelatex
import matplotlib.pyplot as plt
import pandas as pd

from experiments.analysis import metrics as M
from experiments.analysis.pipeline import CELL_COLS


def _cell_points(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, slc in df.groupby(CELL_COLS, dropna=False):
        tag = dict(zip(CELL_COLS, keys))
        agr = M.agreement(slc)
        cost_eur = pd.to_numeric(slc.get("cost_eur"), errors="coerce")
        rows.append({**tag, "qwk": agr["qwk"], "n_scored": agr["n_scored"],
                     "mean_cost_eur": cost_eur.mean() if cost_eur.notna().any() else None,
                     "mean_completion_tok": slc["completion_tokens"].mean()})
    return pd.DataFrame(rows)


def plot(df: pd.DataFrame, out_dir: Path) -> Path | None:
    if df.empty:
        return None
    pts = _cell_points(df)
    paid = pts["mean_cost_eur"].notna().any()
    xcol = "mean_cost_eur" if paid else "mean_completion_tok"
    xlabel = "mean cost (€) per call" if paid else "mean completion tokens (local cost proxy)"
    out_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(3.4, 2.6))
    for reasoning, g in pts.groupby("reasoning"):
        ax.scatter(g[xcol], g["qwk"], s=28, alpha=0.8,
                   marker="o" if reasoning == "off" else "^", label=f"reasoning {reasoning}")
    for _, r in pts.iterrows():
        if pd.notna(r[xcol]) and pd.notna(r["qwk"]):
            ax.annotate(str(r["model"]), (r[xcol], r["qwk"]), fontsize=6,
                        xytext=(2, 2), textcoords="offset points")
    ax.set_xlabel(xlabel, fontsize=8)
    ax.set_ylabel("agreement (QWK)", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=6, loc="best")
    fig.tight_layout()
    pdf = out_dir / "fig63_cost_vs_agreement.pdf"
    fig.savefig(pdf)
    try:                                            # .pgf needs a TeX system on PATH (§9)
        fig.savefig(out_dir / "fig63_cost_vs_agreement.pgf")
    except (RuntimeError, FileNotFoundError) as e:
        print(f"  [fig 6.3] .pdf written; .pgf skipped (no TeX on PATH: {str(e)[:60]})")
    plt.close(fig)
    return pdf


def main() -> int:
    from experiments.analysis.pipeline import RUNS_FILE, load_runs
    out = plot(load_runs(RUNS_FILE), Path(__file__).resolve().parents[2] / "article" / "figures")
    print(f"figure 6.3 -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

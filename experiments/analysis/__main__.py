"""Phase 5 entry point (`make analyse` / `python -m experiments.analysis`).

  python -m experiments.analysis                      # full runs.jsonl -> tables
  python -m experiments.analysis --runs <file.jsonl>  # e.g. the smoke set
  python -m experiments.analysis --coverage           # print the schema-coverage matrix only
  python -m experiments.analysis --runs smoke.jsonl --validate   # end-to-end schema check
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from experiments.analysis import coverage, pipeline
from experiments.analysis.pipeline import REPO_ROOT, RUNS_FILE

TABLES_DIR = REPO_ROOT / "article" / "tables"
RUNS_DIR = REPO_ROOT / "data" / "processed" / "runs"


def _resolve(runs: str | None) -> Path:
    if runs is None:
        return RUNS_FILE
    p = Path(runs)
    return p if p.is_absolute() or p.exists() else (RUNS_DIR / runs)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=None, help="run-rows JSONL (default: runs.jsonl)")
    ap.add_argument("--coverage", action="store_true", help="print coverage matrix and exit")
    ap.add_argument("--validate", action="store_true",
                    help="end-to-end: coverage + run 5.1-5.5 + figure 6.3 on the given runs")
    ap.add_argument("--tables", action="store_true", help="write tidy .tex tables (5.7)")
    args = ap.parse_args(argv)

    cov_rows, schema = coverage.build_matrix()
    print(coverage.render(cov_rows, schema))
    cov_ok = all(r["ok"] for r in cov_rows)
    if args.coverage:
        return 0 if cov_ok else 1

    path = _resolve(args.runs)
    if not path.exists():
        print(f"\n[analyse] no run rows at {path} -- run an arm (or smoke) first.")
        return 0
    df = pipeline.load_runs(path)
    print(f"\n[analyse] {len(df)} run rows from {path.name} "
          f"({df['dataset'].nunique()} dataset(s), {df['config_hash'].nunique()} cells)\n")
    results = pipeline.analyse(df)

    for name, frame in results.items():
        if isinstance(frame, pd.DataFrame):
            print(f"=== {name}  ({len(frame)} rows) ===")
            with pd.option_context("display.max_columns", None, "display.width", 160):
                print(frame.to_string(index=False), "\n")

    fig_ok = True
    if args.validate:
        from experiments.figures import cost_vs_agreement
        out = cost_vs_agreement.plot(df, REPO_ROOT / "article" / "figures")
        fig_ok = out is not None
        print(f"[validate] figure 6.3 -> {out}")
        # prove every consumed field was actually present in the data, not just the schema
        missing_in_data = sorted({f for r in coverage._output_consumes().values()
                                  for f in r} - set(df.columns))
        print(f"[validate] consumed fields absent from THIS run frame: {missing_in_data or 'none'}")
        ok = cov_ok and fig_ok and not missing_in_data
        print(f"\n[validate] END-TO-END {'PASS' if ok else 'FAIL'} "
              f"(coverage={'ok' if cov_ok else 'gap'}, figure={'ok' if fig_ok else 'fail'})")
        return 0 if ok else 1

    if args.tables:
        TABLES_DIR.mkdir(parents=True, exist_ok=True)
        for name, frame in results.items():
            if isinstance(frame, pd.DataFrame):
                (TABLES_DIR / f"{name}.tex").write_text(
                    frame.to_latex(index=False, float_format="%.3f"))
        print(f"[analyse] wrote {len(results)} tables to {TABLES_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

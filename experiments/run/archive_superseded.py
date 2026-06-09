"""Archive the superseded reasoning-ON rows OUT of the canonical store (run ONCE, after
the max_tokens=32768 re-run completes and its π check passes).

Problem it solves: the original reasoning-ON cells were produced at max_tokens=4096 and
TRUNCATED the longest traces (finish_reason=length; Qwen3.5 lost ~50%). They were re-run at
max_tokens=32768 (a new config_hash). Both now sit in runs.jsonl. Per-config_hash analysis
never mixes them, but a NAIVE aggregation over `reasoning=='on'` would pull BOTH and
contaminate RQ1. So we move the 4096-ON rows out of runs.jsonl entirely -> the canonical
analysis input is clean BY CONSTRUCTION, not by every query remembering to filter.

We ARCHIVE, not delete: the 4096-ON rows are themselves the evidence for the truncation
finding (Methods/Threats). They go to data/processed/_archive/ (a directory analysis never
reads) under a DO-NOT-ANALYZE name, with a '#' header that makes any naive json.loads loop
fail loudly on line 1, and the file is made read-only.

Safety: refuses if the runner is still live, and refuses unless EVERY superseded ON row has
a max_tokens=32768 replacement (so we never archive a cell the re-run didn't cover).

  python -m experiments.run.archive_superseded            # dry-run (prints, writes nothing)
  python -m experiments.run.archive_superseded --apply    # do it
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS_FILE = REPO_ROOT / "data" / "processed" / "runs" / "runs.jsonl"
ARCHIVE_DIR = REPO_ROOT / "data" / "processed" / "_archive"
ARCHIVE_FILE = ARCHIVE_DIR / "superseded_reasoning_on_maxtok4096_DO_NOT_ANALYZE.jsonl"
BACKUP_FILE = ARCHIVE_DIR / "runs_before_archive.jsonl.bak"

# identity of a cell ignoring max_tokens -> used to confirm a 32768 replacement exists
_KEY = ("item_id", "dataset", "model", "context_level", "scope", "decomposition", "run_index")


def _is_superseded(r: dict) -> bool:
    return r.get("reasoning") == "on" and int(r.get("max_tokens", 0) or 0) == 4096


def _replacement_key(r: dict) -> tuple:
    return tuple(str(r.get(k)) for k in _KEY)


def _runner_live() -> bool:
    try:
        return subprocess.run(["pgrep", "-f", "experiments.run.matrix run"],
                              capture_output=True).returncode == 0
    except Exception:
        return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="actually rewrite (default: dry-run)")
    args = ap.parse_args(argv)

    if _runner_live():
        print("REFUSED: a matrix run is still live. Wait for it to finish, then re-run.")
        return 1

    rows = [json.loads(l) for l in RUNS_FILE.read_text().splitlines() if l.strip()]
    superseded = [r for r in rows if _is_superseded(r)]
    keep = [r for r in rows if not _is_superseded(r)]

    # every superseded ON cell MUST have a max_tokens=32768 replacement, else the re-run
    # didn't cover it -> abort rather than archive a cell with no clean successor.
    repl = {_replacement_key(r) for r in keep
            if r.get("reasoning") == "on" and int(r.get("max_tokens", 0) or 0) == 32768}
    orphans = [r for r in superseded if _replacement_key(r) not in repl]

    print(f"runs.jsonl rows:        {len(rows):,}")
    print(f"  superseded (on,4096): {len(superseded):,}")
    print(f"  keep (canonical):     {len(keep):,}")
    print(f"  replacement (on,32768): {len(repl):,} cells")
    print(f"  superseded WITHOUT a 32768 replacement: {len(orphans):,}")
    if orphans:
        print("REFUSED: some superseded ON cells have no 32768 replacement "
              "(re-run incomplete). Nothing written.")
        return 2
    if not superseded:
        print("Nothing to archive (no on/4096 rows). Done.")
        return 0
    assert len(keep) + len(superseded) == len(rows), "partition lost rows"

    if not args.apply:
        print("\nDRY-RUN: pass --apply to write. Would:")
        print(f"  - back up runs.jsonl -> {BACKUP_FILE.relative_to(REPO_ROOT)}")
        print(f"  - move {len(superseded):,} rows -> {ARCHIVE_FILE.relative_to(REPO_ROOT)} (read-only)")
        print(f"  - rewrite runs.jsonl with {len(keep):,} canonical rows")
        return 0

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    BACKUP_FILE.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")

    header = (
        "# ==========================================================================\n"
        "# SUPERSEDED RUN ROWS -- DO NOT LOAD INTO ANALYSIS.\n"
        "# reasoning=ON cells produced at max_tokens=4096, which TRUNCATED the longest\n"
        "# reasoning traces (finish_reason=length; Qwen3.5 lost ~50%). REPLACED by the\n"
        "# max_tokens=32768 cells in runs.jsonl. Kept ONLY as evidence for the truncation\n"
        f"# finding (Methods/Threats). Archived {stamp}. This '#' line makes a naive\n"
        "# json.loads loop fail on line 1 -- by design, so these can't silently re-enter.\n"
        "# ==========================================================================\n")
    body = "\n".join(json.dumps(r, ensure_ascii=False) for r in superseded) + "\n"
    ARCHIVE_FILE.write_text(header + body)
    os.chmod(ARCHIVE_FILE, 0o444)   # read-only

    tmp = RUNS_FILE.with_suffix(".jsonl.tmp")
    tmp.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in keep) + "\n")
    tmp.replace(RUNS_FILE)          # atomic

    (ARCHIVE_DIR / "README.md").write_text(
        "# `_archive/` — superseded run rows. NOT analysis input.\n\n"
        "Analysis reads ONLY `data/processed/runs/runs.jsonl`. Files here are quarantined\n"
        "and must never be loaded into Phase 5.\n\n"
        f"- `{ARCHIVE_FILE.name}` — reasoning-ON cells at max_tokens=4096 (truncated), "
        "replaced by max_tokens=32768 in runs.jsonl. Evidence for the truncation finding.\n"
        f"- `{BACKUP_FILE.name}` — full runs.jsonl snapshot taken just before the archive split.\n")

    print(f"\nARCHIVED {len(superseded):,} rows -> {ARCHIVE_FILE.relative_to(REPO_ROOT)} (read-only)")
    print(f"runs.jsonl now {len(keep):,} canonical rows; backup at {BACKUP_FILE.relative_to(REPO_ROOT)}")
    print("Canonical store is clean: no reasoning=on/max_tokens=4096 rows remain.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Archive the GLM-5.1 rows produced on/after 2026-10-15 OUT of the canonical store.

Why: by October 2026 DeepInfra no longer honours enable_thinking=false for zai-org/GLM-5.1. The model
reasons inside the answer instead (June: ~10 output tokens per grade; October: ~1200), and only 15 of 25
re-run June prompts returned the same grade, against 24/25 for Qwen3.5, 23/25 for DeepSeek-V4-Flash and
21/25 for GPT-5.1, whose behaviour was unchanged (drift check, 2026-10-15). October GLM "reasoning off"
cells are therefore a different condition from the June ones, and comparing them (C1 guidance, C2
decomposition, C3 whole-exam) would confound the configuration effect with a provider change.

We ARCHIVE, not delete: the rows are the evidence for the backend-drift observation. They go to
data/processed/_archive/ under a DO-NOT-ANALYZE name with a '#' header (a naive json.loads loop fails
loudly on line 1), and the file is made read-only. Refuses while any run is live.

  python -m experiments.run.archive_glm_drift            # dry-run
  python -m experiments.run.archive_glm_drift --apply
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = REPO_ROOT / "data" / "processed" / "runs"
ARCHIVE_DIR = REPO_ROOT / "data" / "processed" / "_archive"
CUTOFF = "2026-10-15"                                   # first day of the bloco C runs
STORES = {"runs.jsonl": "glm51_oct2026_backend_drift_DO_NOT_ANALYZE.jsonl",
          "conversation.jsonl": "glm51_oct2026_backend_drift_conversation_DO_NOT_ANALYZE.jsonl"}


def _live() -> bool:
    pat = "experiments.run.(matrix run|whole_exam_runner|conversation_runner|bloco_c_run)"
    return subprocess.run(["pgrep", "-f", pat], capture_output=True).returncode == 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)
    if _live():
        print("REFUSED: a run is live.")
        return 1
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for store, arch_name in STORES.items():
        src = RUNS_DIR / store
        if not src.exists():
            continue
        keep, move = [], []
        for line in src.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            (move if r.get("model") == "glm-5.1" and str(r.get("ts", "")) >= CUTOFF else keep).append(line)
        print(f"{store}: {len(keep) + len(move):,} rows | GLM-5.1 since {CUTOFF}: {len(move):,} to archive")
        if not args.apply or not move:
            continue
        backup = ARCHIVE_DIR / f"{store}.before_glm_drift_archive.bak"
        backup.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        arch = ARCHIVE_DIR / arch_name
        header = (f"# DO NOT ANALYZE -- GLM-5.1 rows from {CUTOFF} on: DeepInfra no longer disables its "
                  f"reasoning (backend drift, see experiments/run/archive_glm_drift.py). Archived {stamp}.\n")
        prev = arch.read_text(encoding="utf-8") if arch.exists() else header
        if arch.exists():
            os.chmod(arch, 0o644)
        arch.write_text(prev + "\n".join(move) + "\n", encoding="utf-8")
        os.chmod(arch, 0o444)
        tmp = src.with_suffix(".tmp")
        tmp.write_text("\n".join(keep) + "\n", encoding="utf-8")
        tmp.replace(src)                                # atomic swap
        print(f"  archived -> {arch.name}; backup -> {backup.name}")
    if not args.apply:
        print("dry-run: nothing written (use --apply)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

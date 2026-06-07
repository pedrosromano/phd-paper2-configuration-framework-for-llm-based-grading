"""Minimal .env loader (Phase 0.4) — no third-party dependency.

Reads KEY=VALUE lines from the repo-root .env (gitignored) into os.environ without
overwriting variables already set in the real environment. Call load_env() before
reading any API key. Secrets live ONLY in .env or the shell — never in tracked files.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = REPO_ROOT / ".env"


def load_env(path: Path = ENV_PATH) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        # real environment wins over the file
        os.environ.setdefault(key, value)

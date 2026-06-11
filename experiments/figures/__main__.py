"""`python -m experiments.figures` -> Phase 6 figure set (delegates to phase6.main).

Added 2026-06-11 (audit 🟡-9): `make figures` ran `python -m experiments.figures`, which
failed because the package had no __main__ — the real entry point was experiments.figures.phase6.
"""
from experiments.figures.phase6 import main

raise SystemExit(main())

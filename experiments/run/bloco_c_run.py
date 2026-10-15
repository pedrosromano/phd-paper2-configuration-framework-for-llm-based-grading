"""Bloco C launcher (advisor review, user-approved 2026-10-15). Runs the given C steps in order and, after
each step, computes its first read-out with experiments.analysis.bloco_c and records it in
runs/_bloco_c_status.json for the live monitor.

Two launchers may run AT THE SAME TIME, one per provider queue (since 2026-10-15 runs.jsonl appends and
the spend journal are written under file locks, and each launcher updates only its own steps here):

  python -m experiments.run.bloco_c_run c2 c3 c1 c4          # DeepInfra queue (DeepSeek, Qwen)
  python -m experiments.run.bloco_c_run c1_gpt c5_off c5_on  # OpenAI queue (GPT-5.1)

Resumable: cached cells are skipped. Each step's stdout goes to runs/bloco_c_<step>.log.
"""

from __future__ import annotations

import fcntl
import json
import subprocess
import sys
import time
import traceback
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = REPO_ROOT / "data" / "processed" / "runs"
STATUS = RUNS_DIR / "_bloco_c_status.json"
STATUS_LOCK = RUNS_DIR / "_bloco_c_status.lock"
PY = sys.executable
M = [PY, "-m", "experiments.run.matrix", "run", "--arm"]

# (id, title shown in the monitor, commands run in sequence). Concurrency per provider, 2026-10-15:
# DeepInfra rate-limits DeepSeek above ~48 parallel requests (429s, retried); OpenAI allows 15k req/min.
# GLM-5.1 is not used in bloco C: its reasoning can no longer be switched off on DeepInfra (2026-10-15).
STEPS = [
    ("c2", "C2 · Decomposição critério a critério (RIAYN + PT-CS, Qwen + DeepSeek)",
     [M + ["c2_decomposition", "--concurrency", "48"]]),
    ("c3", "C3 · Exame inteiro numa chamada, 88 exames (Qwen + DeepSeek)",
     [[PY, "-m", "experiments.run.whole_exam_runner", "--model", "qwen3.5", "--exams", "validated"],
      [PY, "-m", "experiments.run.whole_exam_runner", "--model", "deepseek-v4-flash", "--exams", "validated",
       "--concurrency", "24"]]),
    ("c1", "C1 · Guidance no DeepSeek (4 datasets)",
     [M + ["c1_context_roster", "--concurrency", "48"]]),
    ("c4", "C4 · Conversa limpa vs partilhada, 80 exames, k=5 (Qwen + DeepSeek)",
     [[PY, "-m", "experiments.run.conversation_runner", "--models", "qwen3.5,deepseek-v4-flash",
       "--concurrency", "24"]]),
    ("c1_gpt", "C1 · Guidance no GPT-5.1 (4 datasets)",
     [M + ["c1_context_gpt", "--concurrency", "64"]]),
    ("c5_off", "C5 · GPT-5.1 sem reasoning, cobertura completa (k=5)",
     [M + ["c5_anchor_full_off", "--concurrency", "64"]]),
    ("c5_on", "C5 · GPT-5.1 com reasoning, mesmas amostras dos abertos (k=5)",
     [M + ["c5_anchor_full_on", "--concurrency", "48"]]),
]
CONCLUDE_AS = {"c1_gpt": "c1"}                         # both C1 queues share the guidance read-out


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


@contextmanager
def _locked():
    with STATUS_LOCK.open("a") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


def _update(sid: str, **fields) -> None:
    """Read-modify-write ONE step under a file lock, so two launchers never clobber each other."""
    with _locked():
        st = json.loads(STATUS.read_text()) if STATUS.exists() else {"steps": []}
        have = {s["id"] for s in st["steps"]}
        for i, t, _ in STEPS:
            if i not in have:
                st["steps"].append({"id": i, "title": t, "state": "pending"})
        for s in st["steps"]:
            if s["id"] == sid:
                s.update(fields)
        st["updated"] = _now()
        tmp = STATUS.with_suffix(f".{sid}.tmp")
        tmp.write_text(json.dumps(st, ensure_ascii=False, indent=1))
        tmp.replace(STATUS)                            # atomic swap: the monitor never reads a half file


def main(argv: list[str]) -> int:
    wanted = argv or [i for i, _, _ in STEPS]
    by_id = {i: (t, c) for i, t, c in STEPS}
    unknown = [w for w in wanted if w not in by_id]
    if unknown:
        print(f"unknown step(s) {unknown}; known: {list(by_id)}")
        return 1
    for sid in wanted:                                 # the order given on the command line
        title, cmds = by_id[sid]
        _update(sid, title=title, state="running", started=_now(), ended=None, conclusion=None,
                error=None, minutes=None)
        log = RUNS_DIR / f"bloco_c_{sid}.log"
        t0, rc = time.time(), 0
        with log.open("w") as fh:
            for cmd in cmds:
                fh.write(f"$ {' '.join(cmd[1:])}\n"); fh.flush()
                rc = subprocess.run(cmd, cwd=REPO_ROOT, stdout=fh, stderr=subprocess.STDOUT).returncode
                if rc not in (0, 2):                   # 2 = finished with a reasoning-ON pi warning
                    break
        minutes = round((time.time() - t0) / 60, 1)
        if rc not in (0, 2):
            _update(sid, state="failed", ended=_now(), minutes=minutes, error=f"exit code {rc}; see {log.name}")
            print(f"[{sid}] FAILED (exit {rc}); stopping this queue. Log: {log}")
            return rc
        _update(sid, state="analysing", minutes=minutes)
        try:
            from experiments.analysis import bloco_c, phase5
            conclusion = bloco_c.CONCLUDE[CONCLUDE_AS.get(sid, sid)](phase5.load_main())
            _update(sid, state="done" if rc == 0 else "done (verificar π com reasoning)",
                    conclusion=conclusion, ended=_now())
        except Exception:                              # the run is safe on disk; only the read-out failed
            _update(sid, state="done (sem conclusão)", error=traceback.format_exc(limit=3), ended=_now())
        print(f"[{sid}] done in {minutes} min")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

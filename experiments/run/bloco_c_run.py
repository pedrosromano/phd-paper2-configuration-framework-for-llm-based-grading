"""Bloco C launcher (advisor review, user-approved 2026-10-15): runs the C arms ONE AT A TIME (only one
process may append to runs.jsonl and the spend ledger), and after each step computes its first read-out
with experiments.analysis.bloco_c and records it in runs/_bloco_c_status.json for the live monitor.

  python -m experiments.run.bloco_c_run            # all steps, resumable (cached cells are skipped)
  python -m experiments.run.bloco_c_run c2 c3      # only these steps

Each step's stdout goes to runs/bloco_c_<step>.log (the monitor tails the newest log).
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = REPO_ROOT / "data" / "processed" / "runs"
STATUS = RUNS_DIR / "_bloco_c_status.json"
PY = sys.executable

# (id, title shown in the monitor, commands run in sequence)
STEPS = [
    ("c2", "C2 · Decomposição critério a critério (RIAYN + PT-CS, Qwen + DeepSeek)",
     [[PY, "-m", "experiments.run.matrix", "run", "--arm", "c2_decomposition", "--concurrency", "48"]]),
    # GLM-5.1 replaced by DeepSeek-V4-Flash (C2-C4) and GPT-5.1 (C1) on 2026-10-15: DeepInfra no longer
    # disables GLM's reasoning, so its October "off" cells are not the June condition (archive_glm_drift.py).
    ("c3", "C3 · Exame inteiro numa chamada, 88 exames (Qwen + DeepSeek)",
     [[PY, "-m", "experiments.run.whole_exam_runner", "--model", "qwen3.5", "--exams", "validated"],
      [PY, "-m", "experiments.run.whole_exam_runner", "--model", "deepseek-v4-flash", "--exams", "validated",
       "--concurrency", "24"]]),
    ("c1", "C1 · Guidance no DeepSeek e no GPT-5.1 (4 datasets)",
     # 48x on DeepInfra: DeepSeek latency ~11 s/call on 2026-10-15; throughput scales with concurrency
     [[PY, "-m", "experiments.run.matrix", "run", "--arm", "c1_context_roster", "--concurrency", "48"],
      [PY, "-m", "experiments.run.matrix", "run", "--arm", "c1_context_gpt", "--concurrency", "16"]]),
    ("c4", "C4 · Conversa limpa vs partilhada, 80 exames, k=5 (Qwen + DeepSeek)",
     [[PY, "-m", "experiments.run.conversation_runner", "--models", "qwen3.5,deepseek-v4-flash",
       "--concurrency", "16"]]),
    ("c5_off", "C5 · GPT-5.1 sem reasoning, cobertura completa (k=5)",
     [[PY, "-m", "experiments.run.matrix", "run", "--arm", "c5_anchor_full_off"]]),
    ("c5_on", "C5 · GPT-5.1 com reasoning, mesmas amostras dos abertos (k=5)",
     [[PY, "-m", "experiments.run.matrix", "run", "--arm", "c5_anchor_full_on"]]),
]


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _load() -> dict:
    st = json.loads(STATUS.read_text()) if STATUS.exists() else {"steps": []}
    have = {s["id"] for s in st["steps"]}
    for i, t, _ in STEPS:                              # steps added after a first launch
        if i not in have:
            st["steps"].append({"id": i, "title": t, "state": "pending"})
    return st


def _save(st: dict) -> None:
    st["updated"] = _now()
    tmp = STATUS.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=1))
    tmp.replace(STATUS)                                    # atomic swap: the monitor never reads a half file


def _step(st: dict, sid: str) -> dict:
    for s in st["steps"]:
        if s["id"] == sid:
            return s
    raise KeyError(sid)


def main(argv: list[str]) -> int:
    wanted = argv or [i for i, _, _ in STEPS]
    st = _load()
    for sid, title, cmds in STEPS:
        if sid not in wanted:
            continue
        s = _step(st, sid)
        s.update(state="running", started=_now(), ended=None, conclusion=None, error=None)
        _save(st)
        log = RUNS_DIR / f"bloco_c_{sid}.log"
        t0, rc = time.time(), 0
        with log.open("w") as fh:
            for cmd in cmds:
                fh.write(f"$ {' '.join(cmd[1:])}\n"); fh.flush()
                rc = subprocess.run(cmd, cwd=REPO_ROOT, stdout=fh, stderr=subprocess.STDOUT).returncode
                if rc not in (0, 2):                       # 2 = finished with a reasoning-ON pi warning
                    break
        s["minutes"] = round((time.time() - t0) / 60, 1)
        if rc not in (0, 2):
            s.update(state="failed", ended=_now(), error=f"exit code {rc}; see {log.name}")
            _save(st)
            print(f"[{sid}] FAILED (exit {rc}); stopping. Log: {log}")
            return rc
        s.update(state="analysing")
        _save(st)
        try:
            from experiments.analysis import bloco_c, phase5
            df = phase5.load_main()
            s["conclusion"] = bloco_c.CONCLUDE[sid](df)
            s["state"] = "done" if rc == 0 else "done (verificar π com reasoning)"
        except Exception:                                  # the run is safe on disk; only the read-out failed
            s.update(state="done (sem conclusão)", error=traceback.format_exc(limit=3))
        s["ended"] = _now()
        _save(st)
        print(f"[{sid}] {s['state']} in {s['minutes']} min")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

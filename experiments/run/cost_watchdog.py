"""Cost watchdog for the bloco C queues (user request 2026-10-15: the author pays; no surprises).

Every minute it reads spend and, if a cap is crossed, STOPS that provider's queue (launcher + runners):
  * DeepInfra: the provider's OWN billing for the current month (GET /payment/usage), in USD -- the truth,
    not our estimate (pricing.yaml prices proved stale: GLM-5.1 was billed as GLM-5.3, Qwen output dearer).
  * OpenAI: our spend journal since --since (the project key lacks the api.usage.read scope, so the
    provider's figure is not readable; GPT-5.1 prices in pricing.yaml match the public list price).
Prints one status line every --every minutes and one line whenever a cap fires. Read-only otherwise.

  python -m experiments.run.cost_watchdog --deepinfra-cap-usd 25 --openai-cap-eur 55
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from experiments.harness.env import load_env

REPO_ROOT = Path(__file__).resolve().parents[2]
LEDGER = REPO_ROOT / "data" / "processed" / "_spend.json"
JOURNAL = REPO_ROOT / "data" / "processed" / "_spend_journal.jsonl"
QUEUES = {
    "deepinfra": ["experiments.run.bloco_c_run c2", "c1_context_roster", "whole_exam_runner",
                  "conversation_runner", "c2_decomposition"],
    "openai": ["experiments.run.bloco_c_run c1_gpt", "c1_context_gpt", "c5_anchor_full"],
}


def deepinfra_month_usd() -> float:
    period = datetime.now(timezone.utc).strftime("%Y.%m")
    req = urllib.request.Request(f"https://api.deepinfra.com/payment/usage?from={period}",
                                 headers={"Authorization": f"Bearer {os.environ['DEEPINFRA_API_KEY']}"})
    d = json.loads(urllib.request.urlopen(req, timeout=30).read())
    return sum(it["cost"] for m in d["months"] if m["period"] == period for it in m["items"]) / 100  # cents


def openai_eur_since(since: str) -> float:
    tot = 0.0
    if LEDGER.exists():
        tot += sum(e["cost_eur"] for e in json.loads(LEDGER.read_text())["entries"]
                   if e["ts"] >= since and e.get("meta", {}).get("provider") == "openai")
    if JOURNAL.exists():
        for line in JOURNAL.read_text().splitlines():
            if line.strip():
                e = json.loads(line)
                if e["ts"] >= since and e.get("meta", {}).get("provider") == "openai":
                    tot += e["cost_eur"]
    return tot


def stop(provider: str) -> None:
    for pat in QUEUES[provider]:
        subprocess.run(["pkill", "-f", pat], capture_output=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deepinfra-cap-usd", type=float, default=25.0, help="month-to-date, provider-billed")
    ap.add_argument("--openai-cap-eur", type=float, default=55.0, help="spend since --since, our journal")
    ap.add_argument("--since", default="2026-10-15")
    ap.add_argument("--every", type=int, default=10, help="minutes between status lines")
    args = ap.parse_args(argv)
    load_env()
    fired, last_print = set(), 0.0
    while True:
        try:
            di = deepinfra_month_usd()
        except Exception as e:                     # network blip: report, keep watching
            di = None
            print(f"[watchdog] DeepInfra billing unreadable: {type(e).__name__}", flush=True)
        oa = openai_eur_since(args.since)
        now = time.time()
        if di is not None and di > args.deepinfra_cap_usd and "deepinfra" not in fired:
            stop("deepinfra"); fired.add("deepinfra")
            print(f"[watchdog] CAP HIT DeepInfra ${di:.2f} > ${args.deepinfra_cap_usd:.0f}: DeepInfra queue STOPPED", flush=True)
        if oa > args.openai_cap_eur and "openai" not in fired:
            stop("openai"); fired.add("openai")
            print(f"[watchdog] CAP HIT OpenAI €{oa:.2f} > €{args.openai_cap_eur:.0f}: OpenAI queue STOPPED", flush=True)
        if now - last_print >= args.every * 60:
            di_s = f"${di:.2f}" if di is not None else "?"
            print(f"[watchdog] {datetime.now().strftime('%H:%M')} DeepInfra (faturado, mês) {di_s} / "
                  f"${args.deepinfra_cap_usd:.0f} · OpenAI (registo, hoje) €{oa:.2f} / €{args.openai_cap_eur:.0f}",
                  flush=True)
            last_print = now
        live = subprocess.run(["pgrep", "-f", "experiments.run.bloco_c_run"], capture_output=True).returncode == 0
        if not live:
            print(f"[watchdog] queues finished · DeepInfra ${di:.2f} · OpenAI €{oa:.2f}" if di is not None
                  else f"[watchdog] queues finished · OpenAI €{oa:.2f}", flush=True)
            return 0
        time.sleep(60)


if __name__ == "__main__":
    raise SystemExit(main())

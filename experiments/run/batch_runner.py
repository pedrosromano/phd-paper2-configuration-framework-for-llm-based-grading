"""Batch API runner (Pedro's review, 2026-10-16): grade a matrix arm's uncached cells through the OpenAI
Batch API or the Anthropic Message Batches API, both at half the per-token price, and collect the results
into the arm's store with exactly the row schema of the synchronous runner (same prompts, same request
bodies, same parser via adapter_api.result_from_body). The spend ledger records the discounted price; the
paper re-prices every call from its tokens at standard rates (phase5.prepare), so batch and synchronous
cells are costed alike.

  python -m experiments.run.batch_runner submit  --arm i3_sonnet     # one or more batches; state in _batches/
  python -m experiments.run.batch_runner status  --arm i3_sonnet
  python -m experiments.run.batch_runner collect --arm i3_sonnet     # idempotent; stores finished results
  python -m experiments.run.batch_runner wait    --arm i3_sonnet     # poll every minute, then collect

Results that fail or expire are not stored, so a later submit sends them again.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import yaml

from experiments.configs.config import Config
from experiments.harness import adapter_api, prompts, store
from experiments.harness.cost_guard import CostGuard, load_pricing
from experiments.harness.env import load_env
from experiments.run import matrix

STATE_DIR = matrix.RUNS_FILE.parent / "_batches"
CHUNK = {"openai": 20000, "anthropic": 10000}       # requests per batch (well under both providers' caps)
BATCH_FACTOR = 0.5


def _log(msg: str) -> None:
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {msg}", flush=True)


def _ctx(arm_name: str):
    spec = yaml.safe_load(matrix.MATRIX.read_text())
    arm = next(a for a in spec["arms"] if a["name"] == arm_name)
    corpus = pd.read_parquet(matrix.CORPUS)
    by_id = {r["item_id"]: r for _, r in corpus.iterrows()}
    tasks = matrix._arm_tasks(arm, matrix.Sampler(spec, corpus), by_id, matrix.DEFAULT_SEED, {})
    st = matrix._store_for(arm, {})
    return arm, by_id, tasks, st


def _state_path(arm_name: str) -> Path:
    return STATE_DIR / f"{arm_name}.json"


def _load_state(arm_name: str) -> dict:
    p = _state_path(arm_name)
    return json.loads(p.read_text()) if p.exists() else {"arm": arm_name, "batches": [], "map": {}}


def _save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    _state_path(state["arm"]).write_text(json.dumps(state))


def _headers(provider: str) -> dict:
    load_env()
    if provider == "openai":
        return {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"}
    return {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01",
            "content-type": "application/json"}


def submit(arm_name: str, limit: int | None = None) -> int:
    arm, by_id, tasks, st = _ctx(arm_name)
    state = _load_state(arm_name)
    pending = {v["key"] for v in state["map"].values() if not v.get("done")}
    guard = CostGuard(); pricing = load_pricing()
    todo = []
    for it, c in tasks:
        key = f"{it['item_id']}|{c.config_hash}|{c.run_index}"
        if st.has(it["item_id"], c.config_hash, c.run_index) or key in pending:
            continue
        todo.append((it, c, key))
    todo = todo[:limit] if limit else todo
    if not todo:
        _log(f"{arm_name}: nothing to submit ({len(tasks)} cells, all cached or pending)")
        return 0
    providers = {guard.provider_of(c.model) for _, c, _ in todo}
    if len(providers) != 1 or next(iter(providers)) not in CHUNK:
        raise SystemExit(f"one Batch API provider per arm, got {providers}")
    provider = providers.pop()
    # pre-flight: input from the rendered prompt (~4 chars per token), output as in the synchronous runs
    est = sum(guard.cost_eur(c.model, len(prompts.render(c, it)) / 4 * (1.19 if provider == "anthropic" else 1.0), 16)
              for it, c, _ in todo) * BATCH_FACTOR
    _log(f"{arm_name}: {len(todo)} requests to {provider}, estimated €{est:.2f} at the batch price; "
         f"spent €{guard.spent_for(provider):.2f} of €{guard.ceiling_for(provider):.0f}")
    if guard.spent_for(provider) + est > guard.ceiling_for(provider):
        raise SystemExit("REFUSED: the estimate would breach this provider's ceiling")
    H = _headers(provider)
    n0 = len(state["map"])
    for start in range(0, len(todo), CHUNK[provider]):
        chunk = todo[start:start + CHUNK[provider]]
        reqs, ids = [], []
        for j, (it, c, key) in enumerate(chunk):
            cid = f"r{n0 + start + j:07d}"
            mcfg = dict(pricing["models"][c.model]); mcfg.setdefault("model_id", c.model)
            prompt = prompts.render(c, it)
            body = (adapter_api.build_anthropic_payload(mcfg, prompt, c) if provider == "anthropic"
                    else adapter_api._build_payload(mcfg, prompt, c))
            reqs.append({"custom_id": cid, "params": body} if provider == "anthropic" else
                        {"custom_id": cid, "method": "POST", "url": "/v1/chat/completions", "body": body})
            state["map"][cid] = {"key": key, "item_id": str(it["item_id"]), "config": asdict(c)}
            ids.append(cid)
        if provider == "anthropic":
            r = requests.post("https://api.anthropic.com/v1/messages/batches", headers=H, json={"requests": reqs},
                              timeout=600)
            r.raise_for_status(); bid = r.json()["id"]
        else:
            buf = io.BytesIO("\n".join(json.dumps(x) for x in reqs).encode("utf-8"))
            f = requests.post("https://api.openai.com/v1/files", headers=H, files={"file": ("batch.jsonl", buf)},
                              data={"purpose": "batch"}, timeout=600)
            f.raise_for_status()
            r = requests.post("https://api.openai.com/v1/batches", headers={**H, "Content-Type": "application/json"},
                              json={"input_file_id": f.json()["id"], "endpoint": "/v1/chat/completions",
                                    "completion_window": "24h"}, timeout=120)
            r.raise_for_status(); bid = r.json()["id"]
        state["batches"].append({"id": bid, "provider": provider, "n": len(reqs), "ids": [ids[0], ids[-1]],
                                 "submitted": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                 "collected": False})
        _save_state(state)
        _log(f"  batch {bid}: {len(reqs)} requests")
    return 0


def _batch_status(b: dict) -> tuple[bool, dict]:
    H = _headers(b["provider"])
    if b["provider"] == "anthropic":
        j = requests.get(f"https://api.anthropic.com/v1/messages/batches/{b['id']}", headers=H, timeout=120).json()
        return j.get("processing_status") == "ended", j
    j = requests.get(f"https://api.openai.com/v1/batches/{b['id']}", headers=H, timeout=120).json()
    return j.get("status") in ("completed", "failed", "expired", "cancelled"), j


def status(arm_name: str) -> int:
    state = _load_state(arm_name)
    for b in state["batches"]:
        done, j = _batch_status(b)
        counts = j.get("request_counts")
        _log(f"{b['id']} {b['provider']} n={b['n']} done={done} collected={b['collected']} "
             f"status={j.get('processing_status') or j.get('status')} counts={counts}")
    return 0


def _results(b: dict, j: dict) -> list[tuple[str, dict | None]]:
    H = _headers(b["provider"])
    out = []
    if b["provider"] == "anthropic":
        text = requests.get(j["results_url"], headers=H, timeout=600).text
        for line in text.splitlines():
            if line.strip():
                x = json.loads(line)
                res = x.get("result", {})
                out.append((x["custom_id"], res.get("message") if res.get("type") == "succeeded" else None))
    else:
        if j.get("output_file_id"):
            text = requests.get(f"https://api.openai.com/v1/files/{j['output_file_id']}/content", headers=H,
                                timeout=600).text
            for line in text.splitlines():
                if line.strip():
                    x = json.loads(line)
                    resp = x.get("response") or {}
                    out.append((x["custom_id"], resp.get("body") if resp.get("status_code") == 200 else None))
    return out


def collect(arm_name: str) -> int:
    arm, by_id, _, st = _ctx(arm_name)
    state = _load_state(arm_name)
    guard = CostGuard()
    for b in state["batches"]:
        if b["collected"]:
            continue
        done, j = _batch_status(b)
        if not done:
            _log(f"{b['id']}: not finished yet")
            continue
        ok = failed = 0
        for cid, body in _results(b, j):
            m = state["map"].get(cid)
            if m is None:
                continue
            if body is None:
                failed += 1
                state["map"].pop(cid)           # not stored -> a later submit sends it again
                continue
            c = Config(**m["config"])
            item = by_id[m["item_id"]]
            if not st.has(item["item_id"], c.config_hash, c.run_index):
                res = adapter_api.result_from_body(body, c, guard, 0.0, price_factor=BATCH_FACTOR)
                st.append(store.build_run_row(item, c, res, prompts.render(c, item)))
            m["done"] = True
            ok += 1
        b["collected"] = True
        _save_state(state)
        _log(f"{b['id']}: stored {ok} rows, {failed} failed (resubmit them later)")
    _log(f"{arm_name}: {b['provider'] if state['batches'] else ''} spend €{guard.spent_for(b['provider']):.2f}"
         if state["batches"] else f"{arm_name}: no batches")
    return 0


def wait(arm_name: str, every: int = 60) -> int:
    while True:
        state = _load_state(arm_name)
        open_ = [b for b in state["batches"] if not b["collected"]]
        if not open_:
            break
        if all(_batch_status(b)[0] for b in open_):
            collect(arm_name)
            break
        time.sleep(every)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["submit", "status", "collect", "wait"])
    ap.add_argument("--arm", required=True)
    ap.add_argument("--limit", type=int, default=None, help="cap the requests of a submit (validation)")
    a = ap.parse_args(argv)
    return {"submit": lambda: submit(a.arm, a.limit), "status": lambda: status(a.arm),
            "collect": lambda: collect(a.arm), "wait": lambda: wait(a.arm)}[a.cmd]()


if __name__ == "__main__":
    raise SystemExit(main())

"""Read-only live monitor for experiment runs (a tiny localhost web dashboard).

Serves http://127.0.0.1:8765 with a page that polls /status.json and shows, live: the
active arm's progress + ETA, π, throughput, cost vs the two ceilings, latency, errors /
truncations, and the tail of the newest run log. Generic: it reflects whatever is writing
to data/processed/runs/runs.jsonl + runs/*.log, so it works for THIS run and any future one.

SAFETY -- strictly read-only, cannot disturb a running experiment:
  * only reads runs.jsonl (append-only) via an INCREMENTAL tail (no full re-read per poll),
    and the newest *.log; writes nothing the runner touches (nothing at all but HTTP).
  * tolerates the partial last line of a live append, and a runs.jsonl REPLACEMENT (the
    archive step) by detecting shrink and re-reading from 0.
  * cost is summed from the run rows themselves, NOT from _spend.json (which the cost guard
    writes under a lock) -- we never even open that file.
  * binds to localhost only; GET-only handler; pgrep for the LIVE badge is read-only.

  python -m experiments.run.monitor            # serve on :8765
  python -m experiments.run.monitor --port 9000
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import threading
from collections import deque
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = REPO_ROOT / "data" / "processed" / "runs"
RUNS_FILE = RUNS_DIR / "runs.jsonl"
PRICING = REPO_ROOT / "experiments" / "configs" / "pricing.yaml"
_PROG = re.compile(r"([\d,]+)/([\d,]+).*?(?:π|pi)=([\d.]+)")   # "8,340/13,635  π=0.951" (matrix) or "pi=" (runners)
BLOCO_C = RUNS_DIR / "_bloco_c_status.json"                      # written by experiments.run.bloco_c_run
BLOCO_C_PLAN = RUNS_DIR / "_bloco_c_plan.json"                   # per-step new calls + effective s/call
_SPEND = re.compile(r"DeepInfra €([\d.]+) \| OpenAI €([\d.]+)")
_ARMS = re.compile(r"arms=(\[[^\]]*\])")


def _ceilings() -> dict:
    p = yaml.safe_load(PRICING.read_text())
    return {"deepinfra": float(p.get("deepinfra_budget_eur_ceiling", 150)),
            "openai": float(p.get("budget_eur_ceiling", 150))}


class State:
    """Incremental aggregates over runs.jsonl (tail-safe). All scalars + bounded deques --
    never holds the rows, so memory and per-poll cost stay tiny."""

    def __init__(self):
        self.lock = threading.Lock()
        self.offset = 0
        self.buf = b""
        self.total = 0
        self.ok = 0
        self.err = 0
        self.trunc = 0
        self.stalls = 0
        self.cost = {"deepinfra": 0.0, "openai": 0.0}
        self.recent_ts = deque(maxlen=20000)      # for throughput (last 5 min)
        self.recent_lat = deque(maxlen=3000)      # for median/p95
        self.recent_ok = deque(maxlen=3000)       # for live π
        self.ceil = _ceilings()

    def _ingest(self, r: dict) -> None:
        self.total += 1
        pok = bool(r.get("parse_ok"))
        self.ok += pok
        self.recent_ok.append(pok)
        if r.get("error"):
            self.err += 1
        if r.get("finish_reason") == "length":
            self.trunc += 1
        c = r.get("cost_eur")
        if isinstance(c, (int, float)):
            self.cost[r.get("provider", "")] = self.cost.get(r.get("provider", ""), 0.0) + c
        try:
            lat = float(r.get("latency_s"))
            self.recent_lat.append(lat)
            if lat > 120:
                self.stalls += 1
        except (TypeError, ValueError):
            pass
        ts = r.get("ts")
        if ts:
            try:
                self.recent_ts.append(datetime.fromisoformat(ts))
            except ValueError:
                pass

    def tail(self) -> None:
        if not RUNS_FILE.exists():
            return
        size = RUNS_FILE.stat().st_size
        if size < self.offset:                    # truncated/replaced (e.g. archive step) -> reset
            self.__init__()
        with open(RUNS_FILE, "rb") as f:
            f.seek(self.offset)
            chunk = f.read()
            self.offset = f.tell()
        *lines, self.buf = (self.buf + chunk).split(b"\n")
        for l in lines:
            if l.strip():
                try:
                    self._ingest(json.loads(l))
                except json.JSONDecodeError:
                    pass

    def _newest_log(self) -> tuple[str, list[str]]:
        logs = [p for p in RUNS_DIR.glob("*.log") if p.name != "_monitor.log"]  # not our own log
        logs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        if not logs:
            return "", []
        return logs[0].name, logs[0].read_text(errors="replace").splitlines()

    def snapshot(self) -> dict:
        with self.lock:
            self.tail()
            name, lines = self._newest_log()
            live = subprocess.run(["pgrep", "-f", "experiments.run.(matrix run|whole_exam_runner|conversation_runner|bloco_c_run)"],
                                  capture_output=True).returncode == 0
            # active-arm progress from the log's latest "done/total π=" line
            done = total = None
            pi_log = None
            arms = ""
            for l in lines:
                m = _ARMS.search(l)
                if m:
                    arms = m.group(1)
                p = _PROG.search(l)
                if p:
                    done, total, pi_log = (int(p.group(1).replace(",", "")),
                                           int(p.group(2).replace(",", "")), float(p.group(3)))
            finished = any(("DONE in" in l or "REFUSED" in l or "FAIL" in l) for l in lines[-6:])
            # throughput over the last 5 min
            now = datetime.now(timezone.utc)
            recent = [t for t in self.recent_ts if (now - t).total_seconds() <= 300]
            rate = len(recent) / 300 if recent else 0.0          # rows/sec
            remaining = (total - done) if (total and done is not None) else None
            eta = (remaining / rate) if (remaining and rate > 0) else None
            lat = sorted(self.recent_lat)
            pi_live = (sum(self.recent_ok) / len(self.recent_ok)) if self.recent_ok else None
            return {
                "now": now.strftime("%H:%M:%S UTC"), "live": live, "finished": finished,
                "log": name, "arms": arms, "done": done, "total": total,
                "pct": round(100 * done / total, 1) if (total and done is not None) else None,
                "eta_s": round(eta) if eta else None,
                "rate_min": round(rate * 60, 1),
                "pi_log": pi_log, "pi_live": round(pi_live, 4) if pi_live is not None else None,
                "pi_overall": round(self.ok / self.total, 4) if self.total else None,
                "rows": self.total, "errors": self.err, "truncated": self.trunc, "stalls": self.stalls,
                "lat_med": round(lat[len(lat) // 2], 1) if lat else None,
                "lat_p95": round(lat[int(len(lat) * 0.95)], 1) if lat else None,
                "cost": {k: round(v, 2) for k, v in self.cost.items()}, "ceil": self.ceil,
                "tail": lines[-10:],
            }


_STATE = State()

_PAGE = """<!doctype html><meta charset=utf-8><title>experiment monitor</title>
<style>
 body{background:#0d1117;color:#c9d1d9;font:13px ui-monospace,Menlo,monospace;margin:0;padding:18px}
 h1{font-size:15px;margin:0 0 12px} .muted{color:#8b949e}
 .badge{padding:2px 8px;border-radius:10px;font-weight:700}
 .live{background:#1f6f3f;color:#aff5c6} .idle{background:#30363d;color:#8b949e}
 .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px;margin:12px 0}
 .card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:10px}
 .k{color:#8b949e;font-size:11px} .v{font-size:20px;font-weight:700} .s{font-size:11px;color:#8b949e}
 .bar{height:14px;background:#21262d;border-radius:7px;overflow:hidden;margin-top:6px}
 .fill{height:100%;background:linear-gradient(90deg,#1f6feb,#2ea043);width:0}
 pre{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:10px;overflow:auto;white-space:pre-wrap}
 .warn{color:#f0883e}
</style>
<h1>experiment monitor <span id=badge class=badge></span> <span class=muted id=now></span>
 <span class=muted>· read-only</span></h1>
<div class=card id=globalcard style="display:none;margin-bottom:10px"><div class=k>BLOCO C · progresso global</div>
 <div class=bar><div class=fill id=gfill></div></div><div class=s id=gprog></div></div>
<div class=card><div class=k id=armline>arm</div>
 <div class=bar><div class=fill id=fill></div></div>
 <div class=s id=prog></div></div>
<div class=grid id=cards></div>
<div id=blococ></div>
<pre id=tail></pre>
<script>
const C=(k,v,s)=>`<div class=card><div class=k>${k}</div><div class=v>${v??'–'}</div><div class=s>${s||''}</div></div>`;
function hms(s){if(s==null)return'–';let h=s/3600|0,m=(s%3600)/60|0;return h?`${h}h${String(m).padStart(2,'0')}m`:`${m}m`}
async function tick(){
 let d; try{d=await (await fetch('/status.json')).json()}catch(e){return}
 const b=document.getElementById('badge');
 b.textContent=d.live?'● LIVE':(d.finished?'done':'idle'); b.className='badge '+(d.live?'live':'idle');
 document.getElementById('now').textContent=d.now+'  ·  log: '+d.log;
 document.getElementById('armline').textContent=(d.arms||'')+(d.done!=null?`   ${d.done.toLocaleString()}/${d.total.toLocaleString()}`:'');
 document.getElementById('fill').style.width=(d.pct||0)+'%';
 document.getElementById('prog').textContent=(d.pct!=null?d.pct+'%   ':'')+'ETA '+hms(d.eta_s)+'   ·   '+d.rate_min+' rows/min';
 const pi=d.pi_live!=null?d.pi_live:d.pi_overall;
 document.getElementById('cards').innerHTML=[
  C('π (recent)',pi,'overall '+(d.pi_overall??'–')),
  C('rows logged',(d.rows||0).toLocaleString(),''),
  C('€ DeepInfra',d.cost.deepinfra,'/ '+d.ceil.deepinfra),
  C('€ OpenAI',d.cost.openai,'/ '+d.ceil.openai),
  C('latency',d.lat_med!=null?d.lat_med+'s':'–','p95 '+(d.lat_p95??'–')+'s'),
  C('truncated@cap',d.truncated,(d.truncated?'<span class=warn>check cap</span>':'')),
  C('errors',d.errors,''),
  C('infra stalls',d.stalls,'>120s'),
 ].join('');
 document.getElementById('tail').textContent=(d.tail||[]).join('\\n');
 let b2; try{b2=await (await fetch('/bloco_c.json')).json()}catch(e){b2=null}
 const el=document.getElementById('blococ');
 if(!b2||!b2.steps){el.innerHTML='';return}
 let plan; try{plan=await (await fetch('/bloco_c_plan.json')).json()}catch(e){plan=null}
 if(plan&&plan.order){
  let tT=0,dT=0,tC=0,dC=0;
  for(const id of plan.order){const p=plan[id], s=b2.steps.find(x=>x.id==id), w=p.todo*p.spc; tT+=w; tC+=p.todo;
   let f=0; if(s&&(s.state.startsWith('done')||s.state=='analysing'))f=1;
   else if(s&&s.state=='running'&&d.total)f=Math.min(1,d.done/d.total);
   dT+=f*w; dC+=f*p.todo;}
  const pt=100*dT/tT, pc=100*dC/tC;
  document.getElementById('globalcard').style.display='block';
  document.getElementById('gfill').style.width=pt.toFixed(1)+'%';
  document.getElementById('gprog').textContent=`${pt.toFixed(0)}% do tempo estimado · ${pc.toFixed(0)}% das chamadas (${Math.round(dC).toLocaleString()}/${tC.toLocaleString()}) · faltam ~${hms(tT-dT)}`;
 }
 const col={pending:'#30363d',running:'#1f6feb',analysing:'#8957e5',failed:'#da3633'};
 el.innerHTML='<h1 style="margin-top:16px">Bloco C <span class=muted>· atualizado '+(b2.updated||'')+'</span></h1>'+
  b2.steps.map(s=>{const c=col[s.state]||'#1f6f3f';
   const t=(s.started?'início '+s.started.slice(11,16):'')+(s.minutes!=null?' · '+s.minutes+' min':'');
   const body=(s.conclusion||[]).map(x=>'<div>• '+x+'</div>').join('')+(s.error?'<div class=warn>'+s.error+'</div>':'');
   return `<div class=card style="margin:8px 0"><span class=badge style="background:${c};color:#fff">${s.state}</span>
    <b> ${s.title}</b> <span class=s>${t}</span><div style="margin-top:6px">${body}</div></div>`}).join('');
}
tick(); setInterval(tick,4000);
</script>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):                              # GET-only; no write routes exist
        if self.path.startswith("/status"):
            body = json.dumps(_STATE.snapshot()).encode()
            ctype = "application/json"
        elif self.path.startswith("/bloco_c_plan"):
            body = BLOCO_C_PLAN.read_bytes() if BLOCO_C_PLAN.exists() else b"{}"
            ctype = "application/json"
        elif self.path.startswith("/bloco_c"):
            body = BLOCO_C.read_bytes() if BLOCO_C.exists() else b"{}"
            ctype = "application/json"
        else:
            body = _PAGE.encode()
            ctype = "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):                     # silence request logging
        pass


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args(argv)
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"monitor (read-only) -> http://127.0.0.1:{args.port}   (Ctrl-C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

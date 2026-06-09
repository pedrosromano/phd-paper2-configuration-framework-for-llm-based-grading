"""Scientific-integrity audit of runs.jsonl (READ-ONLY; safe while a run is live).

After many restarts / kills / a max_tokens change / a backoff change, this confirms the
data is sound enough to analyse: no corrupt or merged lines from a kill, no duplicate cells,
every stored config_hash matches its own denormalised fields (no drift/collision), the
reasoning-ON re-run is cleanly separated (4096 vs 32768) and never bled into OFF, scores are
in range and consistent with parse_ok, gold matches the corpus (so agreement metrics aren't
computed against wrong references), and the run-invariants (temp/top_p/template version) are
uniform. Prints PASS/FAIL per check.

  python -m experiments.run.integrity_audit
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import pandas as pd

from experiments.configs.config import Config

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS = REPO_ROOT / "data" / "processed" / "runs" / "runs.jsonl"
CORPUS = REPO_ROOT / "data" / "processed" / "corpus.parquet"

_RESULTS = []


def check(name: str, ok: bool, detail="") -> None:
    _RESULTS.append(ok)
    d = str(detail)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}{('  -> ' + d) if d else ''}")


def main() -> int:
    raw = RUNS.read_text().splitlines()
    rows, malformed = [], []
    for i, l in enumerate(raw):
        if not l.strip():
            continue
        try:
            rows.append(json.loads(l))
        except json.JSONDecodeError:
            malformed.append(i)
    n_lines = len(raw)
    print(f"runs.jsonl: {n_lines:,} lines, {len(rows):,} parsed rows\n")

    # 1. line integrity -- a malformed line in the MIDDLE = a kill corrupted it; the LAST line
    #    may just be a live append in progress (not corruption).
    midfile = [m for m in malformed if m != n_lines - 1]
    check("no mid-file corrupt/merged lines (from kills)", not midfile,
          f"{len(midfile)} malformed mid-file lines at {midfile[:5]}" if midfile else
          ("last line is a live partial append (ok)" if malformed else "0 malformed"))

    # 2. no duplicate cache keys (a cell graded+appended twice across restarts)
    keys = Counter((r["item_id"], r["config_hash"], r["run_index"]) for r in rows)
    dups = {k: c for k, c in keys.items() if c > 1}
    check("no duplicate (item_id, config_hash, run_index)", not dups,
          f"{len(dups)} duplicated keys, e.g. {list(dups)[:3]}" if dups else f"{len(keys):,} unique cells")

    # 3. config_hash integrity: recompute from each row's denormalised fields -> must match
    #    the stored hash (catches corruption / hash<->fields drift / collisions).
    mism = 0
    sample = rows if len(rows) <= 60000 else rows[::max(1, len(rows) // 60000)]
    for r in sample:
        try:
            c = Config(dataset=r["dataset"], domain=r["domain"], model=r["model"],
                       reasoning=r["reasoning"], context_level=r["context_level"],
                       scope=r["scope"], decomposition=r["decomposition"],
                       conversation_state=r.get("conversation_state", "none"),
                       temperature=r["temperature"], top_p=r["top_p"],
                       max_tokens=r["max_tokens"], seed=r["seed"], run_index=r["run_index"])
            mism += (c.config_hash != r["config_hash"])
        except Exception:
            mism += 1
    check("stored config_hash == recomputed from fields", mism == 0,
          f"{mism}/{len(sample)} mismatches" if mism else f"{len(sample):,} rows verified")

    # 4. each config_hash maps to ONE consistent config (no collision / inconsistent denorm)
    cols = ["dataset", "domain", "model", "reasoning", "context_level", "scope",
            "decomposition", "conversation_state", "temperature", "top_p", "max_tokens", "seed"]
    bad_hash = 0
    by_hash: dict = {}
    for r in rows:
        sig = tuple(r.get(c) for c in cols)
        if r["config_hash"] in by_hash and by_hash[r["config_hash"]] != sig:
            bad_hash += 1
        by_hash[r["config_hash"]] = sig
    check("each config_hash has one consistent config", bad_hash == 0,
          f"{bad_hash} inconsistent rows" if bad_hash else f"{len(by_hash)} distinct cells")

    # 5. reasoning-ON token budgets are only {4096 superseded, 32768 re-run}; OFF only 4096
    on_mt = Counter(r["max_tokens"] for r in rows if r["reasoning"] == "on")
    off_mt = Counter(r["max_tokens"] for r in rows if r["reasoning"] == "off")
    check("reasoning-ON max_tokens in {4096, 32768} only", set(on_mt) <= {4096, 32768}, dict(on_mt))
    check("reasoning-OFF never re-run at 32768 (clean separation)", 32768 not in off_mt, dict(off_mt))

    # 6. score sanity: parse_ok <=> score present; ABOVE-max is a real concern (fail);
    #    BELOW-0 is expected for PT-CS criterion rubrics with penalty criteria -> clamp to
    #    [0,max] in Phase 5, not corruption (informational, doesn't fail integrity).
    bad, below0 = [], []
    for r in rows:
        s, mx = r["score"], r.get("gold_scale_max")
        if r["parse_ok"] and s is None:
            bad.append("ok_but_none")
        elif (not r["parse_ok"]) and s is not None:
            bad.append("notok_but_score")
        elif r["parse_ok"] and s is not None and isinstance(mx, (int, float)) and not math.isnan(mx):
            if s > mx + 1e-6:
                bad.append("above_max")
            elif s < -1e-6:
                below0.append(r)
    check("scores valid (parse_ok consistent, none above scale max)", not bad,
          dict(Counter(bad)) if bad else "no corruption / no above-max")
    if below0:
        ds = Counter((r["dataset"], r["decomposition"]) for r in below0)
        print(f"  note: {len(below0)} below-0 scores ({len(set(r['item_id'] for r in below0))} items) "
              f"from penalty criteria {dict(ds)} -> clamp to [0,max] in Phase 5 (expected, not corruption)")

    # 7. gold matches the corpus (agreement is computed against the RIGHT reference)
    corpus = pd.read_parquet(CORPUS)[["item_id", "gold_score", "gold_scale_max"]]
    cg = {str(r.item_id): (r.gold_score, r.gold_scale_max) for r in corpus.itertuples()}
    gbad = 0
    for r in rows:
        ref = cg.get(str(r["item_id"]))
        if ref is None:
            gbad += 1
            continue
        gs, gm = ref
        if not _eq(r.get("gold_score"), gs) or not _eq(r.get("gold_scale_max"), gm):
            gbad += 1
    check("row gold matches corpus (right reference)", gbad == 0,
          f"{gbad} rows with wrong/missing gold" if gbad else f"{len(rows):,} rows checked")

    # 8. run invariants uniform
    tpv = {r.get("prompt_template_version") for r in rows}
    temps = {r["temperature"] for r in rows}
    tops = {r["top_p"] for r in rows}
    check("single prompt_template_version", len(tpv) == 1, str(tpv))
    check("temperature==0 and top_p==1 everywhere", temps == {0.0} and tops == {1.0},
          f"temps={temps} top_p={tops}")

    # 9. errors are rows, never lost; report π and error/truncation counts (informational)
    errs = sum(1 for r in rows if r.get("error"))
    trunc32 = sum(1 for r in rows if r["reasoning"] == "on" and r["max_tokens"] == 32768
                  and r.get("finish_reason") == "length")
    on32 = sum(1 for r in rows if r["reasoning"] == "on" and r["max_tokens"] == 32768)
    print(f"\n  info: error-rows={errs} | reasoning-ON@32768={on32:,} "
          f"(residual truncated={trunc32}, {100*trunc32/max(on32,1):.1f}%)")

    ok = all(_RESULTS)
    print(f"\n{'='*60}\nINTEGRITY: {'ALL PASS' if ok else 'FAILURES PRESENT'} "
          f"({sum(_RESULTS)}/{len(_RESULTS)} checks)\n{'='*60}")
    return 0 if ok else 1


def _eq(a, b) -> bool:
    try:
        fa, fb = float(a), float(b)
        if math.isnan(fa) and math.isnan(fb):
            return True
        return abs(fa - fb) < 1e-6
    except (TypeError, ValueError):
        return a == b


if __name__ == "__main__":
    raise SystemExit(main())

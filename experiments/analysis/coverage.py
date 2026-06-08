"""Schema-coverage matrix (the answer to "is the run-row schema complete for Phase 5/6/7?").

For every planned downstream output it lists the run-row FIELDS that output consumes, then
checks each field against the AUTHORITATIVE schema emitted by store.build_run_row. The
consumed-field lists for 5.2-5.5 come straight from the metric functions' `consumes`
declarations (so they can't drift from the code); the rest are declared here. Run:

    python -m experiments.analysis --coverage
"""

from __future__ import annotations

from experiments.analysis import metrics as M


def schema_fields() -> set[str]:
    """The exact keys store.build_run_row writes -- built from a representative row so the
    matrix is checked against the real schema, not a copy that could drift."""
    from experiments.configs.config import Config
    from experiments.harness.grading import GradeResult
    from experiments.harness.store import build_run_row

    item = {"item_id": "x", "question_id": "q", "submission_id": "s",
            "gold_score": 4.0, "gold_scale_max": 5.0}
    cfg = Config("ptcs", "code", "qwen3.5", scope="whole_exam", decomposition="criterion",
                 conversation_state="shared")
    res = GradeResult(score=4.0, parse_ok=True, raw="{}", tokens_in=10, tokens_out=5,
                      latency_s=1.0, model="qwen3.5", reasoning="on", config_hash=cfg.config_hash,
                      reasoning_tokens=3, finish_reason="stop", cost_eur=0.0001)
    row = build_run_row(item, cfg, res, "PROMPT", session_id="sess", order_id="o", order_index=0)
    return set(row.keys())


# Planned outputs -> the run-row fields they consume. 5.2-5.5 pull from the metric code.
def _output_consumes() -> dict[str, tuple[str, ...]]:
    metric = {f"5.2/5.5 metric: {fn.__name__}": fn.consumes for fn in M.METRIC_FUNCS}
    declared = {
        "5.1 aggregate (per-cell records)": (
            "item_id", "config_hash", "run_index", "dataset", "domain", "model", "model_id",
            "provider", "reasoning", "context_level", "scope", "decomposition",
            "conversation_state", "score", "parse_ok", "prompt_tokens", "completion_tokens",
            "latency_s", "cost_eur", "error"),
        "5.5b transfer (public vs PT-CS ranking)": (
            "dataset", "config_hash", "score", "gold_score", "gold_scale_max"),
        "5.6 framework decision guide": (
            "dataset", "domain", "context_level", "scope", "decomposition", "reasoning",
            "model", "cost_eur", "completion_tokens", "score", "gold_score", "gold_scale_max"),
        "6.2 reasoning on/off deltas": (
            "reasoning", "domain", "dataset", "score", "gold_score", "gold_scale_max",
            "cost_eur", "completion_tokens"),
        "6.3 cost-vs-agreement scatter": (
            "model", "config_hash", "cost_eur", "completion_tokens", "provider",
            "score", "gold_score", "gold_scale_max"),
        "6.4 consistency plot": ("item_id", "config_hash", "run_index", "score"),
        "6.6 scope + conversation sub-study": (
            "scope", "conversation_state", "session_id", "order_id", "order_index",
            "question_id", "submission_id", "score", "gold_score", "gold_scale_max"),
        "pi / extractable-rate (CLAUDE.md §6.2)": ("parse_ok", "error"),
        "7.1 backend-conditional reproducibility": (
            "provider", "model_id", "quant", "seed", "temperature", "top_p", "max_tokens",
            "prompt_template_version", "finish_reason"),
        "offline re-parse safety net": ("raw", "prompt", "prompt_hash"),
    }
    return {**declared, **metric}


def build_matrix() -> tuple[list[dict], set[str]]:
    schema = schema_fields()
    rows = []
    for output, fields in _output_consumes().items():
        missing = [f for f in fields if f not in schema]
        rows.append({"output": output, "n_fields": len(fields),
                     "missing": missing, "ok": not missing})
    return rows, schema


def render(rows: list[dict], schema: set[str]) -> str:
    lines = ["SCHEMA-COVERAGE MATRIX  (planned output -> fields consumed -> logged?)", ""]
    width = max(len(r["output"]) for r in rows)
    for r in rows:
        status = "OK " if r["ok"] else "!! "
        miss = "" if r["ok"] else f"  MISSING: {r['missing']}"
        lines.append(f"  [{status}] {r['output']:<{width}}  {r['n_fields']:>2} fields{miss}")
    n_ok = sum(r["ok"] for r in rows)
    lines += ["", f"  {n_ok}/{len(rows)} outputs fully covered by the {len(schema)}-field schema."]
    # also surface fields that nothing consumes yet (kept deliberately, e.g. k, ts)
    used = {f for r in _output_consumes().values() for f in r}
    unused = sorted(schema - used)
    if unused:
        lines.append(f"  logged-but-not-yet-consumed (kept for provenance): {unused}")
    return "\n".join(lines)


def main() -> int:
    rows, schema = build_matrix()
    print(render(rows, schema))
    return 0 if all(r["ok"] for r in rows) else 1

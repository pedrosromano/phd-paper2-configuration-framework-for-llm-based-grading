"""Prompt renderer (Phase 3.2).

Composes the blocks in experiments/configs/prompts.yaml by the config's
(domain, context_level, scope, decomposition). The grounding TYPE (rubric vs reference)
is chosen from what the item actually carries: rubric_json -> rubric (PT-CS/RIAYN),
reference_answer -> reference (Mohler/SemEval). The question stem + student answer are
ALWAYS included; only the guidance varies (context_level). Reasoning on/off is a model
toggle, not part of the prompt.

Output is a single machine-parseable JSON object (holistic: {"score"}; criterion:
{"criteria",[...],"total"}; whole_exam: {"answers":[{question_id,...}]}).

CLI demo:  python -m experiments.harness.prompts
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from string import Template

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
PROMPTS = REPO_ROOT / "experiments" / "configs" / "prompts.yaml"
_BLOCKS: dict | None = None


def _blocks() -> dict:
    global _BLOCKS
    if _BLOCKS is None:
        _BLOCKS = yaml.safe_load(PROMPTS.read_text())
    return _BLOCKS


def rubric_to_text(rubric_json: str | None) -> str:
    """Render rubric_json into readable text. Handles PT-CS [{points,criteria}] and
    RIAYN {"rubric_text": ...}."""
    if not rubric_json:
        return ""
    try:
        obj = json.loads(rubric_json)
    except (json.JSONDecodeError, TypeError):
        return str(rubric_json).strip()
    if isinstance(obj, dict) and "rubric_text" in obj:
        return str(obj["rubric_text"]).strip()
    if isinstance(obj, list):
        lines = []
        for c in obj:
            pts = c.get("points", "?")
            crit = c.get("criteria") or c.get("criterion") or ""
            lines.append(f"- [{pts} mark(s)] {crit}")
        return "\n".join(lines)
    return str(obj).strip()


def _has(v) -> bool:
    """Present = not None, not NaN (parquet nulls round-trip as NaN), not empty/'nan'."""
    if v is None:
        return False
    if isinstance(v, float) and math.isnan(v):
        return False
    return str(v).strip() not in ("", "nan", "None")


def _grounding(config, item) -> str:
    """The grounding block for context_level, choosing rubric or reference from the item."""
    if config.context_level == "none":
        return ""
    b = _blocks()["grounding"]
    rubric = item.get("rubric_json")
    ref = item.get("reference_answer")
    if _has(rubric):
        block = Template(b["rubric"]).safe_substitute(grounding_body=rubric_to_text(rubric))
    elif _has(ref):
        block = Template(b["reference"]).safe_substitute(grounding_body=str(ref).strip())
    else:
        return ""   # item has no grounding -> behaves as no-guidance
    if config.context_level == "with_examples":
        examples = item.get("_examples", "(no examples supplied)")
        block += "\n" + Template(b["examples_header"]).safe_substitute(examples=examples)
    return block.strip()


def _join(*parts: str) -> str:
    return "\n\n".join(p.strip() for p in parts if p and p.strip())


def render(config, item) -> str:
    """Render a question-by-question prompt for one item (dict/Series with schema fields)."""
    b = _blocks()
    instruction = b["instruction"][config.domain]
    grounding = _grounding(config, item)
    body = Template(b["body"]["question_by_question"]).safe_substitute(
        question=str(item["question_text"]).strip(),
        answer=str(item["student_answer"]).strip())
    out_key = f"{config.scope}__{config.decomposition}"
    output = Template(b["output"][out_key]).safe_substitute(max=_fmt(item.get("gold_scale_max", 1)))
    return _join(instruction, grounding, body, output)


def render_whole_exam(config, items: list) -> str:
    """Render a whole-exam prompt for all questions of one PT-CS submission (list of items)."""
    b = _blocks()
    instruction = b["instruction"][config.domain]
    parts = []
    for it in items:
        seg = f"--- QUESTION (question_id={it['question_id']}) ---\n{str(it['question_text']).strip()}"
        if config.decomposition == "criterion" and it.get("rubric_json"):
            seg += f"\nRUBRIC:\n{rubric_to_text(it['rubric_json'])}"
        seg += f"\n\nSTUDENT ANSWER:\n{str(it['student_answer']).strip()}"
        parts.append(seg)
    exam = "\n\n".join(parts)
    out_key = f"{config.scope}__{config.decomposition}"
    output = Template(b["output"][out_key]).safe_substitute(max="the per-question maximum")
    return _join(instruction, exam, output)


def _fmt(x) -> str:
    try:
        f = float(x)
        return str(int(f)) if f.is_integer() else str(f)
    except (TypeError, ValueError):
        return str(x)


# --------------------------------------------------------------------------- demo
def _demo() -> int:
    import pandas as pd
    from experiments.configs.config import Config
    corpus = REPO_ROOT / "data" / "processed" / "corpus.parquet"
    if not corpus.exists():
        print("corpus.parquet not found -- run `make ingest` first.")
        return 1
    df = pd.read_parquet(corpus)

    code = df[df.dataset == "riayn"].iloc[0]
    sa = df[df.dataset == "mohler"].iloc[0]

    print("=" * 70, "\nCODE item (RIAYN) -- with_guidance/holistic/q-by-q\n" + "=" * 70)
    c = Config("riayn", "code", "qwen3.5", context_level="with_guidance")
    print(render(c, code)[:1400])

    print("\n" + "=" * 70, "\nSHORT-ANSWER item (Mohler) -- with_guidance/holistic/q-by-q\n" + "=" * 70)
    c2 = Config("mohler", "short_answer", "qwen3.5", context_level="with_guidance")
    print(render(c2, sa))

    print("\n" + "=" * 70, "\nPT-CS criterion-by-criterion (q-by-q)\n" + "=" * 70)
    ptcs = df[(df.dataset == "ptcs") & (df.domain == "code")].iloc[0]
    c3 = Config("ptcs", "code", "qwen3.5", context_level="with_guidance", decomposition="criterion")
    print(render(c3, ptcs)[:1200])

    print("\n" + "=" * 70, "\nPT-CS WHOLE-EXAM (holistic) -- one submission\n" + "=" * 70)
    sub = df[(df.dataset == "ptcs") & (df.submission_id == df[df.dataset == "ptcs"].submission_id.iloc[0])]
    c4 = Config("ptcs", "code", "qwen3.5", scope="whole_exam")
    print(render_whole_exam(c4, [r for _, r in sub.head(3).iterrows()])[:1400])
    return 0


if __name__ == "__main__":
    raise SystemExit(_demo())

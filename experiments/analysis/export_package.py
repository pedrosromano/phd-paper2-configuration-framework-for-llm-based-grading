"""Reproducibility package for the submission (Pedro, 2026-10-19: "a CSV with the results and a clean script with
only the important things"). Writes submission/reproducibility/grades.csv: every grade the models gave on the
public datasets (Mohler, SemEval, RIAYN) and on the two validation datasets (SAF, HARMOGEN-R), with the human
grade, as used in the paper (0-1 scale, clamped, reasoning-on fallbacks applied). No answer text and nothing
from PT-CS. The companion script submission/reproducibility/recompute.py recomputes the paper's agreement values
and intervals from this file alone.

  python -m experiments.analysis.export_package
"""

from __future__ import annotations

import pandas as pd

from experiments.analysis import instruction, phase5, verification

OUT = phase5.REPO_ROOT / "submission" / "reproducibility" / "grades.csv"
PUBLIC = ["mohler", "semeval", "riayn"]
MODEL = {"qwen3.5": "Qwen3.5-35B-A3B", "deepseek-v4-flash": "DeepSeek-V4-Flash", "glm-5.1": "GLM-5.1",
         "glm-5.1-or": "GLM-5.1", "gpt-5.1": "GPT-5.1", "claude-sonnet-4-6": "Claude Sonnet 4.6"}
INSTR = {"standard": "strict", "partial_credit": "partial_credit", "partial_credit_justified": "partial_credit_justified",
         # the prompt engineering against the zero-collapse (2026-11-05): the code prompt the guide uses on code, and the
         # round-1 candidate prompts A to E (Fig. 1 of the paper)
         "partial_credit_teacher_credit_first": "code_prompt", "partial_credit_substance": "candidate_A",
         "partial_credit_items": "candidate_B", "partial_credit_credit_first": "candidate_C",
         "partial_credit_subtractive": "candidate_D", "partial_credit_teacher": "candidate_E"}
COLS = ["experiment", "dataset", "question_id", "item_id", "model", "provider", "reasoning", "guidance", "prompt",
        "decomposition", "run", "human_grade", "model_grade", "fallback", "output_tokens", "cost_eur"]


def _frame(d: pd.DataFrame, experiment: str) -> pd.DataFrame:
    return pd.DataFrame({
        "experiment": experiment, "dataset": d.dataset, "question_id": d.question_id.astype(str), "item_id": d.item_id,
        "model": d.model.map(MODEL), "provider": d.provider, "reasoning": d.reasoning,
        "guidance": d.context_level.map({"none": "none", "with_guidance": "rubric_or_reference"}),
        "prompt": d["instruction"].fillna("standard").map(INSTR), "decomposition": d.decomposition,
        "run": d.run_index.astype(int), "human_grade": d.gold_norm, "model_grade": d.pred_norm,
        "fallback": d["fallback"].fillna(False).astype(bool) if "fallback" in d else False,
        "output_tokens": pd.to_numeric(d.completion_tokens, errors="coerce"),
        "cost_eur": pd.to_numeric(d.cost_eur, errors="coerce").round(8)})


def build() -> pd.DataFrame:
    m = phase5.load_main()
    m = m[m.dataset.isin(PUBLIC) & (m.scope == "question_by_question")]
    i = instruction.load()
    i = i[i.dataset.isin(PUBLIC) & (i.source == "instruction")]
    z = phase5.prepare(phase5._read(phase5.REPO_ROOT / "data" / "processed" / "runs" / "instruction_substance.jsonl"))
    z = z[z.dataset.isin(PUBLIC)]                                  # RIAYN: every candidate prompt, its same-batch controls too
    v = verification.load()                                        # each row keeps its own instruction
    v = v.assign(context_level=v.kind.map(lambda k: "none" if k == "no guidance" else "with_guidance"))
    parts = [_frame(m, "main"), _frame(i, "follow_up_partial_credit"), _frame(z, "follow_up_prompt_engineering"),
             _frame(v, "validation")]
    out = pd.concat(parts, ignore_index=True)
    out.loc[out.guidance == "none", "prompt"] = "none"          # without guidance the prompt has no instruction block
    out = out[out.model_grade.notna()]                           # unparseable outputs are left out, as in the paper
    return out[COLS].sort_values(["experiment", "dataset", "model", "reasoning", "guidance", "prompt",
                                  "decomposition", "item_id", "run"]).reset_index(drop=True)


def main() -> int:
    out = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"wrote {OUT}: {len(out):,} grades")
    print(out.groupby(["experiment", "dataset"]).size().to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

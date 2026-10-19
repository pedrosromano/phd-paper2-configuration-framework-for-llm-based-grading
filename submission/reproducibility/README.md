# Reproducibility package

Supplementary file of *Configuring LLM-Based Grading in Computer Science: An Empirical Study of Reasoning,
Guidance, Scope, and Cost* (IEEE Access).

## Contents

- `grades.csv`: every grade the models gave on the public datasets (Mohler, SemEval-2013 Task 7, Rubric Is All You
  Need) and on the two validation datasets (SAF, HARMOGEN-R), one row per answer, configuration and repetition.
  The text of the questions and answers is not included; it is in the original datasets, under their own
  licences. PT-CS consists of students' exam answers and is not included.
- `recompute.py`: recomputes, from `grades.csv` alone, the agreement values and 95% intervals of the reasoning
  contrast, the evaluation-guidance contrast, and the validation of the guide.

## Running

Python 3.10 or later with numpy and pandas:

```
python recompute.py
```

It runs in a few seconds and prints three tables.

## Columns of grades.csv

| Column | Meaning |
|---|---|
| `experiment` | `main` (the comparisons of RQ1 to RQ4), `follow_up_instruction` (the grading-instruction experiment), `validation` (SAF and HARMOGEN-R) |
| `dataset` | `mohler`, `semeval`, `riayn`, `saf`, `harmogenr` |
| `question_id`, `item_id` | identifiers of the question and of the answer in this study |
| `model` | Qwen3.5-35B-A3B, DeepSeek-V4-Flash, GLM-5.1, GPT-5.1, Claude Sonnet 4.6 |
| `provider` | the API that served the call |
| `reasoning` | `off` or `on` |
| `guidance` | `none` or `rubric_or_reference` (the rubric for code, the reference answer for short answers) |
| `instruction` | `strict`, `partial_credit`, `partial_credit_justified`, or `none` (no guidance, so no instruction) |
| `decomposition` | `holistic` or `criterion` |
| `run` | repetition index |
| `human_grade` | the human grade, divided by the question's maximum mark (0 to 1) |
| `model_grade` | the model's grade, divided by the question's maximum mark and clamped to 0 to 1 |
| `fallback` | `True` when a reasoning run returned no grade and the grade shown is the one the same model gave that answer with reasoning off (in the validation, the guide's grade) |
| `output_tokens`, `cost_eur` | output tokens of the call and its cost at the providers' standard rates |

Unparseable outputs without reasoning are left out, as in the paper.

## Metric

Quadratic weighted kappa on six ordered levels (0 to 5) of the mean of an answer's repeated grades; a mean that
lies exactly halfway between two levels goes to the even one. A difference between two configurations is computed
on the answers both graded, with a 95% bootstrap interval from 10,000 resamples of the answers (seed 20260610).

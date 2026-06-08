# Raw data provenance (Phase 2 acquisition)

Where each raw dataset came from and how to re-fetch it. `data/raw/` is **gitignored** (large /
sensitive), so this tracked file is the reproducibility record (artifact statement, §6.4). Fetched
2026-06-08 from legitimate public sources.

## Public datasets (fetched autonomously)

### Mohler (short-answer, CS) — `data/raw/mohler/`
- **File used:** `asag-mirror/comparative_evaluation_on_mohler_dataset/dataset/mohler_dataset_edited.csv`
- **Source:** `git clone https://github.com/gsasikiran/Comparative-Evaluation-of-Pretrained-Transfer-Learning-Models-on-ASAG`
- **Shape:** 2,273 rows; cols `id, question, desired_answer, student_answer, score_me, score_other, score_avg`.
  Matches the canonical Mohler & Mihalcea 2011 "Texas" set (2 graders + average, 0–5; reference =
  `desired_answer`). `id` = `question.answer` (e.g. `1.1`). gold = `score_avg`, scale max = 5.
- **Caveat:** a mirror ("edited" = CSV-formatted). Validate the score distribution in the 2.3 report;
  the canonical origin is Mohler & Mihalcea (Rada Mihalcea's UNT page) — cite `mohler_learning_2011`.

### SemEval-2013 Task 7 (short-answer, science) — `data/raw/semeval/`
- **Source:** `git clone https://github.com/myrosia/semeval-2013-task7` (Dzikovska's own release).
- **Contents:** `semeval-5way.zip`, `semeval-3way.zip` → unzipped to `semeval-5way/`, `semeval-3way/`.
- **Layout:** `{beetle,sciEntsBank}/{train,test-unseen-answers,test-unseen-questions,
  test-unseen-domains,reliability}/...xml` (SciEntsBank has unseen-domains; Beetle does not).
  5-way labels (correct / partially_correct_incomplete / contradictory / irrelevant / non_domain);
  3-way and 2-way derivable. Splits map to our `split` field (seen=train, unseen_ans, unseen_q).
- Cite `dzikovska_semeval_2013`.

### RIAYN "Rubric Is All You Need" (code, Java/DSA) — `data/raw/riayn/`
- **Dataset (the real data):** `git clone https://huggingface.co/datasets/BITS-Pilani-GRC/RubricEval`
  - `oop_data/oop_dataset.csv` — 79 rows; cols `user, feedback, appraise, code` (OOP exam, BITS Pilani Fall 2024, one Java problem, 7 methods).
  - `dsa_data/combined_human_scores.csv` — 150 rows; cols `Submission, Solution Name/Number, Step 1..12, Total Marks, Problem` (per-rubric-step marks + `Total Marks` as `score/max`, `Problem` = question; GeeksforGeeks problems).
  - `dsa_data/rubric_eval_grader{1,2}/extracted_data*.csv` — per-grader breakdowns.
- **Tool repo (NOT data, kept for format reference):** `Rubric-Grader/` from
  `git clone https://github.com/BITS-Pilani-GRC/Rubric-Grader` — the grading CLI; `test/` shows the
  expected `prob.txt`/`sol.txt`/`rubric.txt`/`sub/*.java` input format.
- 230 submissions total (80 OOP listed / 79 present + 150 DSA). Cite `pathak_rubric_2025`.

## Private dataset (user-provided — pending)

### PT-CS (GradeGenie MySQL export) — `data/raw/ptcs/`
- **NOT fetched** — the author provides the MySQL export ("forneço em breve"). Parser (2.1) written
  once it lands. PII dropped + AI comments stripped + pseudonymised at ingest (CLAUDE.md §2); ethics
  workstream in progress (gates publication, not the pseudonymised ingest).

## Re-fetch (all public)
```bash
git clone https://github.com/gsasikiran/Comparative-Evaluation-of-Pretrained-Transfer-Learning-Models-on-ASAG data/raw/mohler/asag-mirror
git clone https://github.com/myrosia/semeval-2013-task7 data/raw/semeval/semeval-2013-task7
( cd data/raw/semeval/semeval-2013-task7 && unzip -o semeval-5way.zip -d semeval-5way && unzip -o semeval-3way.zip -d semeval-3way )
git clone https://huggingface.co/datasets/BITS-Pilani-GRC/RubricEval data/raw/riayn/RubricEval
```

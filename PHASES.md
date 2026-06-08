# PHASES.md — Article 2 playbook

Copy-paste one step at a time to Claude Code ("do 0.1", then "do 0.2", …). Every step assumes the rules in
`CLAUDE.md`. **General contract for every step** (don't repeat it each time, it's implied):

> Follow CLAUDE.md. Keep changes scoped to this step. Where a design choice is needed, make a sensible
> default **and tell me** what you chose and why; if it's a genuine fork, ask before proceeding. After the
> step: update **§11 Living Uncertainties** in CLAUDE.md with anything discovered or decided, commit with a
> message referencing the step, and print a short "what I did / what's open / suggested next" summary.
> Never commit `data/raw` or any PII. Never present GradeGenie grades as pure human ground truth.

**Order of work:** state of the art and baselines come **first** (Phase 1), before any experiments — they set
the published-performance context and may change the plan. Experiments only start in Phase 4.

---

## Phase 0 — Repo & environment

**0.1** — Scaffold the repository exactly per CLAUDE.md §3 (folders, `README.md`, `pyproject.toml`,
`.gitignore` covering `data/raw`, `data/processed`, run artifacts, and LaTeX build files). No logic yet.

**0.2** — Set up the Python environment (3.11+, deps from CLAUDE.md §4). Add a `make`/`justfile` (or simple
scripts) for: `ingest`, `run-local`, `run-paid`, `analyse`, `figures`, `paper`. Verify imports.

**0.3** — Local inference: write a tiny `experiments/harness/ollama_check.py` that lists installed Ollama
models and runs a 1-token sanity generation. Then propose the **candidate local roster** (CLAUDE.md §6.1),
print `ollama pull` commands for me to run, and after I've pulled them, **benchmark tokens/s** for each
(short prompt + long reasoning prompt). Record results in §11 (local model selection).

**0.4** — Paid APIs + **cost guard**: implement a persistent spend tally (`data/processed/_spend.json`) and a
pre-flight estimator that refuses any paid arm exceeding the remaining **€150** budget. Wire in API keys via
env vars only (never hard-coded). Do a 1-call smoke test on the cheap DeepSeek API and on the chosen anchor,
logging tokens + cost. (If the anchor isn't decided, list options with rough per-1k-call cost and ask.)

---

## Phase 1 — State of the art & baselines (BEFORE experiments)

Goal: a good (Q1-quality) literature review for the topic — **not a heavy PRISMA** — plus a table of published
performance per dataset that contextualises our later results. The searches are **already done** (Scopus, IEEE
Xplore, ScienceDirect, filtered to ≥2025); their exports sit in `article/related/library/`. This phase can
change the research direction.

**1.1** — **Ingest the prior SLR** into the repo (`/article/related/slr_source/`, the `.tex`) as the
foundation. Everything **up to July 2025 comes from the SLR** — do not re-search that window. Extract from it:
the field map, the metric framework, and any performance numbers already reported on our datasets.

**1.2** — **Unify the literature library.** Read **every** file in `article/related/library/` (discover them;
**do not hard-code filenames** — expect Scopus/IEEE CSVs and ScienceDirect plain-text "citation+abstract"
exports, but handle whatever is there). Normalise all into a **single `library/refs_merged.csv`**, one row per
paper, columns: title, authors, year, venue, DOI, abstract, keywords, citation count, **source(s) of origin**.
**Deduplicate by DOI** (merge duplicates into one row recording all sources; for missing-DOI items use
title+year and **flag uncertain merges** rather than merging blindly). Flag/remove items **before the July-2025
cutoff** (the Scopus `PUBYEAR>2024` let Jan–Jul 2025 through, overlapping the SLR). This step is mechanical —
produce the merged table and let me inspect it before annotation. (Expect noise, esp. from ScienceDirect:
medical/chem/psych LLM papers caught by the query — they get filtered in 1.3.)

**1.3** — **Annotate relevance.** Read abstracts and add columns to `refs_merged.csv`: **relevance**
(high/med/low/exclude) + a short **reason**; a **theme** tag (reasoning / code / dataset-specific / consistency
/ other); and, where reported, **extracted performance** (dataset, metric, value) for the baseline table. Print
a summary of what's in vs out and why.

**1.4** — **Acquire full-text for the central subset only.** Identify the **small** set of papers where the
abstract is insufficient (typically to read exact performance numbers from results tables) — keep this list
deliberately short and justify each. Try to fetch them **autonomously via legitimate open sources only**
(arXiv, institutional repositories, Google Scholar, author pages); save to `library/pdfs/`. **Never bypass
paywalls by illegitimate means** (no pirate sites). For those that remain behind a paywall, hand me **one batch
list** (title + DOI + direct link) so I log in and download them together; resume when I drop them in
`library/pdfs/`. One interruption, not many.

**1.5** — **Published-performance table per dataset** (literature baselines = **context**, per CLAUDE.md §6.3):
from the merged+annotated library (and the central PDFs), tabulate reported metrics (QWK/MAE/accuracy), the
model/method, and the protocol, with citations. Label clearly that these were produced under **different
models/protocols** — they situate our work, they are **not** the success criterion. Save to `article/tables/`
(draft).

**1.6** — **Draft the Related Work / state-of-the-art section**, framed for **TLT** (learning-analytics / EDM /
assessment-tool register; cite TLT papers — Putnikovic & Jovanovic 2023, Gašević/Mello
AI-feedback tool) and positioned vs Jukiewicz / Poličar / GraderAssist (model-comparison demarcation). Keep a margin
note on what to re-frame for **ToE** (foreground pedagogy). Write into `article/` as a real draft, not notes.
**Respect the ~2-page cap** (CLAUDE.md §9.1) — it is written before the results exist, so do not let it balloon
and crowd out Results later.

**1.7** — **DECISION POINT — course-correction check (mandatory).** Compare what the refined state of the art
shows against the planned direction. If anything material has changed — a sub-topic saturated since we planned,
a new published baseline that changes what counts as a contribution, a newly released dataset or model worth
including, or a finding that undercuts a planned claim — **stop, summarise it, and propose a revised direction;
then WAIT for my decision before starting experiments.** If nothing changed, say so explicitly and proceed.

---

## Phase 2 — Ingest → common corpus

**2.1** — **PT-CS extraction** from the MySQL export. Join `resposta_submissao ⋈ pergunta ⋈ teste_submissao`.
Produce rows in the common schema (CLAUDE.md §5). In the same pass: **drop all PII**, **strip the AI comments**
(`criterio_correcao.comentario`), **clean escaped HTML**, keep `cotacao` and `pergunta.cotacao`, and emit a
validation report (counts by domain, null rates, scale ranges, 3 anonymised examples). Also compute and log
the **human-validation evidence** (% where `cotacao` ≠ Σ`nota_parcial`, mean adjustment) into §11, and record
that grades are a **two-teacher consensus** (see §11 consensus-vs-independent).

**2.2** — **EN translation of PT-CS** (questions + rubric; **leave student answers as-is**) via an LLM, written
to `corpus_en.parquet`. This is **for the master's, not this article** — mark it clearly, and note in §11 that
it needs human validation before reuse. Do not let it enter any Article-2 analysis.

**2.3** — **Mohler ingest** from `data/raw/mohler/` into the common schema (question, reference answer, student
answer, mean grade 0–5, scale max). Validation report + 3 examples.

**2.4** — **SemEval-2013 Task 7 ingest** from `data/raw/semeval/` (SciEntsBank + Beetle XML). Map 2/3/5-way
labels, preserve **unseen-answers / unseen-questions** splits, fill reference answers. Validation report.

**2.5** — **Rubric Is All You Need ingest** from `data/raw/riayn/` (OOP + DSA, GitHub) into the common schema:
question, rubric, student code, consensus grade. This is the public **code comparator** (external validity).
Validation report. *(Optional: Menagerie ingest if §11 decides to include it — note its grades are study
re-grades, not real awarded grades.)*

**2.6** — **Unify & validate**: concatenate to `data/processed/corpus.parquet`, assert schema consistency,
normalise scales to a common 0–1 alongside native scales, finalise the **per-dataset context mapping**
(rubric vs reference) and **scope/decomposition applicability** (CLAUDE.md §5), and print a single cross-dataset
summary table. Update §11 (context mapping, scope & decomposition).

---

## Phase 3 — Grading harness

**3.1** — **Config schema** (`experiments/configs`): a typed config = `{dataset, domain, model, reasoning,
context_level, scope, decomposition, k, temperature, run_index}` with a stable `config_hash`. (`scope` =
whole-exam | question-by-question; `decomposition` = holistic | criterion-by-criterion; `context_level` =
no-rubric | with-rubric | +examples.) Add a loader for a matrix YAML.

**3.2** — **Prompt templates** keyed by `(domain, context_level, scope, decomposition)`. Code vs short-answer
variants; holistic vs criterion-by-criterion; question-by-question vs whole-exam (PT-CS). Templates must request
a **machine-parseable** score — and, for whole-exam, **one score per question** in a parseable structure; for
criterion-level, a per-criterion breakdown. Keep them in version-controlled files, not inline strings. Show me
the rendered templates for one code item and one short-answer item.

**3.3** — **Local adapter** (Ollama): `grade(item, config) -> {score, per_criterion?, raw, tokens, latency,
parse_ok}`. Handle the reasoning on/off toggle per model family. Retries via `tenacity`.

**3.4** — **Paid adapters** (anchor + DeepSeek) behind the same interface, **routed through the cost guard**
(every call updates the tally; pre-flight estimate enforced).

**3.5** — **Output parser**: robust score extraction returning `parse_ok`; compute **π extractable-rate**.
Never coerce unparseable output to 0 — mark it. Unit-test on a handful of real and deliberately-messy outputs.

**3.6** — **Cache + logging**: cache by `(item_id, config_hash, run_index)`; reruns skip cached calls. Append
every run row (with all reproducibility fields from CLAUDE.md §8) to `data/processed/runs/`.

**3.7** — **Smoke test**: run the full harness on **5 items × 1 cheap local model × 2 configs × k=2**, end to
end, and show the resulting run rows + a parse-rate readout. Fix anything rough before scaling.

---

## Phase 4 — Run experiments (local first/free, paid last/budgeted)

**4.1** — **Define the pruned config matrix** (CLAUDE.md §7): write the YAML for the baseline config (4.2),
main-effects-at-k=5 on cheap local models, the reduced reasoning arm (smaller models), the sampled
reasoning×criterion cells, the context arm, the scope arm, and the reduced paid-anchor set (k=3). **Print
estimated wall-clock and paid cost per arm and ask me to confirm** before running anything. Record
N-per-condition decisions in §11.

**4.2** — **Establish OUR OWN baseline per dataset** (CLAUDE.md §6.3): run one sensible default config
(e.g. a mid local model, reasoning off, with grounding, question-by-question, holistic) across all datasets at
k=5. This is the **internal reference** against which every controlled comparison is measured — **not** the
published numbers from Phase 1 (those sit alongside as external context). Record it.

**4.3** — Run the **non-reasoning local main-effects** arm (k=5). Resumable. Report progress + parse rates.

**4.4** — **DECISION POINT — interim results review (mandatory).** With the first real results in hand
(baseline + non-reasoning main effects), check: parse rates are healthy (π), scores are sane, the baseline
behaves, and the expected signal is present. Re-estimate wall-clock and paid cost for the remaining arms.
If the harness is off, the signal is absent, or the cost/time projection no longer makes sense, **stop, report,
and propose adjusting scope before the expensive arms.** Wait for my go-ahead before 4.5+.

**4.5** — Run the **reasoning arm** on the smaller local models. Watch wall-clock; if an arm balloons, pause
and propose further pruning.

**4.6** — Run the **decomposition arm** (holistic vs criterion-by-criterion; PT-CS for criterion-level),
scored against the final grade.

**4.7** — Run the **scope arm** (whole-exam vs question-by-question; PT-CS for whole-exam). Verify per-question
scores parse correctly out of whole-exam responses.

**4.8** — Run the **context arm** (no-rubric vs with-rubric; +examples only if §11 includes it).

**4.9** — **Conversation-state sub-study** (on PT-CS): freeze one config (one model, reasoning off, with rubric,
question-by-question) and compare clean-conversation vs shared-history on a subset, **with order controlled**
(shuffle / multiple orders per §11). Report consistency, anchoring, and any order/position effects.

**4.10** — Run the **paid anchor** on the reduced set at k=3 — **only after** the cost guard confirms it fits
the remaining budget. Update the spend tally and §11 cost tracking.

**4.11** — *(optional, gated by §11)* **Fine-tuning arm**: prepare the train/eval split, run the minimal
QLoRA-local or managed fine-tune on one model, grade with it, compare to its base self.

---

## Phase 5 — Analysis

**5.1** — **Aggregate** all run rows into per-`(dataset, model, config)` records (mean score, per-criterion
where present, π, mean tokens/latency/cost).

**5.2** — **Agreement & error metrics** (CLAUDE.md §6.2): QWK (with the chosen binning — record it in §11),
Cohen's κ, Spearman/Pearson, MAE, RMSE; macro-F1/accuracy for SemEval labels. Per dataset (never pooled
across incompatible scales). Report each against **our own baseline** (4.2); show published numbers alongside
as external context only.

**5.3** — **Consistency**: SD/variance across the k runs and ICC per cell. (Ground-truth-free; robust given the
PT-CS two-teacher consensus reference.)

**5.4** — **Cost analysis**: cost/latency/tokens per configuration; the reasoning **5–10× premium**; the
cost-vs-agreement trade-off table.

**5.5** — **Statistical tests**: paired tests for reasoning on/off; a mixed-effects model (or ANOVA) across
the factorial; multiple-comparison correction. **Report effect sizes + confidence intervals, not just
p-values**; note that expensive-factor interactions are OFAT/underpowered and don't over-read single cells
(CLAUDE.md §6.4). Document the model choice in §11.

**5.6** — **Synthesise the framework** (the actual deliverable, CLAUDE.md §1.2): from the controlled
comparisons, build the **decision guide** — a compact table / rules mapping task characteristics (domain,
rubric availability, budget) to a recommended configuration and its cost. This, not the raw numbers, is the
contribution; it becomes the centre of the Discussion.

**5.7** — **Tidy results tables** → `article/tables/*.tex` (auto-generated). One table per claim; no
hand-editing.

---

## Phase 6 — Figures

**6.1** — Figure style setup (consistent fonts/sizes; export `.pdf` and `.pgf` into `article/figures`).
Match IEEEtran column widths.

**6.2** — Reasoning on/off **deltas** by domain and dataset (agreement + cost side by side).

**6.3** — **Cost-vs-agreement** scatter across models/configs (the headline trade-off).

**6.4** — **Consistency** plot (variance/ICC by configuration).

**6.5** — Per-dataset **configuration comparison** (which configuration wins where) — the visual core of the
"framework guidance".

**6.6** — **Scope** effect (whole-exam vs question-by-question) on agreement, and the **conversation-state**
sub-study result (clean vs shared history, with order effects).

**6.7** — Any figure the data demands that we didn't foresee — propose it.

---

## Phase 7 — LaTeX integration

**7.1** — Assemble `/article` with IEEEtran using the Article 1 toolchain (CLAUDE.md §9). The Related Work /
state-of-the-art draft already exists from **Phase 1.4** — pull it in and update it with the experimental
findings; do **not** rewrite it from scratch. State the **RQs (§1.2)** in the Intro and structure Results
around them; make the **synthesised framework (5.6) the centre of the Discussion**. Confirm framing for **TLT
(primary)** and the **ToE** re-framing note (**if ToE, write a structured abstract** — prescribed sections).
Stub the remaining sections (Intro, Design space, Datasets, Method, Results, Discussion incl. **external
validity via public datasets**, Threats incl. **COI**, **ground-truth honesty** — two-teacher consensus,
AI-seeded then human-validated, no measured human ceiling — **narrower code-domain evidence**, and the
**model-set scope** of the guidance — Conclusion).

**7.2** — Wire in the auto-generated **tables** from `article/tables` (incl. the Phase 1.3 published-baseline
table as external context, and the framework decision guide from 5.6).

**7.3** — Wire in the **figures** from `article/figures`.

**7.4** — Compile end to end (`latexmk`), fix any PATH/poisoned-state issues per §9, and produce the PDF.
**Check the page count against the budget (CLAUDE.md §9.1: ≤14 pp, target ~13)**; if over, report which
sections exceed their target rather than trimming blindly. Report what's still placeholder vs done.

**7.5** — **Reproducibility / data-availability**: write the statement and prepare the release bundle (harness
code, prompt templates, config matrices, public-dataset ingest). Include the **anonymised, AI-comment-stripped
PT-CS subset only if ethics permits** (CLAUDE.md §2 gate). State clearly what is and isn't shared and why.

---

### Reminder on what is *fixed* vs *open*
Fixed: order of work (state of the art + baselines first, experiments later); premise (configuration
framework) with **explicit RQs (§1.2)** and a **decision-guide deliverable** (not a leaderboard); arc; the
dimensions (reasoning; context = no-rubric vs with-rubric; scope = whole-exam vs question-by-question;
decomposition = holistic vs criterion-by-criterion; models); the conversation-state sub-study; **two decision
gates** (Phase 1.7 course-correction; Phase 4.4 interim review); ground truth = teacher-validated final grade;
validation via our own controlled comparisons (not by beating published numbers — §6.3); datasets
(short-answer: Mohler + SemEval; code: PT-CS + Rubric Is All You Need; Menagerie optional); PT-vs-EN out of
scope. Open (in §11): the Phase 1.7 course-correction outcome, the Phase 4.4 interim go/adjust, pruning
specifics, model selection, N, interactions, optional few-shot context level, optional datasets
(Menagerie/S-GRADES/PTASAG), fine-tuning inclusion, QWK binning, conversation-state order control, stats model,
budget tracking.

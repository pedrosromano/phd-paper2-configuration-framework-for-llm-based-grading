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
scripts) for: `ingest`, `run` (Phase-4 matrix runner, DeepInfra + anchor), `smoke`, `analyse`, `figures`,
`paper`. Verify imports. *(Renamed from `run-local`/`run-paid` after the 2026-06-08 paradigm change — most
runs are DeepInfra, not local; see Phase 4.)*

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

**1.6b** — **Auditoria de cobertura e integridade bibliográfica do Related Work (gate, antes do 1.7).**
Antes de fechar a Fase 1, verifica e devolve-me três coisas — não assumas que "sem erros" = "tudo
verdadeiro"; o que não conseguires confirmar, sinaliza:
(a) **Cobertura:** cruza todos os PDFs em `article/related/library/pdfs/` (e as entradas de
`refs_merged.csv` marcadas como relevância alta/média) com o que foi efetivamente citado no draft do
Related Work. Devolve a **lista dos não-citados, com a razão de exclusão de cada um**, para eu fazer a
chamada final de relevância (não decidas tu sozinho que um artigo "não importa").
(b) **Integridade bibliográfica:** confirma que cada `\cite` no Related Work tem entrada em
`references.bib`, que não há entradas órfãs (no `.bib` mas não citadas), e que cada entrada citada tem um
DOI ou identificador (arXiv/DOI) resolúvel. **Sinaliza** as entradas sem identificador ou que não
conseguiste confirmar (ex.: sem acesso à net) — em lista separada, para eu validar à mão.
(c) **Rastreabilidade:** sinaliza qualquer referência cuja origem não consigas confirmar contra a
`library/`, o SLR, ou uma fonte aberta — em especial nomes que possam ter vindo de planeamento e não de
fonte real (lembra o caso "Gong"/"Walsh"). Não cites nada que caia nesta lista sem eu confirmar.
Devolve as três listas e espera, antes do 1.7.

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

## Phase 4 — Run experiments (DeepInfra roster + paid anchor; budgeted)

> **Paradigm (2026-06-08, CLAUDE.md §6.1/§4):** the 32 GB ceiling is NOT a constraint. Models run on
> **DeepInfra** (open roster: Qwen3.5, DeepSeek-V4-Flash, GLM-5.1) + **OpenAI** (GPT-5.1 anchor). **Local
> Ollama is convenience/smoke only, NOT a study path** — Phase 3.7 showed a Q4 local model at π=0.60 vs
> DeepInfra π=1.00, and same-name models differ across backends (quantisation, chat template, sampling), so
> local and DeepInfra results are NOT comparable (see `experiments/model_roster.md`). Two separate ceilings
> (cost guard §8): **DeepInfra €150 + OpenAI €150**. Cost is €/token, not wall-clock.

**4.1** — **Define the pruned config matrix** (CLAUDE.md §7): write the YAML for the baseline config (4.2),
main-effects at k=5 across the **DeepInfra roster**, the reduced reasoning arm, the sampled
reasoning×criterion cells, the context arm, the scope arm, and the reduced **paid-anchor (GPT-5.1)** set (k=3).
**Print the estimated € per arm (DeepInfra + OpenAI, via the cost guard) and ask me to confirm** before
running anything. Record N-per-condition decisions in §11.
**Transfer dependency (RQ6):** RQ6 is an *analysis* step (5.5b), not an experimental arm — but it needs the
data. Ensure the configuration you expect to be the **public-dataset winner is ALSO run on PT-CS**, so the
transfer analysis has a like-for-like PT-CS counterpart for that config (otherwise 5.5b has nothing to
compare). If unsure which config wins, include a small set of strong-candidate configs on PT-CS. Record in §11.

**4.2** — **Establish OUR OWN baseline per dataset** (CLAUDE.md §6.3): run one sensible default config
(**Qwen3.5 on DeepInfra**, reasoning off, with grounding, question-by-question, holistic) across all datasets
at k=5 — the baseline MODEL is fixed (user, 2026-06-08): Qwen3.5 (RQ1 primary, Apache-2.0, neutral cross-domain,
continuity with Jayarao). This is the **internal reference** against which every controlled comparison is measured —
**not** the published numbers from Phase 1 (those sit alongside as external context). Record it.

**4.3** — Run the **non-reasoning main-effects** arm across the **DeepInfra roster** (k=5). Resumable. Report
progress + parse rates (π).

**4.4** — **DECISION POINT — interim results review (mandatory).** With the first real results in hand
(baseline + non-reasoning main effects), check: parse rates are healthy (π), scores are sane, the baseline
behaves, and the expected signal is present. Re-estimate **€ (DeepInfra + OpenAI)** for the remaining arms.
If the harness is off, the signal is absent, or the cost projection no longer makes sense, **stop, report,
and propose adjusting scope before the expensive arms.** Wait for my go-ahead before 4.5+.

**4.5** — Run the **reasoning arm** across the roster (reasoning ON via each model's toggle — the dominant
output-token cost). Watch **€ spend** against the DeepInfra ceiling; if an arm balloons, pause and propose
further pruning.

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

**4.11** — *(optional, gated by §11)* **Fine-tuning arm**: prepare the train/eval split, run a minimal
fine-tune on one model — **prefer a managed/DeepInfra-served LoRA** (consistent with the DeepInfra-first
paradigm and comparable to the base served model); QLoRA-local is a fallback only if a managed path is
unavailable. Grade with it, compare to its base self **on the same backend** (don't compare a local
fine-tune against a DeepInfra base — backends aren't comparable).

---

## Phase 5 — Analysis

> **Phase-4 full-data review gates this analysis (2026-06-10).** The §5.0 conventions and the
> **pairing subsets** below are NOT optional — skipping them corrupts central results (three
> contrasts come out biased; SemEval has no metric path as-was; whole-exam cost overcounts 4.5×).
> Apply §5.0 everywhere before any metric.

**5.0** — **Analysis conventions (apply before any metric; record concretes in §11).**
- **Clamp** predicted scores to **[0, gold_scale_max]** — 88 PT-CS criterion rows go **negative** via
  penalty criteria (the parser is correct; grades just can't be < 0).
- **Normalise** to 0–1 (`score / gold_scale_max`) for every cross-item / cross-dataset step. **Never pool
  raw scores** — scales differ (Mohler 5, SemEval 1, **PT-CS heterogeneous 1–12**, RIAYN 4–12).
- **QWK binning (PT-CS):** bin the **normalised** 0–1 score into K ordinal levels (decide K; record in §11) —
  PT-CS native scales are heterogeneous (1–12), so bin on the normalised score, never the native one.
- **SemEval score→label (decided 2026-06-10):** the model emits a continuous 0–1 score but the gold is a
  **binary 2-way label** (correct/incorrect; `gold_score` 0/1). Map with a **fixed, pre-registered threshold
  of 0.5** on the normalised score — **NOT tuned on the data** (tuning would be circular). Report accuracy +
  macro-F1 **per split SEPARATELY** — **seen / unseen_domain / unseen_q / unseen_ans** (distinct
  generalisations; never grouped; `unseen_domain` is the largest unseen, 5.4k). **Also** report threshold-free
  **MAE / Spearman** of the continuous score vs the 0/1 gold (keeps the continuous signal; adds no
  circularity). (3/5-way labels exist but are unused — the model was not asked for them.)
- **Whole-exam cost:** the N question-rows of a submission share ONE call (cost repeats on each row);
  **dedupe by `call_group`** for any token/€ aggregate — **4.5× overcount** otherwise (confirmed).
- **Pairing subsets (MANDATORY — state the N in every contrast or it is biased):**
  - **Reasoning (RQ1):** ON is sampled to **175 items**; pair OFF↔ON on those **175**, never OFF-full-N.
  - **Scope (RQ3):** whole-exam covers **252 questions** (60 PT-CS submissions); restrict the q-by-q
    comparator to the **same 252**, never all 737.
  - **Anchor (RQ4):** GPT-5.1 ran **60 items/dataset**; compare it to the open models on those **60**.
- **Conversation sub-study** = separate `conversation.jsonl` (key incl. `order_id`); `clean` exists only for
  natural order (order-independent by design); analyse order (shared natural vs inverse) and state (clean vs
  shared) **separately, per model** — and read Qwen under the 0-collapse caveat (5.5c).

**5.1** — **Aggregate** run rows into per-cell records (mean/median score, per-criterion where present, **π**,
tokens/latency/cost). Whole-exam cost deduped by `call_group`. **Flag the Qwen-ON truncation exclusion** per
cell (π < 1 there is a non-random drop — see 5.5c / threats).

**5.2** — **Agreement & error** (CLAUDE.md §6.2), **per dataset only, never pooled**, after §5.0 clamp+normalise:
QWK (binned per §5.0), Cohen's κ, Spearman/Pearson, MAE, RMSE; **SemEval per §5.0** (fixed-0.5 accuracy +
macro-F1 **per the 4 splits**, plus continuous MAE/Spearman). Report each **against our own baseline (4.2)**;
published numbers alongside as external context only (§6.3). **Context (RQ2) is two different interventions —
rubric (PT-CS/RIAYN) vs reference answer (Mohler/SemEval) — never pool the "context effect" across them.**

**5.3** — **Consistency — a FIRST-LINE RQ1 result, not a footnote.** SD/variance/ICC across the k runs per
cell (ground-truth-free). **Headline to test: reasoning ON *reduces* consistency** (k-agreement drops OFF→ON
on most cells) even where it shifts agreement — so **RQ1 has TWO dimensions that can diverge: agreement vs
consistency.** Report both and where they disagree (code vs short-answer). Note **temp=0 is NOT determinism**
(10–43% of items vary across k; backend-conditional, §6.4).

**5.4** — **Cost analysis**: tokens/latency/€ per configuration, **deduped by `call_group`** (whole-exam).
Reasoning premium on **total `completion_tokens`** (DeepInfra bundles reasoning) — **not** comparable to
GPT-5.1's itemised `reasoning_tokens` (anchor only; §6.4). Cost-vs-agreement trade-off **on the paired
subsets** (reasoning 175 / anchor 60).

**5.5** — **Statistical tests** on the **paired subsets** (175 / 252 / 60 — state N): paired tests for
reasoning on/off; mixed-effects (or ANOVA) across the factorial; multiple-comparison correction. **Effect
sizes + CIs, not just p**; expensive-factor interactions are OFAT/underpowered — don't over-read single cells
(§6.4). Document the model in §11.

**5.5a** — **RQ1, two-dimensional + model-specific.** Cross **agreement × consistency**, **code vs
short-answer**, per model. The reasoning effect is **model-specific** (see 5.5c); the two axes can diverge —
that divergence is a headline angle, not a caveat.

**5.5b** — **Transfer (RQ6)** — *analysis only, NO new runs.* Compare per-configuration performance + ranking
between the public datasets and **PT-CS**: does the public-winner config **transfer** (generalisation, not
"beating a score", §6.3)? Uses the paired PT-CS counterparts already in the matrix (4.1).

**5.5c** — **The code 0-collapse as a DEDICATED result (feeds the framework).** On PT-CS code the **baseline
(Qwen3.5 OFF) collapses ~42% of grades to 0** — *discrimination* collapse, tied to the lowest QWK (0.47).
**Reasoning ON corrects it for Qwen** (paired 175: frac0 0.53→0.28, meanN 0.26→0.43) **but NOT for GLM /
DeepSeek** (flat/worse) → **model-specific**: when a model collapses, reasoning is the lever; when it already
discriminates, it isn't. Characterise the **distributional shapes** in interpretation: **SemEval bimodal /
0-heavy across all models; Mohler top-heavy** (reference-answer matching). This result, and the
agreement-vs-consistency trade-off (5.5a), are inputs to the framework.

**5.6** — **Synthesise the framework** (the deliverable, §1.2): a **decision guide** mapping task
characteristics **(domain, model baseline-behaviour, rubric availability, budget)** → recommended config + its
cost. Fold in: collapse → **reasoning-as-lever (model-specific)**; **agreement-vs-consistency** trade-off;
**context = two interventions** (rubric vs reference); scope/decomposition **on the paired subsets**; cost
(deduped). The guide, not the raw numbers, is the contribution — centre of the Discussion.

**5.7** — **Tidy results tables** → `article/tables/*.tex` (auto-generated). One table per claim; **state the
paired-subset N**; SemEval **per split**; no hand-editing.

**Threats to carry to Phase 7 (§6.4):** **(a)** Qwen-ON agreement is computed on a **non-random subset** — 337
longest-reasoning items truncated at 32768 and excluded (all Qwen; worst on SemEval 145 / Mohler 111) → report
π + the exclusion, since the hardest cases drop out; **(b)** consistency at temp=0 is **backend-conditional,
not determinism**; **(c)** the **context effect is two interventions** (rubric vs reference); **(d)** the
**anchor is small-N (60)** — a reference point, not an inference target; **(e)** **code evidence is narrower**
(PT-CS + RIAYN, Java/OOP) — state code conclusions tentatively.

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
validity via public datasets** and **transfer (RQ6, from 5.5b)**, Threats incl. **COI**, **ground-truth
honesty** — two-teacher consensus, AI-seeded then human-validated, no measured human ceiling — **narrower
code-domain evidence**, **backend-conditional reproducibility** (§6.4), and the **model-set scope** of the
guidance — Conclusion). **Method must report the backend** (provider, served `model_id`, sampling params,
run dates — all in `data/processed/runs/`).

**7.2** — Wire in the auto-generated **tables** from `article/tables` (incl. the Phase 1.3 published-baseline
table as external context, and the framework decision guide from 5.6).

**7.3** — Wire in the **figures** from `article/figures`.

**7.4** — Compile end to end (`latexmk`), fix any PATH/poisoned-state issues per §9, and produce the PDF.
**Check the page count against the budget (CLAUDE.md §9.1: ≤14 pp, target ~13)**; if over, report which
sections exceed their target rather than trimming blindly. Report what's still placeholder vs done.

**7.5** — **Reproducibility / data-availability**: write the statement and prepare the release bundle (harness
code, prompt templates, config matrices, public-dataset ingest). Include the **anonymised, AI-comment-stripped
PT-CS subset only if ethics permits** (CLAUDE.md §2 gate). State clearly what is and isn't shared and why.

**7.6** — **Verificação bibliográfica final (fecho do paper).** Agora que o `references.bib` está completo
(Related Work + métodos + datasets + discussão), repete a auditoria do 1.6b sobre o artigo **inteiro**:
cada `\cite` tem entrada no `.bib`; sem órfãs; cada entrada tem DOI/ID resolúvel; e — crucial — os papers
de **origem dos datasets** (Mohler, SemEval) e quaisquer baselines da tabela estão citados onde os dados
são usados. Coerência de formato das entradas (campos obrigatórios do IEEEtran preenchidos). Sinaliza, em
lista, tudo o que não tenha identificador ou que não consigas confirmar, para eu validar. Não declares o
paper pronto enquanto esta lista não estiver resolvida.

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

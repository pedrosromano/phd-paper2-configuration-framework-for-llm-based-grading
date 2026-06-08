# CLAUDE.md

> Working spec for **Article 2** of the PhD. This file is intentionally **kept open**: parts of the
> experimental design can only be settled once experiments run. Anything not yet decided lives in
> **§11 Living Uncertainties** and must be updated there as decisions are made — do not silently
> hard-code guesses.

---

## 1. Project

A **configuration framework** for LLM-based automated assessment in Computer Science. The contribution
is **not another grading pipeline** but the **systematic empirical study of the design space** (reasoning,
context, scope, decomposition, model family, fine-tuning) and the **guidance that results** (intended to hold
across the model families tested, not a universal claim): *for a given CS assessment task, which configuration
should you use?*

- This is **Article 2** of the PhD compilation (Article 1 = the published PRISMA SLR, Q1, in IEEE ToE).
- It **feeds Article 3** = the improved **GradeGenie** platform (design decisions fixed here flow there).
- **Target venue: IEEE Transactions on Learning Technologies (TLT)** — primary. **IEEE Transactions on
  Education (ToE)** — fallback. Both Q1 (= 8 PhD points either way). The experimental design serves both;
  only the **framing** differs (see §1.1). The same `IEEEtran` toolchain works for both.
- Arc across the thesis: **Map (SLR) → Analyse (this) → Build (GradeGenie)**.

### 1.2 Research questions & the deliverable's form
The paper answers a fixed set of RQs (refine wording in Phase 1, but keep them explicit — they anchor the
whole study and the Results structure):
- **RQ1 (headline).** How does **reasoning** (extended-thinking on/off) affect grading **quality, consistency,
  and cost**, and does the effect differ between **code** and **short-answer**? (the divergence that motivates
  the paper)
- **RQ2.** How much does **evaluation guidance** (no-rubric vs rubric; optionally +examples) change quality and
  consistency?
- **RQ3.** How do **scope** (whole-exam vs question-by-question) and **decomposition** (holistic vs
  criterion-by-criterion) affect agreement with the final grade?
- **RQ4.** How do **current-generation models** (incl. 2026 open-weight, untested as graders) compare, and what
  is the **cost–quality trade-off** (local vs paid frontier)?
- **RQ5 (sub-study).** Does **conversation state** (clean vs shared history) affect consistency/fairness?
- **RQ6 (transfer).** Does the best configuration found on public datasets **transfer** to a real deployment
  context in Portuguese (PT-CS)?

**The deliverable is a framework, not a leaderboard.** The headline output is a **compact, empirically-grounded
decision guide** — a table / set of rules mapping task characteristics (domain, rubric availability, budget) to
a **recommended configuration and the cost it implies** — synthesised from the controlled comparisons. If the
paper ends as "we benchmarked models and report numbers," it has missed its contribution. Build the framework
artifact explicitly in analysis (Phase 5) and make it the centre of the Discussion.

### 1.1 Venue framing (design for TLT; keep ToE reachable)
TLT scope explicitly includes *tools for formative/summative assessment* and *learning analytics / educational
data mining*, and actively publishes LLM-grading work (e.g. Putnikovic & Jovanovic 2023; the Gašević/Mello
AI-feedback tool, TLT vol. 18) — so frame this paper in that register. (Removed "Gong et al. 2025": a phantom
ref from planning that could not be confirmed in TLT — do not cite it; see `related/related_work_refs.md`.)
- **For TLT (primary):** lean into learning-analytics / EDM / assessment-tool vocabulary; the "configuration
  framework" + "deployed platform" framing fits directly; cite TLT papers in related work. **Note TLT's
  evaluation clause:** papers centred on *evaluating existing technologies* (here, LLMs) are in scope only if
  they offer novel technology or **significant technical/design insights** — so framing Article 2 as a
  *configuration framework with design-space insights* (not just "we benchmarked LLM graders") is what
  qualifies it. The framing is load-bearing, not cosmetic.
- **External validity is a first-class argument** (not a footnote): the single-context PT-CS limitation
  (Java/OOP, one institution) is answered by developing on public datasets — short-answer (Mohler, SemEval)
  and a public code comparator (Rubric Is All You Need). Education reviewers weigh cross-course/population
  generalisation heavily — emphasise this.
- **If it has to move to ToE:** re-foreground the *pedagogical* contribution (instructor workload, assessment
  validity, fairness, computing-education context), make educational implications a substantial section, and
  keep claims conservative. The study itself does not change.
- Both are education journals, not ML venues: the contribution must read as **educational guidance**, with
  threats/fairness/human-in-the-loop prominent and no over-claiming.

---

## 2. NON-NEGOTIABLES (do not lose these)

These are not features; they gate submission. Keep them visible and track them as tasks.

1. **Conflict of interest.** The author owns and built GradeGenie, the source of the PT-CS dataset and
   the target of Article 3. A COI statement **must** appear in the paper. Never present GradeGenie-produced
   grades as independent human ground truth without the framing in §5.
2. **Ethics / GDPR (Iscte).** Secondary use of real student answers for research requires a legal basis,
   a likely Iscte ethics committee opinion, and **pseudonymisation** of the study set. The processed
   dataset **must not** contain `nome`, `email`, `password`, `reset_token`, or any direct identifier.
   This is a parallel workstream starting now, not at submission time. **Gate:** PT-CS experiments and any
   data release must not proceed **to publication** before the legal basis / ethics opinion is confirmed.
3. **Ground-truth honesty.** PT-CS grades are a **consensus grade by two teachers in agreement**, on top of
   *human validation/correction (often substantial) of model-generated suggestions*. Describe them as
   **consensus** (two teachers agreeing on one grade), **not** independent double annotation: there are no two
   separate scores, so **inter-rater agreement / a measured "human ceiling" cannot be reported**. Do not imply
   otherwise — a reviewer will ask for the kappa. Consensus does make the reference more reliable than a single
   rater, which strengthens using LLM-vs-human agreement as a quality measure (not merely "alignment with one
   grader").
4. **No circularity.** Data used to *evaluate* configurations in Article 2 must stay conceptually separate
   from the GradeGenie *system* evaluated in Article 3. Do not validate an improved GradeGenie against
   grades a previous GradeGenie helped produce.

---

## 3. Repository structure

```
/                      repo root
├── CLAUDE.md          this file
├── PHASES.md          phased prompts (the playbook: "do 1.1", "do 1.2", …)
├── README.md          short human-facing overview
├── pyproject.toml     Python deps (managed with uv or pip)
├── /data
│   ├── /raw           untouched source datasets (gitignored; large/sensitive)
│   │   ├── ptcs/      MySQL export of GradeGenie (NEVER commit; contains PII pre-processing)
│   │   ├── mohler/    Mohler CS short-answer
│   │   ├── semeval/   SemEval-2013 Task 7 (SciEntsBank + Beetle)
│   │   ├── riayn/     Rubric Is All You Need (OOP + DSA) — public code comparator
│   │   └── menagerie/ optional (only if §11 includes it)
│   └── /processed     normalised, anonymised, analysis-ready (the common schema)
│       ├── corpus.parquet        unified items (see §5 schema)
│       ├── corpus_en.parquet     EN translation of PT-CS (for the MASTER'S, not this article)
│       └── /runs                 raw model outputs per (item, config, run_index)
├── /experiments       all code to run the study
│   ├── /ingest        dataset parsers → common schema
│   ├── /harness       model-agnostic grading interface + adapters + parser + cache
│   ├── /configs       the (pruned) factorial config matrix
│   ├── /run           experiment runners (local / paid, resumable)
│   ├── /analysis      metrics, consistency, stats, framework synthesis → tidy results tables
│   └── /figures       plotting scripts → article/figures/*.pdf|*.pgf
└── /article           LaTeX (IEEEtran), same toolchain as Article 1 (see §9)
    ├── main.tex
    ├── references.bib
    ├── /related       state-of-the-art material
    │   ├── slr_source/        Article 1 (.tex) — foundation for everything ≤ Jul 2025
    │   ├── library/           literature exports — read ALL dynamically, no hardcoded names
    │   │   ├── *.csv / *.txt   Scopus + IEEE CSVs, ScienceDirect plain-text citation exports
    │   │   ├── refs_merged.csv unified, deduped-by-DOI, annotated (Phase 1.2–1.3)
    │   │   └── pdfs/           full-text for the central subset only (Phase 1.4)
    │   └── sota_draft.tex     the Phase 1 state-of-the-art draft
    ├── /figures       generated figures (do not hand-edit)
    └── /tables        auto-generated tables (do not hand-edit)
```

**Data flow:** `data/raw → experiments/ingest → data/processed/corpus.parquet →
experiments/run → data/processed/runs → experiments/analysis → experiments/figures → article/`.

---

## 4. Environment & toolchain

- **Machine:** MacBook Pro **M1 Max, 32 GB unified memory**. Local model size is memory-bound; inference
  via Metal is slower than a discrete GPU. Reasoning models with long traces are **slow** — design for
  overnight runs (see §7 pruning).
- **Local inference:** **Ollama** (default; scriptable, good Metal support). Fall back to **LM Studio /
  MLX** only for a model not packaged for Ollama. Practical ceiling on 32 GB ≈ **~30B at Q4** (tight, slow);
  prefer smaller variants for the reasoning arm.
- **Paid APIs:** exactly **one frontier anchor** (reasoning toggle, reduced condition set) + optional
  near-free **DeepSeek** API. **Hard budget ceiling: €150** — see §8 cost guard.
- **Python:** 3.11+. Deps: `pandas`, `pyarrow`, `numpy`, `scipy`, `scikit-learn`, `statsmodels`,
  `matplotlib`, `pyyaml`, `tenacity` (retries), `tiktoken`/provider SDKs, `mysql-connector-python`/`pymysql`,
  `beautifulsoup4`/`lxml` (HTML clean + SemEval XML). Pin in `pyproject.toml`.
- **LaTeX:** BasicTeX (TeX Live 2026), `latexmk`, IEEEtran — reuse the Article 1 setup (§9).

---

## 5. Datasets & common schema

Strategy: develop on public datasets (comparability + external validity), confirm on PT-CS (transfer to PT +
real deployment). **Verified landscape (Jun 2026):** code datasets are plentiful but code-with-*human-rubric*
grades are few — most only have pass/fail autograder results. The large code ones (SimGrade ~11k, Sahoo ~25k,
Havare ~3.7k) are **not publicly available** (internal exam data / withdrawn / unreleased). So among *usable*
public code datasets PT-CS is one of the most complete; short-answer has strong public options.

| Dataset | Domain | Lang | Size (approx) | Gold | Notes / role |
|---|---|---|---|---|---|
| **PT-CS** (GradeGenie export) | code (Java) + theory | PT | ~738 code / ~437 theory | final per-question grade (`cotacao`), normalised by `pergunta.cotacao` | rubric JSON; **no reference solution**; **two-teacher consensus**; AI-seeded then human-validated. **Primary code; confirmation/transfer** |
| **Rubric Is All You Need** (OOP+DSA) | code (Java + DSA) | EN | ~230 | two graders collaboratively (consensus) | public (GitHub); question-specific rubrics. **Public code comparator (external validity)** |
| **Mohler** | short-answer (CS) | EN | ~2,273 ans / 80 q | mean of 2 graders, 0–5 | public; question + reference answer. **Primary short-answer** |
| **SemEval-2013 Task 7** (SciEntsBank + Beetle) | short-answer (science) | EN | ~13k facets | 2/3/5-way labels | public; reference; **unseen-answers / unseen-questions** splits. **Development** |
| **Menagerie** (KCL) — *optional* | code (Java CS1) | EN | ~272 | per-dimension letter grades | public (GitHub+OSF, CC BY); ⚠ grades are study **re-grades, not real awarded grades**. **Optional robustness only** |

Chosen core: **Mohler + SemEval** (short-answer) and **PT-CS + Rubric Is All You Need** (code); Menagerie
optional. All public except PT-CS. Not usable / excluded: SimGrade (private), Sahoo (withdrawn), Havare
(unconfirmed), Bounce/Code.org (programmatic labels, not human). Final inclusion of optionals is a §11 decision.

**Common schema (`corpus.parquet`):**
`item_id, dataset, domain{code|short_answer}, language{en|pt}, question_text, reference_answer(nullable),
rubric_json(nullable), student_answer, gold_score, gold_scale_max, label_2way/3way/5way(nullable),
split{seen|unseen_ans|unseen_q|none}, question_id, submission_id(nullable), source_meta`.

**Dataset-specific applicability (important):**
- *Whole-exam scope* (D5a) and *criterion-by-criterion decomposition* (D5b) **only apply to PT-CS** (it has
  multi-question submissions and rubric criteria). Short-answer datasets are single-question with no criteria,
  so for them scope is fixed to question-by-question and decomposition to holistic.
- *Context = grounding* (D3): the **question stem and the student answer are ALWAYS sent** — they are the
  minimum to make the task meaningful and are never a variable. What varies is the **evaluation guidance**
  added on top. The concrete material differs per dataset: **rubric** for PT-CS, **reference answer** for
  Mohler/SemEval. Document this mapping.
- PT-CS has **no reference solution** → do **not** synthesise one (confound). The "+reference" grounding does
  not exist for PT-CS; its grounding is the rubric. (Unless §11 decides otherwise.)

**Ingest must:** strip GradeGenie AI comments (`criterio_correcao.comentario`), drop all PII, clean escaped
HTML (`&gt;`, `<br/>`), normalise scales, and emit a **validation report** (counts, nulls, scale ranges,
examples) per dataset.

---

## 6. Experimental design — the design space

**FIXED factors:**
- **D2 reasoning:** {off, on}. Prefer **within-family toggle** (e.g. Qwen3, GLM) to isolate reasoning from
  vendor — this is a deliberate improvement over prior model-confounded comparisons.
- **D3 context (evaluation guidance):** {no rubric, with rubric} — and *optionally* a third level {+examples}
  (few-shot of already-graded answers; include/drop is a §11 decision). The question stem + student answer are
  **always present**; only the grounding varies. Per-dataset grounding: **rubric** (PT-CS) / **reference
  answer** (short-answer).
- **D5a scope:** {whole-exam (one call), question-by-question}. Measures the effect of cross-question context
  on the grade. Whole-exam applies to **PT-CS only** (multi-question submissions); short-answer is
  question-by-question by nature.
- **D5b decomposition:** {holistic, criterion-by-criterion}, always scored **against the final grade** (we do
  NOT trust per-criterion human scores as truth — see §11). Criterion-level applies to **PT-CS only** (has rubric
  criteria).
- **D1 model:** roster in §6.1.
- **consistency:** **k = 5** repetitions per cell (k = 3 on the paid anchor to save cost).

**FOCUSED SUB-STUDY (not crossed with the full factorial):**
- **Conversation state:** {clean conversation per answer, shared accumulating history}. **Run on PT-CS** (real
  multi-question submissions; rubric available). Hold everything else fixed at one good config (one model,
  reasoning off, with rubric, question-by-question) and vary only this axis on a subset. Shared history may
  improve criterion consistency but can introduce contamination, anchoring, and **order effects** — so the
  **order of answers must be controlled** (shuffle / multiple orders); see §11. Ties to consistency, fairness,
  and reproducibility. Run as a standalone study, not a full dimension, to keep the design tractable.

**OPTIONAL / LATE factor:**
- **D4 fine-tuning:** a **minimal arm** (one model: QLoRA locally *or* a cheap managed fine-tune), compared to
  its non-fine-tuned self. Include only if §11 decides it earns its cost.

**OUT OF SCOPE for this article:** PT-vs-EN language axis (→ master's; EN translation produced in 1.2 but not
analysed here).

### 6.1 Model roster (June 2026) — final selection is a §11 uncertainty
- **Local (Ollama), workhorses, free:** a ~30B Qwen3 (instruct **and** thinking variants — primary D2 toggle);
  Gemma 4 ~26B; a **small DeepSeek-R1 distill (7–14B)** for a *fast* reasoning arm; optionally a coder model
  (e.g. Qwen2.5-Coder 32B) for the code domain. Confirm which actually run acceptably on 32 GB.
- **Cheap API (near-free):** DeepSeek (V3.2/V4) — note China-hosted; only on **anonymised** data.
- **Paid frontier anchor (exactly one):** a model with a clean reasoning on/off toggle (candidates: Gemini
  3.x Pro, a GPT-5.x tier, or Claude Sonnet). Used on a **reduced** condition set, k=3, within budget.

### 6.2 Metrics
- **Agreement:** QWK (binned for continuous PT-CS scores — binning strategy TBD §11), Cohen's κ, Spearman/Pearson r.
- **Error:** MAE, RMSE on normalised 0–1 score.
- **Classification (SemEval labels):** accuracy, macro-F1 (2/3/5-way).
- **Consistency:** SD/variance across k, ICC. (Needs no ground truth — a clean axis regardless of the
  reference; note PT-CS reference is now a two-teacher consensus, more reliable than a single rater.)
- **Operational:** tokens; **cost — € for paid models, wall-clock/compute for local** (define per model class,
  don't conflate); latency; throughput. The headline reasoning premium (≈5–10×) must state **which** cost metric.
- **Leniency:** strictness vs human (cf. "Rubric Is All You Need").
- **Extractable-rate (π):** fraction of runs yielding a parseable grade (cf. local-model studies).

### 6.3 Validation logic (read before claiming anything is "validated")
Develop on the known public datasets (Mohler, SemEval, RIAYN); PT-CS enters **only at the end as transfer
validation**. Two distinct uses of "baseline" — keep them separate:
- **Published baselines = CONTEXT, not the success criterion.** Numbers in the literature (e.g. AutoSAS QWK
  ≈0.79 on ASAP-SAS, BERT on Mohler) were produced with *different models, prompts and protocols* (often
  supervised models from 2019–2024, not 2026 prompted LLMs). "We beat the published number, therefore
  validated" is **biased** — a reviewer will ask whether the gain comes from our method or merely from newer
  models / a different eval protocol. Use published baselines to *situate* our results (show the dataset is
  known, our numbers are plausible), never as the proof.
- **Validation comes from OUR OWN controlled comparisons.** Conclusions are validated by like-for-like
  contrasts we run ourselves under one identical protocol: reasoning on vs off, rubric vs no-rubric, scope A
  vs B, model X vs Y — same items, same metric, same harness. These internal comparisons are the evidence.
- **PT-CS validation = transfer, not "beating a baseline".** After we establish the best configuration on the
  public datasets, PT-CS shows that configuration **transfers** to a real deployment context in Portuguese.
  The claim is generalisation ("what we found holds here too"), not "it beat a published score".
- **Therefore:** for every dataset we must run our own internal baselines (don't rely on numbers we didn't
  produce); report published numbers alongside as external reference, clearly labelled as different-protocol.

### 6.4 Claims discipline, threats & reproducibility (Q1 expectations)
- **Scope the guidance claim.** We test several model families, not all — say guidance holds *across the models
  tested* (reasoning isolated within-family), not universally.
- **Code-domain evidence is narrower than short-answer.** Code = PT-CS + RIAYN (~230), both Java/OOP/DSA;
  short-answer = Mohler + SemEval (larger, more varied). State code-specific conclusions more tentatively, and
  flag this as a threat to validity.
- **Statistics:** report **effect sizes + confidence intervals**, not just p-values. The design is
  full-factorial on the cheap axes but **OFAT for the expensive ones**, so interactions among expensive factors
  (e.g. reasoning × decomposition) are **not fully estimable** — with k=5 and sampled N those cells are
  underpowered. Say so explicitly rather than over-reading a single cell.
- **Reproducibility / artifact statement.** Plan to release: harness code, prompt templates, config matrices,
  and the ingest for the public datasets. PT-CS itself cannot be released (student data); release an
  **anonymised, AI-comment-stripped PT-CS subset only if ethics permits** (see §2 gate). State clearly what is
  and isn't shared and why.
- **ToE needs a structured abstract** (prescribed sections); draft one if the venue becomes ToE.

---

## 7. Pruning principle (because full factorial × k=5 on a Mac is infeasible)

- **Full factorial on cheap axes** (non-reasoning local models, short outputs) at **k=5**.
- **Reduce the expensive combinations**: the reasoning arm uses **smaller** local models; reasoning ×
  criterion-by-criterion is sampled, not fully crossed; the paid anchor runs a **reduced** set at **k=3**.
- Use **OFAT from a baseline** for expensive interactions (vary one factor at a time from a sensible default),
  rather than the full cartesian product.
- Sample **N per condition** (stratified) rather than all items for the costly cells. Final N is a §11 decision.
- Estimate wall-clock before launching any arm; if an arm > ~2 nights, prune further or flag.

---

## 8. Conventions

- **Reproducibility:** fixed seeds where models allow; record model version/tag, quantisation, prompt hash,
  temperature, and date for **every** run row.
- **Caching:** cache by `(item_id, config_hash, run_index)`. Reruns must skip cached calls. This protects
  both cost and time.
- **Cost guard:** a running tally of paid spend persisted to disk; the paid runner **refuses to start** an
  arm whose *estimated* cost would exceed the remaining budget (ceiling **€150**). Print the estimate first.
- **Determinism of parsing:** the output parser returns `(score, per_criterion?, parse_ok)`. Log `parse_ok`
  to compute π. Never silently coerce unparseable output to 0.
- **Everything regenerable:** `data/processed`, `runs`, figures, and tables are build artifacts. Source =
  `experiments/` + `data/raw` + ingest. Gitignore artifacts and all of `data/raw`.
- **Small commits per phase step**; reference the PHASES.md step in the message.
- **Literature library & PDF acquisition:** read everything in `article/related/library/` dynamically (never
  hardcode filenames); unify into one deduped `refs_merged.csv` before triage. Fetch full-text PDFs only for a
  small justified subset, **autonomously via legitimate open sources** (arXiv, repositories, Scholar, author
  pages) — **never bypass paywalls by illegitimate means**; hand the user one batch list of what stays locked,
  rather than interrupting per paper.

---

## 9. Article build (reuse Article 1 toolchain)

- Class: **IEEEtran** `[lettersize,journal]`; bib via BibTeX + `IEEEtran.bst`; class file vendored.
- Compile:
  ```bash
  eval "$(/usr/libexec/path_helper)"
  latexmk -pdf -synctex=1 -interaction=nonstopmode main.tex
  ```
- Clear poisoned state: `latexmk -C main.tex` (and delete `.fdb_latexmk` if "pdflatex gave an error in
  previous invocation" persists; ensure `/Library/TeX/texbin` is on PATH — the Article 1 CLAUDE.md PATH
  gotcha applies here too).
- **Figures** come from `experiments/figures` as `.pdf`/`.pgf`; **tables** are auto-generated to
  `article/tables`. Do not hand-edit either.
- Gitignored build artifacts: `*.aux *.bbl *.blg *.fdb_latexmk *.fls *.log *.synctex* *.pdf`.

### 9.1 Page budget (two-in-one: design for TLT, safe for ToE)
**Limits (verified Jun 2026):** TLT regular paper = **14 pages** (double-column IEEE template, counted after
production, *including references*). ToE publishes **no hard numeric limit** on its author page (it stresses a
structured abstract + evidence beyond self-report); IEEE norm ≈ 12 formatted pages with overlength charges.
**→ Design to ≤14 pages with a working target of ~13**; that fits TLT and trims easily to ~12 if it goes to ToE.

Per-section budget (keep sections from bloating — the **state of the art is the hard cap**, since it's written
first, in Phase 1, from a whole SLR):

| Section | Target (of ~14 pp incl. refs) |
|---|---|
| Abstract + Introduction | ~1.5 |
| Related Work / state of the art | **~2 (hard cap)** |
| Design space / framework + Method (datasets, harness, protocol) | ~3.5 |
| Results | ~3.5 |
| Discussion + framework guidance / implications | ~1.5 |
| Threats (COI, ground-truth honesty, single-context) + Conclusion | ~1 |
| References | ~1 |

If any section exceeds its target, flag it rather than silently overrunning; trim elsewhere or move detail to
supplementary material. The Phase 1 state-of-the-art draft must respect the ~2-page cap even though it is
written before the results exist — do not produce 4 pages of review that later crowd out Results.

---

## 10. Phase roadmap

See **PHASES.md** for the copy-paste prompts. **State of the art and baselines come first; experiments later.**
- **Phase 0** — repo + environment (Ollama, model pulls, API keys, cost guard).
- **Phase 1** — **state of the art & baselines (before experiments):** ingest the prior SLR (foundation for
  everything ≤ Jul 2025); **unify the already-exported literature library** (`article/related/library/`, read
  dynamically) into one deduped, annotated `refs_merged.csv`; fetch full-text only for a small subset
  (autonomously, legitimate sources; batch-list the rest to the user); tabulate published per-dataset
  performance (context); draft Related Work; then a **mandatory course-correction decision point (1.7)**
  (propose redirection if the refined SoA warrants it, and wait).
- **Phase 2** — ingest the datasets → `corpus.parquet` (+ EN translation for the master's).
- **Phase 3** — grading harness: config schema, prompt templates, adapters, parser, cache, smoke test.
- **Phase 4** — run experiments: define pruned matrix, **establish our own baseline first**, then the arms
  (local first/free, paid anchor last/budgeted), with an **interim results-review gate** after the first
  results and before the expensive (reasoning / paid) arms.
- **Phase 5** — analysis: metrics (vs our own baseline), consistency, cost, stats → tidy tables.
- **Phase 6** — figures.
- **Phase 7** — LaTeX integration (Related Work already drafted in Phase 1; assemble, don't rewrite).

---

## 11. LIVING UNCERTAINTIES (resolve with data; update this section as you go)

Status legend: ⬜ open · 🔧 in progress · ✅ resolved (record the decision + date).

- ⬜ **Course-correction (Phase 1.7)** — after the refined state of the art, does the planned direction still
  hold, or does something (saturation, new baseline/dataset/model, undercut claim) warrant a redirection?
  Record the decision before experiments start.
- ⬜ **Interim results gate (Phase 4)** — after the first real results (baseline + non-reasoning main effects),
  is the harness sound (parse rates, sane scores) and the expected signal present before committing time/budget
  to the reasoning and paid arms? Record go / adjust.
- ⬜ **Artifact-release scope** — confirm what ships (harness, prompts, public-dataset configs/ingest) and
  whether the anonymised AI-comment-stripped PT-CS subset can be released (ethics-gated).
- ✅ **Local model selection** (Phase 0.3, 2026-06-07) — roster pulled and benchmarked on M1 Max 32 GB
  (Q4_K_M, via `python -m experiments.harness.ollama_check bench`). All run at acceptable speed. Chosen set:

  | Model | Type | Params | short tok/s | long/reasoning tok/s | Role |
  |---|---|---|---|---|---|
  | `qwen3:30b` | MoE (≈3B active) | 30.5B | 67.1 | **42.8** | primary D2 reasoning toggle (thinking on/off, one family) |
  | `deepseek-r1:14b` | dense (R1-distill) | 14.8B | 23.6 | 18.3 | fast reasoning arm |
  | `qwen3:14b` | dense | 14.8B | 23.5 | 19.6 | smaller reasoning arm (§7) |
  | `gemma3:27b` | dense | 27.4B | 17.1 | **9.6** | second family (no native thinking); slowest — heavy for long outputs |

  The 30B MoE is ~2× the dense 14B despite 2× params (sparse activation) — best workhorse; `gemma3:27b` is the
  cost ceiling for long reasoning outputs. `qwen2.5-coder:32b` (optional code specialist, §6.1) **deferred** to
  the Phase 4 code arm — pull+bench then. "Gemma 4 ~26B" in §6.1 resolves to `gemma3:27b` (no Gemma 4 on Ollama
  Jun 2026). **Install gotcha:** Homebrew *formula* `ollama` 0.30.6 ships an incomplete bottle (no
  `llama-server` GGUF runner → HTTP 500 on every generation); fixed by the official **cask `ollama-app`**
  (full runtime). Server run headless via `nohup ollama serve`.
- ✅ **Paid anchor choice** (Phase 0.4, 2026-06-07) — **GPT-5.1**. Chosen over Gemini 3 Pro / Claude Sonnet
  4.6 because it is the cheapest tier AND the only candidate with a genuinely **binary** reasoning toggle,
  which RQ1's clean reasoning-off condition requires. **D2 mapping (record in the Phase 3.1 config schema):**
  `reasoning_param: reasoning_effort`; **off → `none`** (a true off — behaves as a non-reasoning model; NOT
  the old GPT-5 "minimal", which is different and does not apply here), **on → `high`** (`low`/`medium` also
  exist). **Why not the others:** *Gemini 3 Pro* cannot truly disable reasoning — `thinking_level` minimum is
  `low` (still reasons) and `thinking_budget=0` only disables thinking on Gemini 2.5 Flash/Flash-Lite, not
  3 Pro → unfit for a clean reasoning-off (do not reselect). *Claude Sonnet 4.6* ~1.7× pricier. **Cost per
  1000 grading calls** (defaults 1.5k in / 0.6k out off, 4k out on; EUR@0.92, prices in `pricing.yaml`,
  VERIFY): ≈ **€7.3 off / €38.5 on**. Key via `OPENAI_API_KEY` (env only); smoke test pending key.
- ⬜ **N per condition** — stratified sample sizes, especially for expensive (reasoning × criterion) cells.
- ⬜ **Interactions to probe** — which 2-way interactions are worth the cost vs main-effects-only.
- ⬜ **Fine-tuning arm** — include or drop? If included, which model and QLoRA-local vs managed fine-tune.
- ⬜ **QWK binning** — how to bin continuous PT-CS normalised scores into ordinal levels for QWK.
- ⬜ **Few-shot context level** — include the optional third context level (+examples / few-shot of graded
  answers) or keep context to no-rubric vs with-rubric? Decision pending.
- ⬜ **Scope & decomposition** — confirm whole-exam (D5a) and criterion-by-criterion (D5b) stay PT-CS-only;
  decide how to parse per-question grades out of a whole-exam response.
- ⬜ **Conversation-state sub-study** — order control: shuffle order vs test multiple fixed orders; subset
  size; which single config to freeze for it.
- ⬜ **PT-CS reference** — keep "no synthetic reference" decision, or build one (confound risk)? Default: keep out.
- ⬜ **Context mapping** — finalise the per-dataset "context level" definitions (rubric vs reference) and
  document them so cross-dataset comparison is fair.
- ⬜ **Human-validation evidence** — quantify, in PT-CS, the share of responses where `cotacao` ≠ Σ`nota_parcial`
  and the mean adjustment magnitude (evidence that the two-teacher validation was substantive). Add to paper.
- ⬜ **Consensus vs independent** — confirm grading was single joint (consensus) throughout, or whether any
  separate per-teacher scores existed before reconciliation (if so, a partial inter-rater measure may be
  recoverable). If always joint, describe as consensus only and report no human ceiling.
- ⬜ **EN translation quality** — auto-translation of questions/rubrics needs human validation **before** the
  master's uses it (not blocking this article).
- 🔧 **Cost tracking** — keep the running paid-spend tally here; confirm we stay ≤ €150. **Implemented
  (Phase 0.4):** persistent ledger `data/processed/_spend.json` via `experiments/harness/cost_guard.py`
  (pre-flight estimator refuses any arm that would breach the €150 ceiling; `record()` logs real token cost
  per call). **GPT-5.1 anchor smoke test PASSED** (2026-06-07): replied "pong", 14+10 tok, €0.000108 charged
  (reasoning_effort=none accepted). **Spent so far: €0.0001** of €150. **DeepSeek**: key added and
  authenticates, but the account returned HTTP 402 *Insufficient Balance* — needs top-up before any DeepSeek
  arm can run (harness handled it cleanly, no charge recorded). Keys via env vars / gitignored `.env`
  (loaded by `experiments/harness/env.py`), never committed.
- ⬜ **Statistical model** — paired tests for reasoning on/off; mixed-effects vs ANOVA for the factorial;
  multiple-comparison correction.

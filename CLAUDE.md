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

- This is **Article 2** of the PhD compilation (Article 1 = the PRISMA SLR, IEEE ToE). **Do NOT cite Article 1
  in this paper** (user 2026-10-15): it will not be published when Article 2 is submitted. Its `.tex` stays a
  private source for the state of the art; cite the primary studies directly.
- It **feeds Article 3** = the improved **GradeGenie** platform (design decisions fixed here flow there).
- **Target venue (since 2026-10-15): IEEE Access** (user decision; quartile accepted by the user for the PhD
  points). Built with the vendored `ieeeaccess` class (§9). Access has no hard page limit and a broad
  engineering readership: keep the educational guidance, but the register can be more technical than the
  TLT framing below. *History:* the paper was written for **TLT** (primary) / **ToE** (fallback); §1.1 and
  §9.1 keep that framing as background, and the TLT build is in git history (commit 7ec38b5).
- **Advisor review (Daniel Fernandes, 2026-07-01, 79 PDF comments)** is being addressed on branch
  `revisao-access`. Its state file (all decisions D1–D15, the status of every advisor comment, the bloco C
  results) was removed in the cleanup of 2026-10-18 (Pedro's request) and is in git history:
  `git show dcc1c22:article/review/REVISAO_DF_ESTADO.md`.
- Arc across the thesis: **Map (SLR) → Analyse (this) → Build (GradeGenie)**.

### 1.2 Research questions & the deliverable's form
The paper answers a fixed set of RQs (refine wording in Phase 1, but keep them explicit — they anchor the
whole study and the Results structure):
- **RQ1 (headline).** How does **reasoning** (extended-thinking on/off) affect grading **quality, consistency,
  and cost**, and does the effect differ between **code** and **short-answer**? **Framing (refined Phase 1.7):**
  an **open question**, not a two-field divergence (no peer-reviewed evidence that reasoning *worsens*
  educational scoring exists). Reasoning helps *general* LLM-as-a-judge (Jayarao, arXiv 2509.13332, via the
  same within-family Qwen3 toggle we use) but its effect is task/architecture-dependent (Larionov 2504.08120)
  and overthinking can hurt calibration-sensitive tasks (Stop-Overthinking, TMLR 2025). **State RQ1 as
  grading-specific** — extending the general result into rubric-bounded CS grading with **cost + consistency**
  and the code-vs-short-answer contrast (the angle no prior work covers).
- **RQ2.** How much does **evaluation guidance** (no-rubric vs rubric; optionally +examples) change quality and
  consistency?
- **RQ3.** How do **scope** (whole-exam vs question-by-question) and **decomposition** (holistic vs
  criterion-by-criterion) affect agreement with the final grade?
- **RQ4.** How do **current-generation models** (incl. 2026 open-weight, untested as graders) compare, and what
  is the **cost–quality trade-off** (local vs paid frontier)?
- **RQ5 (sub-study).** Does **conversation state** (clean vs shared history) affect consistency/fairness?
- **RQ6 — REPLACED 2026-10-16 (Pedro's review): RQ6 is now the GRADING INSTRUCTION (strict vs explicit partial
  credit; see §11 'Pedro's review'). The transfer question below and the deployment angle are no longer in the
  paper; kept as history.** Former RQ6 (transfer — PARTIAL, demonstrated at reduced N). Does the configuration guidance found on public
  datasets **transfer** to a real Portuguese deployment context (PT-CS-verified, the curated intervened
  stratum, §2.2/§11)? **Rewritten (2026-06-11; supersedes both the "illustrative" and the "ranking-inversion"
  framings):** transfer is **partial and heterogeneous** — the public top open config (qwen3.5|on,
  statistically tied with glm-5.1|on) is **also the verified short-answer winner**, but the **mid-ranking
  shuffles** (gpt-5.1|off: last on public, strong on verified; deepseek on/off flips), the **per-dataset winner
  varies even within the public set** (Mohler qwen|on, SemEval glm|off, RIAYN glm|on), and under non-validated
  gold the measured **effects were qualitatively wrong** (the rubric-benefit null was a gold artifact). The
  framework's existence argument rests on this **conditionality of effects + below-top unpredictability + the
  gold lesson** — not on a wholesale ranking inversion (the earlier "public winner qwen|off → inversion" claim
  **did not reproduce**; corrected 2026-06-11, see §11 and `tab_ranking_transfer`). Where public and PT-CS
  readings diverge, the two explanations (real-context difference vs residual gold limits) remain
  non-separable — both point to the same prescription: validate locally with a trusted gold.
  - **Current paper reading (2026-10-16; supersedes the numbers above AND the 2026-10-15 ρ=0.81 reading):**
    all eight configurations are compared **on the items every configuration graded** (`phase6._common_items`,
    same rule as Table V / `bloco_c.c10`). Mixing all items for reasoning-off with the reasoning samples for
    reasoning-on had shifted levels by up to 0.10 and made RQ4 contradict RQ1 (found by the final review).
    On common items: code **ρ=0.64 (p=.09, ns)**, GLM-5.1 first and collapsing Qwen3.5|off last on both
    sides; short answers **ρ=0.21 (p=.61)**, order does not transfer (GPT-5.1|off first on the 32 PT-CS
    short items, sixth on public). Paper message: **the effects and the failure mode transfer, the fine
    ranking does not** → the guide confirms close choices locally. Regenerate: `audit_pct_baselines.rq6_transfer`.

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

1. **Ethics / GDPR (Iscte).** Secondary use of real student answers for research requires a legal basis,
   a likely Iscte ethics committee opinion, and **pseudonymisation** of the study set. The processed
   dataset **must not** contain `nome`, `email`, `password`, `reset_token`, or any direct identifier.
   This is a parallel workstream starting now, not at submission time. **Gate:** PT-CS experiments and any
   data release must not proceed **to publication** before the legal basis / ethics opinion is confirmed.
2. **Ground-truth honesty — PT-CS gold has LIMITED, HETEROGENEOUS reliability (revised 2026-06-10, do NOT
   over-claim).** The earlier "two-teacher consensus, human-validated" premise is **OVERSTATED** for much of
   PT-CS. Reality (author, 2026-06-10): PT-CS comes from a **lower-rigour requalification course** (grades
   possibly inflated — flagged as a threat, **not** a finding: the quantitative proxy is weak/unconfirmed and the
   one suggestive code signal is explained by the 0-collapse, see §11) and from **early platform tests** — **not
   all grades were teacher-reviewed**; some may be
   **AI-generated without review**; there may be **bugs**, and some **final grades were adjusted incoherently
   with the per-criterion scores**. So: describe the gold as **mixed-provenance, of limited and uneven
   reliability** — *where* teachers intervened it is a consensus correction of AI-seeded suggestions; elsewhere
   it may be unreviewed AI output. **No inter-rater κ / "human ceiling" is recoverable** (no per-teacher
   scores). **The intervention evidence is quantifiable** (Phase 2.1: % of responses where final `cotacao` ≠
   Σ`nota_parcial` = evidence of a human moving the AI sum); use it to **stratify** PT-CS into *intervened* vs
   *suspected-unreviewed* and report results on the reliable stratum (Phase 5). **This is a first-line threat**,
   not a footnote — and wherever public and PT-CS readings **diverge**, it gives **two non-separable
   explanations** (the real context differs *vs* the gold is unreliable) that point to the **same** prescription:
   validate locally against a gold you trust. **With the verified stratum (§11), PT-CS supports a transfer
   *demonstration at reduced, declared N*; the result is PARTIAL/heterogeneous transfer** (top config carries
   over, the mid-ranking does not — see §1.2 RQ6, corrected 2026-06-11). The framework rests on
   the public datasets and does not depend on PT-CS gold; the conversation sub-study measures model behaviour
   and is gold-independent.
   **Paper presentation (B2, user-ratified 2026-10-15): the paper's PT-CS IS the curated set** — "379
   teacher-validated answers (295 code, 84 short) from 97 exams", defined once in Method by the criterion
   (the final grade departs from the AI-proposed total). The internal history (1184-response export, the
   exact-sum/no-criteria strata, "requalification course", "uneven reliability", the name "PT-CS-verified")
   stays OUT of the paper. Kept in Threats: the selection effect, no inter-rater ceiling, the AI-seeded
   proposal. Whole-exam and conversation runs grade complete deployment exams and say so in one clause. This
   §2.2 analysis remains the internal record; the honesty rule now means: state the criterion, never imply
   the 379 were validated by a separate process.
   **SUPERSEDED 2026-10-18 (Pedro, decision D2 of his second review): the paper no longer states the selection
   criterion or the platform's AI suggestions anywhere (Method or Threats).** PT-CS is "379 answers ... from 97
   exams", graded jointly by two teachers. Author's decision, taken after the integrity concern was raised.
3. **No circularity.** Data used to *evaluate* configurations in Article 2 must stay conceptually separate
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

- **Machine:** MacBook Pro **M1 Max, 32 GB unified memory** — used for orchestration + local convenience
  inference only. **The 32 GB is NOT a constraint on model choice** (paradigm change 2026-06-08): models are
  selected by scientific relevance and run via **DeepInfra** when they don't fit (§6.1).
- **Inference paths (per model, §6.1):**
  - **DeepInfra** (OpenAI-compatible API) — the default for the open-weight roster (Qwen3.5, DeepSeek-V4,
    GLM-5.1, Kimi K2.6); key `DEEPINFRA_API_KEY` via env/`.env`. Has its **own spend ceiling** (§8/§11).
  - **Local Ollama** — convenience only, for models that fit 32 GB and we prefer them (smoke tests, a
    cost-floor point). Not a gate on eligibility.
  - **OpenAI** — the closed paid anchor (GPT-5.1) only.
- **Budgets (two separate ceilings, cost guard §8):** **OpenAI anchor €150** (hard) + a **DeepInfra ceiling**
  (set: **€150**, §11 2026-06-08). Estimate every arm's € before running.
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
| **PT-CS** (GradeGenie export) | code (Java) + theory | PT | ~738 code / ~437 theory | final per-question grade (`cotacao`), normalised by `pergunta.cotacao` | rubric JSON; **no reference solution**; gold is **mixed-provenance, limited/uneven reliability — see §2.2** (where intervened: consensus correction of AI-seeded suggestions); stratified → **PT-CS-verified**. **Primary code; transfer (verified stratum)** |
| **Rubric Is All You Need** (OOP+DSA) | code (Java + DSA) | EN | 149 ingested (~230 in source) | two graders collaboratively (consensus) | public (GitHub); question-specific rubrics. **Public code comparator (external validity)** |
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

### 6.1 Model roster (June 2026) — selected by SCIENTIFIC RELEVANCE, not hardware
**Paradigm (2026-06-08): the 32 GB ceiling is NOT an eligibility criterion.** Treatment is Iscte-approved (unverified, see §11 "Ethics statement facts") and
we have an inference API (**DeepInfra**) for large models. Select by scientific relevance; **infrastructure
(local vs DeepInfra) is a per-model downstream note, never an upstream filter.** Full fresh survey + selection
rationale: `experiments/model_roster.md`. This supersedes the inherited/stale roster benchmarked in Phase 0.3.
- **RQ1 within-family reasoning toggle (priority):** **Qwen3.5** (`enable_thinking`; primary, Apache-2.0,
  continuity with Jayarao), **DeepSeek-V4-Flash** (`enable_thinking`; cheap 284B/13B SOTA), **GLM-5.1** (hybrid;
  strongest open coder 2026 — confirm a clean OFF at 3.4). Each graded reasoning **OFF vs ON** — three open
  vendors isolate reasoning from vendor.
- **Paid frontier anchor (closed, exactly one):** **GPT-5.1** (`reasoning_effort` none/high; €150 ceiling).
  **Since bloco C (C5, 2026-10-15) it is no longer an "anchor" in the paper:** it grades the same items as
  the open models at k=5 and is ranked and counted like them (RQ1 has 20 model-dataset combinations).
- **RQ4 breadth** is covered by these four families (3 open + closed), 3 with a clean toggle. **Kimi K2.6 was
  CUT** (2026-06-08): priciest, no clean toggle, breadth already served — gold-plating vs minimal-effort. The
  cost range $0.14/1M (V4-Flash) → $10/1M-out (GPT-5.1) gives the cost–quality axis.
- **Infra:** most of the roster runs via **DeepInfra** (own spend ceiling, §8/§11); **local Ollama only** for
  models that fit 32 GB and we prefer them (smoke tests / cost-floor). The Phase 0.3 local models
  (`qwen3:30b`, `gemma3:27b`, `deepseek-r1:14b`, `qwen3:14b`) are **convenience only**, superseded by the above.
- **Do NOT restrict any experiment to what fits 32 GB.** Hardware is at most a convenience note for models that
  happen to fit.

### 6.2 Metrics
- **Agreement:** QWK (binned for continuous PT-CS scores — binning strategy TBD §11), Cohen's κ, Spearman/Pearson r.
- **Error:** MAE, RMSE on normalised 0–1 score.
- **Classification (SemEval binary labels):** pooled accuracy + AUROC at the fixed-0.5 cutoff. **Per-split
  reporting CUT (2026-06-15)** — the seen/unseen splits are not a valid generalisation axis for zero-shot
  prompted models (see §11); 2/3/5-way labels unused.
- **Consistency:** SD/variance across k, ICC. (Needs no ground truth — a clean axis regardless of the
  reference; PT-CS gold reliability is limited/uneven — see §2.2 — but consistency does not depend on it.)
- **Operational:** tokens; **cost — € for paid models, wall-clock/compute for local** (define per model class,
  don't conflate); latency; throughput. The headline reasoning premium must state **which** cost metric — and
  it is **measured on `completion_tokens`** (Phase 4 found it **far larger than the old ≈5–10× guess**: ON
  output ran tens× the OFF output, esp. Qwen long traces; the stale "5–10×" is superseded — compute it from
  the data per 5.4, DeepInfra bundles reasoning into completion_tokens; GPT-5.1 itemises reasoning_tokens but
  the two aren't comparable, §6.4).
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
- **Code-domain evidence is narrower than short-answer.** Code = PT-CS + RIAYN (149 ingested), both Java/OOP/DSA;
  short-answer = Mohler + SemEval (larger, more varied). State code-specific conclusions more tentatively, and
  flag this as a threat to validity.
- **Backend-conditional reproducibility (threat).** Results are conditional on the **DeepInfra-served** versions
  of the models + their sampling defaults, NOT pure model properties. Phase 3.7 showed the "same" model differs
  across backends (quantisation, chat template, reasoning/thinking handling, sampling/truncation → local Q4
  π=0.60 vs DeepInfra π=1.00). Therefore: **(a) Methods must report the backend** — provider (DeepInfra/OpenAI),
  exact served `model_id`, sampling params (temperature, max tokens, reasoning toggle), and **run dates** (all
  already logged per-run in `data/processed/runs/`, §8); **(b) Threats must state** that someone running the
  "same" models on another provider may not reproduce the exact numbers — the *configuration guidance* (which
  config beats which) is the transferable claim, not the absolute scores.
  - **Reasoning-cost non-comparability across backends (Phase 3.8, 2026-06-09).** The DeepInfra-served open
    models do **not** expose a separate `reasoning_tokens` field — thinking tokens are folded into
    `completion_tokens` and are not separable. Only the GPT-5.1 anchor reports reasoning tokens distinctly. So
    the cost analysis (5.4) must measure the **reasoning premium on total `completion_tokens`** (reasoning
    included), and state explicitly that the per-token *reasoning* cost is **not** directly comparable between
    DeepInfra and OpenAI (one bundles it, the other itemises it). `reasoning_tokens` is logged per run but is
    null for DeepInfra by design, not by omission.
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

## 7. Pruning principle (because full factorial × k=5 across the roster is costly)

Cost is now **$/token + wall-clock**, not hardware memory (we run via DeepInfra; §6.1). The pruning logic is
unchanged in spirit — keep the matrix affordable — but the lever is **token spend and k**, not model size.

- **Full factorial on cheap axes** (cheap models e.g. DeepSeek-V4-Flash $0.14/$0.28; short outputs) at **k=5**.
- **Reduce the expensive combinations**: the reasoning-ON arm (long traces → many output tokens, the dominant
  cost) is **sampled**, not fully crossed; reasoning × criterion-by-criterion was planned as sampled but
  **ultimately never run** (recorded §11, 2026-06-11); the paid anchor
  (GPT-5.1) runs a **reduced** set at **k=3**.
- Use **OFAT from a baseline** for expensive interactions, rather than the full cartesian product.
- Sample **N per condition** (stratified) rather than all items for the costly cells. Final N is a §11 decision.
- **Estimate € (DeepInfra + OpenAI) before launching any arm** via the cost guard; if an arm exceeds its
  ceiling, prune further or flag. (Wall-clock is rarely the bottleneck now that inference is API-side.)

---

## 8. Conventions

- **Reproducibility:** fixed seeds where models allow; record model version/tag, quantisation, prompt hash,
  temperature, and date for **every** run row.
- **Caching:** cache by `(item_id, config_hash, run_index)`. Reruns must skip cached calls. This protects
  both cost and time.
  **The prompt YAMLs enter `config_hash` byte for byte** (`prompts_version`, `instruction_prompts_version` hash
  the raw files): never edit `experiments/configs/prompts.yaml` or `prompts_instruction.yaml`, not even a
  comment, or every cached cell becomes a new one. (The comment in `prompts_instruction.yaml` that points to
  `article/review/REVISAO_PR_ESTADO.md` stays as it is; that file is in git history, commit dcc1c22.)
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

- Class: **ieeeaccess** (IEEE Access template, vendored with its fonts, maps and logos in
  `article/access-template/`; `article/latexmkrc` adds that folder to the TeX search paths). Author photos in
  `article/bios/`. The class redefines the `\year` primitive: the shim at the top of `main.tex` must stay or
  tikz/pgf fail. Bib via BibTeX + `IEEEtran.bst`. Figure widths in `experiments/figures/phase6.py` follow the
  Access column (85.29 mm) and text width (177.53 mm).
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
- **Float rule (Pedro, 2026-10-18), binding: every table and figure comes AFTER its first reference in the
  running text, at the nearest place after it.**
  - Nearest place for a one-column float: right after the referring paragraph, the bottom of that column, or
    the next column. For a full-width float: the bottom of the reference's page, or else the top of the next
    page.
  - How: define each float in the source right after the paragraph with its first reference, with `[!htb]`
    (one column) or `[!tb]` (full width). The generators (`make_phase5_tables._tex`, `write_guide_table`,
    `make_datasets_table`) write these options.
  - Exception for full-width floats: one may be defined just before that paragraph, after the heading of the
    same subsection, so it can still reach the bottom of that page. This is done for Fig. 6, for Table 4 and
    Fig. 7 (after the heading "The Guide") and for Fig. 9 (after the heading "Test Results", `[!tb]`). It only
    works while the heading is on the same page as the paragraph: on the morning of 2026-10-19 the heading of
    "The Guide" fell on the page before, Table 4 and Fig. 7 were queued from there and landed above their
    reference, and they went back after the paragraph until Pedro's fourth review moved the text again. The
    checker flags it whenever this happens. The patch keeps a float from going above its definition
    point, so it lands at the bottom of the page
    (after all its text) or at the top of the next. The checker confirms it comes after the reference.
  - `main.tex` patches stfloats' `\@addtocurcol` so that a float never goes above its definition point on
    the same page. Do not load `flafter`: it would replace that macro and lose the bottom placement of
    full-width floats.
  - **Checker: `article/tools/check_floats.py`.** It reads the compiled PDF. Running text is Times 10 pt,
    so mentions inside captions and tables do not count as references.
    - It runs after EVERY latexmk build (END hook in `article/latexmkrc`) and by hand with
      `make check-floats`.
    - Every violation is an ERROR and fails the build. There are three kinds:
      - a float before its first reference;
      - a float never referenced;
      - a float not at one of the nearest places above, so never two pages after its reference.
      Pedro does not accept that last case.
    - Every version must have 0 errors. The final version of 2026-10-18 has 0.
    - Tested on 2026-10-18 on a copy with the old guide-section layout (Figs. 9 and 10 two pages after
      their reference): the build failed with exactly those two errors.
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

### 9.2 Writing register (binding for all paper prose)
The paper is written for **human reviewers and readers, not for maximum information density**. Target register:
a strong journal paper in the target venue, technical, precise, and **readable at normal speed** by a
researcher in an adjacent area who does not work on this exact topic.

**Rules:**
- **Acronyms & technical terms — three tiers of explanatory load:**
  - **Tier A** (universally known to the venue — LLM, API, CI): expand at first use; no explanation needed.
  - **Tier B** (field-standard but interpretation-dependent — QWK, ICC, MAE, AUROC, macro-F1): expand at first
    use **plus one light clause** saying what it measures and how to read it. One clause, not a paragraph — the
    reader knows the family, we are calibrating the instrument.
  - **Tier C** (project-specific or uncommon — a coined phenomenon name, a curated data subset, a custom
    metric): **one full plain-language sentence** defining it at first appearance, before it is ever used as
    shorthand.
  - **Never invent acronyms for project-internal concepts** (do not coin an acronym for a multi-word project
    term, write it out; a short descriptive name, used consistently after introducing it once, is fine). When in
    doubt about the tier, **go one tier heavier** — the cost is a clause; the cost of the alternative is a
    reviewer who cannot read the results.
- **Gloss anything a reader stops on, and prefer the ordinary word.** The acronym tiers extend to *any* term a
  non-specialist could pause over: statistical vocabulary (significance, a multiple-comparison correction,
  pooling, a stratum, a robustness check) and project-specific descriptive labels both get a one-clause plain
  gloss at first use or are rewritten in plain words. If a phrase keeps prompting the question "what does that
  mean?", that is the signal to **rewrite it, not to defend it**. Between two accurate words, choose the
  ordinary one over the stiff or rare one (e.g. "cautiously" over "tentatively").
- **Sentence load:** one idea per sentence as the default. If a sentence needs three qualifications, the
  qualifications likely belong in the **threats/limitations** section, not inline — state the claim cleanly and
  point to where it is scoped.
- **Numbers in prose:** a number appears **with its meaning**, not alone ("agreement rose by 0.17, from 0.44
  to 0.61" reads; a bare "+0.170 (N=67)" dropped mid-sentence does not; sample sizes and other bases live in
  **table notes**).
- **Paragraph openers carry the point:** a reader who reads only the first sentence of every paragraph should
  follow the argument of the section.
- **Punctuation:** **avoid em dashes and en dashes as prose punctuation** (the long dash used for asides or
  emphasis). Use commas, colons, parentheses, or separate sentences instead. This applies to **all paper prose,
  including the abstract, captions, and table notes**. Hyphens in compound words (state-of-the-art,
  question-by-question) and minus signs or ranges in math and tables (a delta of -0.043, pages 4-7) are fine
  and not covered by this rule.
- **"X, not Y" constructions are banned as rhetoric** ("empirical, not conceptual"; "operational, not
  predictive"; "not an autonomous system, but..."): they read as templated AI prose. Write the positive claim
  and let context carry the contrast. Sole exception: when the contrast IS the finding.
- **No defensive hedges or disclaimers; assert what the evidence supports.** Openers like "results are real
  but...", conclusions that re-derive methodology, and sections that end by listing what remains difficult are
  banned. Conclusions state findings, magnitudes, and consequences. Weaknesses of the field are reported as
  measured findings, never as accusations against prior work and never phrased so they undermine this paper's
  own evidence.
- **Claims carry magnitude and an anchor.** Effect sizes appear with both endpoint values and an
  interpretation anchor (the scale's maximum, an agreement band such as moderate to substantial, a human
  ceiling from the same experiment). Never convert non-ratio coefficients (kappa/QWK) into percentage changes.
- **Section structure — each section type has its own job; do not leak content across them.** The single most
  important discipline: **a finding appears only in Results (and is interpreted in Discussion).** Do not preview
  results, numbers, or verdicts in the Introduction or Method, and do not introduce new method detail in
  Results. Each section does its own work and only its own work.
  - **Introduction — motivation and the question, never the answer.** State the problem, the gap, the research
    questions, and the contribution *claims at the level of "we study/deliver X"*; do **not** report what was
    found (no result numbers, no "we show that reasoning helps"). It says *what the paper does and why it
    matters*, then hands off.
  - **Method — how the experiments were run, never how they turned out.** Describe the design space, datasets,
    harness, protocol, metrics, and statistics so the study is reproducible. No results, no interpretation, no
    "as we will see". Define instruments here (Tier-B/C calibration of metrics belongs at first use, which is
    usually Method).
  - **Results — the setup→evidence→verdict arc, per subsection:**
    - **Never put the conclusion in the heading.** Headings name the *topic*, not the finding (name the factor
      under study, not the verdict about it). The reader reaches the verdict by reading, not by reading the
      title.
    - **Never open a subsection with its label or a bare claim.** Do not start with the research-question label
      ("RQ N asks…") or with the answer stated flat. Open with the **substance**: what the thing under test
      *is*, what is being compared, and against what baseline, pointing to the figure/table. The first paragraph
      sets up the comparison neutrally.
    - **Put the verdict in a closing paragraph that opens with "Overall, …"** (a light semi-conclusion). State
      the finding once, cleanly, with its practical reading, and only there. Cadence: set up → evidence →
      "Overall, …".
    - **Paragraph openers carry the argument:** a reader skimming first sentences gets setup, then evidence,
      then the "Overall" verdict, in that order.
  - **Discussion — interpretation and synthesis, not a re-listing of results.** Pull the threads together into
    the framework/implications; refer back to Results rather than repeating its numbers.
- **Evidence presentation — comparison over enumeration, figures over dense tables:**
  - **Privilege a comparative reading, not a data dump.** The job of a results subsection is to *compare* (this
    config vs that, with effect size + CI) and say what it means, not to recite every cell. If a table merely
    re-lists what a sentence or figure already says, cut it.
  - **Prefer the right chart to a dense table.** When the point is a comparison of magnitudes or a trade-off,
    a well-chosen figure (bars with CIs, a trade-off scatter) reads faster than a wide numeric table. Choose the
    chart type for the message; do not default to a table because it is easier to generate. Reserve tables for
    reference material a reader will look values up in, not for the headline comparison.
  - **One figure, one message.** If a panel has no level difference to show, do not plot it (state it in prose);
    a chart that "transmits no information" is worse than a sentence.
  - **Place the figure after its reference** (the binding float rule in §9, checked after every build). Prefer
    **inline single-column** figures so they flow with the text; only
    promote to a full-width (`figure*`) float when the content genuinely needs the width. Keep captions readable
    on their own (Tier-B/C terms calibrated) but trim caption text that only describes a panel you removed.
- **Neutral provenance for generated artifacts.** Describe figures and tables as **built from the experiment
  values** (e.g. "created from the run data", "computed from the logged outputs"), not as "generated by the
  analysis script / the code that analysed X". The reader cares that the numbers come from the experiments, not
  about the tooling. (Reproducibility/engine-backed-numbers discipline still applies behind the scenes; it is
  just not the register of the prose.)
- **Naming is a scientific claim, not a label.** Name things by what is *true*, not by what is convenient: pick
  the term that denotes the actual contrast under study, not a loose synonym that happens to be handy but
  describes a different axis. If explaining a phrase takes piece-by-piece unpacking, the phrase is wrong:
  rewrite the idea plainly instead of defending the wording.
- **Do not overclaim, and align prose with the synthesis.** Results prose must not assert more than the tables
  show (a non-significant gain is not "X helps"); and it must agree with the paper's own framework/decision
  table. When a clean-sounding rule contradicts the evidence or the framework, state the honest, conditional
  rule instead, even if it is less catchy. **Any statement of *how* results are reported** (which subset,
  metric, or basis is primary, and which is a robustness check) **must match what the tables and figures
  actually do** — verify the prose against the artifacts, do not describe an intended reporting rule the
  tables do not follow.
- **Limitations belong in one place and must not sap the contribution — and this applies WHILE writing**
  (diretiva Pedro 2026-08-20): a caveat or methodological reservation that surfaces while drafting analysis or
  conclusions goes to the threats section **only if it materially matters to the paper's claims; otherwise it
  is dropped** — not every sentence earns a caveat, and the default for a drafting-time reservation is
  deletion, not relocation. **The threats section's own size is controlled**: it must read as the scoping of a
  solid contribution, never as one disclaimer per finding — if it drifts toward that, prune to the few caveats
  that could actually change a reader's decision. The abstract and the Conclusion carry claims, magnitudes,
  and consequences only, with a methodological caveat admitted there only if the paper would be misread
  without it. State each limitation **once**, in the
  threats/limitations section, not as a recurring caveat threaded through Results, Discussion, and Conclusion;
  a weakness repeated in every section reads as the paper's headline and quietly removes its own relevance.
  The limitations section **leads with containment** (why the limitation does not reach the main conclusions),
  then states each limitation crisply, one per sentence, without wandering into mechanism or mitigation detail
  that belongs in Method. Open it on the strongest reassurance, not the deepest fear.
- **Describe cited work only as it actually reports.** Every claim about what a reference did or found must be
  **checkable against that source**: verify it against the abstract or paper before writing it, not from memory
  or a secondary note, and never characterise a reference beyond what it reports. A misattributed method or
  result is a correctness error, not a wording one. This applies with full force to *future work*, where the
  temptation to contrast "unlike prior work, we will…" invites misstating what prior work did.
- **The Conclusion closes the loop the Introduction opened.** A reader going straight from introduction to
  conclusion should feel continuity: open the conclusion by **returning to the problem the introduction framed**,
  not with an abrupt cold restatement, and let the two be readable back to back. End on strength: the last
  sentence of a section carries its contribution or takeaway, so **cut closing sentences that add no
  information**.
- **Future work separates internal gaps from open questions in the field, and never proposes work already done.**
  Distinguish what *this study* left open (declared design gaps) from what the *literature* has not settled;
  check each proposed direction against prior work and drop or reframe any already addressed, citing to show the
  awareness. A "gap" that is not a genuinely interesting next step is not future work; cut it.
- **Reference and decision tables: make every row self-contained.** When cells wrap to several lines, separate
  rows with a rule or vertical space so a wrapped line is never mistaken for a new row; give the first column a
  header that names *what the rows are keyed on* (not a vague "Item / context"); left-align prose columns rather
  than justify them; keep each cell to its one point and its key number.
- **A figure is graphical, not a container for prose.** Represent the content as nodes, arrows, decisions, and
  short labels, with consistent visual styles for inputs, decisions, and processes; explanatory sentences belong
  in the caption or the body, never as paragraphs inside the figure.
- **No section cross-references in prose** (Pedro, 2026-10-18; comments #3, #29, #30, #37, #38, #41):
  - do not send the reader to another section ("(Section IV-A)", "Section III-C explains why ...");
  - say the thing where it is needed, or point to the figure or table;
  - the section map at the end of the Introduction is the exception.
- **Test:** before any section is declared done, re-read it asking **"would a tired reviewer follow this on
  first pass?"** — if a sentence requires re-reading, rewrite it. **Density is not rigor**; the rigor lives in
  the tables, the engine, and the threats.

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

- ✅ **Course-correction (Phase 1.7, 2026-06-08)** — **PROCEED, no redirection** (user-approved). Refined SoA
  still supports the planned direction; the field moved toward our axes but as point solutions, not a
  systematic design-space study → the framework/decision-guide is the unfilled niche. **Three sharpenings
  recorded:** (1) lead with the decision-guide deliverable, not per-axis numbers; (2) state RQ1 as
  grading-specific (extends Jayarao 2509.13332 into rubric-bounded CS grading with cost+consistency); (3) cite
  not adopt new benchmarks (SAS-Bench/EssayJudge), keep code claims tentative. Full analysis in
  `article/related/course_correction_1.7.md`. Only real change = RQ1 motivation (divergence → open question),
  already absorbed.
- ⬜ **Interim results gate (Phase 4)** — after the first real results (baseline + non-reasoning main effects),
  is the harness sound (parse rates, sane scores) and the expected signal present before committing time/budget
  to the reasoning and paid arms? Record go / adjust.
- ⬜ **Artifact-release scope** — confirm what ships (harness, prompts, public-dataset configs/ingest) and
  whether the anonymised AI-comment-stripped PT-CS subset can be released (ethics-gated).
- ✅ **Model roster** (2026-06-08, paradigm change — supersedes the 0.3 local-only selection below) — **32 GB
  is no longer an eligibility criterion** (Iscte-approved, unverified; DeepInfra API for large models). **Selected by
  scientific relevance** (full survey + rationale: `experiments/model_roster.md`, §6.1): **RQ1 within-family
  toggle** = Qwen3.5 + DeepSeek-V4-Flash + GLM-5.1 (each OFF vs ON); **closed anchor** = GPT-5.1. RQ4 breadth
  = these 4 families (3 with a clean toggle). **Kimi K2.6 CUT** (priciest, no toggle, breadth already served —
  minimal-effort). Infra per-model (mostly DeepInfra; local Ollama = convenience only). **3.4 checks DONE**
  (2026-06-08, smoke-tested live): confirmed DeepInfra IDs `deepseek-ai/DeepSeek-V4-Flash`,
  `Qwen/Qwen3.5-35B-A3B` (the planned 235B-A22B does not exist — 3.5 MoE variants are 35B-A3B / 397B-A17B),
  `zai-org/GLM-5.1`; anchor `gpt-5.1`. **All four toggles are CLEAN** (output tokens off→on: V4-Flash 7→342,
  Qwen3.5 7→3584, **GLM-5.1 10→440 ← clean OFF confirmed, stays in the RQ1 arm**, GPT-5.1 15→569). All
  parse_ok on a real Mohler item; DeepInfra off-mode follows "JSON only" perfectly (7–10 tok).
- ✅ **DeepInfra spend ceiling** (2026-06-08) — **€150** (separate from the OpenAI €150). A **runaway guard**
  (catch bugs), not a usage squeeze: the matrix estimate is ~€30–100, so €150 leaves margin over the worst
  case and only refuses arms that exceed it. In `pricing.yaml` as `deepinfra_budget_eur_ceiling`; per-provider
  enforcement wired at Phase 4.1.
- ⚠️ **Local model selection** (Phase 0.3, 2026-06-07) — **SUPERSEDED by the roster above** (kept as a record
  of local-convenience speeds). Roster pulled and benchmarked on M1 Max 32 GB (Q4_K_M). All ran at acceptable
  speed:

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
- 🔧 **N per condition** (4.1, scaled per user 2026-06-09 — awaiting final go before any run) — in
  `experiments/configs/matrix.yaml` `sampling:`. **Criterion: strong power where we infer, containment where
  we only reference.** Cheap OFF main-effect cells scaled aggressively (they dedupe into baseline/non-reasoning/
  context + the reasoning-OFF side): **Mohler all 2273, SemEval 800, RIAYN all 149, PT-CS code all 737, PT-CS
  theory all 437**. **Reasoning-ON sampled to 175** (RQ1 axis — moderate power; was 60). Whole-exam = 60 PT-CS
  submissions. Conversation sub-study = 20 submissions × 2 orders. **Paid anchor GPT-5.1 pinned at item_cap=60,
  k=3** (reference point, not inference). **Estimated real (deduped) spend ≈ €11.25 DeepInfra (~14.5 h wall @
  8× parallel) + €5.45 OpenAI (~40 min) ≈ €16.7 total** — far under the two €150 ceilings. Print via
  `python -m experiments.run.matrix estimate`. Note (§6.4): this powers the **main effects + reasoning
  contrast**; interactions among expensive factors stay OFAT/underpowered by design — do not over-read them.
- ✅ **Baseline (reference) config** (4.2, user 2026-06-08) — **Qwen3.5** (DeepInfra, reasoning off, with
  grounding, q-by-q, holistic), at k=5 across all datasets. Chosen over DeepSeek-V4-Flash as the internal
  reference because it is the RQ1 primary, Apache-2.0, neutral cross-domain, and continuous with Jayarao —
  all "better/worse than baseline" framing is relative to this. (GLM-5.1 rejected as baseline: code-leaning,
  less neutral.)
- ✅ **RQ6 transfer data dependency** (decided 4.1, 2026-06-09) — RQ6 is a Phase-5 *analysis* (5.5b), not an
  arm. **Covered structurally, no separate transfer arm:** `matrix.yaml` includes **ptcs:code in baseline,
  nonreasoning_main, reasoning_arm, context_arm AND anchor_reduced**, so EVERY candidate config (any model ×
  {off,on} × {none,with_guidance}) already has a like-for-like PT-CS counterpart — whatever wins on the public
  datasets, 5.5b can compare it on PT-CS. (Whole-exam/criterion/conversation are additionally PT-CS-only by
  design.)
- ✅ **PT-CS gold reliability — STRATIFIED (Phase 5, 2026-06-10), RQ6 = partial transfer at reduced N** —
  PT-CS gold is mixed-provenance, limited reliability (§2.2). Stratified by intervention evidence (`cotacao`
  vs Σ`nota_parcial`, re-queried READ-ONLY from the DB → `data/processed/_ptcs_strata.parquet`): of 1184
  responses, only **32.3% INTERVENED** (final ≠ sum, human moved it; mean adjustment 1.43), **33.2% exact-sum**
  (suspected unreviewed), **34.5% no-criteria** (unassessable). **Two-thirds lack evidence of human review.**
  **Re-ran the key contrasts on the INTERVENED stratum (analysis only): the central results HOLD →** collapse
  persists (Qwen frac0 0.49) but QWK rises 0.31→**0.47** (low full-PT-CS QWK was partly gold-quality);
  reasoning ptcs-code dQWK **+0.17** (all-intervened basis, N=67: 0.44→0.61; NB the committed `tab_rq1_reasoning`
  V column and Phase 7 use the **clean-only** intervened basis, N=61 → **+0.113**, same direction — both
  reproduce, different denominators); **ranking transfer is PARTIAL** (corrected
  2026-06-11 — the earlier "ranking inversion holds; public winner qwen|off → intervened-PT-CS winner
  gpt-5.1|on 0.897" **did not reproduce in the 2026-06-11 audit**: under every basis tested — item-mean QWK
  full-N, run-level QWK, MAE, anchor-paired-60 — **qwen|off ranks 7/8 on the public datasets** (mean QWK 0.59);
  the public top is **qwen3.5|on ≈ glm-5.1|on (0.667)** and qwen3.5|on is **also the verified short-answer
  winner (0.795)** → the **top transfers**; what does NOT transfer is the **mid-ranking** (gpt-5.1|off last
  public / strong verified; deepseek on/off flips; verified-code winner = glm-5.1|off) and the per-dataset
  winners vary even within the public set — generated table: `tab_ranking_transfer`, declared basis in its
  caption; the anchor stays unranked corroboration). **KEY:** the rubric "non-transfer" was a **GOLD ARTIFACT** —
  full PT-CS dQWK +0.005 (ns) but INTERVENED **+0.146** (like RIAYN +0.123; digits re-baselined 2026-06-11,
  seed-per-call bootstrap) → on items where a human actually
  aligned the grade to criteria, the rubric helps. So the earlier "rubric doesn't help on PT-CS" is RESOLVED
  (gold quality, not the rubric). **Consequences:** results held → **assertive** wording. **PROMOTION (user
  2026-06-10):** the intervened stratum is promoted to a **transfer dataset of full right — "PT-CS-verified"**
  (curated by the auditable criterion `cotacao ≠ Σnota_parcial`); the rest is **excluded by declared criterion**
  (answers "if you don't trust the gold, why use it?" → we didn't, we curated). RQ6 = **demonstration at
  reduced, declared N** (not case study). **HYBRID PT-CS REPORTING RULE (2026-06-11; supersedes the earlier
  blanket "main tables report PT-CS-verified" — which the 5.7 tables never actually implemented, audit
  2026-06-11):** **(i) paired intra-PT-CS contrasts** (reasoning, scope, decomposition, context-on-PT-CS)
  report **full-N as primary + a PT-CS-verified column as robustness**. **Read the V column honestly, per
  cell** (generated 2026-06-11): where verified N is large it can CONFIRM AND AMPLIFY (context +0.005→+0.146
  sig, N=295; scope −0.033→−0.060, N=77) but also WEAKEN (decomp −0.043 sig → −0.022 ns, N=295 — say so; softening user-ratified 2026-06-11, framework row added linking it to the original distrust of per-criterion scores);
  on the reasoning rows verified N=25–67 → wide/unstable cells (e.g. ptcs-short glm +0.220 full vs −0.022
  V@32) — read those as CI-width caveats, NOT effect re-estimates. **(ii) absolute levels, cross-dataset
  comparisons and transfer: verified only**; **(iii) figures stay verified-only** with captions stating the
  stratum; the full-vs-verified **SENSITIVITY remains itself a result** ("non-validated gold distorts: QWK
  0.31→0.47, and masks real effects: rubric +0.005→+0.146"). State the stratum + N in every caption.
  - **VERIFIED-ONLY THROUGHOUT (2026-06-17, user-ratified) — SUPERSEDES the hybrid rule above for the paper.**
    Every PT-CS *agreement* result in the paper now uses the **PT-CS-verified** stratum: RQ1 reasoning, RQ2
    guidance, RQ3 scope/decomposition, RQ4 per-dataset, RQ6 transfer, all figures, and the framework table
    (guidance +0.146, decomp −0.022, scope −0.060, collapse-repair Qwen +0.113, premium 94--192×). The full
    dataset no longer appears in the Results/Method/Threats prose — the "full-N primary + V column" wording was
    removed from `method.tex`, the results preamble, and `threats.tex`, and no V column appears in any in-paper
    table. **Consequences ratified:** (a) the RQ1 PT-CS-short reasoning cells **GLM +0.220 / GPT +0.208 (full,
    sig) drop to ns** on verified (−0.022 @N=32 / +0.021 @N=11); the surviving significant reasoning cells are
    Qwen on Mohler/SemEval/RIAYN/PT-CS-verified-code (+0.113) and GPT on RIAYN (+0.192); "Qwen sig on 4/5" still
    holds. (b) the **gold-artifact contrast (+0.005 full → +0.146 verified) was REMOVED from RQ2** — verified
    +0.146 now stands alone as the guidance result, so the 2026-06-16 note below ("already shown in RQ2") is
    **STALE**: the artifact is now shown nowhere. (c) the premium in `make_phase5_tables.py` is computed on the
    intervened stratum for PT-CS (public datasets unchanged), so the framework discrim-code range moved 116→94
    at the low end; `tab_rq1_reasoning`/`tab_dimension_contrasts` still carry both bases but are NOT in the
    paper. Rationale: verified is the honest basis (the full PT-CS numbers were on unreliable gold), and it
    removes the dataset-defence framing the author has consistently cut. The conversation sub-study stays
    gold-independent (all 20 submissions, no stratum).
  - **Gold-sensitivity SUBSECTION + table + figure CUT from the paper body (2026-06-16, user-ratified).**
    Rationale: a full results subsection ("Sensitivity to Reference Quality") plus `tab_gold_sensitivity`
    and the full-width `fig6_gold_sensitivity` spent disproportionate space **defending the dataset** rather
    than **building the framework**, and the one framework-relevant point (an unreliable reference hides real
    effects) was **redundant** — the rubric artifact (+0.005 full → +0.146 verified) is already shown in RQ2
    and its figure. **Now:** one short paragraph inside **RQ6 (sec:rq6)** carries the lesson with the key
    numbers (QWK 0.308→0.468 full→verified; rubric +0.005→+0.146; the framework's "validate against trusted
    gold" rule); the **gold-reliability threat stays in §Threats** (the −0.19→−0.27 deviation now inlined
    there, no table). The numbers stay **engine-backed**: the former `tab_gold_sensitivity` block in
    `make_phase5_tables.py` still recomputes them and **prints them as an audit line** (no table emitted);
    `phase6.fig6` was removed and its `.pgf`/`.pdf` deleted. The deviation metric (the weakest, near-circular
    "verified = better gold" claim) is **dropped from the RQ6 prose** and kept only as the conservative-proxy
    threat. Do NOT reintroduce the subsection/figure; if a numeric exhibit is ever needed, git-restore the
    `_tex` call or read the audit print.
  - **Transfer framing (updated 2026-06-11):** stated via the **open models (N=84 OFF / 32 ON, declared)** —
    reasoning helps them on verified short-answer (qwen .652→.795, glm .692→.771); **ranking transfer is
    partial** (the top carries over, the below-top shuffles — `tab_ranking_transfer`). **The GPT-5.1 anchor is
    N=11 → directional corroboration ONLY, never headline/abstract/highlight table, never named "winner"**;
    show its CI beside the QWK (0.897 on 11 items self-defends with a wide CI).
  - **Strata asymmetry (Discussion):** short-answer verified = **19% (84/437)** vs code **295** — short-answer
    transfer rests on a small fraction (say it). Curious inversion: **code**, the "narrow" domain (§6.4), has the
    **comfortable** verified N in transfer.
  - **Criterion LIMIT (threat):** the criterion detects **intervention, not correction** — an exact-sum may be a
    teacher who reviewed and agreed (→ filed "no evidence"); a **conservative proxy**, "intervention evidence" ≠
    "validation guarantee". Declare reduced N in every transfer claim.
  - **Rubric (rewritten):** NOT a "second non-transfer" — the apparent null was a **gold artifact**; on the
    verified stratum the rubric helps (+0.146; Qwen3.5 — the context arm ran on Qwen3.5 only), consistent with
    RIAYN (+0.123) → **the rubric benefit transfers
    when the gold is reliable.** Remaining transfer caveat = the **below-top ranking instability** (thread 1);
    the **gold lesson** = thread 2. Framework rests on the public datasets; conversation is gold-independent.
- ⚠️ **PT-CS gold — GRADE INFLATION (second, distinct threat; document, don't exclude)** (2026-06-10) — beyond
  incomplete validation (resolved by stratification), the source course was a **lower-rigour requalification**
  with a probably **lenient grading standard** (1–2 marks where strict gives 0). **No mechanical exclusion**
  (not detectable by any field) → **first-line threat alongside validation**, with the distinction:
  stratification resolves *"who validated"*; inflation is *"with what standard"*, and the verified stratum does
  **not** resolve it. **Quantified proxy (5b): WEAK — report as NOT supporting inflation; do not manufacture.**
  The reproducible per-dataset signed model−gold deviation (baseline cell **qwen|off|with_guidance|qbq|holistic**,
  item-level; regenerate via `experiments/analysis/phase5.py::signed_deviation`) shows the model is **NOT "stricter
  everywhere"**: short-answer is *lenient* (SemEval **+0.05**, PT-CS-short-verified **+0.10**), code is stricter
  (RIAYN −0.19, Mohler −0.15). The one suggestive signal — PT-CS-verified code being the strictest (−0.27) — is
  **the 0-collapse, not inflation**: its extra-strictness vs comparable RIAYN code **shrinks as the collapse goes
  away** (Qwen −0.077 @frac0≈.49 → DeepSeek −0.039 @frac0≈.13 → GLM −0.018 @frac0≈.13; digits re-verified
  2026-06-11). Robust sub-claim retained: **unvalidated
  (full) gold understates the deviation magnitude** (full PT-CS code −0.19 → verified −0.27; verified further from 0
  in both domains), reinforcing the validation threat. _(Correction 2026-06-11: the earlier numbers here
  (−0.154/−0.149/−0.116; full −0.048/verified −0.104) mixed two unrecorded bases — qwen-only vs all-models-pooled —
  and did not reproduce; replaced with the reproducible baseline-cell computation. Qualitative verdict unchanged and
  now de-confounded.)_ **5.5c competing explanation:** part of the Qwen-0 vs gold-1/2 gap may be **model severity
  × gold leniency**, not only discrimination failure — **comparative** readings (same gold) hold; **absolute**
  ones are qualified; use the **leniency** metric (§6.2) as the lens. **Article 3 lesson — two floors:**
  traceable validation **and** a calibrated rigour standard.
- ✅ **Backend-conditional reproducibility** (2026-06-08) — recorded as a §6.4 threat + a Methods requirement:
  results are conditional on the DeepInfra/OpenAI served versions + sampling params (3.7: same-name models
  differ across backends). Per-run repro fields already logged (`runs/`); the *guidance* transfers, not the
  absolute scores.
- ✅ **Reasoning×criterion cells — PLANNED, NEVER RUN (recorded by the 2026-06-11 audit)** — §7 and PHASES 4.1
  promised "sampled reasoning × criterion-by-criterion" cells; the run data contains **only criterion ×
  qwen3.5|off (737 items)** — no reasoning-ON criterion cell exists, and **no decision to drop it was recorded
  at the time**. Recorded now, honestly: scope was reduced (deliberately or by omission — no contemporaneous
  record), the decomposition claim is therefore **reasoning-OFF only**, and reasoning×criterion is **future
  work**. Do not imply the interaction was measured.
- ⬜ **Interactions to probe** — which 2-way interactions are worth the cost vs main-effects-only.
- ⬜ **Fine-tuning arm** — include or drop? If included, which model and QLoRA-local vs managed fine-tune.
- ✅ **QWK binning** (Phase 5, 2026-06-10) — bin the **normalised** 0–1 score into **K = 5** ordinal levels
  (0..5, 6 bins ≈ Mohler's native 0–5, so QWK is comparable across datasets); fixed a priori, with a
  **sensitivity over K∈{4,5,6}** reported. See Phase 5.0.
- ✅ **SemEval score→label** (Phase 5 review, user 2026-06-10) — the model emits a continuous 0–1
  score; SemEval gold is a **binary 2-way label** (correct/incorrect; gold_score 0/1). Map with a **fixed
  threshold 0.5** on the normalised score — **NOT data-tuned** (would be circular). Report accuracy + AUROC
  (threshold-free MAE/Spearman also available). (3/5-way labels unused — model wasn't asked for them.)
- ⛔ **SemEval seen/unseen SPLITS — CUT (2026-06-15), do NOT reintroduce as a generalisation claim** (user
  decision, option B). The SemEval-2013 Task 7 splits (seen / unseen_ans / unseen_domain / unseen_q) were
  defined for **SUPERVISED** systems **relative to a training set**. Our models are **prompted, zero-shot,
  with no training set**, and the reference answer is provided in every split (no few-shot), so the splits
  **do not denote novelty/familiarity to our grader** — to a zero-shot LLM the four groups are just different
  content subsets, not a train→test shift. The earlier per-split table (old Table IV) and its framing
  (`generalisation`, `domain shift`, `holds up as material gets less familiar`) were **over-claiming and are
  removed**. Results now report **only pooled SemEval accuracy/AUROC** (acc 0.73–0.79, AUROC 0.81–0.85 across
  models, off, with_guidance) plus one sentence stating why we do not split. `phase5.semeval_splits()` is kept
  for audits but **must not** be turned into a generalisation result. **Future writing: never frame SemEval
  splits as generalisation/domain-shift for these models.**
- ✅ **Consistency = first-line RQ1 result** (Phase 5 review, 2026-06-10) — the Phase-4 data shows reasoning
  ON **reduces** k-consistency (even at temp=0, where 10–43% of items still vary — backend-conditional). So
  **RQ1 has two dimensions that can diverge: agreement vs consistency** — analysed as a headline (5.3/5.5a),
  not a footnote. **CAUSAL CAVEAT (rewritten 2026-06-11, upgrades the 2026-06-10 reading; user-ratified 2026-06-11):** within-item SD
  correlates with output length only **moderately and heterogeneously per cell** — Spearman **median 0.46,
  range 0.11–0.78**, weak on Mohler (0.11–0.28 across models); declared basis + regeneration:
  `phase5.sd_length_spearman` (per (dataset,model), with-guidance/qbq/holistic cells, OFF+ON pooled, item
  level; the earlier "~0.6, all models/datasets" had an unrecorded basis and did not reproduce). **Therefore
  the consistency loss under reasoning is NOT reducible to the mechanical length effect:** part is
  **length × backend non-determinism** (more tokens at temp=0 = more chance to diverge), and the **residual
  behaves like a property of reasoning itself**. Present BOTH components; claim neither pure story. The result
  stands (inconsistency is real for the user) but the **explanation must say
  so** — ties to §6.4 (backend-conditional). Do NOT frame it as "the model reasons differently each time".
- ✅ **RQ1 agreement gain — censoring check (verified 5.2, 2026-06-10)** — the Qwen-ON QWK gain is NOT a
  truncation-censoring artifact: it **survives strict pairing on items the ON never truncated** (PT-CS code
  +0.162 loose → +0.138 clean-only, point estimates — the tab_rq1 boot median is +0.136; RIAYN/SemEval even
  grow; *digits corrected 2026-06-11 — the earlier +0.136/+0.110 did not reproduce*). **Two caveats the
  framework must encode:** (a) PT-CS short-answer lost ~45% of the naïve gain to censoring (+0.183→+0.101,
  recomputed 2026-06-11); (b) the truncated items
  ARE genuinely harder (OFF MAE 2–3× higher on them), so the reasoning benefit is established **only on the
  tractable items** — on the hardest (reasoning overflows 32768) we have no clean ON score and **cannot claim
  the benefit extends to them**. Scope the claim accordingly.
- ✅ **Phase-5 pairing subsets** (Phase 5 review, 2026-06-10) — every expensive contrast pairs on its sampled
  subset or it's biased: **reasoning 175**, **scope 252** (whole-exam questions, not all 737), **anchor 60**.
  State the N in each contrast. (Full rationale + the other Phase-4-review corrections — call_group cost
  dedupe 4.2×, context = two interventions, code 0-collapse model-specific, non-random truncation exclusion
  threat — are in the revised Phase 5 in PHASES.md.)
- 🔧 **Score clamping to [0, max]** (Phase 4, 2026-06-09) — Phase 5 must **clamp predicted scores to
  [0, gold_scale_max]** before metrics. Discovered by the integrity audit: 18 PT-CS criterion items
  (88 rows, Qwen3.5, reasoning-off, criterion decomposition) sum to a **negative total** (e.g. -0.5) because
  the rubric has **penalty criteria** ("Descontar caso ordene ao contrário") and the model applied only the
  penalty. The parser is correct (sum matches); negative grades just aren't valid (a question can't score
  below 0), so clamp -0.5→0. Not corruption — a normalisation decision. (No scores ABOVE max exist.)
- ⚠️ **Code-grading 0-collapse (discrimination, not just severity)** (Phase 4, 2026-06-09) — on **PT-CS code**,
  **Qwen3.5 OFF (the baseline)** collapses a large share of grades to **0**: in the whole-exam arm (60
  submissions, all data, not just the validation sample) **42% of scores are exactly 0**, mean 0.82; and the
  q-by-q baseline gives the **same 0s on the same items** (so it's the model, scope-independent, and the raw
  shows explicit `"score":0` with `parse_ok=true` — real judgments, not coercions). This is **discrimination
  collapse at the lower end**, not mere severity — consistent with PT-CS having the **lowest QWK of the datasets (0.31 full / 0.47 verified; K=5 item-mean,
  basis corrected 2026-06-11)** of
  the datasets. **Three Phase-5 watchpoints:** **(a)** for **RQ1 on code**, do NOT conclude "reasoning helps"
  from a level shift alone — check whether reasoning changes **discrimination at the lower end** (e.g. QWK /
  spread among the 0-clustered items), not just the mean; **(b)** read any "**better than baseline on code**"
  with the caveat that the baseline itself collapses to 0 (a low bar — say so); **(c)** ties to **§6.4** (code
  evidence is narrower — PT-CS + RIAYN, Java/OOP — state code conclusions more tentatively).
- ✅ **Few-shot context level** (4.1, user 2026-06-09) — **KEPT OUT.** Context arm stays {none,
  with_guidance}. **Not** excluded for cost (trivial) but because (a) doing it rigorously needs an
  example-selection sub-dimension — a confound we don't want to introduce carelessly — and (b) it is a third
  level of a *secondary* axis (RQ2) while the focus is RQ1. **Reopening is a data decision:** if Phase 5 shows
  with_guidance (rubric/reference) has a strong effect on agreement, +examples becomes a justified extension
  and is added then, **with its own example-selection protocol**. Recorded as a decision + revision condition,
  not a silent omission.
- ✅ **Scope & decomposition** (Phase 2.6, 2026-06-08) — **PT-CS only**, confirmed by data: PT-CS is the only
  dataset with multi-question submissions (181 `submission_id`s grouping items) AND rubric criteria, so
  whole-exam (D5a) and criterion-by-criterion (D5b) apply to it alone. Mohler/SemEval/RIAYN have
  `submission_id`=null (independent items) → question-by-question + holistic only. (Still open: how to parse
  per-question grades out of a whole-exam response — a Phase 3.2 prompt-template concern.)
- ✅ **Conversation-state sub-study (4.9, done 2026-06-10)** — **fixed orders (natural vs inverse)**, NOT
  shuffle (isolates position cleanly, cheap, easy to describe); **sequential within a session, parallel only
  across**; frozen config = reasoning off, with_guidance, q-by-q, holistic, PT-CS code, k=3, 20 submissions.
  **Run on TWO models** (user 2026-06-09): qwen3.5 (RQ1 continuity) **and** glm-5.1 — because Qwen's code
  0-collapse can MASK the order effect (a 0-early/0-late answer can't reveal position). Separate store
  `conversation.jsonl` (keyed incl. order_id so natural/inverse don't collide). **Result:** order effect real
  and **stronger in GLM** (mean|nat−inv| = 0.33 **raw-score points**; **51% of (item,run) pairs** change grade
  with position) than Qwen (0.26, 36%; bases declared 2026-06-11: raw scale, run-level pairs) —
  the collapse partially masks it in Qwen, vindicating the two-model design. Shared history also lowers the
  mean slightly (clean>shared) — anchoring signal for Phase 5. **Phase-5 interpretation:** report Qwen with
  the 0-collapse caveat; GLM is the cleaner read of whether position/anchoring matters.
- ✅ **PT-CS reference** (Phase 2.1, 2026-06-08) — **kept OUT**, confirmed by data: `reference_answer` is
  100% null for PT-CS (no reference solution in the source); grounding is the rubric (`pergunta.criterios`,
  JSON `[{points,criteria}]`). No synthetic reference built (confound).
- ✅ **Context mapping** (Phase 2.6, 2026-06-08) — finalised + verified in the unified corpus: grounding =
  **rubric** for PT-CS (100% rubric, 0% ref) and RIAYN (100% rubric; also has a model solution available),
  **reference answer** for Mohler (100% ref) and SemEval (100% ref). The question stem + student answer are
  always present; only this guidance varies. Encoded in `experiments/ingest/unify.py` (`CONTEXT_MAP`) and
  printed by `make ingest`. Cross-dataset note: **SemEval dominates** raw counts (16,003 of 19,599 = 82%) →
  the experiments must **sample N per condition** (the §11 N decision), not run all items, esp. for SemEval.
- ✅ **Human-validation evidence** (Phase 2.1, 2026-06-08; **recontextualised 2026-06-10**) — of 775 PT-CS
  responses with per-criterion data, **49.3% have `cotacao` ≠ Σ`nota_parcial`** (mean adjustment 1.43 when
  adjusted) — evidence of intervention. **BUT do NOT read this as "validation was real across PT-CS"** (the
  earlier framing): over ALL 1184 responses only **32.3% are intervened**; **33.2% are exact-sum** (suspected
  unreviewed) and **34.5% have no per-criterion record** at all → **two-thirds lack review evidence**. Use the
  intervened/exact-sum/no-criteria **stratification** (see the PT-CS-gold-reliability item above), not a single
  "half were validated" claim, in the Threats section.
- ✅ **Consensus vs independent** (Phase 2.1, 2026-06-08) — **always joint/consensus**. The schema has **no
  per-teacher score columns**: `criterio_correcao` holds a single `comentario` + `nota_parcial` per criterion,
  and `resposta_submissao.cotacao` is the single final grade. **No separate per-teacher scores exist → no
  inter-rater κ / human ceiling recoverable.** Describe as two-teacher consensus only (CLAUDE.md §2).
- ✅ **EN translation produced** (Phase 2.2, 2026-06-08) — `corpus_en.parquet`, **1174 items, 1:1-aligned**
  with `corpus_ptcs.parquet` (same `item_id` → same row → same grade), for the **master's PT-vs-EN comparison
  only — OUT of the Article-2 experimental matrix (Phase 4 never touches it).** **How:** translated from the
  *anonymised* 2.1 output (never the raw export; GDPR); only **question stems (all) + short_answer/theory
  student answers** translated — **code answers, PT code-comments, rubric_json criteria, numeric grades/scales
  untouched** (verified: code identical, 99% theory changed). **Model: `deepseek-ai/DeepSeek-V4-Flash` via
  DeepInfra** (temp 0; user-provided key; anonymised data left the machine to an external provider — authorised
  by the data controller, recorded in `corpus_en_translation_meta.json`). **Still requires human validation
  before any master's use** (machine translation). (Initial gemma3:27b local run abandoned mid-way for speed.)
- 🔧 **Cost tracking** — keep the running paid-spend tally here; confirm we stay ≤ €150. **Implemented
  (Phase 0.4):** persistent ledger `data/processed/_spend.json` via `experiments/harness/cost_guard.py`
  (pre-flight estimator refuses any arm that would breach the €150 ceiling; `record()` logs real token cost
  per call). **GPT-5.1 anchor smoke test PASSED** (2026-06-07): replied "pong", 14+10 tok, €0.000108 charged
  (reasoning_effort=none accepted). **Spend updated 2026-06-11 (ledger `_spend.json`): €55.60 total** — runs.jsonl deduped €35.97 (OpenAI/gpt-5.1 **€10.24** of €150; DeepInfra open roster **€25.73** of €150); the ledger-vs-runs difference is the archived maxtok4096 reasoning arm + smoke/regrades. **€ STAMP: every euro in the paper's cost section regenerates from `phase5.cost_summary()`** (printed by `make analyse`; verified 2026-06-11 — ledger/per-provider figures above match its output; the framework table carries token ratios only, no €). **Operational finding for the paper (7.1):** the a-priori estimate (€16.7) **underestimated the real matrix cost ≈2.2×** (OpenAI 1.9×: €5.45→€10.24; DeepInfra 2.3×: €11.25→€25.73) because **real reasoning completion tokens exceeded the assumed output lengths** — the first ON arm even had to be re-run at an 8× higher token ceiling (4096→32768). Report it as a budgeting datum for practitioners, not just our estimation error. Far under both ceilings. **DeepSeek**: key added and
  authenticates, but the account returned HTTP 402 *Insufficient Balance* — needs top-up before any DeepSeek
  arm can run (harness handled it cleanly, no charge recorded). Keys via env vars / gitignored `.env`
  (loaded by `experiments/harness/env.py`), never committed.
- ⬜ **Statistical model** — paired tests for reasoning on/off; mixed-effects vs ANOVA for the factorial;
  multiple-comparison correction.
- ⛔ **5.8 emergent observation — WITHDRAWN (2026-06-15)** — the one exploratory item was "reasoning ON
  improves SemEval generalisation to NEW domains more than seen (AUROC unseen_domain rises most off→on)". This
  is **withdrawn as uninterpretable**: it rests on the seen/unseen split semantics, which **do not apply to our
  zero-shot prompted models** (splits defined relative to a supervised training set we do not have — see the
  SemEval-splits CUT item above). With the splits invalid as a novelty axis, "rises most on unseen_domain" is
  just reasoning helping on one content subset, with no generalisation meaning. **Do not promote or revive it.**
  The pre-registered, confirmatory results are unaffected (partial ranking transfer RQ6, rubric "non-transfer"
  RQ2 = PT-CS-gold artifact). After this withdrawal the 5.8 emergent-observations gate holds **no** items.
- ✅ **Percent-of-baseline readings in Results prose (Phase 7, 2026-06-15)** — the RQ1, RQ2 and RQ3 sections
  quote each effect as a **percentage of its baseline** (RQ1: dQWK / reasoning-OFF QWK per cell; RQ2: guidance
  dQWK / no-guidance QWK per dataset; RQ3: contrast dQWK / question-by-question-holistic QWK), a relative-magnitude
  reading that is **NOT in any generated table/figure** (those carry absolute dQWK + CIs). These prose numbers are
  **regenerated and auditable** via `experiments/analysis/audit_pct_baselines.py` (reuses the table generator's
  `_qwk_items`/`_boot_ci`, K=5, same SEED, so the dQWK matches `tab_rq1_reasoning`/the RQ2/RQ3 figures; % divides
  the **bootstrap-median dQWK** the prose quotes by the **point QWK baseline**). Current values: RQ1 Mohler +11%,
  SemEval +18%, RIAYN +45%, PT-CS code +41% (verified +23%), PT-CS short Qwen +28% / GLM +59% / GPT +50%, RIAYN
  GPT +32%; RQ2 Mohler +34%, SemEval +67%, RIAYN +29%, PT-CS code +2% (verified +46%); RQ3 scope −12%/−17%
  (full/verified), decomp −14%/−5%. **High % on low/depressed baselines is expected** (PT-CS code RQ1 +41% rides
  the zero-collapse-deflated OFF baseline 0.33 — consistent with the "recovery of a broken baseline" framing, not
  a separate claim). Re-run the script if any of these prose % change.
- ✅ **RQ4 reframed as cost-efficiency + new BY-TASK cost-quality figure (Phase 7, 2026-06-15)** — the old RQ4
  close ("no configuration wins, choose on cost") read as an anticlimax; replaced with two grounded, **per-task**
  conclusions (the pooled-public version was an intermediate step, superseded so prose matches the figure):
  **(i) spread** — on short-answer the 8 configs fall within ~0.07 QWK, on code they span 0.259, so short-answer
  = pick cheapest, code = worth optimising; **(ii) cost-efficiency, by task** — short-answer: cost spans 2 orders
  of magnitude (€0.02–€3.8/1000) for ~no agreement change and **reasoning does not help (slightly hurts)**, so
  cheapest-off wins (DeepSeek/Qwen off ~0.61 @ €0.02–0.04); code: effort pays, **GLM-5.1 leads (0.726 off @
  €0.36, 0.803 on @ €1.29)**, reasoning repairs Qwen's code 0-collapse (0.544→0.754), and **GPT-5.1 is dominated**
  (weakest short-answer; on code 0.787 only at €24/1000, the priciest cell, still below GLM). New **two-panel**
  single-column figure **`fig_rq4_cost`** (`fig:costquality`, QWK vs €/1000 grades, log x, panels short-answer |
  code, shared y) in `experiments/figures/phase6.py`; cost from logged `cost_eur` (NB: matplotlib pgf has no
  eurosym, so the axis label says "EUR", the caption uses €). Per-task prose numbers regenerate via
  `experiments/analysis/audit_pct_baselines.py::rq4`. **€ figures stay backend-conditional (§6.4).**
  **RECONCILED RULE (do NOT write "on for code" as a default):** the RQ4 close and the framework agree on
  **reasoning OFF by default** (cost holds on every task); reasoning earns its keep **only on code, and
  conditionally** (it repairs a collapsed baseline, or local validation shows it pays). The clean "off for
  short, on for code" was considered and **rejected** because the code reasoning gain is **not significant** for
  the discriminating models (GLM +0.077 ns, DeepSeek ns; significant only via Qwen's collapse-repair and
  GPT$|$RIAYN) and would contradict `tab_framework`. **NAMING (2026-06-15): GPT-5.1 is the "closed"/frontier
  anchor, never "paid"** (DeepInfra is paid too; the scientific contrast is open-weight vs closed).
- ✅ **Scope default = one question per call (B3, user 2026-10-15; supersedes "grade in blocks").** The
  framework had recommended grading in blocks of ~4 questions "to cut the per-call overhead", which clashed
  with RQ5/Discussion ("clean, question-by-question grading was the least biased") and confused the advisor.
  The data settle it: per question, whole-exam grading costs only **3% less** (Qwen3.5 off, 252 whole-exam
  questions, call_group-deduped; `audit_pct_baselines.rq3_cost`, and derived in `make_phase5_tables` for the
  framework row) while its ΔQWK is −0.060 (ns, both point estimates below baseline). Criterion scoring
  roughly **doubles** the cost per answer. Framework table, Fig. framework diagram, RQ3, Discussion all say
  "one question per call, holistic, clean conversation".
- ✅ **RQ1 figures plotted a different basis from the prose (fixed 2026-10-15, advisor comment p.6).** Figs.
  rq1trade/rq1 used `phase5.reasoning_contrast` dQWK (point estimate on ALL paired items, incl. the ones whose
  reasoning overflowed), while the prose/Method use the tractable (clean) items + bootstrap median (e.g.
  Qwen|RIAYN figure +0.179 vs prose +0.250). Both figures and the new paper table `tab_rq1_values` now read
  `make_phase5_tables.rq1_cells` (dQWK on tractable items; SD and token premium on all paired items, which
  is what the "16 of 20" count and the 10–925× range always used). No prose claim changed.
- ⬜ **Ethics / GDPR statement (B4)** — user 2026-10-15: deferred ("non-identifying data"; revisit before
  submission). NB: pseudonymised data is still personal data under the GDPR, and Access may ask for an
  ethics statement; the §2.1 gate still applies to publication.
- ✅ **"Framework" wording (B1, user 2026-10-15).** The advisor disliked "framework" (reads as AI prose;
  suggests software to an engineering readership). Title is now *Configuring LLM-Based Grading in Computer
  Science: An Empirical Study of Reasoning, Guidance, Scope, and Cost*; the deliverable is the
  **configuration guide** (Section "The Configuration Guide"; keyword "configuration guidelines"). Do not
  reintroduce "framework" for our deliverable (other people's software frameworks may keep the word).
- ✅ **PT-CS presentation (B2, user 2026-10-15)** — see §2.2 "Paper presentation". Generators and figures
  label it "PT-CS" (no "verified"); the strata table is still generated for audit but not in the paper.
- ✅ **Grade-inflation threat dropped from the paper (2026-10-15).** Its quantitative proxy never supported
  inflation (see the inflation item above); under the §9.2 caveat filter and B2 it no longer earns a
  sentence. The Method sentence on the signed deviation went with it.
- ✅ **Temperature-0 variation re-based (2026-10-15).** Threats said "10 to 43% of items still vary" with a
  dangling reference to the Discussion and no engine source. Recomputed by
  `audit_pct_baselines.temp0_variation` on the paper basis (with guidance, one question per call, holistic,
  PT-CS validated): **9–56% with reasoning off** (18–46% on). Prose updated.
- ✅ **Bloco C approved (user 2026-10-15): C1–C5 + C7–C10; C6 deferred.** C1 guidance on DeepSeek +
  GPT-5.1; C2 criterion decomposition on RIAYN and PT-CS (Qwen + DeepSeek); C3 whole-exam on all 88 exams
  with validated code answers (Qwen + DeepSeek); C4 conversation scaled to 80 exams at k=5 (Qwen + DeepSeek); C5 GPT-5.1 at full open-model
  coverage (k=5); C7 Mohler human ceiling; C8 SemEval cut-off sensitivity; C9 Holm + TOST; C10 regret of
  the guide vs the best configuration in hindsight. **C6 (a model released after June 2026) is NOT run**:
  the study is meant to be of its time; revisit its benefit only after C is done and report to the user.
- ✅ **Equivalence margin PRE-REGISTERED: ±0.05 QWK (user 2026-10-15), fixed BEFORE any C-arm data was
  run.** Used by every TOST in the paper (scope, decomposition, any null result the guide relies on).
  Rationale: smaller changes would not alter any recommendation and are near the binning sensitivity
  (0.033). Do not tune it after seeing the new data.
- 🔧 **Bloco C status (2026-10-15).** Harness ready: criterion decomposition allowed on RIAYN (same rubric
  text as holistic, so the contrast is clean); `item_filter: ptcs_validated` in matrix arms; whole-exam
  runner takes `--model` and `--exams validated` (88 exams); conversation scaled to 80 exams at k=5; new
  arms c1_context_roster, c2_decomposition, c5_anchor_full_off/on. Realistic cost (real per-call costs,
  filter, cache) ≈ €35 (C1 €2.5, C2 €1.4, C5 €31). **BLOCKED:** OpenAI account has no credits
  (insufficient_quota) and the DeepInfra key in .env is rejected (401 invalid_api_key) — user must top up /
  issue a new key. Run arms SEQUENTIALLY (one process at a time writes runs.jsonl and the spend ledger).
- ⚠️ **RIAYN is the DSA subset only (found 2026-10-15).** The corpus holds 149 data-structures-and-algorithms
  submissions over 25 problems (148 Java, 1 Python); the OOP subset was never ingested. Method said "OOP and
  data-structures" — corrected; Table I now shows the RIAYN-DSA published row. Rubrics list marked steps per
  accepted solution path; the gold is the sum of the steps of the student's path.
- ⬜ **C9 Holm result needs a presentation decision (pending user).** On current data, with Holm across the
  20 RQ1 combinations only Qwen|RIAYN stays significant (Qwen Mohler/SemEval/PT-CS code and GPT|RIAYN do not).
  RQ2 guidance survives Holm on all four datasets. No TOST equivalence at ±0.05 yet for scope (N=77) or
  decomposition. Re-run `bloco_c c9` after the C arms; do not change RQ1 prose until the user decides.
- ✅ **GLM-5.1 is not used in bloco C (user 2026-10-15).** Its reasoning can no longer be switched off on
  DeepInfra, so October runs would not match the June "off" condition. C1 runs on DeepSeek + GPT-5.1; C2,
  C3 and C4 on DeepSeek (with Qwen). The October GLM rows were deleted. **Do not draw any paper conclusion
  from this** (user: it is a provider matter). June GLM results stay as they are.
- ⚠️ **Spend: provider billing ≠ our ledger (found 2026-10-15) — re-base the paper's € figures.** DeepInfra's
  own billing (GET /payment/usage) for June 2026: **$83.27** (Qwen3.5 $45.53, GLM-5.1 $30.80, DeepSeek-V4-Flash
  $2.54, DeepSeek-V4-Pro $4.40), against ≈€37 in our ledger: pricing.yaml prices were below the real ones
  (real per 1M tokens: Qwen in $0.14 / out $1.00; DeepSeek-V4-Flash $0.09 / $0.18; yaml had Qwen out $0.60,
  DeepSeek $0.14 / $0.28). GPT-5.1 yaml price ($1.25 / $10) matches the public list price. **TODO before the
  paper's cost claims (€35.97 matrix total, €/1000 grades in the RQ4 figure, the €16.7 estimate story):**
  recompute from real per-token prices (or provider-billed totals) and update pricing.yaml. In October the
  provider billed requests for zai-org/GLM-5.1 as zai-org/GLM-5.3 (June billing shows GLM-5.1, so the June
  GLM data are GLM-5.1). Cost watchdog: `experiments/run/cost_watchdog.py` (reads DeepInfra billing,
  stops a queue at a cap; OpenAI read from our journal because the key lacks api.usage.read).
- ✅ **Bloco C COMPLETE (2026-10-15). Read-outs regenerate via `python -m experiments.analysis.bloco_c` (C7–C10)
  and the launcher's per-step conclusions (runs/_bloco_c_status.json); no prose-only numbers.** 0 error rows,
  0 unparsed rows in runs.jsonl for the C arms (1 unparsed DeepSeek row in conversation.jsonl). Spend today:
  DeepInfra $20.40 provider-billed (of which $18.24 GLM-5.3 before GLM was removed), OpenAI €40.20.
  Headlines (PT-CS = validated answers): **C1 guidance** helps in 11/12 model×dataset combinations (Qwen,
  DeepSeek, GPT-5.1 × Mohler/SemEval/RIAYN/PT-CS code), all 11 survive Holm; exception GPT-5.1|RIAYN −0.005.
  **C2 decomposition** never helps (RIAYN Qwen +0.029, DeepSeek −0.013; PT-CS Qwen −0.022; PT-CS DeepSeek
  −0.072 sig, survives Holm). **C3 scope** (N=295): Qwen −0.091 sig (survives Holm), DeepSeek −0.024 ns.
  **C4 conversation** (80 exams, k=5): shared history lowers grades by 0.012 for Qwen (p=.028), 0.010 for
  DeepSeek (ns) — smaller than the June 20-exam read (Qwen 0.040); order moves grades by 0.081 on average
  and now shifts the mean slightly in OPPOSITE directions per model (DeepSeek +0.013, Qwen −0.015, both
  signed-test sig) → the paper's "order is noise, not a systematic bias" must be nuanced. **C5 GPT-5.1**
  full coverage: off ranks 2nd–3rd of 4 on public data (1st on PT-CS short) — it is NOT "the weakest
  short-answer grader" (that came from 60-item subsets); reasoning helps it only on RIAYN (+0.228, survives
  Holm), Mohler +0.006 is equivalent to zero (TOST ±0.05). **C9 RQ1 with Holm (20 combos): 2 survive
  (Qwen|RIAYN, GPT|RIAYN)**; uncorrected 5. No RQ3 contrast reaches TOST equivalence (CIs too wide).
  **C7** Mohler graders agree QWK 0.491; models 0.73–0.80 vs grader A, 0.23–0.41 vs grader B. **C8** fixed
  0.5 cut is within 0.024 accuracy of the best cut for every model. **C10** guide default regret: short
  answers 0.07–0.09 QWK below the best config (which costs 8–148× more); code with GLM-5.1 off 0.000 (PT-CS)
  / 0.077 (RIAYN) below the best; DeepSeek as the code pick loses 0.08–0.13. **Decisions (user 2026-10-15):** (1) RQ1 keeps per-combination 95% CIs as the
  primary reading, the RQ1 table adds a "survives Holm" column, abstract says "in at most five of twenty
  combinations, two after correcting for multiple comparisons". (2) The June GLM-5.1 conversation data
  STAYS in RQ5: it is complete and internally valid (both arms run in June on GLM-5.1) and covers the first
  20 of the same 80 exams (seeded prefix), so RQ5 reports Qwen + DeepSeek (80 exams, k=5) and GLM-5.1
  (first 20 exams, k=3, June), stated in Method and caption. Only half-finished October GLM runs were
  deleted; never discard complete June experiments.
- ✅ **Guide default rule changed (D13, user 2026-10-15):** both tasks: reasoning off with the strongest model
  that does not collapse to zeros (GLM-5.1 here), not "the cheapest model" on short answers (C10 regret).
  **Written into the paper (2026-10-15):** guide section, new row "Choosing the model" in `tab_framework`,
  `tab_guide_regret` (Table 5: best in hindsight vs GLM-5.1 off vs the cheapest model off, DeepSeek-V4-Flash;
  default gives up 0.000–0.077 at up to 30× lower cost, the cheapest 0.073–0.131 at a further ~10× saving),
  RQ4 short-answer paragraph, Discussion, Conclusion and abstract. Engine: `bloco_c.c10` with
  `GUIDE = {"short_answer"|"code": ["glm-5.1", "cheapest"]}` ("cheapest" resolved per dataset).
- ✅ **Final audit corrections (2026-10-15, four-check review requested by the user).** (1) **PT-CS short
  answers added to the guidance contrast**: the runs existed (none vs with guidance, Qwen/DeepSeek/GPT) but
  `dim_contrasts` had left them out. Guidance is now significant in **13 of 15** combinations after Holm
  (+0.095 to +0.335); exceptions GPT|RIAYN −0.005 and DeepSeek|PT-CS short +0.112 ns (N=84). RQ2 now also
  reports consistency: SD rises in 10 of 15, by at most 0.028 (`audit_pct_baselines.rq2_consistency`).
  (2) **Costs include the conversation sub-study** (€2.76, all DeepInfra; the a-priori estimate priced it
  too): all experiments **€103.9** (OpenAI 50.4, DeepInfra 53.4); planned comparisons **€61.0** vs €16.7
  (**3.7×**; OpenAI 1.9×, DeepInfra 4.5×). (3) **K sensitivity** across all 20 baseline cells is **0.05**
  (was 0.033 on the old Qwen-only basis; `audit_pct_baselines.k_sensitivity`). (4) **Criterion scoring
  costs 1.3–3.1× holistic** per answer (DeepSeek 1.3–1.6, Qwen 2.9–3.1), not "about 2×". (5) One GLM-off
  run is unparsed, so π is "above 0.999", not 1.0. (6) DeepSeek scope CI is [−0.07, +0.03]. (7) Writing
  rule §9.2 applied: no QWK percentages anywhere (Table III "Change" column removed). (8) Fig. 1 (RQ1
  scatter) dropped from the paper as redundant with Fig. 2(a,b) and Table III; the generator still writes it.
- ✅ **Conclusion-strength review (2026-10-16).** RQ4/RQ6 re-based on common items (see §1.2 RQ6): short-answer
  spread **0.074** (not 0.04), code 0.259; reasoning on raises public short-answer agreement by 0.014–0.062
  at 3–200× cost; GLM-5.1|off is the best reasoning-off grader on BOTH tasks (0.585 short, 0.726 code), which
  strengthens D13. Guide gains a **budget ladder** (`bloco_c.regret_all`): GLM-5.1|off has the smallest
  worst-case shortfall of any reasoning-off config (0.077 vs 0.131–0.259); GLM-5.1|on is the most robust
  config overall (≤0.055) at 4.9–7.0× the default's cost; the cheapest (DeepSeek|off) gives up 0.073–0.131.
  New Results findings: Qwen3.5|off is the most reproducible grader on 4/5 datasets yet the one that
  collapses (consistency ≠ quality); the two collapsing models (Qwen, GPT off) are the two weakest code
  graders and own all significant code reasoning gains → the zero rate is the study's key diagnostic.
  Collapse is defined relative to the other candidates (16–17% vs 9% on RIAYN; 32–49% vs 13% on PT-CS).
  Human ceiling now on one basis (reasoning off, all 2273 Mohler answers): models vs each teacher 0.39–0.75
  bracket teacher–teacher 0.49. Guidance costs 1.2–1.8× per grade. Abstract leads with "the cheapest change
  was the most effective" and names zero-collapse.
- ✅ **Temperature-0 variation re-based again (2026-10-15):** with GPT-5.1 at full coverage the reasoning-off
  range is **9–60%** (was 9–56%); Threats updated (`audit_pct_baselines.temp0_variation`).
  **CORRECTED 2026-10-16 (second pass): GPT-5.1 never ran at temperature 0.** The API rejects a temperature
  for GPT-5.1, so `adapter_api` never sends one (the logged 0.0 is only the Config value) and it samples at its
  fixed default. Only the open models and Claude Sonnet 4.6 ran at temperature 0. The paper's temperature-0
  figure is the open models' range, **9–56%** with reasoning off (GPT-5.1 29–60%, reported by the audit
  separately); Method states GPT-5.1's sampling. Never write "all calls use temperature 0".
- ✅ **No run-period distinction in the paper (D12, user 2026-10-15):** no June/October, no "extensions", no
  reproduction-check sentence, no GLM-drift sentence; costs reported for all experiments together.
- ✅ **Pedro's review of the Access draft (2026-10-16, 51 PDF comments) — implemented (commits 9257d38,
  cae86c9) and given a SECOND PASS (2026-10-16 evening: all 51 comments checked, numbers re-verified against
  the engines, corrections listed in section 5 of the state file).** The state file is in git history
  (`git show dcc1c22:article/review/REVISAO_PR_ESTADO.md`; removed in the 2026-10-18 cleanup). Final results: GPT-5.1 with partial
  credit +0.076/+0.106 on code (Holm), zeros 32->20% (softens its collapse, not Qwen's); RQ3 now on three
  models (whole exam never helps; criterion helps only GPT on RIAYN); all experiments EUR 158.7 at standard rates.
  **GUIDE = A MODEL-INDEPENDENT CONFIGURATION (Pedro 2026-10-16, evening; supersedes "the recipe = DeepSeek-V4-Flash"):**
  rubric or reference answer + ask for partial credit + reasoning off + one question per call + one holistic
  score + clean conversation; NO model in the guide, no pre-tests, no conditions. Validated by
  `experiments/analysis/guide_eval.py` on EVERY configuration graded (incl. no guidance, whole exam, criterion,
  justification, shared conversation): **Test 1** (within each model, paired bootstrap 95%, no correction):
  without reasoning 1 of 56 alternatives significantly better (Sonnet strict, PT-CS short, +0.043), 22 no
  difference, 33 worse; reasoning on better in 7 of 17 (5 Qwen), never worse, less consistent in 14/17, 2.6-179x
  cost -> Table 4 (tab_framework, written by guide_eval). **Test 2** (across models, items all no-reasoning
  configs graded): with the best-suited model the guide is the best config on Mohler (GPT-5.1 0.653) and PT-CS
  code (DeepSeek 0.674), within 0.002/0.014/0.043 on SemEval/RIAYN/PT-CS short (<=0.053 on the reasoning
  samples); four models grade code at 0.65-0.76 under it, Qwen 0.50/0.55; with the cheapest model nothing
  cheaper agrees better (one 0.001 tie on SemEval) -> Fig. 8 (phase6.fig_guide_validation). Old Table 5
  (tab_guide_use) removed. Decisions (user):
  **(P1)** a grading-instruction experiment (prompt engineering, "simple and cheap") and a guide that is ONE
  simple recipe: no budget ladder, no "confirm locally", no "check collapse first", no leave-one-out test;
  **(P2)** RQ1 keeps every item: a reasoning run that overflowed takes the same model's reasoning-off grade
  (`phase5.apply_reasoning_fallback`, applied in `load_main`; SD, zero rates and temperature-0 variation use
  the model's own grades only) → RQ1 = **6 of 20 significant, 3 after Holm** (Qwen Mohler, Qwen RIAYN, GPT
  RIAYN); RQ1 and RQ4 now share the same items; **(P3)** GPT-5.1 joins RQ3; a second closed model (Claude
  Sonnet 4.6) as a ~$20 subset; GLM-5.1 off must be found elsewhere (DeepInfra retired it: `zai-org/GLM-5.1`
  is answered by GLM-5.3, which reasons even with thinking off; OpenRouter still serves GLM-5.1 from 13
  providers with `reasoning.mandatory=false` → needs an OpenRouter key); **(P4)** RQ6 (ranking transfer) and
  the whole deployment/transfer angle are REMOVED; RQ6 is now the grading instruction; PT-CS = our new dataset
  of complete exams (the only one for scope/conversation); **(P5)** PT-CS is described per question, one
  sentence on the selection (teachers changed the platform's suggested score), no correction-feature detail;
  **(P6)** NEW, at the end: a "guide in use" evaluation (`experiments/analysis/guide_eval.py`) comparing the
  recipe with every configuration on QWK, SD, zeros and cost.
  **Instruction experiment** (`prompts_instruction.yaml`, store `instruction.jsonl`, engine
  `experiments/analysis/instruction.py`; standard cells keep their hashes): partial credit raises
  DeepSeek-V4-Flash on code by 0.06–0.07 (Holm-significant) and is equivalent on short answers; it does NOT
  repair Qwen3.5's zero-collapse (Qwen's justifications name what the student got right and still give 0);
  the justification variant was unstable and dropped. GPT-5.1 runs (i4 arms, Batch API) wait for OpenAI
  credit; Claude Sonnet 4.6 runs via the Message Batches API with structured output enforcing the JSON-only
  score (`experiments/run/batch_runner.py`; Mohler capped at 800). Harness: `NoCredits` stops a provider
  without storing rows (OpenAI 429 credit_balance_exhausted had been retried for 15 min per call).
- ✅ **Pedro's second review (2026-10-18, 48 PDF comments on the version 3 PDF).** Its state file (every
  comment, its status, decisions D1–D7 with options and recommendations) is in git history:
  `git show dcc1c22:article/review/REVISAO_PR2_ESTADO.md` (removed in the 2026-10-18 cleanup). Done and
  committed (dcc1c22). Facts established in this round, do not regress them:
  - **Model choice (#14)**: "among the strongest open models" was false for Qwen3.5-35B-A3B (mid-table:
    Artificial Analysis 6 Jun 2026 and Arena 9 Jun 2026 snapshots). GLM-5.1 was the #1 open model on Arena text
    and code, and 4th on Artificial Analysis. DeepSeek-V4-Flash was in the top 15 open models on both.
    **Paper text (Pedro, 2026-10-18): the choice is justified by PRIOR GRADING STUDIES, in ONE short sentence**
    with citations per family. Pedro rejected the long version that named every author ("almost a literature
    review"). The evidence behind the citations:
    Four of the five families have a grading record:
    - Jukiewicz: 18 models;
    - Cipriano et al.: Claude 3.5 Sonnet closest to the human graders;
    - Moazzez et al.: Claude the most consistent;
    - Li et al.: GPT-4o first, DeepSeek-V3 second;
    - Aminah et al.: DeepSeek with the lowest MAE on Mohler;
    - Jiang & Fowler: Qwen 2.5 72B about as accurate as GPT-4o;
    - Havare et al.: a 7B Qwen coder matched Codestral 22B;
    - Cisneros-Gonzalez et al.: a dataset graded by DeepSeek and Qwen;
    - Jayarao: the Qwen thinking switch.
    GLM-5.1 has NO grading record. It is justified only as the #1 open model on the Arena code leaderboard
    (31 May 2026), because the study grades code. Never claim a grading record for GLM. Every claim was checked
    against the study's abstract.
  - **Related Work (#7–#9)**: rubric effects were already studied (Nugroho 2025, 10 LLMs; Yoshida 2025;
    Pathak), and lenient vs strict prompts too (Venkatraman 2026, 2 LLMs). Claim only the combination (one
    protocol, 5 models, 4 datasets, 2 domains, k=5, cost), never being first. Pathak's κ: 0.41–0.43 without
    a rubric, 0.60–0.65 with the best question-specific rubric.
  - **Conversation sub-study exams**: 80 drawn at random (seed 20260609) from the 181 PT-CS exams with code
    answers. Only 34 of them are among the 97 exams of the 379 graded answers, so never describe them as a
    subset of those.
  - **k / K**: k = repetitions; the QWK scale is "six ordered levels". The symbol K was removed from the paper.
  - **Decisions taken by Pedro (2026-10-18, evening), all implemented:**
    - **D1:** the grading instruction is a FOLLOW-UP experiment (not RQ6). There are 5 RQs, and
      "F. Follow-Up: Asking for Partial Credit" is motivated by the zero-collapse.
    - **D2: NO mention anywhere of the platform suggesting grades or of how the 379 PT-CS answers were
      selected.** This is the author's decision and supersedes the B2 "kept in Threats" rule in §2.2. Do not
      re-add it. The conversation exams are still described as drawn from the 181 collection exams with code.
    - **D3:** the body says the open models ran "via DeepInfra". A footnote states the one exception
      (GLM-5.1 partial credit via OpenRouter/Z.ai) and that we treat both providers as one backend
      (strict 0.726 on RIAYN on both). Never write that nothing ran elsewhere.
    - **D4:** the guide section is intro (why, measures, rule) -> A. the guide (Table 4 =
      `make_phase5_tables.write_guide_table`) -> B. the two tests -> C. results. Test 1 is a figure
      (`phase6.fig_guide_test1`, Fig. 8) and Test 2 is Fig. 9.
    - **D5:** validation framing = "33 significantly better, 22 no significant difference, 1 worse" of 56
      alternatives without reasoning. Pedro's sentence goes in the abstract and Intro: "against every other
      configuration of the same model, and against the best configuration of any model, at what cost".
    - **D7:** RQ4 uses all five sets (`audit_pct_baselines.rq4`).
    - Guidance range is **0.095–0.335** (the old "0.10–0.34" was double rounding). Partial-credit cost on code
      is **5–9%**.
    - The marked-PDF tools (latexdiff steps, flatten, post-processing) are in git history:
      `git show dcc1c22:article/review/tools/README.md`.
  - **AI-use statement (IEEE policy, Acknowledgment section, 2026-10-18): final wording is Pedro's own;
    do not change it without asking him.** "During the preparation of this work, the authors used Claude
    Opus 5 (Anthropic) to help write the scripts that run the experiments and process the data for the tables
    and figures, and to help revise the text. The research questions, study design, interpretation of the
    results, discussion, and conclusions are the authors' own; the authors checked all results and take full
    responsibility for the content."
- ✅ **Pedro's third review (2026-10-18, 18 PDF comments on the marked version 6): implemented and VALIDATED
  by Pedro.** The final PDF is `~/Desktop/artigo_2_access_final_2026-10-18.pdf` (17 pages). Cleanup done at his
  request:
  - the intermediate PDFs went to the Trash;
  - `article/review/` was deleted (it is in git history at dcc1c22);
  - six stale figures and `tab_guide_regret.tex` were deleted;
  - the unused booktabs package was removed;
  - the build files and the session's temporary files were removed.
  NOT committed: Pedro commits and pushes only when he says so. Facts and decisions, do not regress them:
  - **Validation as percentages**: the abstract and the Conclusion give Test 1 as shares of the 56 alternatives
    without reasoning (59% better, 39% no significant difference, 2% worse; counts 33, 22, 1). The guide
    section keeps the counts, with the percentages in parentheses.
  - **Introduction**: the zero-collapse is named as the reason for the follow-up experiment. Pedro asked for this,
    and it is the one result the Introduction previews. The five RQs "were set before the experiments", which
    is why the follow-up is reported apart from them.
  - **Providers**: the GLM-5.1/OpenRouter footnote was removed at Pedro's request. The body said the open models
    ran "mainly via the DeepInfra" API. Pedro asked (2026-10-19) to remove "mainly"; the sentence now says they ran
    via DeepInfra "and GLM-5.1 also via OpenRouter", which keeps it true (raised with him as a doubt). Never write
    that every open-model run used DeepInfra.
  - **Model choice**: the cited studies found Claude, GPT, DeepSeek and Qwen models "among the best graders
    tested". GPT cites Li and Seßler, because Jukiewicz's abstract names no best model.
  - **Fig. 8 is the guide's prompt**, verbatim from `experiments/configs/prompts.yaml` and
    `prompts_instruction.yaml` (partial-credit grounding, holistic output). Keep it in sync if the templates
    change.
  - **Float placement**: superseded the same evening by the binding float rule in §9 (every float after its
    first reference, checked after every build). The paper is 17 pages, and the last page holds only the
    last biography.
  - The abstract is at the 250-word limit.
  - Future work is limited to three directions: zero-collapse; other languages, institutions and students;
    and few-shot examples and fine-tuning.
- 🔧 **Validation of the guide (Pedro, 2026-10-18; called "additional verification" until his fourth review of
  2026-10-19): protocol fixed here BEFORE any call.** An independent pre-submission review (in `~/Downloads`,
  "Parecer de revisão IEEE Access") said the guide was validated on the data that built it. Pedro decided to test
  it on data that played no part in building it. **Naming (Pedro, 2026-10-19): "validation" is used ONLY for these
  two datasets; the comparisons on the study's own data are the "tests"; never "verification".** The code keeps
  the names `verification.py`, `verification.jsonl` and `corpus_verification.parquet`. The budget is internal and
  is never given as a reason in the manuscript.
  - **Datasets**, in their own corpus (`corpus_verification.parquet`, `experiments/ingest/ingest_verification.py`)
    and store (`runs/verification.jsonl`), never mixed with the study:
    - SAF (Filighera et al., ACL 2022, CC BY 4.0): English short answers on communication networks, consensus of
      two trained annotators, partial credit, a reference answer per question. A seeded random 300 of 2,981
      answers (all 31 questions pooled; splits mean nothing to prompted models); reasoning on the first 150.
    - HARMOGEN-R v2.0 (Mendonça et al., Zenodo 10.5281/zenodo.17284944, CC BY 4.0): C++ code answers of a
      data-structures course, in Portuguese; all 129 non-empty code answers (3 questions); the gold is the
      mean of four instructors, independent and blind, with their own rubric (points per criterion).
  - **Configurations:** the guide (guidance, partial credit, reasoning off, one question per call, holistic,
    clean conversation) and alternatives that change ONE setting: no guidance; the strict instruction;
    reasoning on (with partial credit); and, on code, a score per criterion (with partial credit). Scope and
    conversation state cannot be tested (no complete exams). Arms `v_*` in `matrix.yaml`.
  - **Models:** Qwen3.5-35B-A3B and DeepSeek-V4-Flash (DeepInfra), GLM-5.1 (OpenRouter), GPT-5.1 (OpenAI Batch
    API), Claude Sonnet 4.6 (Anthropic Message Batches; reasoning off only, as in the study). k = 3.
  - **Statistics:** QWK on the six levels of the mean of the k grades, as in the study. Δ = alternative − guide
    on the same answers; paired bootstrap over answers, 10,000 resamples, 95% CI, no correction (as Test 1).
  - **Verification criterion, fixed now:** the guide passes on a dataset if, for every model, no alternative
    without reasoning agrees with the teachers significantly better than the guide. Reasoning on is reported
    with its cost, because the guide gives it up on purpose. Also reported: the guide with each model against
    the best configuration on that dataset.
  - **Budget (internal):** ceiling €50 for everything, estimate €33 from the rendered prompts with batch
    discounts (DeepInfra 6.5, OpenRouter 9.9, OpenAI 9.1, Anthropic 7.6). Stop if spend passes €45.
  - **Amendment after the smoke test, before the main runs (2026-10-18):** Claude Sonnet 4.6 does not run the
    criterion alternative. Its adapter enforces a score-only JSON, and in the study it graded holistically only.
    The criterion alternative therefore runs on four models.
  - **Second amendment (2026-10-18, 23:20), before any GLM result was compared:** GLM-5.1 runs on HARMOGEN-R
    code only, in its own arms (`v_harm_glm`, `v_harm_criterion_glm`, `v_harm_reasoning_glm`) at concurrency 3.
    OpenRouter throttled it to about 3 requests per minute at concurrency 16 (180 calls in 70 minutes), which put
    the full design at more than a day. In the study, GLM-5.1's partial-credit runs were code-only too. The 180
    GLM rows already stored for SAF (no guidance only, no guide rows) are not analysed.
    **Withdrawn on 2026-10-19:** Pedro added OpenRouter credit, and GLM-5.1 runs every configuration on SAF too
    (arms `v_saf_glm`, `v_saf_reasoning_glm`; the 200 early rows are the same cells and are kept).
  - **Run notes (all runs complete, 2026-10-19):** every cell has k = 3 and the store has no error rows.
    - 84 DeepInfra calls (reasoning on, code) timed out at the 10-minute read limit; all were re-graded with
      `regrade_errors --store verification.jsonl --corpus corpus_verification.parquet` (now generic: store, corpus,
      workers, and the instruction in the rebuilt config), the last 27 with `GRADER_HTTP_TIMEOUT=2400`.
    - OpenRouter ran out of credit once (GLM-5.1 code reasoning at 350 of 387); Pedro topped it up and the rest ran.
      GLM-5.1 on SAF ran into a temporary store while the re-grade rewrote the main one, then was merged (backups
      in `data/processed/_archive/`).
    - 9 GLM-5.1 code reasoning runs returned no grade (4 at the output limit, 5 malformed) and take the guide's
      grade (Method: "A reasoning run that returned no grade takes the guide's grade"); 5 GLM-5.1 code runs without
      reasoning are malformed ("!!!" output from the provider) and are left out.
    - Logged spend EUR 41.5 at list prices (OpenRouter 16.3, OpenAI 12.9, DeepInfra 6.3, Anthropic 6.0), under the
      EUR 45 stop.
  - ✅ **Result (final, 2026-10-19, `python -m experiments.analysis.verification`):**
    - SAF: criterion met with all five models (10 comparisons: 0 better, 3 no difference, 7 worse). Guide QWK
      0.62-0.73; GLM-5.1's guide (0.726) is the best configuration without reasoning on SAF. No guidance -0.18 to
      -0.30; strict instruction worse for GLM-5.1 (-0.055) and Claude (-0.049), within 0.03 for the other three.
    - HARMOGEN-R: criterion met with four of five; for DeepSeek-V4-Flash, criterion scoring agreed better (+0.088,
      CI from +0.008). GLM-5.1 0.901 and GPT-5.1 0.884 (instructors agree with each other at 0.87-0.93; within
      0.017 and 0.034 of the best configuration, GLM-5.1 criterion 0.918); Claude 0.798. Qwen3.5 and
      DeepSeek-V4-Flash collapsed under the guide (40% and 36% zeros against 7% for the instructors).
    - Reasoning on raised agreement in 6 of 8 comparisons, never lowered it: code, all significant, +0.032 GLM,
      +0.058 GPT, +0.156 DeepSeek, +0.247 Qwen (zeros 36->20% and 40->16%), at 3.5-26x the cost; SAF +0.096 Qwen
      and +0.110 DeepSeek (significant), GPT +0.051 and GLM +0.023 (not significant), at 3.5-55x.
    - Paper: Method "Configuration Guide Validation", guide section D "Guide Validation" with Fig. 10
      (`phase6.fig_guide_validation`, drawn like the tests' Fig. 9; Table 5 left the paper on 2026-10-19 and its
      values are in the supplementary material), abstract and Conclusion. **Pedro (2026-10-19) rejected checking a model's zero rate before using it on code: the guide
      stays without pre-tests.**
- ✅ **Independent pre-submission review (2026-10-18; "Parecer de revisão IEEE Access" in `~/Downloads`): Pedro's
  decisions, validated by him with version 9 on 2026-10-19.** Verdict of the review: "Reject, updates required" (Access's
  major revision); every factual claim it made about the paper was checked and found correct.
  - **Statistics, only what is standard practice (Pedro):** a survey of 16 comparable papers read in full (12 at or
    above Access level: AAAI, EMNLP Findings, LAK, ICER, AIED, IJAIED, C&E:AI, Bioinformatics, Neural Networks, C&E
    Open) found no cluster-aware inference on agreement and no equivalence margins; the best practice is CIs, tests,
    Holm, and repeated runs. So the paper now has: 10,000 bootstrap resamples (`make_phase5_tables.NB`, one
    vectorised engine `_boot_dist`/`_point` shared by bloco_c, guide_eval, instruction, verification), point
    estimates everywhere (no bootstrap medians; this removed the "discrepancies" the review found between Table 3
    and RQ4), the p-value method and the half-to-even rounding stated in Method, Table 3 marking significant SD
    changes in bold ("17 of 20, significantly in 10"), and one sentence that all 12 public-set reasoning changes
    were positive. NOT done (beyond practice): cluster bootstrap by question, single-run QWK, discretisation
    sensitivity of differences, meta-analysis, MAE in %, exam totals, fallback sensitivity. Their zero-cost
    results are kept for a response letter (cluster: RQ1 5/20, 2 after Holm; guidance 11/15; Test 1 with the
    margin 25 better / 10 equivalent / 1 worse / 20 inconclusive; single-run dQWK -0.007 on average).
  - **Numbers that moved with the engine:** guidance 13 of 15 significant, 12 after Holm (GPT-5.1 PT-CS short
    loses it), 0.095 to 0.336; Test 1 32 better / 23 no difference / 1 worse (57/41/2%); RQ1 still 6 of 20, 3
    after Holm (Qwen SemEval and PT-CS short intervals start at +0.002).
  - **Text:** Qwen3.5-35B-A3B named in full, size as an alternative explanation (Jayarao measured thinking on
    0.6B-4B Qwen3); zero-collapse framed as a specific form of severity (RIAYN's leniency, Venkatraman, Sapkota &
    Murshed 2026), no "not described in the literature"; the Introduction no longer claims "the first" and cites
    Yoshida (Findings EMNLP 2025); "validated" kept only for the additional verification; the guide is said to be
    the baseline plus the partial-credit request; Test 2 also with the model fixed in advance; RQ5 noise baseline
    (`audit_pct_baselines.rq5_noise`) and Wang et al. 2024 on position bias; contamination (Sainz 2023) and prompt
    language in Threats; Okabe-Ito palette in the figures; data and code availability statement (Pedro: the code is
    available on request; no public release); supplementary material (`experiments/analysis/supplementary.py` ->
    `article/supplementary.tex`); bib fixed (no "Journal Abbreviation", arXiv ids, volumes and pages).
  - **AI statement:** Pedro's text, with one change at his request (2026-10-19): "to help revise the text of all
    sections".
  - **Abstract (250 words):** rewritten with fewer numbers and without "at what cost"; Test 1 is now "only one of 56
    alternatives without reasoning agreed better" (no percentages; the Conclusion keeps 57/41/2%), and it ends
    with the additional verification. The ethics statement is the `\tfootnote` (first-page footnote) in main.tex.
  - **Floats:** Fig. 6 after its paragraph; in the guide section the Test 1 figure is defined at the top of "How
    the Guide Was Tested" ([!b], it takes the bottom of that page) and the Fig. 8 reference moved to the end of
    its paragraph. 19 pages, 0 checker errors. **Marked PDF against version 6 = commit dcc1c22 (Pedro,
    2026-10-19): the marks go against the last version he ANNOTATED (`..._revisto6_alteracoes_2026-10-18.pdf`,
    built at 18:25 and committed as dcc1c22 at 18:26), not against later versions he only validated (7fae099).**
    Built with latexdiff (changed tables shown whole; the new ethics footnote marked by hand); PDFs on the Desktop as `artigo_2_access_revisto8[_alteracoes]_2026-10-19.pdf` (version 8, after revisto7
    of 18 October; the early-morning `revisto5_2026-10-19` PDFs went to the Trash) and
    `artigo_2_access_suplementar_2026-10-19.pdf`. Method: at most 0.6% unparseable outputs per configuration
    without reasoning, across all experiments (worst: GLM-5.1 on HARMOGEN-R, 2 of 387). Not committed (Pedro commits when he says so).
- ✅ **Pedro's fourth review (2026-10-19, 21 comments on `artigo_2_access_revisto8_alteracoes_2026-10-19.pdf`):
  implemented in version 9 and VALIDATED by Pedro the same day ("parece-me tudo ok"); the three doubts put to him
  ("and GLM-5.1 also via OpenRouter", the reading of his comment at the start of "Test Results", Table 5 moved to the
  supplementary material) stand as implemented.** His instruction for this round: say what will change, and
  where he signals that a text is unclear, explain what it meant and show the new text so he can check it.
  - **Naming:** "validation" only for SAF and HARMOGEN-R (see the validation entry above); "tested" for Tests 1
    and 2. Section VI "presents, tests, and validates" the guide.
  - **Figures:** the tests (Fig. 9, `phase6.fig_guide_tests`) and the validation (Fig. 10,
    `phase6.fig_guide_validation`) share one design: (a) per alternative, the share of comparisons in which the
    guide agreed significantly better / no difference / the alternative better, with counts and the relative
    cost; (b) the guide's QWK with each model against the best configuration without reasoning and the range of
    all of them (validation: plus the HARMOGEN-R instructors' band). They replaced the Test 1 and Test 2 figures
    and Table 5. The supplementary material gained a Test 2 table.
  - **Table 1** has no footnotes: models are tick columns; the footnotes only repeated the paragraph above.
  - **Abstract (250 words):** "helped in only one of six"; "From these results we built a model-independent
    configuration guide: ..."; Test 1 from the guide's side ("agreed significantly better than 32 of 56 ..., and
    worse than one"); the last sentence states the validation result.
  - **Text:** Introduction (tests vs validation paragraph; the follow-up also asks whether partial credit repairs
    the zero-collapse; contribution 2 covers every configuration choice); Method (decomposition: the grade is the
    model's total, not the sum of its criterion scores, because some rubrics describe alternative solutions);
    RQ1 ("the 95% interval starts at +0.002, so those two gains are only barely significant"); guide section C
    opens by contrasting the tests with the validation, D opens with the principle of the validation; "agreed
    better" became "agreed significantly better" wherever the claim is about significance.
  - **Ethics footnote:** Pedro asked whether it suffices for Access. Answer given: it meets PSPB 8.1.1.E (an
    explanation instead of an approval, plus why no further consent); Iscte does not review studies after the
    fact; a written authorisation from the course direction is optional and would add one clause. Footnote
    unchanged pending his decision.
  - **Final (2026-10-19):** `~/Desktop/artigo_2_access_final_2026-10-19.pdf` (19 pages, 0 checker errors, abstract
    250 words) and `~/Desktop/artigo_2_access_suplementar_final_2026-10-19.pdf` (9 pages). Every intermediate and
    annotated PDF went to the Trash, with the handoff file, the verification run logs and the two verification
    store backups; nothing committed (Pedro commits when he says so).
  - **Supplementary material, checked against every promise of the paper** (Method: "every prompt template, the
    models' identifiers and prices, the unparseable outputs per model, and the values behind every figure"; Data
    Availability: "the prompt templates and the models' settings"): prompts; models with identifiers, providers,
    reasoning switches, prices, calls and the sampling settings (temperature 0, GPT-5.1 at its default, output
    caps 4,096 / 32,768); unparseable outputs; and one table per figure, each naming it: Fig. 1 is Table 3 of the
    paper; Figs. 2 and 3 (QWK before and after); Fig. 4 (`phase6.rq4_points`); Fig. 5
    (`phase6.conversation_effects`, now 10,000 resamples like everything else); Fig. 6 (QWK and zeros per
    instruction); Fig. 9 (Test 1 and Test 2); Fig. 10 (validation, with zeros and the instructors' agreement). The
    figures and the supplement read the same helpers, so their numbers cannot drift apart. Its Table 1 had the
    DeepSeek identifier printed over the Provider column and two tables ran past the margin: all tables are now
    footnotesize with ragged-right wrapping columns; checked for overlapping words and margins page by page.
- **Ethics statement facts (Pedro, 2026-10-18):** PT-CS comes from exams of the UpSkill professional
  requalification course at Iscte, graded on the platform for real, with the answers reused later. The
  platform's terms said answers could be used for research; students knew it was an academic platform and that
  answers were sent to external services. Pedro does not know what the June note "treatment is Iscte-approved"
  referred to, so it must not be cited. Iscte does not approve studies submitted after the fact, so the paper
  gives the explanation IEEE allows (PSPB §8.1.1.E) instead of an approval, and never claims an exemption.

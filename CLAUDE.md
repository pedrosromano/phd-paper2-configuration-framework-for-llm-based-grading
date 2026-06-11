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
- **RQ6 (transfer — PARTIAL, demonstrated at reduced N).** Does the configuration guidance found on public
  datasets **transfer** to a real Portuguese deployment context (PT-CS-verified, the curated intervened
  stratum, §2.3/§11)? **Rewritten (2026-06-11; supersedes both the "illustrative" and the "ranking-inversion"
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
3. **Ground-truth honesty — PT-CS gold has LIMITED, HETEROGENEOUS reliability (revised 2026-06-10, do NOT
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
| **PT-CS** (GradeGenie export) | code (Java) + theory | PT | ~738 code / ~437 theory | final per-question grade (`cotacao`), normalised by `pergunta.cotacao` | rubric JSON; **no reference solution**; gold is **mixed-provenance, limited/uneven reliability — see §2.3** (where intervened: consensus correction of AI-seeded suggestions); stratified → **PT-CS-verified**. **Primary code; transfer (verified stratum)** |
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
**Paradigm (2026-06-08): the 32 GB ceiling is NOT an eligibility criterion.** Treatment is Iscte-approved and
we have an inference API (**DeepInfra**) for large models. Select by scientific relevance; **infrastructure
(local vs DeepInfra) is a per-model downstream note, never an upstream filter.** Full fresh survey + selection
rationale: `experiments/model_roster.md`. This supersedes the inherited/stale roster benchmarked in Phase 0.3.
- **RQ1 within-family reasoning toggle (priority):** **Qwen3.5** (`enable_thinking`; primary, Apache-2.0,
  continuity with Jayarao), **DeepSeek-V4-Flash** (`enable_thinking`; cheap 284B/13B SOTA), **GLM-5.1** (hybrid;
  strongest open coder 2026 — confirm a clean OFF at 3.4). Each graded reasoning **OFF vs ON** — three open
  vendors isolate reasoning from vendor.
- **Paid frontier anchor (closed, exactly one):** **GPT-5.1** (`reasoning_effort` none/high; €150 ceiling).
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
- **Classification (SemEval labels):** accuracy, macro-F1 (2/3/5-way).
- **Consistency:** SD/variance across k, ICC. (Needs no ground truth — a clean axis regardless of the
  reference; PT-CS gold reliability is limited/uneven — see §2.3 — but consistency does not depend on it.)
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
  is no longer an eligibility criterion** (Iscte-approved; DeepInfra API for large models). **Selected by
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
  PT-CS gold is mixed-provenance, limited reliability (§2.3). Stratified by intervention evidence (`cotacao`
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
- ✅ **SemEval score→label + splits** (Phase 5 review, user 2026-06-10) — the model emits a continuous 0–1
  score; SemEval gold is a **binary 2-way label** (correct/incorrect; gold_score 0/1). Map with a **fixed
  threshold 0.5** on the normalised score — **NOT data-tuned** (would be circular). Report accuracy + macro-F1
  **per split separately**: seen / unseen_domain / unseen_q / unseen_ans (distinct generalisations; never
  grouped). **Also** report threshold-free MAE/Spearman of the continuous score vs the 0/1 gold. (3/5-way
  labels unused — model wasn't asked for them.)
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
- ✅ **5.8 emergent observations (Phase 5 close, 2026-06-10)** — the gate (log unexpected patterns, promote
  only with sign-off, label exploratory/post-hoc) holds **one** item: **reasoning ON improves SemEval
  generalisation to NEW domains more than seen** (AUROC unseen_domain rises most with reasoning) — exploratory,
  not pre-registered. **Verified 2026-06-11 under the corrected with-guidance-only filter** (the original
  semeval_splits pooled Qwen's no-guidance rows — fixed): the pattern HOLDS across all 4 models — unseen_domain
  AUROC rises off→on (+0.013…+0.039) while seen/unseen_q fall for the open models. **NOT emergent (these were
  pre-registered RQs → confirmatory):** the partial ranking transfer (RQ6, corrected 2026-06-11) and the rubric
  "non-transfer" (RQ2, now resolved as a PT-CS-gold artifact). The `unseen_ans` ON split (N 27–30) is noise —
  not interpreted.

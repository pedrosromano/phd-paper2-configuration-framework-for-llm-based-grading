# SLR foundation (Phase 1.1) — extracted from Article 1

> **What this is.** A structured distillation of **Article 1** (the published PRISMA SLR,
> *"Automated Essay Grading in Education: A Systematic Literature Review"*) to serve as the
> **foundation for everything ≤ July 2025**. Source: `slr_source/bare_jrnl_new_sample4.tex`
> (790 lines, 665 bib entries). Per CLAUDE.md §10 / PHASES 1.1 we **do not re-search the
> ≤ Jul-2025 window** — it is covered here. The post-cutoff window (Jul 2025 →) is what the
> library merge (Phase 1.2) and full-text subset (1.4) must cover.
>
> Citation keys below are the SLR's own `references.bib` keys (reusable in Article 2).
> Published numbers are **different-model / different-protocol CONTEXT**, never our success
> criterion (CLAUDE.md §6.3).

---

## 1. Field map (the SLR's chronological + cross-cutting structure)

The SLR organises the field into **five eras** plus a cross-cutting synthesis. This is the
spine for the Article 2 Related Work narrative (Phase 1.6), to be **compressed to the ~2-page
cap** and re-pointed at the configuration-framework angle.

| Era | Window | What defined it |
|---|---|---|
| **Foundations** | 2003–2016 | Feature-engineered AES/ASAG (e-rater/Criterion), OCR+LSA for handwriting, **prompt-transfer problem** emerges, classical transfer to cut per-question labels, early question-independent code grading. |
| **AES evolution** | 2016–2022 | Neural encoders (LSTM, **BERT**), domain-adaptive pretraining, standardised QWK on **ASAP/ASAP-SAS**, first **process-efficiency** work (clustering, "shared grading", action-reduction). |
| **Early LLM transition** | 2022–2023 | First LLM graders; shift from "how accurate" to **trust / explainability / error-type effects** (FP vs FN); entailment framings on SciEntsBank. |
| **Tool-augmented & multimodal** | 2024 | End-to-end **OCR → NLP/LLM → grade/feedback** pipelines, LMS integration, and first **operational metrics** (time, cost, tokens, usability). |
| **Consolidation & trust** | 2025 | **Local/structured** grading ("grading events", LoRA local), **benchmarks** exposing limits (PBLBench), **cross-lingual** evidence (Twi), rubric-based **code** grading with partial credit, fine-tuning as enabler. |

**Cross-cutting themes** (recur across eras): (a) human agreement (QWK/κ/ICC/Kendall's W);
(b) **human-in-the-loop as the deployment-ready win** (64–85% effort/action reductions *with*
review, not full automation); (c) **multimodality raises evaluation complexity** (presentations
QWK 0.82 in isolation; multimodal PBL only 59% ranking acc); (d) **ethics/fairness/trust**
(black-box concern, adversarial gameability, student/teacher acceptance).

---

## 2. Metric framework (the SLR's primer → what Article 2 adopts)

The SLR defines **six metric families** (its Table "metrics-primer"). They map almost 1:1 onto
CLAUDE.md §6.2, which is a useful confirmation that our metric plan is grounded in the prior
synthesis. Directional cues in brackets.

| Family | Metrics | Article 2 use (CLAUDE.md §6.2) |
|---|---|---|
| **Agreement** [↑] | QWK, weighted κ, ICC, Kendall's W, Pearson r | **QWK** (binned for continuous PT-CS — §11), Cohen's κ, Spearman/Pearson r |
| **Error (regression)** [↓ MAE/RMSE; ↑ R²/within-±1] | MAE, RMSE, MSE, R², within-±1 | **MAE, RMSE** on normalised 0–1 |
| **Classification** [↑] | accuracy, balanced acc, P/R/F1 (macro/weighted), TPR | **accuracy, macro-F1** for SemEval 2/3/5-way |
| **Ranking/consistency** [↑ rank; ↓ nSD/drift] | ranking acc, **nSD**, inter/intra-rater, temporal **drift**, **π extractable-rate** | **SD/variance across k, ICC**; **π extractable-rate**; (no human ceiling for PT-CS — consensus, §2) |
| **Robustness** [↓ harmful] | FP/FN profiles, adversarial sensitivity, boundary behaviour | threats / leniency framing; adversarial noted as threat |
| **Operational** [↓ time/cost; ↑ throughput] | time/throughput, action reduction, **API calls/tokens/cost**, latency, usability | **tokens; € (paid) / wall-clock (local)**; latency; throughput; reasoning **5–10× premium** |

Canonical definitions present in the SLR (reuse, don't re-derive): **QWK** eq. with quadratic
weights `w_ij=(i-j)²/(K-1)²` (Cohen 1968); **MAE** = mean |y−ŷ|; **P/R/F1** (van Rijsbergen);
**accuracy**. The SLR's headline epistemic point — *"the same 'high performance' can mean high
QWK vs low MAE vs high accuracy"* — directly motivates our **multi-metric, per-dataset, never-
pooled** reporting.

---

## 3. Published performance on / near OUR datasets (CONTEXT for Phase 1.5)

Extracted from the SLR's comparative table and prose. **These are external reference points
produced under different models/prompts/protocols (mostly supervised 2019–2025 or minimally-
prompted LLMs) — they situate our results; they are NOT the bar to beat (CLAUDE.md §6.3).**
The success criterion is our own controlled comparisons.

### Short-answer — Mohler (our PRIMARY short-answer)
| Study | Method | Protocol | Reported | Key |
|---|---|---|---|---|
| Fischer 2025 (NodeGrade) | semantic-sim + LLM hybrid | Mohler benchmark | **r = 0.73, QWK = 0.55** (moderate; struggles on boundary cases) | `fischer_evaluation_2025` |
| Duong 2024 | GPT-4 embeddings/completions, few-shot | SE dataset **+ Mohler** | **r = 0.844** (best, few-shot); context improves quality | `duong_automatic_2024` |
| Mello 2025 | GPT-4o vs BERT/TF-IDF | "Texas/Mohler" + PT_ASAG, **seen vs unseen** | BERT best on **seen** (MAE↓ to 0.34 on PT_ASAG); **GPT-4o competitive on unseen** (PT_ASAG unseen: GPT-4o MAE 0.51 vs BERT 0.58) | `ferreira_mello_automatic_2025` |

### Short-answer — SemEval-2013 Task 7 / SciEntsBank (our DEVELOPMENT set)
| Study | Method | Protocol | Reported | Key |
|---|---|---|---|---|
| Kazi 2023 | RoBERTa + MNLI (entailment) | **SciEntsBank** | **weighted-F1 ≈ 0.72**; gains on "contradiction" class | `kazi_enhancing_2023` |

### Short-answer benchmark context — ASAP-SAS / ASAP (NOT our dataset; the canonical anchor)
| Study | Method | Reported | Key |
|---|---|---|---|
| Kumar 2019 (AutoSAS) | feature-rich + tree | **mean QWK = 0.79** on ASAP-SAS (prior SOTA band 0.7–0.8) | `kumar_get_2019` |
| Dadi 2025 | DL + coherence | **QWK ≈ 0.81** (ASAP), **0.79** (own OS dataset); adversarial-sensitive | `dadi_robust_2025` |
| ElMassry 2025 (SLR) | BERT-family on ASAP | best holistic **QWK ≈ 0.83** | `elmassry_systematic_2025` |

### Code grading with human rubric (our PRIMARY code = PT-CS + RIAYN)
Closest published analogues — note **code-with-human-rubric grades are rare** (CLAUDE.md §5):
| Study | Method | Dataset | Reported | Key |
|---|---|---|---|---|
| Havare 2025 | code LLM + **DPO** fine-tune | new rubric set (27 problems, **3,725 subs**, 210 criteria, 27,966 datapoints, 22 TAs) | **Qwen-2.5-Coder-7B ≈ 85% micro-accuracy** (ties Codestral-22B, far cheaper); ~20% error "too high for full automation" | `havare_ai-based_2025` |
| Grandel 2024 | GPT-4 + human-in-loop, rubric | 26 students, 3 assignments | **98.21% acc, R=100%, P=59.30%**, 81.2% less time (small N) | `grandel_applying_2024` |
| Motiwala 2025 (SQL) | fine-tuned Llama-3 Text2SQL | WikiSQL 100-query subset | 87% execution accuracy (execution-grounded) | `motiwala_auto-assess_2025` |

> **Note on RIAYN ("Rubric Is All You Need"):** our chosen public code comparator is **not** in
> the SLR table (it is a dataset we add). Its own reported numbers must be pulled from the RIAYN
> paper in **Phase 1.5** (likely a 1.4 PDF target). Havare is the nearest in-SLR reference point.

### LLM-as-grader consistency / rubric-dependence (motivates RQ1, RQ2, RQ5)
| Study | Finding | Key |
|---|---|---|
| Pack 2024 | GPT-4 high **ICC 0.897/0.927** but **temporal drift**; r 0.731/0.638 across two times | `pack_large_2024` |
| Moazzez 2024 | 4 LLMs, 672 trials: Claude **ICC 0.828** (best) vs Copilot **0.293** (worst) — model choice dominates consistency | `moazzez_assessing_2024` |
| Tate 2024 | minimal-prompt ChatGPT: human–human κ 0.79 vs **human–AI κ 0.23–0.52** (low for summative) yet up to 89% within-±1 | `tate_can_2024` |
| García-Huertes 2024 | GPT rubric-conditioned, 18 reports × 10 repeats: **clearer rubrics → higher consistency**; logged tokens/cost (559 calls, 1.075M tok, $0.82) | `garcia-huertes_leveraging_2024` |
| Espino 2025 | open Llama agents on essays: QWK 0.38–0.46, **collapse to mid-range** | `espino_essay_2025` |

---

## 4. Gaps the SLR identifies → what Article 2 is positioned to fill

The SLR's own conclusions hand the baton to this paper (it literally names "controlled
experiments on recent LLMs ... shared rubrics, datasets, repeated runs, common agreement/error
metrics" as future work). Mapping its gaps to our RQs:

- **"No single best grader" — task–metric–deployment triad, not a leaderboard.** → Our
  **configuration framework / decision guide** is exactly the response (CLAUDE.md §1.2). Strong
  framing support for TLT's "design insight" clause (§1.1).
- **Prompting LLMs show high QWK *dispersion*** (multi-study mean ≈0.46, broad variance) vs
  supervised DL ≈0.81. → motivates our **consistency axis** (k=5 repeats, ICC, nSD) and treating
  LLM grading as needing calibration, not assumed.
- **Reasoning was never isolated within a family** in prior work (model-confounded). → **RQ1**
  within-family reasoning toggle (Qwen3; GPT-5.1 anchor none/high) is a deliberate improvement.
- **Rubric explicitness is decisive** (Pack, Moazzez, García-Huertes). → **RQ2** no-rubric vs
  with-rubric (+optional examples).
- **Generalisation > beating supervised on seen prompts** (Mello seen/unseen). → **RQ6**
  transfer to PT-CS; the seen/unseen narrative validates our "transfer, not beating a baseline".
- **Temporal drift / repeatability under-reported.** → consistency metrics are first-class here.
- **Code-with-human-rubric is scarce** (most code = pass/fail autograders; Havare's set unreleased
  per §5). → our **PT-CS + RIAYN** code arm is a genuine contribution; but **state code claims
  tentatively** (narrower evidence, §6.4).
- **SLR's recommended "reporting bundle"** = (i) ≥1 agreement/error metric, (ii) rubric/scale
  transparency, (iii) ≥1 robustness/consistency probe, (iv) operational indicators. → Article 2
  should satisfy all four explicitly (it already plans to).

---

## 5. Practical carry-overs

- **Toolchain:** the SLR uses the **same IEEEtran + BasicTeX/latexmk** setup we reuse (CLAUDE.md
  §9); its `IEEEtran.cls` is vendored in `slr_source/`. The PATH gotcha (`/Library/TeX/texbin`)
  applies here too.
- **Bibliography:** `slr_source/references.bib` (665 entries) is a ready reservoir of ≤Jul-2025
  citations — reuse keys directly; the Phase 1.2 library merge should **dedupe against it** so we
  don't double-cite or re-review the covered window.
- **Cutoff boundary:** SLR completed **July 2025** over Scopus + ScienceDirect + IEEE Xplore.
  Therefore Phase 1.2's exports (which let Jan–Jul 2025 through via `PUBYEAR>2024`) **overlap**
  this window and must be filtered to **> Jul 2025** to avoid re-reviewing covered work.

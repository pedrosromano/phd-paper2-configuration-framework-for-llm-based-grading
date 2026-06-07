# Library annotation summary (Phase 1.3)

> Two layers: (a) a **reproducible rule-based pass** (`annotate_refs.py`) that tags every row
> of `refs_merged.csv` with `relevance / reason / theme / perf / perf_dataset` — recall-oriented
> triage, deliberately coarse; (b) the **human-curated read below**, where the abstracts that
> matter were actually read to validate relevance, fix false hits, and seed the Phase 1.5
> performance table and the Phase 1.6 Related Work. The library was pre-filtered by grading-ish
> queries, so most non-excluded rows really are about grading; the rule pass's job is to surface
> the central subset, not to produce a tiny set.

## Rule-pass distribution (1093 rows)

| relevance | n | | theme (non-excluded) | n |
|---|---|---|---|---|
| high | 299 | | grading | 374 |
| med | 535 | | consistency | 260 |
| low | 16 | | code | 103 |
| **exclude** | **243** | | reasoning | 88 |
| | | | dataset-specific / other | 25 |

`exclude` = non-education-domain LLM papers from the broad ScienceDirect query (medical, chem,
manufacturing, security, etc.). 119 rows carry an auto-extracted metric; 32 name a dataset.
**Caveat:** `perf` is best-effort regex and contains noise (e.g. "QWK=3.9%" is really a *3.9%
improvement*; "ACCURACY=99.99%" is suspicious) — every number must be re-verified against the
paper in Phase 1.5. Two false dataset hits were fixed (a "Texas" chemical-emissions paper; a
medical "grade group" paper) by tightening the matcher.

## Curated highlights — what actually matters for Article 2

### A. Papers reporting on OUR datasets (Phase 1.5 seed; verify numbers from source)
| Paper (year) | Dataset(s) | Reported (to verify) | Why it matters |
|---|---|---|---|
| Evaluating Open-Source LLMs for Automatic Short Answer Scoring (2025) | **Mohler** | QWK 0.948, MAE 0.30 (GPT-3.5T / LLaMA3-70B / DeepSeek) | open-source LLMs on Mohler — our exact theme; strong numbers |
| iAttention Transformer (2025) | **Mohler+SemEval+SciEntsBank+Beetle** | — | covers all four of our short-answer sets at once |
| Contrastive Error Mining (CEM-FT) for LLM Assessment (2026) | **Mohler+SciEntsBank+Beetle** | — (few-shot reasoning *stability*) | consistency + LLM, our short-answer sets |
| Auto-marking short answer in science: BERT→GPT-4 (2026) | **ASAP+SciEntsBank+Beetle** | — | transformer→LLM survey on science short-answer |
| RUBRA: Agentic ASAG with LLMs+RAG (2025) | **SciEntsBank** | — | agentic rubric grading |
| NodeGrade (2025) | **SemEval-2013 T7** | outperforms GPT-4 on SemEval | already in SLR (`in_slr`) |
| Comparative GPT vs BERT for open-ended scoring (2026); Prompt-driven augmentation (2025); Semantic descriptive evaluator (2026) | **Mohler (+SciEntsBank)** | — | additional Mohler comparators |
| **RIAYN ("Rubric Is All You Need")** | — | **not in the library exports** | our code comparator; pull its numbers directly from the RIAYN paper in 1.5 (1.4 target) |

### B. Reasoning applied to scoring — directly RQ1 (the field moved here post-Jul-2025)
- *Automatic Short Answer Grading with LLMs: From Memorization to Reasoning* (2026) — names our exact axis.
- *Zero-Training AES with Reasoning LLM* (2025, ASAP QWK 0.757); *LLM Agents at the Roundtable: dialectical reasoning for essay scoring* (2025); *AutoSCORE multi-agent* (2026); *ADSC dual-stream* (2026).
- *Chain-of-Thought guided fine-tuning for rubric-assisted AES* (2026); *Explainable AI via rubric-aligned CoT prompting* (2026); *Teach-to-reason: rationale-driven multi-trait AES* (2026).
- *Comparison of Claude (Sonnet/Opus) and ChatGPT incl. GPT-o1* on programming assessments (2025) — a reasoning-model comparison.
- *LLM-Based Scoring of Geography Worksheets: Accuracy, Reasoning and Reproducibility* (2026) — reasoning **and** reproducibility together.
> **1.7 implication:** these are mostly *point solutions* (a framework, a prompt, an agent setup), **not** a systematic design-space study isolating reasoning **within a model family** while measuring **cost** and **consistency**. Our contribution still looks unfilled — but we must now position explicitly against this cluster.

### C. Consistency / reliability — RQ5 + our consistency axis
- *EvalCouncil: committee-based for reliable, unbiased grading* (2025); *SURE: self-consistency + selective human review* (2026); *Rubric-Guided Evaluation for Consistent Scoring* (2025).
- *Can AI grade your essays? multidimensional, open+closed LLMs* (2025, Spearman 0.74, ICC 0.80); *ASAG in Sustainability Education: AI–human agreement* (2026, QWK 0.585, ICC 0.667).

### D. Rubric / evaluation guidance — RQ2
- *Reflective Prompt Engineering for Rubric Optimization* (2026); *Systemic Functional Prompting for AES with GPT-4* (2025); *Rubric-Guided Evaluation Framework* (2025).

### E. Code grading with LLMs — our code domain (state claims tentatively, §6.4)
- *Using GenAI to Assess Design Patterns in Student-Written Code* (2025, OOP — close to PT-CS/RIAYN); *StepGrade: context-aware LLM programming grading* (2025); *Automated Evaluation of Programming Short-Answer Questions with LLMs* (2025); *Assessing LLMs for Feedback in Programming Problem Solving* (2025); *Code Explanation Assessment + analogical reasoning* (2025); *Toward Automated UML Diagram Assessment* (2025).

### F. Scope / decomposition & human-AI collaboration — RQ3
- *Open-ended Structured Question Assessment with Human-LLM Collaboration* (2026, **scoring-point-level** ≈ our criterion decomposition); *Towards Human-Like Grading: unified LLM framework for subjective questions* (2025); *Grading MOOCs with LLMs* (2025).

### G. New benchmarks / datasets & CS-education framing (TLT/ToE positioning)
- *SAS-bench: fine-grained benchmark for short-answer scoring with LLMs* (2026) — a benchmark to cite/contrast.
- *Educational Evaluation with MLLMs: Framework, Dataset* (2025); *AMMORE* (math, 2025); *BeSTraP* novel DB-course dataset (2026); *ROARs* (Ghana reading, 2025, GPT-4 QWK 0.91/F1 0.87).
- *Emerging AI and the Need for a Novel Evaluation Framework in Undergraduate CS Education* (2026) — **our framing register**; *Language Models are Few-Shot Graders* (2025).

## Candidate full-text targets for Phase 1.4 (keep short)
Only where the abstract withholds numbers we need for the 1.5 context table or for positioning:
1. Evaluating Open-Source LLMs for ASAG (Mohler) — exact per-model QWK/MAE.
2. iAttention Transformer — per-dataset (Mohler/SemEval/SciEntsBank/Beetle) values.
3. CEM-FT (Contrastive Error Mining) — per-dataset values + the consistency claim.
4. **RIAYN paper** — our code comparator's own reported numbers (not in exports).
5. SAS-bench — to know what it measures (avoid overlap / cite as related benchmark).
6. From-Memorization-to-Reasoning ASAG (2026) — closest external RQ1 evidence.
(Try legitimate open sources first; batch-list whatever stays paywalled — Phase 1.4.)

## What's excluded and why
243 rows excluded: LLM papers outside education/assessment (process safety, defect detection,
clinical/OSCE-medical except where genuinely about student assessment, RAG for industry, etc.).
16 `low` = education+assessment-adjacent but not grading (tutoring, question generation, MCQ ICL).
`in_slr`=True rows (≈13 at high relevance) are already covered by Article 1 and should be cited
from there, not re-reviewed.

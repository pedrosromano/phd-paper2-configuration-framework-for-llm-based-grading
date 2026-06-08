# Related Work — validated reference set (input reinforcement, 2026-06-08)

> Validation of the user's candidate list against the SLR (`slr_source/references.bib` + `.bbl`,
> numbered refs in `[]`) and the library (`refs_merged.csv`), plus legitimate open-source lookup.
> **Not added to any draft** (that is Phase 1.6); papers are only listed here once located/read.
> Nothing below is invented — anything I could not locate is in list **(c)** for the user.

---

## (a) VALIDATED — keep, with role

### 1. Positioning anchors (the pair we position our contribution *against*)
- **Mello et al. 2025** — `ferreira_mello_automatic_2025` **[SLR 118]**. "ASAG in the LLM Era: Does GPT-4 with
  Prompt Engineering beat Tuned models?" GPT-4o vs classical ASAG, **seen/unseen splits**, incl. PT (PT_ASAG).
  ✓ In SLR. **Role:** closest comparator; our transfer/generalisation framing (RQ6) leans on its seen/unseen logic.
- **Arz von Straussenburg et al. 2025** — `arz_von_straussenburg_enabling_2025` **[SLR 115]**. "Enabling
  Responsible LLM-Based Grading … Reproducible Data Preparation Pipeline." Local hosting, anonymisation,
  structured **"grading events"**, **LoRA** fine-tuning on course data. ✓ In SLR. **Role:** *sibling paper* to
  our approach (local + privacy + structured records + fine-tuning) — we extend it from a pipeline to a
  systematic configuration study.

### 2. Dataset-origin papers (mandatory citation when we use them) — NOT in SLR/library; located open
- **Mohler & Mihalcea 2009** — "Text-to-Text Semantic Similarity for ASAG", EACL 2009, ACL Anthology **E09-1065**.
- **Mohler, Bunescu & Mihalcea 2011** — "Learning to Grade Short Answer Questions using Semantic Similarity",
  ACL 2011. **This is the graded Mohler dataset we actually use** (~2,273 answers, 0–5, CS courses; Pearson/MAE/
  RMSE). PDF fetched (`mohler_2011_acl.pdf`). **Cite both** (2009 origin + 2011 dataset).
- **Dzikovska et al. 2013** — "SemEval-2013 Task 7: The Joint Student Response Analysis and 8th RTE Challenge"
  (*SEM 2013). SciEntsBank + Beetle, 5-way labels (correct/partially-correct/contradictory/irrelevant/non-domain),
  unseen-answers / unseen-questions splits. PDF fetched (`dzikovska_semeval2013_task7.pdf`). **Cite for SemEval.**

### 3. RQ1 divergence (reasoning) — the heart of the contribution
- **"Explicit Reasoning Makes Better Judges"** — Jayarao, Gupta, Varshney, Dwivedi, **arXiv 2509.13332**
  (Sep 2025). PDF fetched (`explicit_reasoning_judges_2509.13332.pdf`). **Verified:** thinking vs non-thinking
  in LLM-as-a-judge using **Qwen3 (0.6/1.7/4B) with the thinking toggle** → thinking ≈ +10% accuracy at <2×
  cost. **Role:** general-domain "**reasoning helps judging**" anchor — and it uses the *exact* within-family
  Qwen3 toggle we adopt, so it both motivates RQ1 and validates the method. (Read before citing — done.)
- **RewardBench** (LLM-as-judge / reward-model benchmark) — **Located, verify final ID** (Lambert et al. 2024,
  arXiv 2403.13787). **Role:** context for the LLM-as-a-judge framing. *I did not re-fetch it this pass — confirm
  the ID before it enters the draft.*

### 4. Code-grading-with-rubric anchors (our domain)
- **Mazzone et al. 2024** — `mazzone_exploring_2024` **[SLR 108]**. Locally-run open-source LLMs in intro CS;
  **TA support, not final grader.** ✓ In SLR.
- **Moazzez et al. 2024** — `moazzez_assessing_2024` **[SLR 95]**. "Assessing the Consistency of Open-Source LLMs
  for Algorithm Evaluation" — **consistency (ICC / nSD)** of LLMs grading programming answers by rubric. ✓ In SLR.
- **Havare et al. 2025** — `havare_ai-based_2025` **[SLR 131]**. Rubric-based code grading with **partial credit**;
  ~**85% micro-accuracy**; "**~20% error still too high for full automation**". ✓ In SLR.
- **RIAYN — "Rubric Is All You Need"** — Pathak et al., **arXiv 2503.23989** (ICER 2025). PDF held
  (`riayn_2503.23989.pdf`); **ID confirmed by reading p.1**. DSA 150 + OOP 80 ≈ 230 subs; Spearman/Cohen's κ +
  *Leniency*. **Role:** our public code comparator **and** the "rubric-is-the-key-context" thesis → ties to our
  evaluation-guidance dimension (RQ2).
- **Manorat et al. 2025** — `manorat_artificial_2025` **[SLR 121]**. SLR of AI in programming education;
  **dynamic vs static grading**, semi-automatic triage framing. ✓ In SLR.

### 5. Model-comparison-as-graders — treat as DEMARCATION ("this exists → we do a framework, not a ranking")
- **Jukiewicz 2026** — "A systematic comparison of LLMs for automated assignment assessment in programming
  education." Library; DOI **10.1016/j.caeo.2026.100364**. First large-scale side-by-side LLM comparison,
  **6000+ submissions**, grade-distribution / strict-vs-lenient analysis. **Role:** the canonical "yet another
  model ranking" we differentiate from.
- **Poličar et al. 2025** — "Automated assignment grading with LLMs: Insights from a **bioinformatics** course."
  Library; DOI **10.1093/bioinformatics/btaf196**. **This IS the "bioinformatics model-comparison paper" the user
  listed separately — same paper (deduped).** **Role:** demarcation (domain-specific model comparison).
- **GraderAssist 2025** — "Graph-Based **Multi-LLM** Framework for Transparent and Reproducible Automated
  Evaluation." Library; DOI **10.3390/informatics12040123**. **Role:** demarcation + relevant to our consistency
  axis (reproducibility across evaluators).
- *(RQ4 baseline-context use: Jukiewicz reports grade distributions/leniency, not QWK/MAE on our datasets, so it
  feeds the demarcation narrative more than the numeric context table.)*

### 6. Venue (TLT) citations — journal fit, not from SLR
- **Putnikovic & Jovanovic 2023** — "Embeddings for ASAG: A Scoping Review", **IEEE TLT** 16(2), DOI
  **10.1109/TLT.2023.3253071**. ✓ Confirmed. **Role:** TLT-register anchor + ASAG scoping review.
- **Gašević/Mello AI-feedback tool (TLT)** — **Located, verify exact paper/DOI:** candidate "Empowering
  Instructors with AI: Evaluating the Impact of an AI-driven Feedback Tool in Learning Analytics" (and/or TLT
  DOI **10.1109/TLT.2025.3562379**). **Role:** TLT deployed-tool citation. *Confirm which before drafting.*

### Support-claim citations (all ✓ in SLR — confirmed, ready to use)
- **Li et al. 2023** `li_am_2023` **[75]** — "Am I Wrong, or Is the Autograder Wrong? Effects of AI Grading
  Mistakes on Learning" (ICER). **Harmful FP/FN for learning** — strong for TLT.
- **Pack et al. 2024** `pack_large_2024` **[96]** — LLM AES validity/reliability, **temporal drift → justifies k=5**.
- **García-Huertes et al. 2024** `garcia-huertes_leveraging_2024` **[90]** — **clearer rubrics → higher consistency**.
- **Kazi & Kahanda 2023** `kazi_enhancing_2023` **[82]** — fine-tuning for ASAG, **SciEntsBank** baseline (F1≈0.72).
- **Fischer et al. 2025** `fischer_evaluation_2025` **[119]** — NodeGrade; **Mohler/SemEval** published baselines.
- **Duong & Meng 2024** `duong_automatic_2024` **[107]** — GPT ASAG in SE courses, uses **Mohler**, context helps.

---

## (b) DISCARDED / merged — with reason
- **"Bioinformatics model-comparison paper" as a separate entry** → **merged into Poličar et al. 2025** (it *is*
  that paper: Oxford *Bioinformatics*, btaf196). Not a separate reference.
- *(No candidate was outright discarded — all located items are genuinely on-topic. The only correction is the
  dedup above.)*

---

## (c) NOT LOCATABLE — please provide (do not draft from these until supplied & read)
1. **Education "reasoning *worsens* essay scoring" leaderboard/paper** — the counter-signal to "Explicit
   Reasoning Makes Better Judges", and the decisive half of the RQ1 divergence. I found only a **non-peer-
   reviewed Substack analysis** ("A Clearer View of LLM Performance in Education", edtechinsiders) reporting
   *"thinking models show no clear advantage for essay scoring; extended reasoning may drift from rubrics;
   Gemini 2.0 Flash best cost-performance"* + an unnamed leaderboard. **No peer-reviewed source located.**
   CLAUDE.md §1.1 calls it "Walsh / the educational reasoning leaderboard" — please give the exact ref
   (author/arXiv/DOI or leaderboard URL). This is load-bearing for RQ1; I won't cite the blog as evidence.
2. **Gong et al. 2025 (TLT)** — listed as a TLT LLM-grading citation; I could **not** confirm a Gong et al.
   2025 paper in IEEE TLT (the SLR "gong" hits are unrelated; web search didn't surface it). Please provide
   the exact title/DOI, or confirm if it was conflated with the Gašević/Mello TLT tool above.

## PDFs fetched this pass (open sources; in `library/pdfs/`, gitignored)
`explicit_reasoning_judges_2509.13332.pdf`, `mohler_2011_acl.pdf`, `dzikovska_semeval2013_task7.pdf`.

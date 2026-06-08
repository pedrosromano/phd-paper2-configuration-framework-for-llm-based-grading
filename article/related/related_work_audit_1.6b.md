# Related Work audit — Phase 1.6b gate (2026-06-08)

Cross-check of the Phase 1.6 draft (`sota_draft.tex`) against the PDFs, the annotated library,
and `references.bib`. **Gate: return the three lists and wait before 1.7.** Nothing here is a
unilateral relevance decision — the non-cited list is for the user's final call.

The draft cites **33 distinct keys**; `references.bib` has **34 entries**; `make paper` builds
with **0 undefined citations/references**.

## (a) Coverage — relevant material NOT cited (user makes the final relevance call)

### PDFs in `library/pdfs/` not cited (2 of 10)
| PDF | Paper | Why not cited (proposed — confirm) |
|---|---|---|
| `sasbench_2505.07247` | SAS-Bench (Lai et al. 2026) | New benchmark to *position against*; left out of the ~2pp draft for space. **Candidate to add** (one sentence in the datasets/demarcation para). |
| `from_memorization_to_reasoning_lak26` | ASAG with LLMs: From Memorization to Reasoning (Cong et al. 2026) | Closest external **RQ1** evidence. RQ1 para already anchors on Jayarao/Larionov/Sui; this is a 4th. **Candidate to add** if RQ1 needs an education-domain reasoning point. |

### In the baseline table but not formally `\cite`d
- `grandel_applying_2024` (GPT-4 code rubric, 98.21% acc / P 59%) — appears by name in
  `published_baselines.csv` but has **no `references.bib` entry** and is not cited. It is an
  Article-1 SLR ref. **Action needed:** add it to the bib and wire the table to `\cite` in
  Phase 7, or drop the row. (All other table rows map to cited keys.)

### Curated high/med papers from `annotation_summary.md` not cited
High/med relevance = 834 rows; a 2-page Related Work cites representative **anchors per theme**,
not whole clusters. The notable annotated papers deliberately *not* cited (blanket reason: space
/ represented by an anchor already cited) — promote any you want in-text:
- **Reasoning cluster:** Zero-Training AES with Reasoning LLM; LLM Agents Roundtable; CoT-guided/
  rubric-aligned AES (×2); Teach-to-reason multi-trait. *(Anchor cited: Jayarao.)*
- **Consistency cluster:** EvalCouncil (committee); SURE (self-consistency + human review).
  *(Anchors cited: Moazzez, Pack, Tate.)*
- **Rubric/guidance cluster:** Reflective Prompt Engineering; Systemic Functional Prompting.
  *(Anchor cited: García-Huertes; RIAYN.)*
- **Code cluster:** StepGrade; Programming short-answer with LLMs; GenAI design-patterns (OOP).
  *(Anchors cited: Mazzone, Havare, RIAYN, Manorat.)*
- **CS-education framing:** "Need for a Novel Evaluation Framework in Undergraduate CS Education".
  *(Candidate for the contribution para if we want an explicit CS-ed framing cite.)*

## (b) Bibliographic integrity
- **Missing (cited but no bib entry):** NONE. ✓
- **Orphan (in bib, not cited):** `li_am_2023` — **intentional**: reserved for the `[ToE]`
  reframing comment (harmful FP/FN argument). Keep, or cite in body if staying with TLT.
- **Cited without a DOI/arXiv identifier (3):** `mohler_text_2009`, `mohler_learning_2011`,
  `dzikovska_semeval_2013` — dataset-origin **conference papers** that predate routine DOIs.
  They have stable **ACL Anthology** IDs (Mohler 2009 = E09-1065; the 2011 ACL-HLT and the *SEM-2013
  Task 7 papers are on the ACL Anthology). **Action:** add Anthology IDs/URLs (I did not guess the
  exact 2011/2013 IDs — confirm or let me fetch them) — flagged rather than fabricated.
- All other 30 cited entries carry a DOI or arXiv ID. ✓

## (c) Traceability — origin not fully confirmed (do NOT rely on without your confirmation)
- **`romano_slr_2025`** — Article 1 (your own published SLR). **Real**, but I only have title +
  venue (IEEE ToE); **exact author list, year, volume, and DOI are placeholders.** Please supply.
- **`gasevic_feedback_tool_2025`** — the TLT AI-feedback tool. **Located** as a candidate
  ("Empowering Instructors with AI…", and/or TLT DOI 10.1109/TLT.2025.3562379) but the **exact
  paper/authors/DOI is unconfirmed**. Please confirm which paper, or I drop the cite.
- All other cited references trace to the library, the Article-1 SLR `.bib`, or a verified open
  source (arXiv/DOI). No new planning-phantoms detected (the "Gong"/"Walsh" cases were already
  removed).

## RESOLUTION (user decisions applied 2026-06-08)
- **grandel_applying_2024** added to `references.bib` (SLR ref 106, DOI 10.1145/3643795.3648375);
  the baseline table now emits `\cite{...}` per row (CSV `ref` column remapped to bibkeys) -- no
  uncited table row remains.
- **From-Memorization-to-Reasoning** (`cong_memorization_2026`, LAK 2026) promoted to a 4th RQ1
  anchor -- it is educational-domain ASAG, framing grading as reasoning (grounds the previously
  thin educational side); cited without over-claiming a reasoning-on/off result it does not test.
- **SAS-Bench** (`lai_sasbench_2026`, arXiv 2505.07247) added as one sentence (relevant short-answer
  LLM benchmark).
- **ACL Anthology IDs confirmed at the source** (aclanthology.org) and added: Mohler 2009 = E09-1065,
  Mohler 2011 = P11-1076, Dzikovska 2013 = S13-2045 -> no cited entry now lacks an identifier.
- **gasevic_feedback_tool_2025 removed** (cite + bib entry) -- unconfirmed nice-to-have; TLT venue
  fit stands on Putnikovic \& Jovanovic 2023.
- **romano_slr_2025** kept as a **TODO placeholder** (Article 1 not yet published; user supplies the
  full entry later) so the draft still compiles.
- Final state: `make paper` builds with **0 undefined**; 35 cited / 36 bib entries; one intentional
  orphan (`li_am_2023`, reserved for the ToE reframing); one TODO (`romano_slr_2025`).

## Summary for the user
- **Bib builds clean**, no missing entries, one intentional orphan.
- **3 cited entries lack a DOI** (dataset papers) → add ACL Anthology IDs.
- **2 cited entries are traceability-flagged** (`romano_slr_2025`, `gasevic_feedback_tool_2025`)
  → you supply/confirm.
- **Coverage gaps to rule on:** SAS-Bench, From-Memorization (PDFs), `grandel_applying_2024`
  (table), and any annotated-cluster papers you want promoted.

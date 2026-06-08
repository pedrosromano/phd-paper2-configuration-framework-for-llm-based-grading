# Phase 1.7 — Course-correction decision point (2026-06-08)

Mandatory check before experiments: does the refined state of the art (Phases 1.1--1.6b) still
support the planned direction (CLAUDE.md §1, §6 RQs, decision-guide deliverable), or has something
material changed? Four triggers per PHASES 1.7: (1) a sub-topic saturated, (2) a new baseline that
changes what counts as a contribution, (3) a new dataset/model worth including, (4) a finding that
undercuts a planned claim.

## Verdict: PROCEED — no redirection. Three sharpenings to record (below).

The planned design (reasoning × guidance × scope × decomposition × model, with consistency and a
focused conversation-state sub-study; develop-on-public, transfer-to-PT-CS; decision-guide as the
deliverable) holds. The field moved hard toward our exact topics since July 2025, but as **point
solutions**, not as a systematic design-space study. The unfilled niche is the **synthesis**.

## (1) Saturation? Partial, in the RIGHT direction — strengthens, not threatens
Post-cutoff work clusters on our axes (reasoning-in-grading, consistency, rubric guidance,
multi-agent, CS-education framing) — dozens of papers (see `annotation_summary.md`). Each is a single
framework / prompt / agent. **None** crosses the axes systematically, isolates reasoning within a
model family, or outputs a task→configuration guide. Saturation of *individual* questions raises the
bar for novelty on any single axis, which is exactly why the **framework/decision-guide** (not
per-axis numbers) must be the headline.

## (2) New baselines that change the contribution bar
- **Jayarao et al. 2025 (`explicit_reasoning_judges`, arXiv 2509.13332)** — the closest neighbour.
  It shows explicit reasoning helps *general* LLM-as-a-judge using the **same within-family Qwen3
  thinking toggle** we planned. This **validates our method** but also partially answers
  "does reasoning help judging" in the general domain. **Not a scoop of our contribution:** it is not
  educational grading, not rubric-bounded short-answer/code, and reports no cost/consistency trade-off
  or task→config guidance. **Action:** RQ1 must be stated as *grading-specific* (rubric-bounded,
  calibration-sensitive, code vs short-answer, with cost + consistency), explicitly extending Jayarao
  rather than re-asking it. (Already cited and framed in the draft.)
- **RIAYN (`pathak_rubric_2025`)** — question-specific rubric >> no-rubric on code (κ_B 0.41→0.60–0.65).
  This *supports* RQ2 but means "rubric helps code grading" is partly established. Our contribution is
  the **systematic, cross-domain mapping** (with reasoning/scope/decomposition), not "rubric helps".
- No published baseline reframes the deliverable; all sit as external context (Table~published).

## (3) New datasets / models worth including?
- **Datasets:** SAS-Bench (Gaokao short-answer), EssayJudge (multimodal AES), AMMORE (math), ROARs
  (reading) surfaced. **None displaces** our core (Mohler + SemEval short-answer; PT-CS + RIAYN code):
  they are non-CS, non-rubric-code, or multimodal (out of scope). Keep them as *related benchmarks*
  to cite, not adopt. The §5 landscape claim (code-with-human-rubric is scarce) **still holds**.
- **Models:** reasoning models (o1/o3/GPT-5.x, DeepSeek-R1, Qwen3 thinking) are now mainstream — this
  **confirms** our roster (Qwen3 within-family toggle; GPT-5.1 anchor with a true `none`/`high` toggle)
  and the timeliness of RQ1. No change.

## (4) Findings that undercut a planned claim?
- **The only real change:** the original RQ1 motivation ("a divergence between two fields — reasoning
  helps general judging but a published educational leaderboard shows it *worsens* essay scoring")
  was **falsified**: directed search found **no peer-reviewed** evidence that reasoning worsens
  educational scoring (only grey literature). **Already absorbed** (CLAUDE.md/PHASES phantom refs
  removed; RQ1 reframed to an *open question* anchored on Jayarao + Larionov 2504.08120 [adjacent
  MT/summ, task/arch-dependent] + Stop-Overthinking 2503.16419 [TMLR]). This is a *motivation* change,
  not a *design* change — the within-family on/off experiment is unchanged and now better grounded.
- Nothing undercuts the decision-guide deliverable, the dimensions, the gates, or the validation logic.

## Sharpenings to record (no redirection)
1. **Lead with the framework.** Given the crowded space, foreground the *decision guide* (task→config→cost)
   and the systematic design-space coverage as the contribution; treat per-axis results as evidence,
   not as the headline. (Reinforces CLAUDE.md §1.2 — already the intent.)
2. **RQ1 is grading-specific.** State it as extending the general "reasoning helps judging" result
   (Jayarao) into rubric-bounded CS grading, with cost and consistency, and the code-vs-short-answer
   contrast — the angle no one has done.
3. **Cite, don't adopt, the new benchmarks** (SAS-Bench/EssayJudge) and keep code-domain claims
   tentative (narrower evidence, §6.4).

## Decision requested
Confirm **proceed to Phase 2 (ingest)** with the three sharpenings recorded, or flag an adjustment.
Per PHASES 1.7, waiting for your decision before any experiment work begins.

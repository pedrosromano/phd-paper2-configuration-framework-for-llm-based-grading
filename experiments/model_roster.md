# Model roster — fresh survey + selection (2026-06-08)

**Paradigm change (user, 2026-06-08):** the 32 GB hardware ceiling is **no longer an eligibility
criterion**. Ethics/treatment is Iscte-approved and we have an inference API (DeepInfra) for large
models. **Select models by scientific relevance, not by what fits the Mac.** Infrastructure is a
**downstream, per-model** note (local if it fits and we prefer; DeepInfra otherwise / for speed),
never an upstream filter. This supersedes the inherited, stale roster benchmarked in Phase 0.3.

## Fresh survey (open-weight SOTA, June 2026)
From a current web survey (not training memory): the open-weight frontier is now **DeepSeek-V4**
(Pro 1.6T/49B-active; **Flash** 284B/13B-active, 1M ctx), **Qwen3.5** (dense+MoE, 0.8B→397B;
thinking/non-thinking), **GLM-5.1** (Z.ai; strongest open *coding* model 2026, hybrid thinking),
**Kimi K2.6** (Moonshot; SOTA agentic/coding, multimodal). All are served on **DeepInfra**.
Reasoning toggles: **Qwen3.5** `chat_template_kwargs={enable_thinking: false}`; **DeepSeek-V4**
`enable_thinking`; **GLM-5.1** hybrid (thinking default-on, toggleable); **Kimi K2.6** is
agentic/reasoning-by-default with **no clean on/off** → unfit for the within-family RQ1 toggle.

## Selected roster (representative, not exhaustive — k=5 multiplies cost)
Guided by: (1) within-family reasoning toggle for RQ1 [priority]; (2) code/short-answer strength;
(3) currency/representativeness for RQ4; (4) matrix discipline.

| Model | Role | Reasoning toggle | Infra | DeepInfra price /1M (in/out, VERIFY) |
|---|---|---|---|---|
| **Qwen3.5** (mid MoE, e.g. 30B/235B) | **RQ1 primary** within-family toggle; Apache-2.0; continuity w/ Jayarao (same family); strong general+code | ✅ `enable_thinking` | DeepInfra (small variant also runs local) | ~$0.10–0.40 |
| **DeepSeek-V4-Flash** (284B/13B) | RQ1 toggle + **cheap** SOTA + RQ4 breadth; the cost-floor workhorse | ✅ `enable_thinking` | DeepInfra | **$0.14 / $0.28** |
| **GLM-5.1** | RQ1 toggle + **code domain** (strongest open coder 2026) | ✅ hybrid (confirm clean OFF at 3.4) | DeepInfra | ~$0.40 / $0.60 |
| **GPT-5.1** (closed) | **Paid frontier anchor** (unchanged); closed-model reference | ✅ `reasoning_effort none/high` | OpenAI API | $1.25 / $10 |

**RQ1 within-family toggle arm** = Qwen3.5, DeepSeek-V4-Flash, GLM-5.1 (each graded reasoning OFF vs
ON) + GPT-5.1 anchor (none/high). Three open vendors + one closed → isolates reasoning from vendor
robustly. **RQ4 model comparison** spans DeepSeek/Qwen/GLM (open) vs GPT-5.1 (closed) — four families,
three with a clean toggle — with a cost range from $0.14/1M (V4-Flash) to $10/1M-out (GPT-5.1).

**Kimi K2.6 — CUT (2026-06-08).** Considered for RQ4 breadth, but dropped on the minimal-effort
principle: it is the priciest of the lot (~$0.55/$1.10), has **no clean reasoning toggle** (so it
can't join the RQ1 arm, the study's focus), and RQ4 breadth is already well served by the four
families above. Its distinctive strength is agentic/long-horizon work, not rubric-bounded
short-answer/code grading — no grading-specific reason to keep it. Re-add only if a concrete
grading-relevant case appears.

**Optional convenience (not core):** the four models benchmarked locally in Phase 0.3
(`qwen3:30b`, `qwen3:14b`, `gemma3:27b`, `deepseek-r1:14b`) remain available for **free local smoke
tests** and a cheap cost-floor point if wanted, but are superseded by the current-gen roster above
for the actual study. A small **Qwen3.5** variant can run local on 32 GB for the same purpose.

## Infrastructure is per-model, not a filter
- Local (Ollama) only where a model **fits 32 GB AND we prefer it** (smoke tests, cost-floor).
- DeepInfra for everything that doesn't fit or where speed matters (most of the roster).
- GPT-5.1 stays on the OpenAI API (the closed anchor, separate €150 ceiling).

## Cost / budget (two separate ceilings, like the anchor's)
- **OpenAI anchor:** €150 ceiling (unchanged; cost guard enforces).
- **DeepInfra (open models): €150 ceiling** (user, 2026-06-08) — a **runaway guard** (catch bugs), not
  a usage squeeze. The matrix estimate is ~€30–100, so €150 leaves margin over the worst case; since
  the guard only refuses arms that *exceed* it, it never makes us spend more. Prices are cheap; the
  multiplier is **k=5 × matrix × 4 datasets**, dominated by reasoning-ON output tokens. The exact
  matrix (sample N, which cells get k=5 vs reduced) is **Phase 4.1**; per-arm € estimate + enforcement
  wired then via the cost guard (DeepInfra models in `pricing.yaml`).

## Verified at Phase 3.4 (2026-06-08, live smoke test) ✅
- **GLM-5.1 clean OFF — CONFIRMED.** Output tokens off→on: 10→440 → the hybrid toggle genuinely disables
  reasoning. GLM stays in the RQ1 arm, no caveat needed. (All toggles clean: V4-Flash 7→342, Qwen3.5 7→3584,
  GPT-5.1 15→569.)
- **DeepInfra model IDs confirmed:** `deepseek-ai/DeepSeek-V4-Flash`, `Qwen/Qwen3.5-35B-A3B`
  (the planned `Qwen3.5-235B-A22B` does NOT exist; 3.5 MoE variants are 35B-A3B and 397B-A17B — picked the
  efficient 35B-A3B), `zai-org/GLM-5.1`. Anchor `gpt-5.1`. All grade a real Mohler item parse_ok; DeepInfra
  off-mode emits clean JSON in 7–10 tokens.

## Phase 3.7 end-to-end smoke confirms the local/DeepInfra split (2026-06-08)
Full pipeline (config→prompt→adapter→parser→cache/log) over 5 items × off/on × k=2 = 20 runs:
- **Local `qwen3:30b`: pi=0.60** in BOTH modes — it rambles past the token cap before emitting JSON
  (mean out 1919/3625 tok). **Unreliable for grading.**
- **DeepInfra `deepseek-v4-flash`: pi=1.00** in both modes (off 7 tok/1.3s, on 242 tok/11s); cache rerun
  skipped 20/20. → **confirms the decision: real runs on DeepInfra; local Ollama is convenience only.**
  (Teaser RQ1 signal: on-mode mean_score 4.50 vs off 3.80 on Mohler, N=5 — the study quantifies it.)

## Still open (operational, not blocking)
- Live DeepInfra prices to reconcile against `pricing.yaml` estimates (cost guard logs actual usage).
- Whether to include a small local Qwen3.5 for a free cost-floor point.

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
| **GLM-5.1** | RQ1 toggle + **code domain** (strongest open coder 2026) | ✅ hybrid | DeepInfra | ~$0.40 / $0.60 |
| **Kimi K2.6** | **RQ4 breadth** (4th major family) + code/agentic SOTA | ✗ (default reasoning) → not in RQ1 toggle arm | DeepInfra | ~$0.55 / $1.10 |
| **GPT-5.1** (closed) | **Paid frontier anchor** (unchanged); closed-model reference | ✅ `reasoning_effort none/high` | OpenAI API | $1.25 / $10 |

**RQ1 within-family toggle arm** = Qwen3.5, DeepSeek-V4-Flash, GLM-5.1 (each graded reasoning OFF vs
ON) + GPT-5.1 anchor (none/high). Three open vendors + one closed → isolates reasoning from vendor
robustly. **RQ4 model comparison** spans DeepSeek/Qwen/GLM/Kimi (open) vs GPT-5.1 (closed), with a
cost range from $0.14/1M (V4-Flash) to $10/1M-out (GPT-5.1).

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
- **DeepInfra (open models):** needs its own ceiling. Prices above are cheap, but **k=5 × full
  matrix × 4 datasets** is the multiplier. The exact matrix (sample N, which cells get k=5 vs
  reduced) is **Phase 4.1**; the per-arm € estimate + ceiling enforcement is wired then via the cost
  guard (DeepInfra models added to `pricing.yaml`). **TODO (user):** set the DeepInfra spend ceiling
  (proposed default below) and confirm exact DeepInfra model IDs/prices against the live model list.

## To verify before Phase 4 (operational, not scientific)
- Exact DeepInfra model IDs (`deepseek-ai/DeepSeek-V4-Flash` ✓ confirmed; Qwen3.5 / GLM-5.1 /
  Kimi-K2.6 IDs + live prices) and the precise size variant of Qwen3.5/GLM to use.
- Whether to include a small local Qwen3.5 for the cost-floor.
- Re-benchmark is unnecessary (API), but confirm each model's reasoning-toggle param in a smoke test.

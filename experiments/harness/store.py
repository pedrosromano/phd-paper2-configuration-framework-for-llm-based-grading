"""Run cache + logging (Phase 3.6).

Cache key = (item_id, config_hash, run_index) (CLAUDE.md §8). A run that already exists is
SKIPPED on rerun (protects cost + time). Every run row is appended to
data/processed/runs/runs.jsonl with the full reproducibility bundle: model key + resolved
model_id + provider + quant, prompt hash, temperature, reasoning, date, plus the config
dimensions and the GradeResult (score/parse_ok/tokens/latency/raw never discarded).

  run_one(item, config, grade_fn, store)  -> (row, was_cached)
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from experiments.configs.config import prompts_version
from experiments.harness import prompts

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = REPO_ROOT / "data" / "processed" / "runs"
RUNS_FILE = RUNS_DIR / "runs.jsonl"
PRICING = REPO_ROOT / "experiments" / "configs" / "pricing.yaml"

# local-convenience model -> quantisation (Phase 0.3 pulls were Q4_K_M)
_LOCAL_QUANT = {"qwen3:30b": "Q4_K_M", "qwen3:14b": "Q4_K_M", "gemma3:27b": "Q4_K_M",
                "deepseek-r1:14b": "Q4_K_M", "qwen2.5-coder:32b": "Q4_K_M"}
_PRICING_CACHE: dict | None = None


def _pricing() -> dict:
    global _PRICING_CACHE
    if _PRICING_CACHE is None:
        _PRICING_CACHE = yaml.safe_load(PRICING.read_text())
    return _PRICING_CACHE


def _model_meta(model: str) -> dict:
    """Resolve the reproducibility tag/provider/quant for a model key."""
    m = _pricing().get("models", {}).get(model)
    if m is not None:
        return {"model_id": m.get("model_id", model), "provider": m.get("provider", "api"),
                "quant": None}
    return {"model_id": model, "provider": "ollama", "quant": _LOCAL_QUANT.get(model)}


def prompt_hash(prompt: str) -> str:
    return hashlib.sha1((prompt or "").encode("utf-8")).hexdigest()[:16]


class RunStore:
    def __init__(self, path: Path = RUNS_FILE):
        self.path = path
        self._keys: set[tuple] = set()
        self._index: dict[tuple, dict] = {}
        if path.exists():
            for line in path.read_text().splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                k = (row["item_id"], row["config_hash"], row["run_index"])
                self._keys.add(k)
                self._index[k] = row

    def has(self, item_id: str, config_hash: str, run_index: int) -> bool:
        return (item_id, config_hash, run_index) in self._keys

    def get(self, item_id: str, config_hash: str, run_index: int) -> dict | None:
        return self._index.get((item_id, config_hash, run_index))

    def append(self, row: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        k = (row["item_id"], row["config_hash"], row["run_index"])
        self._keys.add(k)
        self._index[k] = row

    def __len__(self) -> int:
        return len(self._keys)


def build_run_row(item, config, result, prompt: str, *,
                  session_id=None, order_id=None, order_index=None, call_group=None) -> dict:
    """The LOCKED run-row schema. Because the cache keys on config_hash, a field missing
    here cannot be back-filled without re-running -- so everything Phase 5/6/7 needs is
    logged at write time. Tokens are kept SEPARATE (never an aggregate total); config is
    denormalized (every axis as its own column + config_hash); failures are rows too
    (error set, score=None) so pi and counts stay correct; the rendered prompt and raw
    output are stored verbatim for offline re-parse without re-calling the model."""
    meta = _model_meta(config.model)
    return {
        # --- identity / cache key (item_id, config_hash, run_index) ---
        "item_id": str(item["item_id"]),
        "config_hash": config.config_hash,
        "run_index": config.run_index,
        # --- config dimensions, denormalized (one column per axis) ---
        "dataset": config.dataset, "domain": config.domain,
        "model": config.model, "model_id": meta["model_id"], "provider": meta["provider"],
        "reasoning": config.reasoning, "context_level": config.context_level,
        "scope": config.scope, "decomposition": config.decomposition,
        "conversation_state": config.conversation_state,
        "question_id": str(item.get("question_id", "")),
        "submission_id": _strornone(item.get("submission_id")),
        # --- conversation sub-study linkage (Phase 4.9; None for the main factorial) ---
        "session_id": session_id, "order_id": order_id, "order_index": order_index,
        # --- whole-exam grouping: the N questions of one submission share ONE call; cost/
        #     tokens repeat on each row, so dedupe by call_group for per-call cost (5.4) ---
        "call_group": call_group,
        # --- sampling / reproducibility bundle (CLAUDE.md §8) ---
        "quant": meta["quant"], "temperature": config.temperature,
        "top_p": config.top_p, "max_tokens": config.max_tokens, "seed": config.seed,
        "prompt_template_version": prompts_version(),
        "prompt_hash": prompt_hash(prompt), "prompt": prompt, "k": config.k,
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        # --- result (raw + tokens never discarded; tokens kept separate) ---
        "score": result.score, "parse_ok": result.parse_ok,
        "gold_score": _num(item.get("gold_score")), "gold_scale_max": _num(item.get("gold_scale_max")),
        # gold labels carried for SemEval classification (5.2 macro-F1/accuracy) + split
        # breakdown, so analysis never re-joins the corpus (CLAUDE.md §5 / §6.2).
        "label_2way": _strornone(item.get("label_2way")),
        "label_3way": _strornone(item.get("label_3way")),
        "label_5way": _strornone(item.get("label_5way")),
        "split": _strornone(item.get("split")),
        "prompt_tokens": result.tokens_in, "completion_tokens": result.tokens_out,
        "reasoning_tokens": result.reasoning_tokens, "cost_eur": result.cost_eur,
        "latency_s": result.latency_s, "finish_reason": result.finish_reason,
        "error": result.error,
        "per_criterion": result.per_criterion, "answers": result.answers,
        "raw": result.raw,
    }


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _strornone(v):
    if v is None:
        return None
    s = str(v).strip()
    return s if s and s.lower() != "nan" else None


def run_one(item, config, grade_fn, store: RunStore, *,
            session_id=None, order_id=None, order_index=None) -> tuple[dict, bool]:
    """Skip-if-cached, else grade + log. grade_fn(item, config) -> GradeResult.
    session_id/order_id/order_index thread through the conversation sub-study (Phase 4.9)."""
    if store.has(item["item_id"], config.config_hash, config.run_index):
        return store.get(item["item_id"], config.config_hash, config.run_index), True
    result = grade_fn(item, config)
    prompt = prompts.render(config, item)
    row = build_run_row(item, config, result, prompt, session_id=session_id,
                        order_id=order_id, order_index=order_index)
    store.append(row)
    return row, False

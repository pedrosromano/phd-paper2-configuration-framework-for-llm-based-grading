"""Typed grading configuration + stable config_hash + matrix loader (Phase 3.1).

A Config is one cell of the experimental design (CLAUDE.md §6). The cache key is
(item_id, config_hash, run_index) -- so config_hash identifies the CELL and must NOT
depend on run_index or k.

Axes:
  dataset        ptcs | mohler | semeval | riayn
  domain         code | short_answer            (PT-CS has both; an axis for it)
  model          a roster model key (pricing.yaml) or a local-convenience Ollama tag
  reasoning      off | on                        (D2; mapped per model: e.g. GPT-5.1 none/high)
  context_level  none | with_guidance | with_examples
                   - "with_guidance" = the dataset's grounding: RUBRIC (PT-CS/RIAYN) or
                     REFERENCE answer (Mohler/SemEval). "with_examples" adds few-shot (§11 optional).
  scope          question_by_question | whole_exam       (whole_exam = PT-CS only)
  decomposition  holistic | criterion                    (criterion  = PT-CS only)
  k              repetitions (consistency); temperature; run_index in [0, k)

Applicability (CLAUDE.md §5/§6, verified Phase 2.6):
  - whole_exam and criterion apply to PT-CS ONLY.
  - reasoning=on requires the model to support a reasoning toggle.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from itertools import product
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
PRICING = REPO_ROOT / "experiments" / "configs" / "pricing.yaml"
PROMPTS = REPO_ROOT / "experiments" / "configs" / "prompts.yaml"

DATASETS = {"ptcs", "mohler", "semeval", "riayn"}
DOMAINS = {"code", "short_answer"}
# which domains actually exist per dataset (Phase 2.6 corpus)
DATASET_DOMAINS = {
    "mohler": {"short_answer"}, "semeval": {"short_answer"},
    "riayn": {"code"}, "ptcs": {"code", "short_answer"},
}
REASONING = {"off", "on"}
CONTEXT_LEVELS = {"none", "with_guidance", "with_examples"}
SCOPES = {"question_by_question", "whole_exam"}
DECOMPOSITIONS = {"holistic", "criterion"}
# Conversation-state sub-study (CLAUDE.md §6 / Phase 4.9). "none" = not part of the
# sub-study (the default for the main factorial: each call is an independent conversation).
# "clean" = a fresh conversation per answer; "shared" = one accumulating history per session.
CONVERSATION_STATES = {"none", "clean", "shared"}

# Cell-defining fields read straight off the Config. config_hash ALSO folds in the
# resolved model_id+provider and the prompt-template version (see config_hash) so that
# changing ANY output-affecting setting busts the cache. Excludes k and run_index by
# design (those are separate cache dimensions, not part of the cell identity).
_HASH_FIELDS = ("dataset", "domain", "model", "reasoning", "context_level",
                "scope", "decomposition", "temperature", "top_p", "max_tokens",
                "seed", "conversation_state")
# Local-convenience Ollama tags (smoke tests / cost-floor); roster models come from pricing.yaml.
LOCAL_MODELS = {"qwen3:30b", "qwen3:14b", "gemma3:27b", "deepseek-r1:14b", "qwen2.5-coder:32b"}

# Cheap caches (config_hash is hit thousands of times during matrix expansion).
_PRICING_MODELS: dict | None = None
_PROMPTS_VERSION: str | None = None


class ConfigError(ValueError):
    pass


def _pricing_models() -> dict:
    global _PRICING_MODELS
    if _PRICING_MODELS is None:
        _PRICING_MODELS = yaml.safe_load(PRICING.read_text()).get("models", {})
    return _PRICING_MODELS


def prompts_version() -> str:
    """Short hash of prompts.yaml. Any edit to the template file changes this, so it
    enters config_hash and busts the cache -- a re-rendered prompt is a different cell."""
    global _PROMPTS_VERSION
    if _PROMPTS_VERSION is None:
        _PROMPTS_VERSION = hashlib.sha1(PROMPTS.read_bytes()).hexdigest()[:12]
    return _PROMPTS_VERSION


def resolve_model_id(model: str) -> str:
    return _pricing_models().get(model, {}).get("model_id", model)


def resolve_provider(model: str) -> str:
    m = _pricing_models().get(model)
    return m.get("provider", "api") if m is not None else "ollama"


def known_models() -> set[str]:
    return set(_pricing_models()) | LOCAL_MODELS


def _model_has_toggle(model: str) -> bool:
    """True if the model exposes a reasoning on/off toggle (pricing.yaml reasoning_param/values)."""
    m = _pricing_models().get(model)
    if m is None:                       # local-convenience model: assume togglable (qwen3/r1 think)
        return True
    return bool(m.get("reasoning_param")) or bool(m.get("reasoning_values"))


@dataclass(frozen=True)
class Config:
    dataset: str
    domain: str
    model: str
    reasoning: str = "off"
    context_level: str = "with_guidance"
    scope: str = "question_by_question"
    decomposition: str = "holistic"
    conversation_state: str = "none"
    k: int = 5
    temperature: float = 0.0
    top_p: float = 1.0
    max_tokens: int = 4096
    seed: int | None = None
    run_index: int = 0

    def validate(self) -> "Config":
        if self.dataset not in DATASETS:
            raise ConfigError(f"bad dataset {self.dataset!r}")
        if self.domain not in DOMAINS:
            raise ConfigError(f"bad domain {self.domain!r}")
        if self.domain not in DATASET_DOMAINS[self.dataset]:
            raise ConfigError(f"dataset {self.dataset!r} has no {self.domain!r} items")
        if self.reasoning not in REASONING:
            raise ConfigError(f"bad reasoning {self.reasoning!r}")
        if self.context_level not in CONTEXT_LEVELS:
            raise ConfigError(f"bad context_level {self.context_level!r}")
        if self.scope not in SCOPES:
            raise ConfigError(f"bad scope {self.scope!r}")
        if self.decomposition not in DECOMPOSITIONS:
            raise ConfigError(f"bad decomposition {self.decomposition!r}")
        if self.conversation_state not in CONVERSATION_STATES:
            raise ConfigError(f"bad conversation_state {self.conversation_state!r}")
        if self.model not in known_models():
            raise ConfigError(f"unknown model {self.model!r}; add to pricing.yaml or LOCAL_MODELS")
        if self.k < 1 or not (0 <= self.run_index < self.k):
            raise ConfigError(f"run_index {self.run_index} out of [0,{self.k})")
        # applicability
        if self.scope == "whole_exam" and self.dataset != "ptcs":
            raise ConfigError("whole_exam scope is PT-CS only")
        if self.decomposition == "criterion" and self.dataset != "ptcs":
            raise ConfigError("criterion decomposition is PT-CS only")
        if self.conversation_state in ("clean", "shared") and self.dataset != "ptcs":
            raise ConfigError("conversation-state sub-study (clean/shared) is PT-CS only")
        if self.reasoning == "on" and not _model_has_toggle(self.model):
            raise ConfigError(f"model {self.model!r} has no reasoning toggle for reasoning=on")
        return self

    @property
    def config_hash(self) -> str:
        """Identity of the experimental CELL: every setting that can change the model
        output. Folds in the resolved model_id + provider (the same key can map to a
        different served model/backend) and the prompt-template version, on top of the
        scalar _HASH_FIELDS. Excludes item_id / run_index / k (separate cache dimensions).
        Changing any included setting yields a new hash -> no silent stale-cache reuse."""
        payload = {k: getattr(self, k) for k in _HASH_FIELDS}
        payload["model_id"] = resolve_model_id(self.model)
        payload["provider"] = resolve_provider(self.model)
        payload["prompt_template_version"] = prompts_version()
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]

    @property
    def template_key(self) -> tuple[str, str, str, str]:
        """Prompt-template key (CLAUDE.md §3.2): (domain, context_level, scope, decomposition)."""
        return (self.domain, self.context_level, self.scope, self.decomposition)

    def as_row(self) -> dict:
        d = asdict(self)
        d["config_hash"] = self.config_hash
        return d


def _norm_reasoning(v):
    # YAML 1.1 parses bare off/on as booleans -> normalise back to "off"/"on".
    return {False: "off", True: "on"}.get(v, v)


def expand_arm(arm: dict) -> list[Config]:
    """Expand one matrix 'arm' (each axis a scalar or list) into validated Configs,
    cartesian over list-valued axes, with run_index 0..k-1. Inapplicable cells are skipped.
    Cartesian axes: dataset/domain/model/reasoning/context_level/scope/decomposition/
    conversation_state. Per-arm scalars (not crossed): k, temperature, top_p, max_tokens, seed."""
    axes = ["dataset", "domain", "model", "reasoning", "context_level", "scope",
            "decomposition", "conversation_state"]
    vals = {a: (arm[a] if isinstance(arm.get(a), list) else [arm.get(a)]) for a in axes}
    vals["reasoning"] = [_norm_reasoning(v) for v in vals["reasoning"]]
    if not arm.get("conversation_state"):
        vals["conversation_state"] = ["none"]   # default: not the sub-study
    k = int(arm.get("k", 5))
    temp = float(arm.get("temperature", 0.0))
    top_p = float(arm.get("top_p", 1.0))
    max_tokens = int(arm.get("max_tokens", 4096))
    seed = arm.get("seed")                       # None unless the arm pins one
    out: list[Config] = []
    for combo in product(*(vals[a] for a in axes)):
        base = dict(zip(axes, combo))
        for ri in range(k):
            try:
                out.append(Config(**base, k=k, temperature=temp, top_p=top_p,
                                  max_tokens=max_tokens, seed=seed, run_index=ri).validate())
            except ConfigError:
                break  # inapplicable cell -> skip all its run_indices
    return out


def load_matrix(path: str | Path) -> list[Config]:
    """Load a matrix YAML ({arms: [ {name, dataset:[...], model:[...], ...}, ... ]}) -> Configs.
    De-duplicates by (config_hash, run_index)."""
    spec = yaml.safe_load(Path(path).read_text())
    seen: set[tuple[str, int]] = set()
    configs: list[Config] = []
    for arm in spec.get("arms", []):
        for c in expand_arm(arm):
            key = (c.config_hash, c.run_index)
            if key not in seen:
                seen.add(key)
                configs.append(c)
    return configs

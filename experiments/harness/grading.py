"""Shared grading result type (Phase 3.3). Returned by every adapter (Ollama, DeepInfra,
OpenAI) so the runner/cache/analysis are adapter-agnostic."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class GradeResult:
    score: float | None            # holistic/total score on the item's native scale (None if unparseable)
    parse_ok: bool                 # did we extract a valid score? (feeds the pi extractable-rate)
    raw: str                       # raw model output (never discarded)
    tokens_in: int
    tokens_out: int
    latency_s: float
    model: str
    reasoning: str                 # "off" | "on"
    config_hash: str
    per_criterion: list | None = None   # criterion decomposition: [{"criterion","score"}, ...]
    answers: list | None = None         # whole-exam: [{"question_id","score"|...}, ...]
    error: str | None = None
    reasoning_tokens: int | None = None  # API-reported thinking tokens (None if backend hides them)
    finish_reason: str | None = None     # natural stop | length (token cap) | content_filter | done_reason
    cost_eur: float | None = None        # € charged for this call (paid models; None for local)

    def as_row(self) -> dict:
        return asdict(self)

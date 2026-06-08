"""Output parser (Phase 3.3 basic version; HARDENED in Phase 3.5).

Extracts a structured grade from raw model text. Returns (parsed_dict, parse_ok). NEVER
coerces unparseable output to 0 (CLAUDE.md §8) -- score stays None and parse_ok=False so
the pi extractable-rate is honest. 3.5 adds regex fallbacks, messy-output unit tests, and
the pi computation; the interface stays the same.
"""

from __future__ import annotations

import json
import re


def _strip_thinking(s: str) -> str:
    return re.sub(r"<think>.*?</think>", "", s, flags=re.S | re.I)


def _extract_json(text: str) -> dict | None:
    """First top-level JSON object in the text (handles ```json fences + surrounding prose)."""
    t = _strip_thinking(text)
    t = re.sub(r"```(?:json)?", "", t)
    # scan for a balanced {...}
    start = t.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(t)):
            if t[i] == "{":
                depth += 1
            elif t[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(t[start:i + 1])
                    except json.JSONDecodeError:
                        break
        start = t.find("{", start + 1)
    return None


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_output(raw: str, scope: str, decomposition: str) -> tuple[dict, bool]:
    """Parse per the (scope, decomposition) of the prompt.
    Returns ({score, per_criterion, answers}, parse_ok)."""
    out = {"score": None, "per_criterion": None, "answers": None}
    obj = _extract_json(raw or "")

    if scope == "whole_exam":
        answers = (obj or {}).get("answers")
        if isinstance(answers, list) and answers:
            out["answers"] = answers
            return out, True
        return out, False

    if decomposition == "criterion":
        if obj is not None:
            total = _num(obj.get("total"))
            crits = obj.get("criteria")
            if total is None and isinstance(crits, list):  # fall back to summing criteria
                s = sum(x for x in (_num(c.get("score")) for c in crits) if x is not None)
                total = s if crits else None
            out["per_criterion"] = crits if isinstance(crits, list) else None
            out["score"] = total
            return out, total is not None
        return out, False

    # holistic
    if obj is not None and _num(obj.get("score")) is not None:
        out["score"] = _num(obj.get("score"))
        return out, True
    # last-ditch: a bare "score": N anywhere (3.5 expands these fallbacks)
    m = re.search(r'"?score"?\s*[:=]\s*(-?\d+(?:\.\d+)?)', raw or "", re.I)
    if m:
        out["score"] = float(m.group(1))
        return out, True
    return out, False

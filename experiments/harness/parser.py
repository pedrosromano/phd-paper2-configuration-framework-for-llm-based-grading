"""Robust output parser (Phase 3.5).

Extracts a structured grade from raw model text and reports parse_ok. NEVER coerces
unparseable output to 0 (CLAUDE.md §8): score stays None and parse_ok=False, so the
pi extractable-rate is honest.

Layers (most reliable first):
  1. balanced JSON object, parsed leniently (json -> fix quotes/commas -> ast.literal_eval);
  2. for holistic, regex fallbacks anchored to a score/grade/mark CONTEXT (so "score higher
     than 1" or stray numbers do NOT match): `score: N`, `score is/of N`, `N/M`, `N out of M`.
Criterion sums criteria when total is absent; whole_exam returns the answers list.

pi = mean(parse_ok) over a set of runs (compute_pi).
"""

from __future__ import annotations

import ast
import json
import re

NUM = r"-?\d+(?:\.\d+)?"


def _strip_thinking(s: str) -> str:
    s = re.sub(r"<think>.*?</think>", "", s, flags=re.S | re.I)
    s = re.sub(r"<\|?thinking\|?>.*?<\|?/?thinking\|?>", "", s, flags=re.S | re.I)
    return s


def _loads_lenient(s: str):
    """json.loads, then fix common LLM JSON slips, then ast.literal_eval."""
    for attempt in (s,):
        try:
            return json.loads(attempt)
        except (json.JSONDecodeError, TypeError):
            pass
    fixed = re.sub(r",\s*([}\]])", r"\1", s)            # trailing commas
    try:
        return json.loads(fixed)
    except (json.JSONDecodeError, TypeError):
        pass
    try:                                                # single quotes / py literals
        v = ast.literal_eval(s)
        return v if isinstance(v, dict) else None
    except (ValueError, SyntaxError):
        return None


def _iter_json_objects(text: str):
    """Yield balanced {...} substrings (handles braces inside strings)."""
    i, n = 0, len(text)
    while i < n:
        if text[i] == "{":
            depth, in_str, esc = 0, False, False
            for j in range(i, n):
                c = text[j]
                if in_str:
                    if esc:
                        esc = False
                    elif c == "\\":
                        esc = True
                    elif c == '"':
                        in_str = False
                elif c == '"':
                    in_str = True
                elif c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        yield text[i:j + 1]
                        i = j
                        break
        i += 1


def _first_json(text: str) -> dict | None:
    t = re.sub(r"```(?:json)?", "", _strip_thinking(text or ""))
    for cand in _iter_json_objects(t):
        obj = _loads_lenient(cand)
        if isinstance(obj, dict):
            return obj
    return None


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _holistic_fallback(raw: str) -> float | None:
    t = _strip_thinking(raw or "")
    pats = [
        rf'["\']?(?:total|score|grade|mark|nota)["\']?\s*[:=]\s*["\']?({NUM})',  # score: N / "total": N
        rf'(?:score|grade|mark|nota)\s+(?:is|of|=|:)\s*({NUM})',                 # score is/of N
        rf'({NUM})\s*(?:/|out of)\s*\d+(?:\.\d+)?\s*(?:marks?|points?)?',         # N/M, N out of M
    ]
    for p in pats:
        m = re.search(p, t, re.I)
        if m:
            return _num(m.group(1))
    return None


def parse_output(raw: str, scope: str, decomposition: str) -> tuple[dict, bool]:
    """Parse per the prompt's (scope, decomposition). Returns
    ({score, per_criterion, answers}, parse_ok)."""
    out = {"score": None, "per_criterion": None, "answers": None}
    obj = _first_json(raw or "")

    if scope == "whole_exam":
        answers = obj.get("answers") if isinstance(obj, dict) else None
        if isinstance(answers, list) and answers:
            out["answers"] = answers
            return out, True
        return out, False

    if decomposition == "criterion":
        if isinstance(obj, dict):
            crits = obj.get("criteria") if isinstance(obj.get("criteria"), list) else None
            total = _num(obj.get("total"))
            if total is None and crits:                 # sum criterion scores
                vals = [_num(c.get("score")) for c in crits if isinstance(c, dict)]
                vals = [v for v in vals if v is not None]
                total = sum(vals) if vals else None
            out["per_criterion"] = crits
            out["score"] = total
            if total is not None:
                return out, True
        # criterion prompt but no JSON -> try a holistic-style total as last resort
        out["score"] = _holistic_fallback(raw)
        return out, out["score"] is not None

    # holistic
    if isinstance(obj, dict):
        s = _num(obj.get("score"))
        if s is None:
            s = _num(obj.get("total"))                  # model may have used "total"
        if s is not None:
            out["score"] = s
            return out, True
    out["score"] = _holistic_fallback(raw)
    return out, out["score"] is not None


def compute_pi(parse_ok_flags) -> float:
    """pi extractable-rate = fraction of runs yielding a parseable grade."""
    flags = list(parse_ok_flags)
    return round(sum(1 for f in flags if f) / len(flags), 4) if flags else 0.0

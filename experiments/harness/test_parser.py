"""Unit tests for the output parser (Phase 3.5). Run: .venv/bin/pytest experiments/harness/test_parser.py"""

import pytest

from experiments.harness.parser import compute_pi, parse_output

# ---- holistic: should parse (raw -> expected score) ----
HOLISTIC_OK = [
    ('{"score": 4}', 4.0),
    ('{"score": 4.5}', 4.5),
    ('```json\n{"score": 3}\n```', 3.0),
    ('Here is my grade:\n{"score": 2}\nThanks!', 2.0),
    ("{'score': 5}", 5.0),                                   # single quotes
    ('{"score": 4,}', 4.0),                                  # trailing comma
    ('<think>long chain of reasoning ...</think>\n{"score": 1}', 1.0),
    ('Score: 4/5', 4.0),
    ('I would give this 4 out of 5.', 4.0),
    ('The score is 3.', 3.0),
    ('{"score": 0}', 0.0),                                   # a real 0 IS valid (not a parse failure)
    ('blah blah {"reason": "ok", "score": 2} blah', 2.0),
]

# ---- holistic: should FAIL (parse_ok False, score None, never coerced to 0) ----
HOLISTIC_FAIL = [
    "I cannot grade this answer.",
    "The answer is partially correct, but a score higher than 1 would be generous.",  # no anchored number
    "",
    "This is a great answer.",
    "I'm sorry, I can't help with that.",
]


@pytest.mark.parametrize("raw,expected", HOLISTIC_OK)
def test_holistic_ok(raw, expected):
    out, ok = parse_output(raw, "question_by_question", "holistic")
    assert ok is True
    assert out["score"] == expected


@pytest.mark.parametrize("raw", HOLISTIC_FAIL)
def test_holistic_fail(raw):
    out, ok = parse_output(raw, "question_by_question", "holistic")
    assert ok is False
    assert out["score"] is None          # NEVER coerced to 0


def test_criterion_with_total():
    raw = '{"criteria": [{"criterion":"a","score":1},{"criterion":"b","score":2}], "total": 3}'
    out, ok = parse_output(raw, "question_by_question", "criterion")
    assert ok and out["score"] == 3.0 and len(out["per_criterion"]) == 2


def test_criterion_sums_when_total_missing():
    raw = '{"criteria": [{"criterion":"a","score":1},{"criterion":"b","score":1.5}]}'
    out, ok = parse_output(raw, "question_by_question", "criterion")
    assert ok and out["score"] == 2.5


def test_criterion_fail():
    out, ok = parse_output("no rubric scores here", "question_by_question", "criterion")
    assert ok is False and out["score"] is None


def test_whole_exam_ok():
    raw = '{"answers": [{"question_id":"7","score":2},{"question_id":"9","score":3}]}'
    out, ok = parse_output(raw, "whole_exam", "holistic")
    assert ok and len(out["answers"]) == 2


def test_whole_exam_fail():
    out, ok = parse_output('{"score": 2}', "whole_exam", "holistic")
    assert ok is False and out["answers"] is None


def test_pi():
    assert compute_pi([True, True, False, True]) == 0.75
    assert compute_pi([]) == 0.0
    assert compute_pi([False, False]) == 0.0

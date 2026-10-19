"""Recompute the agreement values and confidence intervals of
"Configuring LLM-Based Grading in Computer Science" from grades.csv.

grades.csv holds every grade the models gave on the public datasets (Mohler, SemEval, RIAYN) and on the two
validation datasets (SAF, HARMOGEN-R), one row per answer, configuration and repetition, with the human grade.
Grades are on a 0-1 scale (the question's maximum mark is 1). The answers' text is not included; it is in the
original datasets, under their own licences.

Metric: quadratic weighted kappa (QWK) on six ordered levels (0 to 5) of the mean of an answer's repeated grades
(halves go to the even level). A difference between two configurations is computed on the answers both graded,
with a 95% bootstrap interval from 10,000 resamples of the answers (seed 20260610).

Requires Python 3.10+, numpy and pandas.   Run:  python recompute.py
"""

import numpy as np
import pandas as pd

LEVELS, RESAMPLES, SEED = 6, 10_000, 20260610
W = np.subtract.outer(np.arange(LEVELS), np.arange(LEVELS)) ** 2.0


def kappas(counts):
    """QWK of each confusion matrix in a stack of shape (B, 6, 6): human grade in rows, model grade in columns."""
    n = counts.sum(axis=(1, 2))
    expected = counts.sum(axis=2)[:, :, None] * counts.sum(axis=1)[:, None, :] / n[:, None, None]
    return 1 - (counts * W).sum(axis=(1, 2)) / (expected * W).sum(axis=(1, 2))


def levels(x):
    """Six levels of a 0-1 score. x*5 is first rounded to 9 decimals, so that a mean that lies exactly halfway
    between two levels goes to the even one, whatever floating-point error its summation left."""
    return np.clip(np.round(np.round(np.asarray(x, dtype=float) * (LEVELS - 1), 9)), 0, LEVELS - 1).astype(int)


def per_answer(rows):
    """Mean model grade and the human grade of each answer."""
    return rows.groupby("item_id").agg(model=("model_grade", "mean"), human=("human_grade", "first"))


def qwk(rows):
    a = per_answer(rows)
    cells = levels(a.human) * LEVELS + levels(a.model)
    return float(kappas(np.bincount(cells, minlength=LEVELS ** 2).reshape(1, LEVELS, LEVELS).astype(float))[0])


def compare(base, other):
    """QWK(other) - QWK(base) on the answers both graded, with its 95% bootstrap interval, and N."""
    a, b = per_answer(base), per_answer(other)
    items = sorted(set(a.index) & set(b.index))
    a, b = a.loc[items], b.loc[items]
    ca = levels(a.human) * LEVELS + levels(a.model)
    cb = levels(a.human) * LEVELS + levels(b.model)
    n, size = len(items), LEVELS ** 2

    def two(idx):                                            # QWK of base and other for each row of resampled indices
        m = idx.shape[0]
        off = (np.arange(m) * size)[:, None]
        cnt = lambda c: np.bincount((off + c[idx]).ravel(), minlength=m * size).reshape(m, LEVELS, LEVELS)
        return kappas(cnt(ca).astype(float)), kappas(cnt(cb).astype(float))

    qa, qb = two(np.arange(n)[None, :])
    rng = np.random.default_rng(SEED)
    diffs = []
    for start in range(0, RESAMPLES, 500):
        ra, rb = two(rng.integers(0, n, (min(500, RESAMPLES - start), n)))
        diffs.append(rb - ra)
    lo, hi = np.percentile(np.concatenate(diffs), [2.5, 97.5])
    return float(qb[0] - qa[0]), float(lo), float(hi), n


def cell(d, **conditions):
    for column, value in conditions.items():
        d = d[d[column] == value]
    return d


def show(title, rows):
    print(f"\n{title}")
    print(pd.DataFrame(rows, columns=["model", "dataset", "N", "QWK before", "QWK after", "change", "95% CI"])
          .to_string(index=False))


def fmt(base, other):
    change, lo, hi, n = compare(base, other)
    items = sorted(set(base.item_id) & set(other.item_id))
    return [n, f"{qwk(base[base.item_id.isin(items)]):.3f}", f"{qwk(other[other.item_id.isin(items)]):.3f}",
            f"{change:+.3f}", f"[{lo:+.3f}, {hi:+.3f}]"]


def main():
    g = pd.read_csv("grades.csv", dtype={"question_id": str})
    main_ = g[g.experiment == "main"]
    base = dict(guidance="rubric_or_reference", instruction="strict", decomposition="holistic")

    rows = []                                                # reasoning off -> on, on the sampled answers (RQ1)
    for (model, ds), d in main_.groupby(["model", "dataset"]):
        on = cell(d, reasoning="on", **base)
        if on.empty:
            continue
        off = cell(d, reasoning="off", **base)
        rows.append([model, ds] + fmt(off[off.item_id.isin(set(on.item_id))], on))
    show("Reasoning: off (before) and on (after), with guidance, strict instruction", rows)

    rows = []                                                # no guidance -> rubric or reference answer (RQ2)
    for (model, ds), d in main_.groupby(["model", "dataset"]):
        none = cell(d, reasoning="off", guidance="none")
        if none.empty:
            continue
        rows.append([model, ds] + fmt(none, cell(d, reasoning="off", **base)))
    show("Evaluation guidance: none (before) and the rubric or reference answer (after), reasoning off", rows)

    rows = []                                                # the guide against each alternative (validation)
    v = g[g.experiment == "validation"]
    guide = dict(reasoning="off", guidance="rubric_or_reference", instruction="partial_credit", decomposition="holistic")
    alternatives = {"no guidance": dict(reasoning="off", guidance="none"),
                    "strict instruction": dict(guide, instruction="strict"),
                    "criterion scoring": dict(guide, decomposition="criterion"),
                    "reasoning on": dict(guide, reasoning="on")}
    for (ds, model), d in v.groupby(["dataset", "model"]):
        gd = cell(d, **guide)
        for name, conditions in alternatives.items():
            alt = cell(d, **conditions)
            if not alt.empty:
                rows.append([f"{model}, {name}", ds] + fmt(gd, alt))
    show("Validation: the guide (before) against each alternative (after), on SAF and HARMOGEN-R", rows)


if __name__ == "__main__":
    main()

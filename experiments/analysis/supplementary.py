"""Supplementary material (independent review, 2026-10-18): every prompt template, the models and their prices, the
share of unparseable outputs per configuration, and the values behind every figure of the paper.

Writes article/supplementary.tex, a standalone document built from the same engines as the paper (no hand-edited
numbers). Compile with:  cd article && latexmk -pdf supplementary.tex

  python -m experiments.analysis.supplementary
"""

from __future__ import annotations

import textwrap

import pandas as pd
import yaml

from experiments.analysis import guide_eval, instruction, make_phase5_tables as mpt, phase5, verification
from experiments.harness.cost_guard import load_pricing

OUT = phase5.REPO_ROOT / "article" / "supplementary.tex"
PROMPTS = phase5.REPO_ROOT / "experiments" / "configs" / "prompts.yaml"
PROMPTS_I = phase5.REPO_ROOT / "experiments" / "configs" / "prompts_instruction.yaml"
ROSTER = ["qwen3.5", "deepseek-v4-flash", "glm-5.1", "glm-5.1-or", "gpt-5.1", "claude-sonnet-4-6"]
MNAME = {"qwen3.5": "Qwen3.5-35B-A3B", "deepseek-v4-flash": "DeepSeek-V4-Flash", "glm-5.1": "GLM-5.1",
         "glm-5.1-or": "GLM-5.1 (OpenRouter)", "gpt-5.1": "GPT-5.1", "claude-sonnet-4-6": "Claude Sonnet 4.6"}
DNAME = {"mohler": "Mohler", "semeval": "SemEval", "riayn": "RIAYN", "ptcs": "PT-CS code", "ptcs-short": "PT-CS short"}


def _esc(s) -> str:
    return (str(s).replace("\\", r"\textbackslash{}").replace("&", r"\&").replace("%", r"\%").replace("_", r"\_")
            .replace("#", r"\#").replace("$", r"\$"))


def _sg(x, d=3) -> str:
    return f"{x:+.{d}f}".replace("-", "$-$") if pd.notna(x) else "--"


def _table(caption: str, cols: list[str], rows: list[list], spec: str) -> str:
    """A longtable in footnotesize (so that the widest tables stay inside the margins); p{} columns are set ragged
    right, so that a long cell wraps instead of running into the next column."""
    spec = spec.replace("p{", r">{\raggedright\arraybackslash}p{")
    head = " & ".join(cols) + r" \\ \hline"
    body = "\n".join(" & ".join(str(c) for c in r) + r" \\" for r in rows)
    return (r"\begingroup\footnotesize" + "\n" + rf"\begin{{longtable}}{{{spec}}}" + "\n" + rf"\caption{{{caption}}}\\"
            + "\n" + r"\hline" + "\n" + head + "\n" + r"\endfirsthead" + "\n" + r"\hline" + "\n" + head + "\n"
            + r"\endhead" + "\n" + body + "\n" + r"\hline" + "\n" + r"\end{longtable}" + "\n" + r"\endgroup" + "\n")


def prompts_section() -> str:
    b, ib = yaml.safe_load(PROMPTS.read_text()), yaml.safe_load(PROMPTS_I.read_text())
    blocks = [("Task, code", b["instruction"]["code"]), ("Task, short answer", b["instruction"]["short_answer"]),
              ("Guidance, rubric, strict instruction", b["grounding"]["rubric"]),
              ("Guidance, reference answer, strict instruction", b["grounding"]["reference"]),
              ("Guidance, rubric, partial credit (the guide)", ib["grounding"]["rubric"]),
              ("Guidance, reference answer, partial credit (the guide)", ib["grounding"]["reference"]),
              ("Question and answer", b["body"]["question_by_question"]),
              ("Output, one holistic score (the guide)", b["output"]["question_by_question__holistic"]),
              ("Output, a score per criterion", b["output"]["question_by_question__criterion"]),
              ("Output, partial credit with a justification first",
               ib["output"]["question_by_question__holistic__justified"]),
              ("Output, whole exam, one holistic score per question", b["output"]["whole_exam__holistic"])]
    out = [r"\section{Prompt templates}",
           "Every prompt is assembled from these blocks, in this order: the task, the guidance (omitted without "
           "guidance), the question and the student answer, and the output format. Placeholders written as "
           r"\texttt{\$name} are filled for each answer. A whole-exam prompt lists every question of the exam, each "
           "with its maximum score, rubric, and student answer, after the task block. In a shared conversation the first "
           "answer is sent with the task block and every later answer as the next turn, with its question, guidance, "
           "answer, and output format. Reasoning is switched on or off through each model's settings and is never "
           "mentioned in the prompt."]
    for name, text in blocks:
        lines = [w for ln in text.rstrip().splitlines() for w in (textwrap.wrap(ln, 105) or [""])]
        out += [rf"\subsection*{{{name}}}", r"\begin{Verbatim}[fontsize=\footnotesize]", *lines, r"\end{Verbatim}"]
    return "\n".join(out) + "\n"


def models_section() -> str:
    pr = load_pricing()
    eur = float(pr["eur_per_usd"])
    stores = [phase5._read(p) for p in (phase5.RUNS, phase5.INSTR, phase5.CONV, verification.VERIF)]
    counts = pd.concat([s[["model", "provider"]] for s in stores], ignore_index=True).value_counts()
    rows = []
    for m in ROSTER:
        p = pr["models"][m]
        rv = p.get("reasoning_values") or {}
        par, off, on = p.get("reasoning_param", ""), rv.get("off"), rv.get("on")
        if isinstance(off, dict):                      # OpenRouter: {"enabled": False} under "reasoning"
            k = next(iter(off))
            par, off, on = f"{par}.{k}", off[k], on[k]
        val = lambda v: str(v).lower() if isinstance(v, bool) else str(v)
        switch = rf"\texttt{{{_esc(par)}}}: {val(off)} / {val(on)}" if rv else "off only"
        n = int(counts[counts.index.get_level_values(0) == m].sum())
        rows.append([MNAME[m], rf"\texttt{{{_esc(p.get('model_id', m)).replace('/', '/' + chr(92) + 'allowbreak{}')}}}", p["provider"].replace("openrouter", "OpenRouter (Z.ai)")
                     .replace("deepinfra", "DeepInfra").replace("openai", "OpenAI").replace("anthropic", "Anthropic"),
                     switch, f"{p['input_per_1m_usd']:.2f}", f"{p['output_per_1m_usd']:.2f}", f"{n:,}"])
    cap = ("Models, backends, and prices. Prices are the providers' standard rates in US dollars per million input and "
           f"output tokens, converted at {eur:.2f} euros per dollar; batch discounts are not applied. Calls counts every "
           "graded call in the study and the validation. All calls were made between June and October 2026. Sampling, "
           "the same in every experiment: temperature 0 for the open models and Claude Sonnet 4.6 (GPT-5.1 accepts no "
           "temperature and samples at its fixed default); output capped at 4,096 tokens with reasoning off and 32,768 "
           "with reasoning on.")
    return (r"\section{Models, backends, and prices}" + "\n"
            + _table(cap, ["Model", "Served identifier", "Provider", "Reasoning switch (off / on)", "In", "Out", "Calls"],
                     rows, "p{2.6cm}p{3.3cm}p{1.9cm}p{3.6cm}rrr"))


def parse_section() -> str:
    d = pd.concat([phase5.prepare(phase5._read(p)).assign(store=n) for n, p in
                   [("main", phase5.RUNS), ("instruction", phase5.INSTR), ("conversation", phase5.CONV),
                    ("verification", verification.VERIF)]], ignore_index=True)
    d["unparsed"] = ~d.parse_ok.astype(bool)
    g = d.groupby(["model", "reasoning"]).agg(calls=("unparsed", "size"), unparsed=("unparsed", "sum"))
    g["share"] = g.unparsed / g.calls
    rows = [[MNAME.get(m, m), r, f"{int(x.calls):,}", int(x.unparsed), f"{100 * x.share:.2f}\\%"]
            for (m, r), x in g.iterrows()]
    cap = ("Unparseable outputs, by model and reasoning mode, over every configuration. With reasoning off, an "
           "unparseable output is left out of the metrics; with reasoning on, it takes the grade the same model gave that "
           "answer with reasoning off (in the validation, the guide's grade). With reasoning on, Qwen3.5's "
           "unparseable outputs are runs that reached the output limit without a grade.")
    return r"\section{Unparseable outputs}" + "\n" + _table(cap, ["Model", "Reasoning", "Calls", "Unparsed", "Share"], rows,
                                                             "llrrr")


def contrasts_sections() -> str:
    df = phase5.load_main()
    dc = mpt.dim_contrasts(df, mpt.INTERV if hasattr(mpt, "INTERV") else guide_eval._INTERV)
    out = []
    for fam, title, cap in [
        ("guidance", "Evaluation guidance (RQ2)",
         "Evaluation guidance (Fig. 2 of the paper): agreement (QWK) without guidance (before) and with it (after), on "
         "the answers graded both ways, and the change, per model and dataset, reasoning off. Holm marks the gains that stay significant after Holm's correction across the 15 combinations."),
        ("scope", "Scope (RQ3)", "Grading the whole exam in one call (after) against one call per question (before), "
         "Fig. 3 of the paper: agreement on the PT-CS code answers, reasoning off; Holm over the three models."),
        ("decomp", "Decomposition (RQ3)", "Scoring criterion by criterion (after) against one holistic score (before), "
         "Fig. 3 of the paper: agreement, reasoning off; Holm over the six combinations.")]:
        g = dc[dc.family == fam]
        rows = [[MNAME.get(r.model, r.model), DNAME.get(r.dataset, r.dataset), int(r.N), f"{r.QWK_A:.3f}",
                 f"{r.QWK_A + r.dQWK:.3f}", _sg(r.dQWK), f"[{_sg(r.lo)}, {_sg(r.hi)}]", "yes" if r.sig_holm else ""]
                for r in g.itertuples()]
        out.append(rf"\section{{{title}}}" + "\n" + _table(cap, ["Model", "Dataset", "N", "QWK before", "QWK after",
                                                                r"$\Delta$QWK", "95\\% CI", "Holm"], rows, "llrrrrlc"))
    return "\n".join(out)


def instruction_section() -> str:
    out = []
    lv = instruction.levels(instruction.load())
    lv = lv[lv.instruction.isin(["standard", "partial_credit", "partial_credit_justified"])]
    iname = {"standard": "strict", "partial_credit": "partial credit", "partial_credit_justified": "partial credit, "
             "justification first"}
    lrows = [[MNAME.get(r.model, r.model), DNAME.get("ptcs-short" if (r.dataset == "ptcs" and r.domain == "short_answer")
                                                   else r.dataset, r.dataset), iname[r.instruction], int(r.N),
              f"{r.QWK:.3f}", f"{r.zero_pct:.1f}\\%", f"{r.teacher_zero_pct:.1f}\\%"]
             for r in lv.sort_values(["model", "dataset", "domain", "instruction"]).itertuples()]
    out.append(r"\section{Grading instruction (follow-up experiment)}" + "\n" + _table(
        "Grading instruction (Fig. 6 of the paper): agreement (QWK) and share of grades that are exactly zero under each "
        "instruction, per model and dataset, reasoning off, with the teachers' share of zeros. GPT-5.1's strict cells "
        "are its runs of the main comparison.",
        ["Model", "Dataset", "Instruction", "N", "QWK", "Zeros", "Teachers' zeros"], lrows, "llp{3.2cm}rrrr"))
    ins = instruction.contrasts(instruction.load())
    rows = [[MNAME.get(r.model, r.model), DNAME.get("ptcs-short" if (r.dataset == "ptcs" and r.domain == "short_answer")
                                                  else r.dataset, r.dataset), _esc(r.contrast), int(r.N), _sg(r.dQWK),
             f"[{_sg(r.lo)}, {_sg(r.hi)}]", "yes" if r.sig_holm is True else ""] for r in ins.itertuples()]
    out.append(_table(
        "Grading instruction: the change in agreement between instructions, per model and dataset, reasoning off. Holm "
        "runs over the comparisons against the strict instruction.",
        ["Model", "Dataset", "Comparison", "N", r"$\Delta$QWK", "95\\% CI", "Holm"], rows, "llp{4.2cm}rrlc"))
    return "\n".join(out)


def rq4_section() -> str:
    from experiments.figures import phase6
    pts = phase6.rq4_points(phase5.load_main())
    rows = [[r.task, MNAME.get(r.model, r.model), r.reasoning, f"{r.QWK:.3f}", f"{r.eur_1000:.3f}"]
            for r in pts.itertuples()]
    cap = ("Cost and agreement by task (Fig. 4 of the paper): per model and reasoning mode, with guidance, one question "
           "per call, holistic, QWK averaged over the task's answer sets (short answers: Mohler, SemEval, PT-CS; code: "
           "RIAYN, PT-CS), on the answers every configuration graded, and the cost of 1000 grades in euros.")
    return r"\section{Models and cost (RQ4)}" + "\n" + _table(
        cap, ["Task", "Model", "Reasoning", "QWK", "Euros per 1000"], rows, "llcrr")


def conversation_section() -> str:
    from experiments.figures import phase6
    ce = phase6.conversation_effects()
    rows = [[MNAME.get(r.model, r.model), r.effect, int(r.N), _sg(r.mean, 4), f"[{_sg(r.lo, 4)}, {_sg(r.hi, 4)}]"]
            for r in ce.itertuples()]
    cap = ("Conversation state (Fig. 5 of the paper), PT-CS code, baseline configuration, grades as a fraction of the "
           "scale: the mean grade in a shared conversation minus that with a clean conversation per answer (over "
           "answers), and, within the shared conversation, the mean absolute and the mean signed change between the "
           "exam's own order and the reverse (over answer and repetition pairs), with 95\\% bootstrap intervals. "
           "Qwen3.5 and DeepSeek-V4-Flash: 80 exams, $k=5$; GLM-5.1: the first 20 of those exams, $k=3$.")
    return r"\section{Conversation state (RQ5)}" + "\n" + _table(
        cap, ["Model", "Effect", "N", "Mean", "95\\% CI"], rows, "llrrl")


def test1_section() -> str:
    t = guide_eval.within_model(guide_eval.rows())
    rows = []
    for r in t.sort_values(["model", "set", "kind"]).itertuples():
        lo, hi = r.ci95
        kind = r.kind
        if kind == "shared conversation":              # each exam in its own order and in reverse (two alternatives)
            kind += ", reverse order" if "inverse" in r.contrast else ", exam order"
        rows.append([MNAME.get(r.model, r.model), r.set, _esc(kind), int(r.N), _sg(r.dQWK), f"[{_sg(lo)}, {_sg(hi)}]",
                     f"{r.cost_x:.2f}", f"{r.sd_alt:.3f} / {r.sd_guide:.3f}"])
    cap = ("Test 1 (Fig. 9a of the paper): every other configuration of the same model against the guide's configuration, on the answers both "
           r"graded. $\Delta$QWK is the alternative minus the guide (95\% bootstrap interval, no correction); Cost is the "
           "alternative's cost per grade relative to the guide's; SD is the within-answer standard deviation across "
           "repetitions, alternative / guide.")
    return r"\section{Test 1 of the guide}" + "\n" + _table(
        cap, ["Model", "Dataset", "Alternative", "N", r"$\Delta$QWK", "95\\% CI", "Cost", "SD"], rows,
        "llp{3.1cm}rrlrl")


def test2_section() -> str:
    """The values behind panel (b) of the tests figure: every configuration without reasoning, per dataset, on the
    answers they all graded."""
    f = guide_eval.field(guide_eval.rows(), "B")
    lab = {"standard": "strict", "partial_credit": "partial credit", "partial_credit_justified": "partial credit, "
           "justification first", "guid": "guidance", "noguid": "no guidance", "qbq": "per question",
           "exam": "whole exam", "hol": "holistic", "crit": "per criterion"}
    rows = []
    for _, _, lbl in guide_eval.SETS:
        for r in f[f.set == lbl].sort_values("QWK", ascending=False).itertuples():
            _, _, ins, guid, sc, dec, _ = r.cfg.split("|")
            rows.append([lbl, MNAME.get(r.model, r.model), "; ".join(lab[x] for x in (guid, ins, sc, dec)),
                         int(r.N), f"{r.QWK:.3f}", f"{r.eur_1000:.3f}", "yes" if r.guide else ""])
    cap = ("Test 2 (Fig. 9b of the paper): every configuration graded without reasoning, per dataset, on the answers they all graded: "
           "agreement (QWK) and cost of 1000 grades in euros. Guide marks the guide's configuration.")
    return r"\section{Test 2 of the guide}" + "\n" + _table(
        cap, ["Dataset", "Model", "Configuration", "N", "QWK", "Euros", "Guide"], rows, "llp{5.2cm}rrrc")


def verification_section() -> str:
    t = verification.contrasts(verification.load())
    rows = []
    for r in t.itertuples():
        if r.kind == "guide":
            rows.append([MNAME.get(r.model, r.model), r.set.split(" (")[0], "guide", int(r.N), f"{r.QWK:.3f}", "", "",
                         f"{r.SD:.3f}", f"{100 * r.zeros:.0f}\\%"])
        else:
            rows.append([MNAME.get(r.model, r.model), r.set.split(" (")[0], _esc(r.kind), int(r.N), f"{r.QWK:.3f}",
                         _sg(r.dQWK), f"[{_sg(r.lo)}, {_sg(r.hi)}]", f"{r.SD:.3f}", f"{100 * r.zeros:.0f}\\%"])
    ins = verification.instructors()
    cap = ("Validation of the guide on SAF and HARMOGEN-R, which played no part in building it (Fig. 10 of the paper), "
           r"every configuration: agreement (QWK), the change against the guide on the same answers ($\Delta$QWK, 95\% "
           "bootstrap interval), the within-answer standard deviation across the three repetitions, and the share of "
           "grades that are exactly zero. On HARMOGEN-R the four instructors agree with each other at "
           f"{ins['pairs_min']:.3f} to {ins['pairs_max']:.3f} QWK (every pair) and give zero to "
           f"{100 * ins['gold_zeros']:.0f}\\% of the answers.")
    return r"\section{Validation of the guide}" + "\n" + _table(
        cap, ["Model", "Dataset", "Configuration", "N", "QWK", r"$\Delta$QWK", "95\\% CI", "SD", "Zeros"], rows,
        "lllrrrllr")


def main() -> int:
    doc = [r"\documentclass[10pt]{article}", r"\usepackage[margin=2cm]{geometry}", r"\usepackage[T1]{fontenc}",
           r"\usepackage{array,longtable,fancyvrb}", r"\usepackage{mathptmx}",
           r"\title{Configuring LLM-Based Grading in Computer Science: Supplementary Material}", r"\date{}",
           r"\begin{document}", r"\maketitle",
           "This supplement gives the prompt templates, the models and their prices, the share of unparseable outputs, and "
           "tables with the values behind the figures of the paper. Every value is computed from the logged runs, with the "
           "metrics and bootstrap of the paper (QWK on six levels of the mean of the repeated grades; 10,000 resamples of "
           r"the answers; 95\% intervals). The values of Fig.~1 are in Table~3 of the paper; Figs.~2 to~6, 9, and~10 "
           "have their own tables below, each naming its figure; Figs.~7 and~8 show the guide and its prompt, whose "
           "templates are given in Section~1.",
           prompts_section(), models_section(), parse_section(), contrasts_sections(), rq4_section(),
           conversation_section(), instruction_section(), test1_section(), test2_section(), verification_section(), r"\end{document}"]
    OUT.write_text("\n\n".join(doc) + "\n")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

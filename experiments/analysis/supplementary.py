"""Supplementary material (independent review, 2026-10-18): every prompt template, the models and their prices, the
share of unparseable outputs per configuration, and the values behind every figure of the paper.

Writes article/supplementary.tex, a standalone document built from the same engines as the paper (no hand-edited
numbers). Compile with:  cd article && latexmk -pdf supplementary.tex

  python -m experiments.analysis.supplementary
"""

from __future__ import annotations

import re
import textwrap

import pandas as pd
import yaml

from experiments.analysis import guide_eval, instruction, make_phase5_tables as mpt, phase5, verification
from experiments.harness.cost_guard import load_pricing

OUT = phase5.REPO_ROOT / "article" / "supplementary.tex"
PROMPTS = phase5.REPO_ROOT / "experiments" / "configs" / "prompts.yaml"
PROMPTS_I = phase5.REPO_ROOT / "experiments" / "configs" / "prompts_instruction.yaml"
PROMPTS_V = phase5.REPO_ROOT / "experiments" / "configs" / "prompts_instruction_variants.yaml"
PROMPTS_V2 = phase5.REPO_ROOT / "experiments" / "configs" / "prompts_instruction_variants2.yaml"
PROMPTS_S = phase5.REPO_ROOT / "experiments" / "configs" / "prompts_instruction_substance.yaml"
ROSTER = ["qwen3.5", "deepseek-v4-flash", "glm-5.1", "glm-5.1-or", "gpt-5.1", "claude-sonnet-4-6"]
MNAME = {"qwen3.5": "Qwen3.5-35B-A3B", "deepseek-v4-flash": "DeepSeek-V4-Flash", "glm-5.1": "GLM-5.1",
         "glm-5.1-or": "GLM-5.1 (OpenRouter)", "gpt-5.1": "GPT-5.1", "claude-sonnet-4-6": "Claude Sonnet 4.6"}
DNAME = {"mohler": "Mohler", "semeval": "SemEval", "riayn": "RIAYN", "ptcs": "PT-CS code", "ptcs-short": "PT-CS short"}
# The paper's figure and table numbers, read from article/main.aux after a build, so that "Fig. N of the paper" follows
# the paper (the follow-up diagram became Fig. 1 on 2026-11-05 and shifted every other figure by one). The defaults are
# the numbers of that version; a mismatch with the aux file is printed.
AUX = phase5.REPO_ROOT / "article" / "main.aux"
_NUM = {"fig:promptexp": 1, "fig:rq1": 2, "fig:rq2": 3, "fig:rq3": 4, "fig:costquality": 5, "fig:conversation": 6,
        "fig:rq6": 7, "fig:frameworkdiagram": 8, "fig:guideprompt": 9, "fig:guiderefs": 10}


def _n(label: str) -> str:
    try:
        m = re.search(r"\\newlabel\{" + re.escape(label) + r"\}\{\{(\d+)\}", AUX.read_text())
    except FileNotFoundError:
        m = None
    if m and int(m.group(1)) != _NUM[label]:
        print(f"  note: {label} is {m.group(1)} in main.aux (default {_NUM[label]})")
    return m.group(1) if m else str(_NUM[label])


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


_KEEP = ("RUBRIC:", "REFERENCE", "QUESTION", "STUDENT", "$", "{", "[", "- ")


def _reflow(text: str, width: int = 100) -> list[str]:
    """Verbatim prompt text for the page: the YAML templates are hard-wrapped at about 115 characters, wider than the
    page, so sentences are joined back into paragraphs and wrapped at `width`; labels, placeholders, JSON lines and
    blank lines stay on their own lines."""
    out, para = [], []
    for ln in text.rstrip().splitlines():
        if not ln.strip() or ln.lstrip().startswith(_KEEP):
            if para:
                out += textwrap.wrap(" ".join(para), width)
                para = []
            out += textwrap.wrap(ln, width) or [""]
        else:
            para.append(ln.strip())
    if para:
        out += textwrap.wrap(" ".join(para), width)
    return out


def prompts_section() -> str:
    b, ib = yaml.safe_load(PROMPTS.read_text()), yaml.safe_load(PROMPTS_I.read_text())
    cw = yaml.safe_load(PROMPTS_V2.read_text())["partial_credit_teacher_credit_first"]
    blocks = [("Task, code", b["instruction"]["code"]), ("Task, short answer", b["instruction"]["short_answer"]),
              ("Guidance, rubric, strict prompt", b["grounding"]["rubric"]),
              ("Guidance, reference answer, strict prompt", b["grounding"]["reference"]),
              ("Guidance, rubric, partial credit (the guide on short answers)", ib["grounding"]["rubric"]),
              ("Guidance, reference answer, partial credit (the guide on short answers)", ib["grounding"]["reference"]),
              ("Guidance, rubric, code prompt (the guide on code)", cw["grounding"]["rubric"]),
              ("Question and answer", b["body"]["question_by_question"]),
              ("Output, one holistic score (the guide on short answers)", b["output"]["question_by_question__holistic"]),
              ("Output, code prompt: what earns marks first (the guide on code)",
               cw["output"]["question_by_question__holistic"]),
              ("Output, a score per criterion", b["output"]["question_by_question__criterion"]),
              ("Output, partial credit with a justification first",
               ib["output"]["question_by_question__holistic__justified"]),
              ("Output, whole exam, one holistic score per question", b["output"]["whole_exam__holistic"])]
    out = [r"\section{Prompt templates}\label{sec:prompts}",
           "Every prompt is assembled from these blocks, in this order: the task, the guidance (omitted without "
           "guidance), the question and the student answer, and the output format. Placeholders written as "
           r"\texttt{\$name} are filled for each answer. A whole-exam prompt lists every question of the exam, each "
           "with its maximum score, rubric, and student answer, after the task block. In a shared conversation the first "
           "answer is sent with the task block and every later answer as the next turn, with its question, guidance, "
           "answer, and output format. Reasoning is switched on or off through each model's settings and is never "
           "mentioned in the prompt."]
    for name, text in blocks:
        lines = _reflow(text)
        out += [rf"\subsection*{{{name}}}", r"\begin{Verbatim}[fontsize=\footnotesize]", *lines, r"\end{Verbatim}"]
    return "\n".join(out) + "\n"


# Every run store (2026-11-06: the follow-up's code-prompt runs and the validation's code-prompt runs were missing
# from the call and unparsed counts, which say "every graded call" and "every configuration").
_STORES = {"main": phase5.RUNS, "instruction": phase5.INSTR, "conversation": phase5.CONV,
           "verification": verification.VERIF,
           "instruction_substance": phase5.REPO_ROOT / "data" / "processed" / "runs" / "instruction_substance.jsonl",
           "verification_variant": verification.VARIANT}


def models_section() -> str:
    pr = load_pricing()
    eur = float(pr["eur_per_usd"])
    stores = [phase5._read(p) for p in _STORES.values()]
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
           "graded call in the study and the validation; on PT-CS, the whole-exam and conversation calls also grade "
           "the answers of those exams that have no grade. All calls were made between June and November 2026. "
           "Sampling, "
           "the same in every experiment: temperature 0 for the open models and Claude Sonnet 4.6 (GPT-5.1 was called "
           "without a temperature setting and samples at its default); output capped at 4,096 tokens with reasoning off and 32,768 "
           "with reasoning on.")
    return (r"\section{Models, backends, and prices}" + "\n"
            + _table(cap, ["Model", "Served identifier", "Provider", "Reasoning switch (off / on)", "In", "Out", "Calls"],
                     rows, "p{2.6cm}p{3.3cm}p{1.9cm}p{3.6cm}rrr"))


def parse_section() -> str:
    d = pd.concat([phase5.prepare(phase5._read(p)).assign(store=n) for n, p in _STORES.items()], ignore_index=True)
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


def rq1_section() -> str:
    """Reasoning off versus on (RQ1): the values behind Fig. 2 of the paper, from make_phase5_tables.rq1_cells (the
    paper's Table 3 until 2026-11-05, when Pedro moved it here to bring the paper down to 19 pages)."""
    df = phase5.load_main()
    interv = set(pd.read_parquet(phase5.REPO_ROOT / "data" / "processed" / "_ptcs_strata.parquet")
                 .query("stratum=='intervened'").item_id)
    cells = mpt.rq1_cells(df, interv)
    order = [("mohler", "short_answer", "Mohler"), ("semeval", "short_answer", "SemEval"), ("riayn", "code", "RIAYN"),
             ("ptcs", "code", "PT-CS code"), ("ptcs", "short_answer", "PT-CS short")]
    rows = []
    for ds, dom, lbl in order:
        for m in ["qwen3.5", "glm-5.1", "deepseek-v4-flash", "gpt-5.1"]:
            c = cells[(cells.dataset == ds) & (cells.domain == dom) & (cells.model == m)]
            if c.empty:
                continue
            c = c.iloc[0]
            dq = f"\\textbf{{{_sg(c.dQWK)}}}" if c.sig else _sg(c.dQWK)
            sd = (f"{c.SDk_off:.3f} $\\to$ \\textbf{{{c.SDk_on:.3f}}}" if (c.sd_sig_up or c.sd_sig_down)
                  else f"{c.SDk_off:.3f} $\\to$ {c.SDk_on:.3f}")
            rows.append([lbl, MNAME.get(m, m), int(c.N), f"{c.QWK_off:.3f}", dq, f"[{_sg(c.lo)}, {_sg(c.hi)}]",
                         "yes" if c.sig_holm else "", f"{c.prem_x:.0f}$\\times$", sd])
    cap = ("Reasoning off versus on (RQ1; Fig.~" + _n("fig:rq1") + " of the paper), per model and dataset. "
           r"$\Delta$QWK is QWK with reasoning on minus QWK off, on the N sampled answers; a reasoning run that reached "
           "the output limit without returning a grade counts with the grade the same model gave that answer with "
           r"reasoning off. Bold marks a 95\% bootstrap interval that excludes zero; Holm marks the gains that stay "
           "significant after Holm's correction for the 20 comparisons. Tokens is how many times more output tokens "
           "reasoning used, on all paired answers. SD is the mean within-answer standard deviation across repetitions "
           "(lower is more consistent), on the model's own grades (runs that fell back are left out); bold marks a "
           r"change whose 95\% bootstrap interval excludes zero.\label{tab:rq1supp}")
    return r"\section{Reasoning (RQ1)}" + "\n" + _table(
        cap, ["Dataset", "Model", "N", "QWK off", r"$\Delta$QWK", "95\\% CI", "Holm", "Tokens", "SD off $\\to$ on"],
        rows, "llrrrlcrl")


def contrasts_sections() -> str:
    df = phase5.load_main()
    dc = mpt.dim_contrasts(df, mpt.INTERV if hasattr(mpt, "INTERV") else guide_eval._INTERV)
    out = []
    for fam, title, cap in [
        ("guidance", "Evaluation guidance (RQ2)",
         "Evaluation guidance (Fig. " + _n("fig:rq2") + " of the paper): agreement (QWK) without guidance (before) and with it (after), on "
         "the answers graded both ways, and the change, per model and dataset, reasoning off. Holm marks the gains that stay significant after Holm's correction across the 15 combinations."),
        ("scope", "Scope (RQ3)", "Grading the whole exam in one call (after) against one call per question (before), "
         "Fig. " + _n("fig:rq3") + " of the paper: agreement on the PT-CS code answers, reasoning off; Holm over the three models."),
        ("decomp", "Decomposition (RQ3)", "Scoring criterion by criterion (after) against one holistic score (before), "
         "Fig. " + _n("fig:rq3") + " of the paper: agreement, reasoning off; Holm over the six combinations.")]:
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
    lab = lambda r: ("GLM-5.1 (DeepInfra)" if (r.model == "glm-5.1-or" and r.instruction == "standard" and r.dataset == "ptcs")
                     else MNAME.get(r.model, r.model))      # GLM-5.1's strict PT-CS code cells are the main DeepInfra runs
    lrows = [[lab(r), DNAME.get("ptcs-short" if (r.dataset == "ptcs" and r.domain == "short_answer")
                                                   else r.dataset, r.dataset), iname[r.instruction], int(r.N),
              f"{r.QWK:.3f}", f"{r.zero_pct:.1f}\\%", f"{r.teacher_zero_pct:.1f}\\%"]
             for r in lv.sort_values(["model", "dataset", "domain", "instruction"]).itertuples()]
    dr = instruction.drift(instruction.load())
    dr = dr[dr.model.isin(["qwen3.5", "deepseek-v4-flash"])]
    gp = instruction.glm_providers()
    out.append(r"\section{The prompt (follow-up experiment, first part)}" + "\n" + _table(
        "The prompt (Fig. " + _n("fig:rq6") + " of the paper, light and hatched bars): agreement (QWK) and share of grades that are "
        "exactly zero under the strict and the partial-credit prompt, per model and dataset, reasoning off, with the "
        "human graders' share of zeros; the values of the code prompt (the solid bars) are in "
        "Section~\\ref{sec:zerocollapse}. Qwen3.5 and "
        "DeepSeek-V4-Flash graded the strict prompt again in this experiment, as a control, and their strict "
        "cells are those runs: their QWK stayed within "
        f"{(dr.QWK_rerun - dr.QWK_original).abs().max():.3f} of the strict runs of the main comparison, with the same "
        f"grade in {dr.same_grade_pct.min():.0f} to {dr.same_grade_pct.max():.0f}\\% of the answer and repetition "
        "pairs. GPT-5.1's strict cells are its runs of the main comparison. GLM-5.1's partial-credit runs went through "
        "OpenRouter; its strict cells are the OpenRouter runs on RIAYN and the DeepInfra runs of the main comparison "
        "on PT-CS code. On RIAYN, where it graded the strict prompt on both providers, the QWK was "
        f"{gp['qwk_deepinfra']:.3f} (DeepInfra) and {gp['qwk_openrouter']:.3f} (OpenRouter), and two runs of the same "
        f"answer gave the same grade in {100 * gp['same_across']:.0f}\\% of the pairs across providers, against "
        f"{100 * gp['same_deepinfra']:.0f}\\% and {100 * gp['same_openrouter']:.0f}\\% within each.",
        ["Model", "Dataset", "Prompt", "N", "QWK", "Zeros", "Human graders' zeros"], lrows, "llp{3.2cm}rrrr"))
    ins = instruction.contrasts(instruction.load())
    rows = [[MNAME.get(r.model, r.model), DNAME.get("ptcs-short" if (r.dataset == "ptcs" and r.domain == "short_answer")
                                                  else r.dataset, r.dataset), _esc(r.contrast), int(r.N), _sg(r.dQWK),
             f"[{_sg(r.lo)}, {_sg(r.hi)}]", "yes" if r.sig_holm is True else ""] for r in ins.itertuples()]
    out.append(_table(
        "The prompt: the change in agreement between prompts, per model and dataset, reasoning off. Holm "
        "runs over the comparisons against the strict prompt.",
        ["Model", "Dataset", "Comparison", "N", r"$\Delta$QWK", "95\\% CI", "Holm"], rows, "llp{4.2cm}rrlc"))
    return "\n".join(out)


def zero_collapse_section() -> str:
    """The prompt engineering against the zero-collapse (follow-up, 2026-11-05): values from zero_collapse."""
    from experiments.analysis import zero_collapse as ZC
    out = [r"\section{Prompt engineering against the zero-collapse (follow-up experiment)}\label{sec:zerocollapse}",
           "These tables give the values behind the second part of the follow-up experiment (Fig.~" + _n("fig:promptexp")
           + " of the paper). A zero is counted as undeserved when the human graders gave the answer at least 20\\% of "
           "its marks. The candidate prompts were developed on PT-CS code and RIAYN with Qwen3.5 and DeepSeek-V4-Flash, "
           "each against the partial-credit prompt graded in the same batch; all five models then graded every set of "
           "the study that has a rubric with the code prompt."]
    dg = ZC.diagnosis()
    out.append(_table(
        "Written justifications behind undeserved zeros (partial credit with a justification first; Qwen3.5 and "
        "DeepSeek-V4-Flash on PT-CS code and RIAYN): the share that name something the answer does correctly, and the "
        "reasons given for withholding every mark (keyword counts; one justification can give several reasons).",
        ["Justifications", "Name something correct"] + [k[0].upper() + k[1:] for k in ZC.REASONS],
        [[dg["runs"], f"{dg['names_something_correct']:.0f}\\%"] + [f"{dg[k]:.0f}\\%" for k in ZC.REASONS]],
        "rrp{3.6cm}p{3.0cm}p{3.0cm}"))
    t = ZC.pilot()
    lab = dict((k, l) for k, l, _ in ZC.WORDINGS) | {"partial_credit": "partial-credit prompt (control)"}
    rows = [[MNAME.get(r.model, r.model), DNAME.get(r.dataset, r.dataset), _esc(lab[r.wording]),
             f"{r.zeros:.1f}\\%", f"{r.undeserved:.1f}\\%", f"{r.QWK:.3f}",
             "" if pd.isna(r.dQWK) else f"{_sg(r.dQWK)} [{_sg(r.lo)}, {_sg(r.hi)}]", f"{r.MAE:.3f}", f"{r.out_tok:.0f}"]
            for r in t.itertuples()]
    out.append(_table(
        "Development (PT-CS code and RIAYN): each candidate prompt against the partial-credit prompt graded in "
        "the same batch. Round 1 tried five candidates, A to E, each applying one technique against a reason in the "
        "justifications; round 2, designed after round 1, joined C and E into the code prompt. $\\Delta$QWK is the "
        "candidate minus the control, with its 95\\% interval.",
        ["Model", "Dataset", "Prompt", "Zeros", "Undeserved zeros", "QWK", "$\\Delta$QWK [95\\% CI]", "MAE",
         "Output tokens"], rows, "llp{2.9cm}rp{1.4cm}rp{2.6cm}rp{1.05cm}"))
    a = ZC.all_models()
    dn = lambda r: "PT-CS short" if (r.dataset == "ptcs" and r.domain == "short_answer") else DNAME.get(r.dataset, r.dataset)
    out.append(_table(
        "The code prompt against the partial-credit prompt, all five models, every set of the study with a rubric (the solid "
        "bars of Fig. " + _n("fig:rq6") + " of the paper). GLM-5.1 "
        "has no partial-credit cell on the PT-CS short answers and is compared there with the strict prompt. The "
        "guide uses the code prompt on code only.",
        ["Model", "Dataset", "Against", "QWK", "$\\Delta$QWK [95\\% CI]", "Zeros", "MAE", "Cost"],
        [[MNAME.get(r.model, r.model), dn(r), r.against, f"{r.QWK_before:.3f} $\\to$ {r.QWK_after:.3f}",
          f"{_sg(r.dQWK)} [{_sg(r.lo)}, {_sg(r.hi)}]", f"{r.zeros_before:.1f} $\\to$ {r.zeros_after:.1f}\\%",
          f"{r.MAE_before:.3f} $\\to$ {r.MAE_after:.3f}", f"{r.cost_x:.2f}$\\times$"]
         for r in a.sort_values(["domain", "dataset", "model"]).itertuples()], "llp{1.6cm}rp{2.6cm}rrr"))
    hz = ZC.human_zeros()
    out.append(_table(
        "Whose zeros are deserved on Mohler (strict prompt, reasoning off): on the answers each model scored zero, the "
        "share the first grader scored 0 or 1 of 5 and the share both graders scored 2.5 or more; the first grader "
        f"gave zero to {hz['mohler_grader_zero_pct'][0]:.1f}\\% of all answers and the second to "
        f"{hz['mohler_grader_zero_pct'][1]:.1f}\\%, and {hz['mohler_spreadsheet_errors']} answers in the public release "
        "are spreadsheet errors (\\texttt{\\#NAME?}), which every model scores zero.",
        ["Model", "Zeros", "First grader 0--1", "Both graders 2.5+"],
        [[MNAME[r.model], f"{r.zeros:.1f}\\%", f"{r.first_grader_0_or_1:.0f}\\%", f"{getattr(r, '_4'):.0f}\\%"]
         for r in hz["mohler"].itertuples()], "lrrr"))
    v = yaml.safe_load(PROMPTS_V.read_text())
    s = yaml.safe_load(PROMPTS_S.read_text())
    tx = [(lab["partial_credit_substance"], s["grounding"]["rubric"])]
    tx += [(lab[k], v[k]["grounding"]["rubric"] + ("\n" + v[k]["output"]["question_by_question__holistic"]
                                                    if "output" in v[k] else ""))
           for k in ["partial_credit_items", "partial_credit_credit_first", "partial_credit_subtractive", "partial_credit_teacher"]]
    out.append("The round-1 candidate prompts, verbatim (the round-2 prompt is the code prompt of Section~\\ref{sec:prompts}):")
    for name, text in tx:
        lines = _reflow(text)
        out += [rf"\subsection*{{{_esc(name[0].upper() + name[1:])}}}", r"\begin{Verbatim}[fontsize=\footnotesize]", *lines,
                r"\end{Verbatim}"]
    return "\n".join(out)


def rq4_section() -> str:
    from experiments.figures import phase6
    pts = phase6.rq4_points(phase5.load_main())
    rows = [[r.task, MNAME.get(r.model, r.model), r.reasoning, f"{r.QWK:.3f}", f"{r.eur_1000:.3f}"]
            for r in pts.itertuples()]
    cap = ("Cost and agreement by task (Fig. " + _n("fig:costquality") + " of the paper): per model and reasoning mode, with guidance, one question "
           "per call, holistic, QWK averaged over the task's answer sets (short answers: Mohler, SemEval, PT-CS; code: "
           "RIAYN, PT-CS), on the answers every configuration graded, and the cost of 1000 grades in euros.")
    return r"\section{Models and cost (RQ4)}" + "\n" + _table(
        cap, ["Task", "Model", "Reasoning", "QWK", "Euros per 1000"], rows, "llcrr")


def conversation_section() -> str:
    from experiments.figures import phase6
    ce = phase6.conversation_effects()
    rows = [[MNAME.get(r.model, r.model), r.effect, int(r.N), _sg(r.mean, 4), f"[{_sg(r.lo, 4)}, {_sg(r.hi, 4)}]"]
            for r in ce.itertuples()]
    cap = ("Conversation state (Fig. " + _n("fig:conversation") + " of the paper), PT-CS code, baseline configuration, grades as a fraction of the "
           "scale: the mean grade in a shared conversation minus that with a clean conversation per answer (over "
           "answers), and, within the shared conversation, the mean absolute and the mean signed change between the "
           "exam's own order and the reverse (over answer and repetition pairs), with 95\\% bootstrap intervals that "
           "resample whole exams. The 97 exams of PT-CS, every code answer, $k=5$, for the three open models; N is "
           "the number of exams.")
    return r"\section{Conversation state (RQ5)}" + "\n" + _table(
        cap, ["Model", "Effect", "N", "Mean", "95\\% CI"], rows, "llrrl")


def references_section() -> str:
    """The values behind the guide's figure (Pedro's review of 2026-11-06): per model and dataset, the guide against
    the baseline and against reasoning on, on the study's data and on the validation datasets."""
    r = guide_eval.references()
    nm = {"baseline": "baseline", "reasoning on": "reasoning on"}
    _eur = lambda v: f"{v:.3f}" if v < 1 else f"{v:.2f}"
    rows = [[x.set, MNAME.get(x.model, x.model), nm[x.ref], int(x.N),
             f"{x.q_ref:.3f} / {x.q_guide:.3f}", _sg(x.dQWK), f"[{_sg(x.lo)}, {_sg(x.hi)}]",
             f"{x.sd_ref:.3f} / {x.sd_guide:.3f}", f"{_eur(x.eur_ref)} / {_eur(x.eur_guide)}"]
            for x in r.itertuples()]
    cap = ("The guide against the baseline configuration (strict prompt, reasoning off) and against reasoning on (Fig. "
           + _n("fig:guiderefs") + " of the paper), per model and dataset, on the answers both graded (with reasoning "
           r"on, the sampled answers). QWK is the reference's / the guide's on those answers; $\Delta$QWK is the reference "
           r"minus the guide, with its 95\% bootstrap interval (no correction); SD is the within-answer standard "
           "deviation across repetitions, reference / guide, on the model's own grades; EUR is the cost per 1000 "
           "grades, reference / guide. SAF and HARMOGEN-R are the validation datasets; the others are the tests. On "
           "the validation datasets, reasoning on was graded with the partial-credit prompt.")
    return r"\section{The guide against the baseline and reasoning on}\label{sec:guiderefs}" + "\n" + _table(
        cap, ["Dataset", "Model", "Reference", "N", "QWK", r"$\Delta$QWK", "95\\% CI", "SD", "EUR"],
        rows, "lllrrrlrr")


def test1_section() -> str:
    t = guide_eval.within_model(guide_eval.rows())
    rows = []
    for r in t.sort_values(["model", "set", "kind"]).itertuples():
        lo, hi = r.ci95
        kind = KIND.get(r.kind, r.kind)
        if kind == "shared conversation":              # each exam in its own order and in reverse (two alternatives)
            kind += ", reverse order" if "inverse" in r.contrast else ", exam order"
        rows.append([MNAME.get(r.model, r.model), r.set, _esc(kind), int(r.N), _sg(r.dQWK), f"[{_sg(lo)}, {_sg(hi)}]",
                     f"{r.cost_x:.2f}", f"{r.sd_alt:.3f} / {r.sd_guide:.3f}"])
    cap = ("Every configuration against the guide, within each model (the comparison the paper summarises in one "
           "sentence after Fig. " + _n("fig:guiderefs") + "): every other configuration of the same model against the guide's configuration, on the answers both "
           r"graded. $\Delta$QWK is the alternative minus the guide (95\% bootstrap interval, no correction); Cost is the "
           "alternative's cost per grade relative to the guide's, with both priced at the guide's provider rates (for "
           "GLM-5.1, OpenRouter's) and a whole-exam call's cost split over its questions; SD is the within-answer "
           "standard deviation across repetitions, alternative / guide, on the model's own grades (reasoning runs that "
           "fell back to the reasoning-off grade are left out). The strict prompt is the strict runs of the main "
           "comparison.")
    return r"\section{The guide against every other configuration of the same model}" + "\n" + _table(
        cap, ["Model", "Dataset", "Alternative", "N", r"$\Delta$QWK", "95\\% CI", "Cost", "SD"], rows,
        "llp{3.1cm}rrlrl")


def test2_section() -> str:
    """The values behind panel (b) of the tests figure: every configuration without reasoning, per dataset, on the
    answers they all graded."""
    f = guide_eval.field(guide_eval.rows(), "B")
    lab = {"standard": "strict", "partial_credit": "partial credit", "partial_credit_justified": "partial credit, "
           "justification first", "partial_credit_teacher_credit_first": "code prompt",
           "guid": "guidance", "noguid": "no guidance", "qbq": "per question",
           "exam": "whole exam", "hol": "holistic", "crit": "per criterion"}
    rows = []
    for _, _, lbl in guide_eval.SETS:
        for r in f[f.set == lbl].sort_values("QWK", ascending=False).itertuples():
            _, _, ins, guid, sc, dec, _ = r.cfg.split("|")
            rows.append([lbl, MNAME.get(r.model, r.model), "; ".join(lab[x] for x in (guid, ins, sc, dec)),
                         int(r.N), f"{r.QWK:.3f}", f"{r.eur_1000:.3f}", "yes" if r.guide else ""])
    cap = ("Every configuration graded without reasoning, of any model, per dataset, on the answers they all graded "
           "(the comparison across models summarised in one sentence after Fig. " + _n("fig:guiderefs") + " of the paper): "
           "agreement (QWK) and cost of 1000 grades in euros. Guide marks the guide's configuration.")
    return r"\section{The guide against the configurations of every model}" + "\n" + _table(
        cap, ["Dataset", "Model", "Configuration", "N", "QWK", "Euros", "Guide"], rows, "llp{5.2cm}rrrc")


# display names of the validation alternatives (internal kind keys keep the old "wording" names)
KIND = {"earlier wording": "partial-credit prompt (code)", "code wording on short answers": "code prompt (short answers)",
        "strict instruction": "strict prompt"}


def verification_section() -> str:
    t = verification.contrasts(verification.load())
    rows = []
    for r in t.itertuples():
        if r.kind == "guide":
            rows.append([MNAME.get(r.model, r.model), r.set.split(" (")[0], "guide", int(r.N), f"{r.QWK:.3f}", "", "",
                         "", f"{r.SD:.3f}", f"{100 * r.zeros:.0f}\\%"])
        else:
            ni = "" if r.kind == "reasoning on" else ("yes" if r.noninferior else "no")
            rows.append([MNAME.get(r.model, r.model), r.set.split(" (")[0], _esc(KIND.get(r.kind, r.kind)), int(r.N), f"{r.QWK:.3f}",
                         _sg(r.dQWK), f"[{_sg(r.lo)}, {_sg(r.hi)}]", ni, f"{r.SD:.3f}", f"{100 * r.zeros:.0f}\\%"])
    ins = verification.instructors()
    cap = ("Validation of the guide on SAF and HARMOGEN-R, which played no part in building it (lower part of Fig. " + _n("fig:guiderefs") + " of the paper), "
           r"every configuration: agreement (QWK), the change against the guide on the same answers ($\Delta$QWK, 95\% "
           "bootstrap interval), whether the guide is non-inferior to the alternative (Non-inf.: the upper bound of the "
           r"90\% interval of $\Delta$QWK is below the $+0.05$ margin fixed in advance; alternatives without reasoning), "
           "the within-answer standard deviation across the three repetitions, and the share of "
           "grades that are exactly zero. On HARMOGEN-R, which is code, the guide and its score per criterion use the code "
           "prompt, and reasoning on was run with the partial-credit prompt. On HARMOGEN-R each instructor agrees with the mean of the other three at "
           f"{ins['loo_min']:.3f} to {ins['loo_max']:.3f} QWK ({ins['pairs_min']:.3f} to {ins['pairs_max']:.3f} between "
           "pairs of instructors), and they give zero to "
           f"{100 * ins['gold_zeros']:.0f}\\% of the answers.")
    return r"\section{Validation of the guide}" + "\n" + _table(
        cap, ["Model", "Dataset", "Configuration", "N", "QWK", r"$\Delta$QWK", "95\\% CI", "Non-inf.", "SD", "Zeros"],
        rows, "llp{2.9cm}rrrlclr")


def robustness_section() -> str:
    from experiments.analysis import robustness
    ct = robustness.cluster_table()
    hol = lambda x: "--" if pd.isna(x) else str(int(x))
    rows = [[_esc(r.result), int(r.of), int(r.sig_answers), hol(r.holm_answers), int(r.sig_questions),
             hol(r.holm_questions)] for r in ct.itertuples()]
    out = [r"\section{Robustness checks}\label{sec:robustness}" + "\n" + _table(
        "Resampling whole questions instead of answers. The paper's intervals resample the answers; answers to the "
        "same question may be alike, so here the questions of the compared answers are resampled with replacement "
        "(10,000 times, same seed). Counts of significant results (95\\% interval excluding zero) and of those that "
        "survive Holm's correction in their family. Criterion scoring counts its significant changes in either "
        "direction (a gain for GPT-5.1 on RIAYN and a loss for DeepSeek-V4-Flash on PT-CS code). The validation is "
        "not recomputed this way: HARMOGEN-R has only three questions.",
        ["Result", "Of", "Answers", "Holm", "Questions", "Holm"], rows, "p{6.4cm}rrrrr")]
    sr = robustness.single_run()
    sm = robustness.single_summary(sr)
    rows = [[r.part, _esc(KIND.get(r.kind, r.kind)), int(r.n), _sg(r.d_k), _sg(r.d_1), int(r.flips)] for r in sm.itertuples()]
    gu = sr.drop_duplicates(["part", "model", "set"])
    gap = gu.guide_k - gu.guide_1
    fl_ = sr[(sr.d_k > 0) != (sr.d_1 > 0)]
    fl = float(fl_[["d_k", "d_1"]].abs().to_numpy().max()) if len(fl_) else 0.0
    out.append(_table(
        "QWK on single runs. The paper computes QWK on the mean of the repeated grades of each answer, while the guide "
        "makes one call per answer. Here the guide and each alternative are scored run by run (each run against the "
        "same run of the other) and the differences averaged over the runs: the mean $\\Delta$QWK (alternative minus "
        "guide) on the mean of the grades and on single runs, per alternative, and the comparisons whose sign "
        f"differs. On single runs the guide's QWK is {gap.mean():.3f} lower on average ({_sg(gap.min())} to "
        f"{_sg(gap.max())}); the comparisons whose sign differs are all within {fl:.3f} of zero.",
        ["Part", "Alternative", "N", r"Mean of $k$", "Single run", "Sign differs"], rows, "llrrrr"))
    fb = robustness.fallback_sensitivity()
    rows = [[MNAME.get(r.model, r.model), DNAME.get("ptcs-short" if (r.dataset == "ptcs" and r.domain == "short_answer")
                                                  else r.dataset, r.dataset), f"{r.fallback_pct:.1f}\\%",
             _sg(r.d_with), f"[{_sg(r.lo_with)}, {_sg(r.hi_with)}]", _sg(r.d_own), f"[{_sg(r.lo_own)}, {_sg(r.hi_own)}]"]
            for r in fb.itertuples()]
    out.append(_table(
        "Reasoning runs that reached the output limit. In the paper such a run takes the grade the same model gave "
        "that answer with reasoning off (With fallback); here those runs are left out and each answer's reasoning-on "
        "grade is the mean of its other runs (Own runs only). Only Qwen3.5 had such runs in the main comparison. "
        r"$\Delta$QWK is reasoning on minus off, with its 95\% bootstrap interval.",
        ["Model", "Dataset", "Fallback runs", r"$\Delta$QWK, with fallback", "95\\% CI", r"$\Delta$QWK, own runs only",
         "95\\% CI"], rows, "llrrlrl"))
    dz = robustness.discretisation()
    nice = lambda c: ", ".join(MNAME.get(x.split(" ")[0], x.split(" ")[0]) + " " + DNAME.get(
        {"ptcs-code": "ptcs", "ptcs-short_answer": "ptcs-short"}.get(x.split(" ")[1], x.split(" ")[1].split("-")[0]),
        x.split(" ")[1]) for x in c.split(", "))
    rows = [[_esc(r.rule), int(r.significant), int(r.holm), _esc(nice(r.cells))] for r in dz.itertuples()]
    out.append(_table(
        "Discretisation of the agreement measure. Reasoning on against off (RQ1, 20 combinations) with QWK computed "
        "on six levels and halves rounded to the even level (the paper), with halves rounded up, and on five or seven "
        "levels: the number of significant gains, those that survive Holm's correction, and which they are.",
        ["Rule", "Significant", "Holm", "Significant gains"], rows, "p{3.6cm}rrp{8.4cm}"))
    # fourth independent review (2026-11-04): a continuous metric and the signed bias beside QWK
    mr = robustness.mae_rq1()
    dn = lambda r: DNAME.get("ptcs-short" if (r.dataset == "ptcs" and r.domain == "short_answer") else r.dataset, r.dataset)
    rows = [[dn(r), MNAME.get(r.model, r.model), int(r.N), f"{r.MAE_off:.3f}", f"{r.MAE_on:.3f}", _sg(r.dMAE),
             f"[{_sg(r.lo)}, {_sg(r.hi)}]", _sg(r.bias_off),
             (f"{100 * r.acc_off:.0f}\\% / {100 * r.acc_on:.0f}\\%" if r.dataset == "semeval" else "")]
            for r in mr.itertuples()]
    out.append(_table(
        "Reasoning (RQ1) in mean absolute error. The same answers and grades as Table~\\ref{tab:rq1supp} (a reasoning run "
        "that reached the output limit carries the reasoning-off grade), scored as the mean absolute error between "
        "the mean of an answer's grades and the human grade on the 0 to 1 scale, with reasoning off and on, its "
        r"change (on minus off; negative is better) with a 95\% paired bootstrap interval, the signed bias with "
        "reasoning off (model minus human; negative is more severe), and on SemEval the accuracy at the 0.5 cut-off.",
        ["Dataset", "Model", "N", "MAE off", "MAE on", r"$\Delta$MAE", "95\\% CI", "Bias off", "Accuracy off / on"],
        rows, "llrrrrlrr"))
    mv = robustness.mae_validation()
    rows = [[r.set.split(" (")[0], MNAME.get(r.model, r.model), _esc(KIND.get(r.kind, r.kind)), int(r.N), f"{r.MAE_guide:.3f}",
             f"{r.MAE_alt:.3f}", _sg(r.dMAE), f"[{_sg(r.lo)}, {_sg(r.hi)}]"] for r in mv.itertuples()]
    out.append(_table(
        "Validation of the guide (lower part of Fig. " + _n("fig:guiderefs") + " of the paper) in mean absolute error: the guide and each alternative on the "
        r"same answers, the change (alternative minus guide; negative means the alternative errs less) with a 95\% "
        "paired bootstrap interval.",
        ["Dataset", "Model", "Alternative", "N", "MAE guide", "MAE alt.", r"$\Delta$MAE", "95\\% CI"],
        rows, "lllrrrrl"))
    lo = robustness.instructors_loo()
    mods = [c for c in lo.columns if c not in ("held_out", "instructor_vs_rest")]
    rows = [[f"Instructor {i + 1}",
             f"{r['instructor_vs_rest']:.3f}"] + [f"{r[m]:.3f}" for m in mods] for i, (_, r) in enumerate(lo.iterrows())]
    out.append(_table(
        "HARMOGEN-R ceiling on a comparable basis: each instructor's grades against the mean of the other three, and "
        "each model's grades under the guide against that same mean (QWK, six levels).",
        ["Held out", "Instructor"] + [MNAME.get(m, m) for m in mods], rows, "l" + "r" * (1 + len(mods))))
    return "\n".join(out)


def main() -> int:
    doc = [r"\documentclass[10pt]{article}", r"\usepackage[margin=2cm]{geometry}", r"\usepackage[T1]{fontenc}",
           r"\usepackage{array,longtable,fancyvrb}", r"\usepackage{mathptmx}",
           r"\makeatletter\newcommand{\needspace}[1]{\begingroup\setlength{\dimen@}{#1}\vskip\z@\@plus\dimen@"
           r"\penalty-100\vskip\z@\@plus-\dimen@\vskip\dimen@\penalty9999\vskip-\dimen@\vskip\z@skip\endgroup}"
           r"\makeatother",
           r"\title{What Should an LLM Grader Be Given? Supplementary Material}", r"\date{}",
           r"\begin{document}", r"\maketitle",
           "This supplement gives the prompt templates, the models and their prices, the share of unparseable outputs, and "
           "tables with the values behind the figures of the paper. Every value is computed from the logged runs, with the "
           "metrics and bootstrap of the paper (QWK on six levels of the mean of the repeated grades; 10,000 resamples of "
           r"the answers; 95\% intervals). Figs.~" + _n("fig:rq1") + " to~" + _n("fig:rq6") + " and~" + _n("fig:guiderefs")
           + " have their own tables below, each naming its figure. Fig.~" + _n("fig:promptexp")
           + " is the design of the follow-up experiment, and Figs.~" + _n("fig:frameworkdiagram") + " and~"
           + _n("fig:guideprompt") + " show the guide and its prompt, whose templates are given in Section~\\ref{sec:prompts}. "
           "Section~\\ref{sec:zerocollapse} gives the values behind the prompt engineering of the follow-up experiment. "
           "Two further sections compare the guide with every other configuration graded without reasoning, within each "
           "model and across models, "
           "and Section~\\ref{sec:robustness} gives four robustness checks: resampling whole questions instead "
           "of answers, QWK on single runs instead of the mean of the repeated grades, reasoning runs that reached the "
           "output limit left out, and other discretisations of the agreement measure. A separate supplementary file "
           "holds every grade the models gave on the public and validation datasets, with a script that recomputes the "
           "reported agreement values and intervals from them.",
           prompts_section(), models_section(), parse_section(), rq1_section(), contrasts_sections(), rq4_section(),
           conversation_section(), instruction_section(), zero_collapse_section(), references_section(), test1_section(), test2_section(), verification_section(), robustness_section(),
           r"\end{document}"]
    text = "\n\n".join(doc).replace("\\section{", "\\needspace{14\\baselineskip}\\section{")
    OUT.write_text(text + "\n")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

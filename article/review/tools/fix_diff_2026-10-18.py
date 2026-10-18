"""Post-process latexdiff output: clean the deleted RQ6 item, show the replaced Table 4 as a whole new table,
mark redrawn figures, and add a reading note after \maketitle."""
import re, sys, pathlib
d = pathlib.Path(sys.argv[1]); new_flat = pathlib.Path(sys.argv[2]).read_text()
s = d.read_text()
# 1. the deleted RQ6 item and the new follow-up sentence
a = s.index("\\DIFdelbegin %DIFDELCMD < \\item %%%")
b = s.index("\\DIFaddbegin \\DIFadd{.\n}\\DIFaddend", a) + len("\\DIFaddbegin \\DIFadd{.\n}\\DIFaddend")
s = s[:a] + ("\\item \\DIFdel{RQ6. How does the grading instruction, applying the guidance strictly or awarding partial "
             "credit explicitly, affect agreement and cost?}\n\\end{itemize}\n\\DIFadd{The follow-up experiment, designed "
             "after the first results, asks how the grading instruction affects agreement and cost.}") + s[b:]
# 2. Table 4: replace the diffed table by the new one, all in blue
start = s.index("\\begin{table*}[!t]\\centering\\footnotesize\n\\caption{The configuration guide\\DIFdelbeginFL")
end = s.index("\\end{table*}", start) + len("\\end{table*}")
ns = new_flat.index("\\begin{table*}[!t]\\centering\\footnotesize\n\\caption{The configuration guide:")
ne = new_flat.index("\\end{table*}", ns) + len("\\end{table*}")
tab = new_flat[ns:ne].replace("\\caption{", "\\caption{\\DIFaddFL{[New table.]} ", 1)
tab = tab.replace("\\setlength{\\tabcolsep}{5pt}", "\\setlength{\\tabcolsep}{5pt}\\color{blue}", 1)
s = s[:start] + tab + s[end:]
# 3. redrawn figures: flag in the caption
for lbl in ["fig:rq1", "fig:costquality"]:
    i = s.index("\\label{%s}" % lbl)
    c = s.rindex("\\caption{", 0, i)
    s = s[:c] + "\\caption{\\DIFaddFL{[Figure redrawn.]} " + s[c + len("\\caption{"):]
# 4. reading note
note = ("\\noindent\\fcolorbox{blue}{white}{\\parbox{0.96\\columnwidth}{\\footnotesize\\textbf{Revision of 18 October "
        "2026.} Text in \\DIFadd{blue, underlined} was added and text in \\DIFdel{red, struck through} was removed, "
        "relative to the version of 16 October. Figures~1 and~4 were redrawn, Figure~8 is new, and Table~4 is new.}}"
        "\n\\vspace{4pt}\n")
s = s.replace("\\maketitle\n", "\\maketitle\n" + note, 1)
d.write_text(s)
print("ok")

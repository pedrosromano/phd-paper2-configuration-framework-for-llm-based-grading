# Marked PDF (changes against the version Pedro annotated)

Used for the 2026-10-18 round (`~/Desktop/artigo_2_access_revisto4_alteracoes_2026-10-18.pdf`, base commit `b45cffb`).

1. Get `latexdiff-so` (self-contained) from CTAN: `https://mirrors.ctan.org/support/latexdiff.zip`, unzipped
   in a temporary folder. It is not part of BasicTeX.
2. Old version: `git archive <base-commit> article | tar -x -C <tmp>/old`. New version: a copy of `article/` without
   build files.
3. Flatten both: `python3 flatten.py <dir> <out.tex>`. It inlines sections, related work and tables, and keeps
   the `\input` of the `.pgf` figures.
4. Diff:
   `perl latexdiff-so --type=UNDERLINE --config="PICTUREENV=(?:picture|DIFnomarkup|tikzpicture)[\w\d*@]*" old_flat.tex new_flat.tex > diff.tex`
5. Repair what latexdiff cannot mark (`fix_diff_2026-10-18.py`):
   - a table replaced wholesale is shown in blue as "[New table.]";
   - the deleted RQ6 list item;
   - redrawn figures are flagged in their captions;
   - a reading note goes after `\maketitle`.
   The fixes are specific to that round; adapt them for the next one.
6. Compile in the copy of `article/`: `latexmk -C diff.tex; latexmk -pdf -f diff.tex`.

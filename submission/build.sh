#!/bin/zsh
# Assemble the submission folder and copy it to the Desktop (Pedro, 2026-10-19: one folder with everything for
# the submission, copied to the Desktop at every new version).
#
# Expects the engines to have been run (tables, figures, supplementary.tex); this script only builds and packs:
#   submission/manuscript.pdf, supplementary.pdf, cover_letter.pdf, reproducibility_package.zip
# and copies the folder to ~/Desktop/artigo_2_submissao/.
#
#   zsh submission/build.sh
set -e
ROOT=${0:A:h:h}
SUB=$ROOT/submission
DEST=$HOME/Desktop/artigo_2_submissao
eval "$(/usr/libexec/path_helper)"

cd $ROOT && .venv/bin/python -m experiments.analysis.export_package > /dev/null
cd $ROOT/article
latexmk -pdf -interaction=nonstopmode main.tex > /dev/null
latexmk -pdf -interaction=nonstopmode supplementary.tex > /dev/null
cp main.pdf $SUB/manuscript.pdf
cp supplementary.pdf $SUB/supplementary.pdf

cd $SUB
latexmk -pdf -interaction=nonstopmode cover_letter.tex > /dev/null
latexmk -c cover_letter.tex > /dev/null

rm -f reproducibility_package.zip
(cd reproducibility && zip -q -X ../reproducibility_package.zip README.md recompute.py grades.csv)

rm -rf $DEST && mkdir -p $DEST
cp manuscript.pdf supplementary.pdf cover_letter.pdf reproducibility_package.zip $DEST/
echo "submission folder ready: $DEST"
ls -l $DEST

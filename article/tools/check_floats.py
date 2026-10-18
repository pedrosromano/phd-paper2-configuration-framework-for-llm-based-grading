#!/usr/bin/env python3
"""Check that every table and figure appears after its first reference in the text, and as close to it as
the layout allows (Pedro's rule, 2026-10-18). Runs after every build (article/latexmkrc) and by hand:

    python3 tools/check_floats.py [main.pdf]          (from article/)

It reads the compiled PDF, so it checks what the reader sees:
- running text is the body font (Times) at the body size; captions, table cells, figure labels and the
  bibliography are smaller or in the class's sans font, so a "Fig. 3" written there is not a reference;
- a float is found by its caption ("FIGURE n." or "TABLE n."). It is full width when its caption spans both
  columns, otherwise it sits in the column of its caption;
- reading order on a page: full-width floats at the top, the left column, the right column, full-width
  floats at the bottom. Inside a column, a float at its top comes before the column's text, one at its
  bottom after it, and one between paragraphs at its own height.

Rules (every violation is an ERROR and the exit status is 1, so the build fails):
- a float comes before its first reference in the text, or is never referenced;
- a float is not at one of the nearest places after its first reference (so it can never sit two pages
  after it):
    full width: the bottom of the reference's page or the top of the next page;
    one column: later in the reference's column, or in the next column.
"""
from __future__ import annotations

import pathlib
import re
import sys
from dataclasses import dataclass

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    sys.exit("check_floats: PyMuPDF (fitz) is missing; run it with /usr/bin/python3, which has it.")

BODY_FONT = "Times"         # family prefix of the running-text font
BODY_MIN_SIZE = 9.5         # the body is 10 pt; captions, tables and figure text are 8 pt or less
CAPTION = re.compile(r"^(FIGURE|TABLE)\s+(\d+)\.")
NUM = r"\d+[a-z]?"
SEP = r"\s*(?:,|–|-|and|to)\s*"
REFS = {
    "FIGURE": re.compile(rf"\bFigs?\.\s*({NUM}(?:{SEP}(?:Figs?\.\s*)?{NUM})*)"),
    "TABLE": re.compile(rf"\bTables?\s+({NUM}(?:{SEP}{NUM})*)"),
}
TOP, BOTTOM, HERE = "top", "bottom", "in the text"


@dataclass
class Float:
    kind: str           # FIGURE or TABLE
    num: int
    page: int           # 1-based
    full: bool          # spans both columns
    col: int            # 0 left, 1 right (single column only)
    zone: str           # top, bottom, in the text
    y: float            # caption top, from the top of the page

    @property
    def key(self):
        if self.full:
            return (self.page, -1 if self.zone == TOP else 2, self.y)
        y = -1.0 if self.zone == TOP else 1e6 if self.zone == BOTTOM else self.y
        return (self.page, self.col, y)

    def where(self) -> str:
        span = "full width" if self.full else ("left column" if self.col == 0 else "right column")
        return f"page {self.page}, {self.zone} ({span})"

    def name(self) -> str:
        return f"{'Fig.' if self.kind == 'FIGURE' else 'Table'} {self.num}"


def _numbers(group: str) -> list[int]:
    """'1–3' -> [1, 2, 3]; '5b and 6' -> [5, 6]."""
    out: list[int] = []
    parts = re.split(r"(–|-|to|,|and)", group)
    prev, rng = None, False
    for p in parts:
        p = p.strip()
        if p in ("–", "-", "to"):
            rng = True
            continue
        m = re.search(r"(\d+)", p)
        if not m:
            continue
        n = int(m.group(1))
        if rng and prev is not None and n > prev:
            out.extend(range(prev + 1, n + 1))
        else:
            out.append(n)
        prev, rng = n, False
    return out


def analyse(pdf: str):
    doc = fitz.open(pdf)
    body = []        # (key, text) of running-text lines, in reading order
    floats: list[Float] = []
    for pno, page in enumerate(doc, 1):
        mid = page.rect.width / 2
        lines, caps = [], []
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                spans = [s for s in line["spans"] if s["text"].strip()]
                if not spans:
                    continue
                text = "".join(s["text"] for s in line["spans"])
                x0, y0, x1, y1 = line["bbox"]
                n = sum(len(s["text"]) for s in spans)
                nb = sum(len(s["text"]) for s in spans
                         if s["font"].startswith(BODY_FONT) and s["size"] >= BODY_MIN_SIZE)
                m = CAPTION.match(text.strip())
                if m and not spans[0]["font"].startswith(BODY_FONT):
                    caps.append((m.group(1), int(m.group(2)), block["bbox"]))
                elif nb >= 0.6 * n:
                    col = 0 if x1 <= mid + 5 else 1 if x0 >= mid - 5 else -1
                    lines.append((col, y0, y1, text))
        for col, y0, _y1, text in sorted(lines, key=lambda t: (t[0], t[1])):
            body.append(((pno, col, y0), text))
        for kind, num, (bx0, by0, bx1, by1) in caps:
            full = bx0 < mid - 20 and bx1 > mid + 20
            col = 0 if bx1 <= mid + 5 else 1
            if full:
                above = any(y1 <= by0 + 1 for c, y0, y1, t in lines)
                zone = BOTTOM if above else TOP
            else:
                above = any(c == col and y1 <= by0 + 1 for c, y0, y1, t in lines)
                below = any(c == col and y0 >= by1 - 1 for c, y0, y1, t in lines)
                zone = TOP if not above else BOTTOM if not below else HERE
            floats.append(Float(kind, num, pno, full, col, zone, by0))
    # first reference of each float, in reading order
    text, index = "", []
    for key, t in body:
        index.append((len(text), key))
        text += t + " "
    first: dict[tuple[str, int], tuple] = {}
    for kind, rx in REFS.items():
        for m in rx.finditer(text):
            key = max(k for off, k in index if off <= m.start())
            for n in _numbers(m.group(1)):
                if (kind, n) not in first or key < first[(kind, n)]:
                    first[(kind, n)] = key
    return floats, first


def check(pdf: str) -> int:
    if not pathlib.Path(pdf).is_file():
        print(f"check_floats: {pdf} not found; build the paper first (make paper).")
        return 1
    floats, first = analyse(pdf)
    errors = 0
    print(f"Float placement check: {pdf}")
    for f in sorted(floats, key=lambda f: (f.kind, f.num)):
        ref = first.get((f.kind, f.num))
        if ref is None:
            print(f"  ERROR    {f.name():8s} {f.where()}: never referenced in the text")
            errors += 1
            continue
        rp, rc, _ = ref
        rwhere = f"page {rp}, {'left' if rc == 0 else 'right' if rc == 1 else 'full-width'} column"
        if f.key <= ref:
            print(f"  ERROR    {f.name():8s} {f.where()}: before its first reference ({rwhere})")
            errors += 1
            continue
        if f.full:
            near = (f.page == rp and f.zone == BOTTOM) or (f.page == rp + 1 and f.zone == TOP)
            hint = f"the bottom of page {rp} or the top of page {rp + 1}"
        else:
            nxt = (rp, 1) if rc == 0 else (rp + 1, 0)
            near = (f.page, f.col) in ((rp, rc), nxt)
            hint = f"after the reference in its column, or in the next column"
        if near:
            print(f"  ok       {f.name():8s} {f.where()}; first reference {rwhere}")
        else:
            print(f"  ERROR    {f.name():8s} {f.where()}: too far from its first reference ({rwhere}); "
                  f"it must be at {hint}")
            errors += 1
    print(f"  {len(floats)} floats, {errors} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(check(sys.argv[1] if len(sys.argv) > 1 else "main.pdf"))

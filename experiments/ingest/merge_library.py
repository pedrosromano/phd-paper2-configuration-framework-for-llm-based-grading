"""Unify the literature library into one deduped table (Phase 1.2).

Reads EVERY export in article/related/library/ (discovered dynamically — no hard-coded
filenames), normalises the three known formats into one schema, dedups by DOI (title+year
fallback, flagged), cross-checks against Article 1's references.bib to mark already-covered
(<=Jul-2025) work, and writes refs_merged.csv for manual inspection before annotation (1.3).

This step is MECHANICAL: it merges and flags; it does not judge relevance (that is 1.3).

Formats handled:
  - Scopus CSV     (BOM; columns Authors/Title/Year/DOI/Cited by/Abstract/Author Keywords...)
  - IEEE Xplore CSV(Document Title/Authors/Publication Year/DOI/Abstract/Article Citation Count...)
  - ScienceDirect  plain-text citation+abstract export (blank-line-separated records)

Run:  python -m experiments.ingest.merge_library
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
LIBRARY_DIR = REPO_ROOT / "article" / "related" / "library"
SLR_BIB = REPO_ROOT / "article" / "related" / "slr_source" / \
    "phd-paper1-automated-essay-grading-in-education-slr" / "references.bib"
OUT_CSV = LIBRARY_DIR / "refs_merged.csv"

COLUMNS = [
    "title", "authors", "year", "venue", "doi", "abstract", "keywords",
    "cited_by", "sources", "in_slr", "cutoff_flag", "merge_uncertain", "n_merged",
]


# --------------------------------------------------------------------- helpers
def norm_doi(doi: str | None) -> str:
    if not doi or not isinstance(doi, str):
        return ""
    d = doi.strip().lower()
    d = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", d)
    # exports often append a sentence period / trailing punctuation to the URL line
    return d.strip().rstrip(" .,;)")


def norm_title(title: str | None) -> str:
    if not title or not isinstance(title, str):
        return ""
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def to_year(val) -> str:
    if val is None:
        return ""
    m = re.search(r"(19|20)\d{2}", str(val))
    return m.group(0) if m else ""


def cutoff_flag(year: str) -> str:
    """SLR cutoff = Jul 2025. <2025 = covered/old; 2025 = overlap (verify vs in_slr);
    >=2026 = clearly new; unknown = blank."""
    if not year:
        return "unknown_year"
    y = int(year)
    if y < 2025:
        return "pre_cutoff"
    if y == 2025:
        return "overlap_2025"
    return "post_cutoff"


# --------------------------------------------------------------------- parsers
def parse_scopus(path: Path) -> list[dict]:
    df = pd.read_csv(path, encoding="utf-8-sig", dtype=str).fillna("")
    out = []
    for _, r in df.iterrows():
        kw = "; ".join(x for x in [r.get("Author Keywords", ""),
                                   r.get("Index Keywords", "")] if x).strip("; ")
        out.append({
            "title": r.get("Title", "").strip(),
            "authors": r.get("Authors", "").strip(),
            "year": to_year(r.get("Year", "")),
            "venue": r.get("Source title", "").strip(),
            "doi": r.get("DOI", "").strip(),
            "abstract": r.get("Abstract", "").strip(),
            "keywords": kw,
            "cited_by": r.get("Cited by", "").strip(),
            "source": "scopus",
        })
    return out


def parse_ieee(path: Path) -> list[dict]:
    df = pd.read_csv(path, dtype=str).fillna("")
    out = []
    for _, r in df.iterrows():
        kw = "; ".join(x for x in [r.get("Author Keywords", ""),
                                   r.get("IEEE Terms", "")] if x).strip("; ")
        out.append({
            "title": r.get("Document Title", "").strip(),
            "authors": r.get("Authors", "").strip(),
            "year": to_year(r.get("Publication Year", "")),
            "venue": r.get("Publication Title", "").strip(),
            "doi": r.get("DOI", "").strip(),
            "abstract": r.get("Abstract", "").strip(),
            "keywords": kw,
            "cited_by": r.get("Article Citation Count", "").strip(),
            "source": "ieee",
        })
    return out


def parse_sciencedirect(path: Path) -> list[dict]:
    """Records are separated by blank lines. Within a record:
    line0=authors, line1=title, line2=venue; a doi.org line; a bare 4-digit year line;
    'Abstract:' and 'Keywords:' prefixed lines."""
    text = path.read_text(encoding="utf-8", errors="replace")
    blocks = re.split(r"\n\s*\n", text)
    out = []
    for blk in blocks:
        lines = [ln.rstrip() for ln in blk.splitlines() if ln.strip()]
        if len(lines) < 3:
            continue
        doi = year = abstract = keywords = venue = ""
        for ln in lines:
            if "doi.org/" in ln and not doi:
                doi = norm_doi(ln)
            elif ln.lower().startswith("abstract:"):
                abstract = ln.split(":", 1)[1].strip()
            elif ln.lower().startswith("keywords:"):
                keywords = ln.split(":", 1)[1].strip()
            elif re.fullmatch(r"(19|20)\d{2},?", ln) and not year:
                year = ln.rstrip(",")
        authors = lines[0].rstrip(",")
        title = lines[1].rstrip(",")
        # venue = 3rd line if it doesn't look like a year/metadata line
        if len(lines) >= 3 and not re.match(r"(Volume|Pages|ISSN|\d)", lines[2]):
            venue = lines[2].rstrip(",")
        if not title:
            continue
        out.append({
            "title": title, "authors": authors, "year": year, "venue": venue,
            "doi": doi, "abstract": abstract, "keywords": keywords,
            "cited_by": "", "source": "sciencedirect",
        })
    return out


def detect_and_parse(path: Path) -> list[dict]:
    if path.suffix.lower() == ".txt":
        return parse_sciencedirect(path)
    head = path.read_text(encoding="utf-8-sig", errors="replace")[:200].lower()
    if "document title" in head:
        return parse_ieee(path)
    if "author full names" in head or '"authors"' in head:
        return parse_scopus(path)
    # default: try scopus layout
    return parse_scopus(path)


# --------------------------------------------------------------------- SLR bib
def load_slr_keys() -> tuple[set[str], set[str]]:
    """Return (DOIs, normalised titles) present in Article 1's references.bib."""
    if not SLR_BIB.exists():
        return set(), set()
    text = SLR_BIB.read_text(encoding="utf-8", errors="replace")
    dois = {norm_doi(m) for m in re.findall(r"doi\s*=\s*[{\"]([^}\"]+)[}\"]", text, re.I)}
    titles = {norm_title(m) for m in re.findall(r"title\s*=\s*[{]([^}]+)[}]", text, re.I)}
    return {d for d in dois if d}, {t for t in titles if t}


# --------------------------------------------------------------------- merge
def merge(records: list[dict]) -> pd.DataFrame:
    by_doi: dict[str, dict] = {}
    by_title: dict[str, dict] = {}
    merged: list[dict] = []

    def blank_row(rec: dict) -> dict:
        return {
            "title": rec["title"], "authors": rec["authors"], "year": rec["year"],
            "venue": rec["venue"], "doi": norm_doi(rec["doi"]), "abstract": rec["abstract"],
            "keywords": rec["keywords"], "cited_by": rec["cited_by"],
            "sources": {rec["source"]}, "merge_uncertain": False, "n_merged": 1,
        }

    def absorb(dst: dict, rec: dict) -> None:
        dst["sources"].add(rec["source"])
        dst["n_merged"] += 1
        # keep the richer abstract / longer fields, max cited_by
        if len(rec["abstract"]) > len(dst["abstract"]):
            dst["abstract"] = rec["abstract"]
        for f in ("venue", "keywords", "authors"):
            if len(rec[f]) > len(dst[f]):
                dst[f] = rec[f]
        try:
            if int(rec["cited_by"] or 0) > int(dst["cited_by"] or 0):
                dst["cited_by"] = rec["cited_by"]
        except ValueError:
            pass

    for rec in records:
        d = norm_doi(rec["doi"])
        t = norm_title(rec["title"])
        if d:
            if d in by_doi:
                absorb(by_doi[d], rec)
            else:
                row = blank_row(rec)
                by_doi[d] = row
                merged.append(row)
                if t:
                    by_title.setdefault(t, row)
        elif t and t in by_title:
            absorb(by_title[t], rec)
            by_title[t]["merge_uncertain"] = True  # title-only merge
        else:
            row = blank_row(rec)
            if t:
                by_title[t] = row
            merged.append(row)

    slr_dois, slr_titles = load_slr_keys()
    for row in merged:
        row["sources"] = "; ".join(sorted(row["sources"]))
        row["in_slr"] = bool(
            (row["doi"] and row["doi"] in slr_dois)
            or (norm_title(row["title"]) in slr_titles)
        )
        row["cutoff_flag"] = cutoff_flag(row["year"])

    return pd.DataFrame(merged)[COLUMNS]


# --------------------------------------------------------------------- main
def main() -> int:
    files = sorted(p for p in LIBRARY_DIR.iterdir()
                   if p.suffix.lower() in (".csv", ".txt") and p.name != OUT_CSV.name)
    print(f"Discovered {len(files)} library files:")
    all_records: list[dict] = []
    for f in files:
        recs = detect_and_parse(f)
        print(f"  {f.name:<32} -> {len(recs):4d} records")
        all_records.extend(recs)

    df = merge(all_records)
    df.to_csv(OUT_CSV, index=False)

    # ---- summary ----
    print(f"\nRaw records: {len(all_records)}  ->  merged rows: {len(df)} "
          f"(removed {len(all_records) - len(df)} duplicates)")
    print(f"Written: {OUT_CSV.relative_to(REPO_ROOT)}\n")
    print("By source-combination:")
    print(df["sources"].value_counts().to_string())
    print("\nBy cutoff flag:")
    print(df["cutoff_flag"].value_counts().to_string())
    print(f"\nAlready in Article-1 SLR (in_slr=True): {int(df['in_slr'].sum())}")
    print(f"Missing DOI: {(df['doi'] == '').sum()}")
    print(f"Title-only (uncertain) merges: {int(df['merge_uncertain'].sum())}")
    print(f"Multi-source (cross-database) rows: {(df['n_merged'] > 1).sum()}")
    print("\nYear distribution:")
    print(df["year"].value_counts().sort_index().to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""PT-CS (GradeGenie) ingest -> common schema (Phase 2.1).

Join resposta_submissao  pergunta  teste_submissao, keep ONLY open-response question
types (Teorica -> short_answer, Programacao/Codigo -> code; MCQ and True/False are
closed-response and excluded). Drop ALL PII (never touch `utilizador`; pseudonymise the
submission grouping; redact any e-mail embedded in free text), strip AI comments
(criterio_correcao.comentario is never selected into the corpus), clean escaped HTML
while PRESERVING code angle-brackets, keep `cotacao` (gold) and `pergunta.cotacao`
(scale max). Emit a validation report + the human-validation evidence
(cotacao vs sum of criterio_correcao.nota_parcial).

Grades are a TWO-TEACHER CONSENSUS over human-validated, AI-seeded suggestions -- NOT
independent double annotation (CLAUDE.md §2). No per-teacher scores exist in the schema,
so no inter-rater kappa / human ceiling is recoverable.

Run:  python -m experiments.ingest.ingest_ptcs
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

import pandas as pd

from experiments.ingest import ptcs_db, schema

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT = REPO_ROOT / "data" / "processed" / "corpus_ptcs.parquet"

TYPE_DOMAIN = {1: "short_answer", 4: "code"}  # 1=Teorica, 4=Programacao/Codigo
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_FORMAT_TAGS = re.compile(
    r"</?(p|div|span|b|i|u|strong|em|ul|ol|li|pre|code|h[1-6]|table|tr|td|th|tbody|thead|font)\b[^>]*>",
    re.I,
)


def clean_html(s: str | None) -> str:
    """Strip editor formatting tags then unescape entities -- WITHOUT eating code's
    angle brackets (those are &lt;/&gt; entities, unescaped only after tag removal)."""
    if s is None:
        return ""
    s = str(s)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = _FORMAT_TAGS.sub("", s)
    s = html.unescape(s)          # &gt; -> >, &lt; -> <, &nbsp; -> \xa0
    s = s.replace("\xa0", " ")
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def redact_emails(s: str) -> tuple[str, int]:
    n = len(EMAIL_RE.findall(s))
    return (EMAIL_RE.sub("[EMAIL]", s), n) if n else (s, 0)


def fetch() -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = ptcs_db.fetch_dicts(
        """
        SELECT rs.id              AS rs_id,
               rs.id_teste_submissao AS submission_raw,
               rs.id_pergunta     AS question_id,
               rs.resposta        AS student_answer,
               rs.cotacao         AS gold_score,
               p.enunciado        AS question_text,
               p.criterios        AS rubric_json,
               p.cotacao          AS gold_scale_max,
               p.tipo_pergunta    AS tipo,
               p.teste            AS teste_id,
               p.ordem            AS ordem
        FROM resposta_submissao rs
        JOIN pergunta p          ON rs.id_pergunta = p.id
        JOIN teste_submissao ts  ON rs.id_teste_submissao = ts.id   -- existence only; no PII selected
        WHERE p.tipo_pergunta IN (1, 4)
        """
    )
    # human-validation evidence source: sum of per-criterion partials per response
    parts = ptcs_db.fetch_dicts(
        "SELECT id_resposta_submissao AS rs_id, SUM(nota_parcial) AS sum_parcial, "
        "COUNT(*) AS n_crit FROM criterio_correcao GROUP BY id_resposta_submissao"
    )
    return pd.DataFrame(rows), pd.DataFrame(parts)


def build(df_raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = df_raw.copy()
    # pseudonymise submissions: deterministic anon id by sorted raw submission id
    uniq = sorted(df["submission_raw"].dropna().unique())
    sub_map = {raw: f"sub_{i:04d}" for i, raw in enumerate(uniq, 1)}
    df["submission_id"] = df["submission_raw"].map(sub_map)

    # clean text + redact emails (defence-in-depth against embedded PII)
    email_hits = 0
    cleaned_q, cleaned_a = [], []
    for _, r in df.iterrows():
        q = clean_html(r["question_text"])
        a = clean_html(r["student_answer"])
        q, n1 = redact_emails(q)
        a, n2 = redact_emails(a)
        email_hits += n1 + n2
        cleaned_q.append(q)
        cleaned_a.append(a)
    df["question_text"] = cleaned_q
    df["student_answer"] = cleaned_a

    out = pd.DataFrame({
        "item_id": "ptcs:" + df["submission_id"] + ":" + df["question_id"].astype(str),
        "dataset": "ptcs",
        "domain": df["tipo"].map(TYPE_DOMAIN),
        "language": "pt",
        "question_text": df["question_text"],
        "reference_answer": None,                       # PT-CS has no reference solution (§5)
        "rubric_json": df["rubric_json"].where(df["rubric_json"].astype(str).str.strip() != "", None),
        "student_answer": df["student_answer"],
        "gold_score": pd.to_numeric(df["gold_score"], errors="coerce"),
        "gold_scale_max": pd.to_numeric(df["gold_scale_max"], errors="coerce"),
        "label_2way": None, "label_3way": None, "label_5way": None,
        "split": "none",
        "question_id": df["question_id"].astype(str),
        "submission_id": df["submission_id"],
        "source_meta": [json.dumps({"teste_id": int(t), "ordem": int(o), "tipo": int(tp)})
                        for t, o, tp in zip(df["teste_id"], df["ordem"], df["tipo"])],
    })
    out = schema.add_gold_norm(out)
    # drop blank (unanswered) submissions -- legitimate but not a grading test; report the count
    blank = out["student_answer"].astype(str).str.strip() == ""
    n_blank = int(blank.sum())
    out = out[~blank].reset_index(drop=True)
    # de-dup any item_id collisions (same submission+question appearing twice) by keeping first
    dup = out["item_id"].duplicated().sum()
    out = out.drop_duplicates("item_id").reset_index(drop=True)
    return out, {"email_redactions": email_hits, "item_id_dups_dropped": int(dup),
                 "submissions": len(uniq), "blank_answers_dropped": n_blank}


def human_validation_evidence(out: pd.DataFrame, df_raw: pd.DataFrame,
                              parts: pd.DataFrame) -> dict:
    """% of responses where final cotacao != sum(nota_parcial), and mean adjustment."""
    m = df_raw[["rs_id", "gold_score"]].merge(parts, on="rs_id", how="inner")
    m["gold_score"] = pd.to_numeric(m["gold_score"], errors="coerce")
    m["sum_parcial"] = pd.to_numeric(m["sum_parcial"], errors="coerce")
    m = m.dropna(subset=["gold_score", "sum_parcial"])
    diff = (m["gold_score"] - m["sum_parcial"]).abs()
    adjusted = diff > 1e-6
    return {
        "responses_with_criteria": int(len(m)),
        "pct_final_neq_sum_parcial": round(100 * adjusted.mean(), 1) if len(m) else None,
        "mean_adjustment_abs": round(float(diff.mean()), 4) if len(m) else None,
        "mean_adjustment_when_adjusted": round(float(diff[adjusted].mean()), 4) if adjusted.any() else 0.0,
    }


def report(out: pd.DataFrame, meta: dict, hve: dict) -> None:
    print(f"\n=== PT-CS ingest report ({len(out)} items) ===")
    print("By domain:\n" + out["domain"].value_counts().to_string())
    print(f"\nSubmissions (pseudonymised): {meta['submissions']}  |  "
          f"email redactions: {meta['email_redactions']}  |  "
          f"blank answers dropped: {meta['blank_answers_dropped']}  |  "
          f"item_id dups dropped: {meta['item_id_dups_dropped']}")
    print("\nNull rates:")
    for c in ["question_text", "student_answer", "rubric_json", "reference_answer"]:
        empty = out[c].isna() | (out[c].astype(str).str.strip() == "")
        print(f"  {c:18}: {empty.mean()*100:5.1f}% empty")
    print("\nScale ranges:")
    print(f"  gold_score   : [{out.gold_score.min()}, {out.gold_score.max()}]")
    print(f"  gold_scale_max: {sorted(out.gold_scale_max.dropna().unique())[:8]}...")
    oob = ((out.gold_norm < 0) | (out.gold_norm > 1)).sum()
    print(f"  gold_norm out-of-range rows: {oob}")
    print("\nHuman-validation evidence (cotacao vs sum nota_parcial):")
    for k, v in hve.items():
        print(f"  {k}: {v}")
    print("\n3 anonymised examples:")
    for _, r in out.sample(min(3, len(out)), random_state=7).iterrows():
        print(f"  [{r.domain}] {r.item_id} score={r.gold_score}/{r.gold_scale_max}")
        print(f"     Q: {r.question_text[:90]!r}")
        print(f"     A: {r.student_answer[:90]!r}")


def main() -> int:
    df_raw, parts = fetch()
    out, meta = build(df_raw)
    out = schema.validate(out, dataset="ptcs")
    hve = human_validation_evidence(out, df_raw, parts)
    schema.write_parquet(out, OUT)
    report(out, meta, hve)
    print(f"\nWrote {OUT.relative_to(REPO_ROOT)}")
    print("NOTE: grades are a two-teacher CONSENSUS (AI-seeded, human-validated); "
          "no per-teacher scores exist -> no inter-rater kappa / human ceiling.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Read-only connection to the PT-CS (GradeGenie) production MySQL (Phase 2.1).

Credentials come from .env (gitignored) via env.py -- NEVER hard-coded, NEVER committed.
This module only ever issues SELECTs. It deliberately provides no write path and never
touches the `utilizador` table (student PII): students are referenced only by opaque
integer FKs, which the ingest pseudonymises.
"""

from __future__ import annotations

import os

import mysql.connector

from experiments.harness.env import load_env

REQUIRED = ["PTCS_DB_HOST", "PTCS_DB_PORT", "PTCS_DB_USER", "PTCS_DB_PASSWORD", "PTCS_DB_NAME"]


def connect(timeout: int = 30):
    """Return a read-only-intent MySQL connection (SSL required, DigitalOcean managed)."""
    load_env()
    missing = [k for k in REQUIRED if not os.environ.get(k)]
    if missing:
        raise RuntimeError(f"PT-CS DB credentials missing from environment/.env: {missing}")
    return mysql.connector.connect(
        host=os.environ["PTCS_DB_HOST"],
        port=int(os.environ["PTCS_DB_PORT"]),
        user=os.environ["PTCS_DB_USER"],
        password=os.environ["PTCS_DB_PASSWORD"],
        database=os.environ["PTCS_DB_NAME"],
        ssl_disabled=False,           # DO managed MySQL requires TLS
        connection_timeout=timeout,
    )


def fetch_dicts(query: str, params: tuple | None = None) -> list[dict]:
    """Run a SELECT and return rows as dicts. Read-only."""
    q = query.lstrip().lower()
    if not (q.startswith("select") or q.startswith("with") or q.startswith("describe")
            or q.startswith("show")):
        raise ValueError("ptcs_db.fetch_dicts is read-only: only SELECT/WITH/DESCRIBE/SHOW allowed.")
    conn = connect()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(query, params or ())
        rows = cur.fetchall()
        cur.close()
        return rows
    finally:
        conn.close()

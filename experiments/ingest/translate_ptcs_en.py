"""Parallel EN translation of the PT-CS corpus (Phase 2.2) -- FOR THE MASTER'S, not this article.

Produces corpus_en.parquet ALIGNED 1:1 with corpus_ptcs.parquet (same item_id -> same row ->
same grade), differing only in language of the translated text. It is a parallel view of ONE
dataset in two languages, NOT a second dataset, and is OUT of this article's experimental matrix
(Phase 4 never touches it).

GDPR: translates the ALREADY-ANONYMISED output of 2.1 (corpus_ptcs.parquet), never the raw export.
What is translated (only): question stems (enunciado) for all items, and student answers for
short_answer (theory) items. What is NOT touched: code answers (programming), PT comments inside
code, the rubric_json criteria text, and all numeric fields (grades/scales). Translation is a
METHODOLOGICAL VARIABLE -- model/prompt/date are recorded alongside the dataset.

Local model only (free; does not spend the article's paid budget). The EN text needs human
validation before any master's use.

Run:  python -m experiments.ingest.translate_ptcs_en [--model qwen3:30b] [--limit N]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from experiments.harness.env import load_env
from experiments.ingest import schema

DEEPINFRA_URL = "https://api.deepinfra.com/v1/openai/chat/completions"

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "data" / "processed" / "corpus_ptcs.parquet"
OUT = REPO_ROOT / "data" / "processed" / "corpus_en.parquet"
CACHE = REPO_ROOT / "data" / "processed" / "_translation_cache.json"
META = REPO_ROOT / "data" / "processed" / "corpus_en_translation_meta.json"
OLLAMA = "http://localhost:11434"

PROMPT = (
    "Translate the following Portuguese {kind} into English. "
    "Preserve code, identifiers, technical terms and line breaks. "
    "Output only the translation, no preamble or commentary.\n\n{text}"
)


def _key(kind: str, text: str, model: str) -> str:
    return hashlib.sha1(f"{model}\x00{kind}\x00{text}".encode("utf-8")).hexdigest()


def _strip_thinking(s: str) -> str:
    """Remove any leaked reasoning: <think>..</think> blocks and a common preamble line."""
    import re
    s = re.sub(r"<think>.*?</think>", "", s, flags=re.S | re.I).strip()
    # drop a single leading meta-preamble sentence if present (defensive)
    s = re.sub(r"^(Okay|Hmm|Sure|Here(?:'s| is)|Let'?s|The user)[^\n]*\n+", "", s, count=1, flags=re.I)
    return s.strip()


def _load_cache() -> dict:
    return json.loads(CACHE.read_text()) if CACHE.exists() else {}


def _save_cache(cache: dict) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False))


def translate(text: str, kind: str, model: str, cache: dict) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    k = _key(kind, text, model)
    if k in cache:
        return cache[k]
    prompt = PROMPT.format(kind=kind, KIND=kind.upper(), text=text)
    # backend by model name: "org/model" -> DeepInfra (OpenAI-compatible); else local Ollama
    if "/" in model:
        out = _deepinfra(prompt, model)
    else:
        if "qwen" in model.lower():
            prompt += "\n/no_think"   # Qwen3's reliable thinking-off switch
        out = _ollama(prompt, model)
    out = _strip_thinking(out)
    cache[k] = out
    return out


def _ollama(prompt: str, model: str) -> str:
    payload = {"model": model, "prompt": prompt, "stream": False, "think": False,
               "options": {"temperature": 0.0, "num_predict": 2048}}
    req = urllib.request.Request(f"{OLLAMA}/api/generate",
                                 data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode("utf-8")).get("response", "").strip()


def _deepinfra(prompt: str, model: str) -> str:
    """OpenAI-compatible chat completion. For DeepSeek reasoning models the chain-of-thought
    arrives in message.reasoning_content (ignored); message.content is the clean answer."""
    load_env()
    key = os.environ.get("DEEPINFRA_API_KEY")
    if not key:
        raise RuntimeError("DEEPINFRA_API_KEY missing from .env")
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}],
               "temperature": 0.0, "max_tokens": 4096}
    req = urllib.request.Request(
        DEEPINFRA_URL, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        msg = json.loads(r.read().decode("utf-8"))["choices"][0]["message"]
    return (msg.get("content") or "").strip()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="gemma3:27b")
    p.add_argument("--limit", type=int, default=0, help="translate only first N items (testing)")
    args = p.parse_args(argv)

    df = pd.read_parquet(SRC)
    if args.limit:
        df = df.head(args.limit).copy()
    cache = _load_cache()

    # unique enunciados (translate once per question), all items
    q_unique = df.drop_duplicates("question_id")[["question_id", "question_text"]]
    print(f"Translating {len(q_unique)} unique question stems + "
          f"{(df.domain=='short_answer').sum()} theory answers (model={args.model}) ...")
    qmap: dict[str, str] = {}
    t0 = time.perf_counter()
    for i, (_, r) in enumerate(q_unique.iterrows(), 1):
        qmap[r.question_id] = translate(r.question_text, "exam question", args.model, cache)
        if i % 10 == 0:
            _save_cache(cache)
            print(f"  questions {i}/{len(q_unique)}  ({time.perf_counter()-t0:.0f}s)")

    en_q, en_a = [], []
    for j, (_, r) in enumerate(df.iterrows(), 1):
        en_q.append(qmap[r.question_id])
        if r.domain == "short_answer":
            en_a.append(translate(r.student_answer, "student answer", args.model, cache))
        else:
            en_a.append(r.student_answer)  # code: untouched (incl. PT comments)
        if j % 25 == 0:
            _save_cache(cache)
            print(f"  items {j}/{len(df)}  ({time.perf_counter()-t0:.0f}s)")
    _save_cache(cache)

    out = df.copy()
    out["language"] = "en"
    out["question_text"] = en_q
    out["student_answer"] = en_a
    # rubric_json, gold_*, ids, labels: unchanged. Re-validate (gold_norm already present).
    out = schema.validate(out, dataset="ptcs-en")
    schema.write_parquet(out, OUT)

    is_api = "/" in args.model
    meta = {
        "produced": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "purpose": "MASTER'S PT-vs-EN comparison only; OUT of Article-2 experimental matrix",
        "source": "corpus_ptcs.parquet (anonymised 2.1 output) -- never the raw export",
        "model": args.model,
        "host": "DeepInfra (OpenAI-compatible API)" if is_api else "local Ollama",
        "temperature": 0.0,
        "data_residency_note": (
            "Anonymised student answers + question stems were sent to DeepInfra (external "
            "inference provider; DeepSeek model is China-origin). No PII (CLAUDE.md §6.1 'DeepSeek "
            "only on anonymised data' satisfied). Authorised by the data controller (the author), "
            "who provided the DeepInfra key. Master's artifact only."
        ) if is_api else "All inference local; no data left the machine.",
        "translated": "question stems (all) + student answers (short_answer/theory only)",
        "not_translated": "code answers, PT comments in code, rubric_json criteria, numeric grades/scales",
        "prompt_template": PROMPT,
        "items": int(len(out)),
        "validation": "REQUIRES human validation before master's use (machine translation).",
    }
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    print(f"\nWrote {OUT.relative_to(REPO_ROOT)} ({len(out)} items) + "
          f"{META.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

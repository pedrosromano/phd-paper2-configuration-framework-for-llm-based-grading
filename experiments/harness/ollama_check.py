"""Ollama sanity + benchmark utility (Phase 0.3).

Talks to the local Ollama server over its HTTP API (default http://localhost:11434)
using only the standard library — no SDK, no third-party deps — so it runs before the
harness proper exists.

Subcommands:
  list            list installed models (name, size, quant, params)   [default]
  sanity [MODEL]  one-token generation against MODEL (or all installed) to prove the
                  round-trip works
  bench  [MODEL]  measure decode tokens/s on a short prompt and a long "reasoning"
                  prompt; writes a JSON/markdown report under data/processed/

Examples:
  python -m experiments.harness.ollama_check
  python -m experiments.harness.ollama_check sanity qwen3:30b
  python -m experiments.harness.ollama_check bench qwen3:30b --report
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

OLLAMA_HOST = "http://localhost:11434"
REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = REPO_ROOT / "data" / "processed"

# Prompts for the benchmark. Short = a typical grading-sized instruction; long =
# forces a chain of reasoning so we measure decode speed under a realistic load.
SHORT_PROMPT = "Reply with a single word: OK."
LONG_PROMPT = (
    "Think step by step and show your full reasoning. A student answer to a Java "
    "exam question is given a rubric with five criteria worth 2 points each. "
    "Work through, criterion by criterion, how you would decide a fair score for a "
    "partially-correct answer, discussing trade-offs, edge cases, and how partial "
    "credit should be apportioned. Be thorough."
)


def _post(path: str, payload: dict, timeout: float = 600.0) -> dict:
    """POST JSON to the Ollama API and return the parsed (non-streaming) response."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_HOST}{path}", data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get(path: str, timeout: float = 5.0) -> dict:
    with urllib.request.urlopen(f"{OLLAMA_HOST}{path}", timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def server_up() -> bool:
    try:
        _get("/api/tags", timeout=3.0)
        return True
    except (urllib.error.URLError, OSError):
        return False


def _hint_and_exit() -> "list[dict]":
    print(
        "Ollama server is not reachable at "
        f"{OLLAMA_HOST}.\n\n"
        "  - Install:  brew install ollama   (or https://ollama.com/download)\n"
        "  - Start:    ollama serve          (runs in the foreground; or launch the app)\n"
        "  - Verify:   ollama list\n",
        file=sys.stderr,
    )
    sys.exit(2)


def list_models() -> "list[dict]":
    if not server_up():
        _hint_and_exit()
    models = _get("/api/tags").get("models", [])
    if not models:
        print("No models installed. Pull some first (see Phase 0.3 roster).")
        return []
    print(f"{'MODEL':<32}{'SIZE':>10}  {'PARAMS':>8}  {'QUANT':>10}")
    for m in sorted(models, key=lambda x: x.get("name", "")):
        details = m.get("details", {})
        size_gb = m.get("size", 0) / 1e9
        print(
            f"{m.get('name', '?'):<32}{size_gb:>8.1f}GB  "
            f"{details.get('parameter_size', '?'):>8}  "
            f"{details.get('quantization_level', '?'):>10}"
        )
    return models


def sanity(model: str) -> bool:
    """One-token generation; returns True on a clean round-trip."""
    t0 = time.perf_counter()
    try:
        r = _post(
            "/api/generate",
            {"model": model, "prompt": "Say hi.", "stream": False,
             "options": {"num_predict": 1}},
            timeout=120.0,
        )
    except urllib.error.HTTPError as e:
        print(f"  [{model}] FAILED: HTTP {e.code} {e.reason}")
        return False
    except (urllib.error.URLError, OSError) as e:
        print(f"  [{model}] FAILED: {e}")
        return False
    dt = time.perf_counter() - t0
    text = (r.get("response") or "").strip().replace("\n", " ")
    print(f"  [{model}] OK  ({dt:.1f}s)  ->  {text[:40]!r}")
    return True


def bench_one(model: str, prompt: str, num_predict: int = 256) -> dict:
    """Run one generation, return timing + decode tokens/s from Ollama's counters."""
    r = _post(
        "/api/generate",
        {"model": model, "prompt": prompt, "stream": False,
         "options": {"num_predict": num_predict, "temperature": 0.0}},
    )
    eval_count = r.get("eval_count", 0)
    eval_ns = r.get("eval_duration", 0) or 1
    prompt_eval_count = r.get("prompt_eval_count", 0)
    total_ns = r.get("total_duration", 0)
    return {
        "model": model,
        "decode_tokens": eval_count,
        "decode_tokens_per_s": round(eval_count / (eval_ns / 1e9), 2),
        "prompt_tokens": prompt_eval_count,
        "total_seconds": round(total_ns / 1e9, 2),
    }


def bench(model: str, write_report: bool = False) -> dict:
    if not server_up():
        _hint_and_exit()
    print(f"Benchmarking {model} ...")
    short = bench_one(model, SHORT_PROMPT, num_predict=32)
    print(f"  short  : {short['decode_tokens_per_s']:>7.2f} tok/s "
          f"({short['decode_tokens']} tok, {short['total_seconds']}s)")
    long = bench_one(model, LONG_PROMPT, num_predict=512)
    print(f"  long   : {long['decode_tokens_per_s']:>7.2f} tok/s "
          f"({long['decode_tokens']} tok, {long['total_seconds']}s)")
    result = {"model": model, "short": short, "long": long}
    if write_report:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        out = REPORT_DIR / "_ollama_bench.json"
        existing = json.loads(out.read_text()) if out.exists() else {}
        existing[model] = result
        out.write_text(json.dumps(existing, indent=2))
        print(f"  -> appended to {out.relative_to(REPO_ROOT)}")
    return result


def main(argv: "list[str] | None" = None) -> int:
    p = argparse.ArgumentParser(description="Ollama sanity + benchmark (Phase 0.3)")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("list", help="list installed models (default)")
    sp = sub.add_parser("sanity", help="one-token generation")
    sp.add_argument("model", nargs="?", help="model tag; default = all installed")
    bp = sub.add_parser("bench", help="benchmark decode tokens/s")
    bp.add_argument("model", nargs="?", help="model tag; default = all installed")
    bp.add_argument("--report", action="store_true", help="write data/processed/_ollama_bench.json")
    args = p.parse_args(argv)

    if args.cmd in (None, "list"):
        list_models()
        return 0

    if not server_up():
        _hint_and_exit()
    targets = ([args.model] if args.model
               else [m["name"] for m in _get("/api/tags").get("models", [])])
    if not targets:
        print("No models installed to operate on.")
        return 1

    if args.cmd == "sanity":
        print("Sanity generation:")
        ok = all(sanity(m) for m in targets)
        return 0 if ok else 1
    if args.cmd == "bench":
        for m in targets:
            bench(m, write_report=args.report)
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

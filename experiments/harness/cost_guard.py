"""Cost guard for paid model calls (Phase 0.4).

Two jobs (CLAUDE.md §8):
  1. A persistent spend tally on disk (data/processed/_spend.json) — every paid call
     records its real token cost.
  2. A pre-flight estimator that REFUSES to start a paid arm whose estimated cost would
     push total spend past the EUR ceiling (€150). Prints the estimate first.

Pricing + budget live in experiments/configs/pricing.yaml (edit there, not here).

CLI:
  python -m experiments.harness.cost_guard status            # show ledger + remaining budget
  python -m experiments.harness.cost_guard estimate MODEL N  # estimate N calls of MODEL
  python -m experiments.harness.cost_guard selftest          # offline logic check (no API)
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
PRICING_PATH = REPO_ROOT / "experiments" / "configs" / "pricing.yaml"
LEDGER_PATH = REPO_ROOT / "data" / "processed" / "_spend.json"


class BudgetExceeded(RuntimeError):
    """Raised by pre-flight when an estimated arm would breach the EUR ceiling."""


def load_pricing(path: Path = PRICING_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@dataclass
class Estimate:
    model: str
    n_calls: int
    input_tokens: int
    output_tokens: int
    cost_eur: float

    def __str__(self) -> str:
        return (
            f"{self.model}: {self.n_calls} calls "
            f"(~{self.input_tokens:,} in + {self.output_tokens:,} out tok) "
            f"≈ €{self.cost_eur:.2f}"
        )


class CostGuard:
    def __init__(self, pricing: dict | None = None, ledger_path: Path = LEDGER_PATH):
        self.pricing = pricing or load_pricing()
        self.ledger_path = ledger_path
        self.eur_per_usd = float(self.pricing["eur_per_usd"])
        self.ceiling_eur = float(self.pricing["budget_eur_ceiling"])  # OpenAI anchor
        di = self.pricing.get("deepinfra_budget_eur_ceiling")
        self.deepinfra_ceiling_eur = float(di) if di is not None else None
        self._ledger = self._load_ledger()

    def provider_of(self, model: str) -> str:
        return self.pricing.get("models", {}).get(model, {}).get("provider", "unknown")

    def ceiling_for(self, provider: str) -> float:
        if provider == "deepinfra":
            return self.deepinfra_ceiling_eur if self.deepinfra_ceiling_eur is not None else float("inf")
        if provider in ("openai",):
            return self.ceiling_eur
        return self.ceiling_eur  # default/anchor-style providers (deepseek/anthropic/google) on the €150

    def spent_for(self, provider: str) -> float:
        return round(sum(e["cost_eur"] for e in self._ledger["entries"]
                         if e.get("meta", {}).get("provider") == provider), 6)

    def remaining_for(self, provider: str) -> float:
        return self.ceiling_for(provider) - self.spent_for(provider)

    # ---- ledger persistence -------------------------------------------------
    def _load_ledger(self) -> dict:
        if self.ledger_path.exists():
            data = json.loads(self.ledger_path.read_text())
            data.setdefault("entries", [])
            data.setdefault("total_spent_eur", 0.0)
            data["ceiling_eur"] = self.ceiling_eur  # keep in sync with config
            return data
        return {"ceiling_eur": self.ceiling_eur, "total_spent_eur": 0.0, "entries": []}

    def _save_ledger(self) -> None:
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.ledger_path.write_text(json.dumps(self._ledger, indent=2))

    # ---- pricing ------------------------------------------------------------
    def _model_price(self, model: str) -> dict:
        models = self.pricing.get("models", {})
        if model not in models:
            raise KeyError(
                f"Unknown model '{model}'. Known: {', '.join(sorted(models))}. "
                f"Add it to {PRICING_PATH.relative_to(REPO_ROOT)}."
            )
        return models[model]

    def cost_eur(self, model: str, input_tokens: int, output_tokens: int) -> float:
        p = self._model_price(model)
        usd = (
            input_tokens / 1e6 * float(p["input_per_1m_usd"])
            + output_tokens / 1e6 * float(p["output_per_1m_usd"])
        )
        return usd * self.eur_per_usd

    # ---- estimation + pre-flight -------------------------------------------
    def estimate(
        self,
        model: str,
        n_calls: int,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        reasoning: bool = False,
    ) -> Estimate:
        """Estimate the cost of an arm. Falls back to default per-call token
        assumptions from pricing.yaml when measured counts aren't supplied."""
        d = self.pricing["default_call_tokens"]
        in_per = input_tokens if input_tokens is not None else int(d["input"])
        out_per = (
            output_tokens
            if output_tokens is not None
            else int(d["output_reasoning"] if reasoning else d["output"])
        )
        tot_in, tot_out = in_per * n_calls, out_per * n_calls
        return Estimate(model, n_calls, tot_in, tot_out,
                        self.cost_eur(model, tot_in, tot_out))

    def remaining_eur(self) -> float:
        return self.ceiling_eur - float(self._ledger["total_spent_eur"])

    def preflight(self, estimate: Estimate, *, verbose: bool = True) -> Estimate:
        """Print the estimate; raise BudgetExceeded if it would breach the ceiling."""
        remaining = self.remaining_eur()
        projected = float(self._ledger["total_spent_eur"]) + estimate.cost_eur
        if verbose:
            print(f"[cost-guard] {estimate}")
            print(f"[cost-guard] spent €{self._ledger['total_spent_eur']:.2f} / "
                  f"€{self.ceiling_eur:.0f}  |  remaining €{remaining:.2f}  |  "
                  f"after this arm €{projected:.2f}")
        if projected > self.ceiling_eur:
            raise BudgetExceeded(
                f"Arm '{estimate.model}' (~€{estimate.cost_eur:.2f}) would push spend to "
                f"€{projected:.2f}, over the €{self.ceiling_eur:.0f} ceiling "
                f"(remaining €{remaining:.2f}). Refusing to start."
            )
        return estimate

    # ---- recording ----------------------------------------------------------
    def record(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        meta: dict | None = None,
    ) -> float:
        """Record one real paid call; persist; return the EUR charged. The provider is
        auto-stamped into meta so per-provider spend (OpenAI vs DeepInfra) is computable."""
        cost = self.cost_eur(model, input_tokens, output_tokens)
        m = dict(meta or {})
        m.setdefault("provider", self.provider_of(model))
        self._ledger["entries"].append({
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_eur": round(cost, 6),
            "meta": m,
        })
        self._ledger["total_spent_eur"] = round(
            float(self._ledger["total_spent_eur"]) + cost, 6
        )
        self._save_ledger()
        return cost

    # ---- reporting ----------------------------------------------------------
    def status(self) -> str:
        n = len(self._ledger["entries"])
        lines = [
            f"Ledger: {self.ledger_path.relative_to(REPO_ROOT)}",
            f"  ceiling      €{self.ceiling_eur:.2f}",
            f"  spent        €{float(self._ledger['total_spent_eur']):.4f}",
            f"  remaining    €{self.remaining_eur():.4f}",
            f"  calls logged {n}",
        ]
        return "\n".join(lines)


# --------------------------------------------------------------------------- CLI
def _selftest() -> int:
    """Offline check of the estimator + refusal logic, using a throwaway ledger."""
    import tempfile

    pricing = load_pricing()
    with tempfile.TemporaryDirectory() as td:
        guard = CostGuard(pricing=pricing, ledger_path=Path(td) / "_spend.json")
        # 1) estimate maths
        est = guard.estimate("deepseek-chat", n_calls=1000)
        print("estimate (1000 deepseek-chat, default tokens):", est)
        assert est.cost_eur > 0
        # 2) record updates the tally
        charged = guard.record("deepseek-chat", 1500, 600, meta={"smoke": True})
        # ledger stores spend rounded to 6 dp; allow for that
        assert abs(guard._ledger["total_spent_eur"] - charged) < 1e-6
        print(f"recorded 1 call: €{charged:.6f}; remaining €{guard.remaining_eur():.2f}")
        # 3) pre-flight refuses an over-budget arm
        big = guard.estimate("claude-sonnet-4-6", n_calls=5_000_000, reasoning=True)
        try:
            guard.preflight(big, verbose=False)
        except BudgetExceeded as e:
            print("refused as expected:", str(e)[:80], "...")
        else:
            print("ERROR: over-budget arm was NOT refused")
            return 1
        # 4) an affordable arm passes
        ok = guard.estimate("deepseek-chat", n_calls=100)
        guard.preflight(ok, verbose=False)
        print("affordable arm passed pre-flight OK")
    print("selftest: PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Cost guard (Phase 0.4)")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("status", help="show ledger + remaining budget")
    ep = sub.add_parser("estimate", help="estimate an arm")
    ep.add_argument("model")
    ep.add_argument("n_calls", type=int)
    ep.add_argument("--reasoning", action="store_true")
    sub.add_parser("selftest", help="offline logic check")
    args = p.parse_args(argv)

    if args.cmd == "selftest":
        return _selftest()
    guard = CostGuard()
    if args.cmd == "estimate":
        est = guard.estimate(args.model, args.n_calls, reasoning=args.reasoning)
        try:
            guard.preflight(est)
        except BudgetExceeded as e:
            print(f"[cost-guard] WOULD REFUSE: {e}")
            return 1
        return 0
    # default: status
    print(guard.status())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

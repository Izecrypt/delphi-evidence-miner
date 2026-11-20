"""CLI: list markets, rank them, draft a submission (dry run)."""
import argparse
from datetime import datetime, timezone, timedelta

from .config import Config
from .markets import Market, rank_markets
from .evidence import Evidence, Source, FactIndex, compose_note, fact_key
from .ledger import Ledger
from .submissions import Submitter

SCOUT_TOPICS = {"politics", "economics", "crypto", "technology", "current events"}


def mock_markets() -> list[Market]:
    now = datetime.now(timezone.utc)
    return [
        Market("m1", "Will the CBN hold rates in Q4?", "economics",
               0.62, now + timedelta(days=5), now + timedelta(days=4), 120.0),
        Market("m2", "Will a top-10 crypto hit a new ATH in 2026?", "crypto",
               0.28, now + timedelta(days=9), now + timedelta(days=8), 300.0),
        Market("m3", "Will team X win the league?", "sports",
               0.55, now + timedelta(days=2), now + timedelta(days=1), 80.0),
    ]


def main() -> None:
    ap = argparse.ArgumentParser(description="delphi evidence miner")
    ap.add_argument("cmd", choices=["markets", "draft"], help="list ranked markets | draft a dry-run submission")
    ap.add_argument("--market", help="market id for draft")
    args = ap.parse_args()

    cfg = Config()
    ledger = Ledger("data/ledger.jsonl")
    markets = mock_markets()

    if args.cmd == "markets":
        for m in rank_markets(markets, SCOUT_TOPICS):
            print(f"{m.id}  pot=${m.reward_pot:<7.0f} closes={m.close_time:%b %d}  {m.question}")

    elif args.cmd == "draft":
        ev = Evidence(
            market_id=args.market or "m2",
            note=compose_note(
                "Regulatory filings show X.",
                [Source("https://example.gov/filing", "2026-11-20",
                        "Verbatim key text goes here so the judge does not need the page.",
                        "data/screenshots/filing.png")],
            ),
        )
        fact_key(ev)
        idx = FactIndex()
        if idx.is_repeat(ev):
            print("REPEAT — do not submit")
            return
        sub = Submitter(cfg, ledger)
        result = sub.submit(ev, ev.market_id)
        print(f"status={result.status} id={result.submission_id}")
        print(ledger.totals())


if __name__ == "__main__":
    main()

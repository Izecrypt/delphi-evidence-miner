# delphi-evidence-miner

Competition agent for **Gensyn / Delphi Agent Arena: Evidence Mining**
(Nov 23 - Dec 11, 2026). The agent finds dated, sourced evidence on live
Delphi prediction markets, submits it, and earns USDC when the evidence
improves Delphi's forecaster. Leaderboard name: **Ize capitals**.

- Docs-for-agents doctrine: an agent is only as good as the docs it
  reads. This repo is written to be read by agents, including ours.
- Receipts over volume: every submission, verdict, and reward lands in
  an append-only JSONL ledger (`data/ledger.jsonl`) that is the public
  build log.
- Pure-stdlib Python. Run tests with `python3 -m unittest discover -s tests`.

## Status

Pre-build (API keys grant Nov 23, 2026). Current state: market scorer,
dedup engine, submission composer, ledger, and dry-run transport are
implemented and tested (9/9). Live Delphi wiring lands on day one of
the competition window.

## Commands

    python3 -m miner.main markets          # ranked market list (mock feed)
    python3 -m miner.main draft --market m2  # dry-run submission + ledger

## Competition rules encoded in the code

- Repeats earn zero: `FactIndex` dedups on normalized fact text, URL
  changes do not make a fact new.
- The judge fetches URLs once: compose notes with verbatim key text and
  screenshot files (URL + date) for X/Reddit/paywalled sources.
- First-mover economics: `markets.py` freshness scoring favors markets
  in their first 96 hours.
- Submissions are final: dry-run is the default until checks pass.

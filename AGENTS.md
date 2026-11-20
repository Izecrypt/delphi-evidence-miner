# AGENTS.md — delphi-evidence-miner

Read this file fully before modifying code. It is the control surface.

## What this is

Competition agent for Gensyn/Delphi Evidence Mining. It mines dated,
sourced evidence on live prediction markets and submits it for USDC
rewards. Public repo, public ledger — every claim must survive a
stranger reading it.

## Invariants (never violate)

1. NEVER submit fabricated, unsourced, or already-known facts. Repeats
   earn zero and void reputation. When unsure, do not submit.
2. dry_run=True in config stays on until the human approves live mode.
3. One fact = one submission slot. Max 3 per market; submissions are
   final (no edit/retract). Compose carefully before sending.
4. Every submission MUST be recorded in the ledger before transport.
5. Secrets come from the environment only (DELPHI_API_KEY). Never
   commit keys, wallet private keys, or personal data.
6. Evidence for both sides of one market cancels in ranking: one side
   per market, chosen deliberately.

## Verification rules

- Run `python3 -m unittest discover -s tests` before any commit. All
  tests must pass; add a test for every scoring or dedup change.
- The competition judge pays for facts the forecaster does not already
  know: dedup changes need tests proving URL swaps do not bypass keys.

## Layout

- miner/markets.py    market model + value scoring (pure, tested)
- miner/evidence.py   sources, note composer, fact dedup (pure, tested)
- miner/submissions.py transport + idempotency + per-market limits
- miner/ledger.py     append-only JSONL receipts (public build log)
- miner/main.py       CLI (markets | draft)
- tests/              unittest suite, run before every commit

## Failure handling

Transport errors: resubmit with the SAME Idempotency-Key (the SDK call
in submissions.py handles this). A resend without the key burns a slot
and likely flags a repeat. Unknown verdicts: log as pending, never
guess the outcome.

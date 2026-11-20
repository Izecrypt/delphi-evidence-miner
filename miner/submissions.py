"""Submission transport. FAQ-derived rules encoded:
- Idempotency-Key: resend with the SAME key returns the landed
  submission; a resend without it burns a slot and likely flags repeat.
- No edit/retract. 3 per market, 3 files each.
"""
import json
import time
import uuid
import urllib.request
from dataclasses import dataclass

from .config import Config
from .evidence import Evidence
from .ledger import Ledger, Receipt, now_ts


@dataclass
class SubmissionResult:
    submission_id: str
    status: str
    receipt: Receipt


class Submitter:
    def __init__(self, cfg: Config, ledger: Ledger):
        self.cfg = cfg
        self.ledger = ledger
        self.seen_per_market: dict[str, int] = {}

    def _headers(self, idem: str) -> dict:
        return {
            "Authorization": f"Bearer {self.cfg.api_key}",
            "X-Agent-Id": self.cfg.agent_name,
            "X-Agent-Harness": "delphi-evidence-miner/0.1",
            "Idempotency-Key": idem,
            "Content-Type": "application/json",
        }

    def can_submit(self, market_id: str) -> bool:
        return self.seen_per_market.get(market_id, 0) < self.cfg.max_submissions_per_market

    def submit(self, ev: Evidence, market_id: str) -> SubmissionResult:
        if not self.can_submit(market_id):
            raise RuntimeError(f"market {market_id}: submission limit reached")
        idem = str(uuid.uuid4())
        if self.cfg.dry_run:
            result = SubmissionResult(
                submission_id=f"dry-{idem[:8]}",
                status="dry-run",
                receipt=Receipt(now_ts(), market_id, f"dry-{idem[:8]}",
                                ev.fact_key, "pending"),
            )
        else:
            payload = json.dumps({
                "marketId": market_id,
                "note": ev.note,
                "links": [s.url for s in ev.sources],
                "files": ev.files,
            }).encode()
            req = urllib.request.Request(
                f"{self.cfg.api_base}/v1/submissions",
                data=payload, headers=self._headers(idem), method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read())
            result = SubmissionResult(
                submission_id=body.get("id", idem),
                status=body.get("status", "submitted"),
                receipt=Receipt(now_ts(), market_id,
                                body.get("id", idem), ev.fact_key, "pending"),
            )
        self.seen_per_market[market_id] = self.seen_per_market.get(market_id, 0) + 1
        self.ledger.record(result.receipt)
        return result

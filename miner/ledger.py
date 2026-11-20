"""Append-only receipts ledger. Every submission, verdict, and reward is
logged as JSONL — this file is the public build log and the scoreboard
receipt in one."""
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Receipt:
    ts: float
    market_id: str
    submission_id: str
    fact_key: str
    verdict: str            # pending | judged | repeat | settled
    rationale: str = ""
    judgment_reward: float = 0.0
    settlement_reward: float = 0.0


class Ledger:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def record(self, r: Receipt) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(r)) + "\n")

    def all(self) -> list[Receipt]:
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text().splitlines():
            if line.strip():
                out.append(Receipt(**json.loads(line)))
        return out

    def totals(self) -> dict:
        rs = self.all()
        return {
            "submissions": len(rs),
            "judged": sum(1 for r in rs if r.verdict == "judged"),
            "judgment_usdc": sum(r.judgment_reward for r in rs),
            "settlement_usdc": sum(r.settlement_reward for r in rs),
        }


def now_ts() -> float:
    return time.time()

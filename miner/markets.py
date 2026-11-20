"""Market model and prioritization. Pure logic, fully testable."""
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Market:
    id: str
    question: str
    category: str
    yes_odds: float
    close_time: datetime
    evidence_cutoff: datetime
    reward_pot: float
    forecaster_prob: float | None = None  # None -> use odds as fallback

    def hours_until(self, now: datetime | None = None) -> float:
        now = now or datetime.now(timezone.utc)
        return (self.evidence_cutoff - now).total_seconds() / 3600


def coverage_score(market: Market, topics_covered: set[str]) -> float:
    """How well our existing scouts cover this market's category. 0..1."""
    return 1.0 if market.category in topics_covered else 0.4


def freshness_score(market: Market, now: datetime | None = None) -> float:
    """First-mover economics: fresh markets pay, drained ones don't."""
    h = market.hours_until(now)
    if h <= 0:
        return 0.0
    if h < 24:
        return 0.4  # late, likely mined
    if h < 96:
        return 1.0  # sweet spot
    return 0.8


def value_score(market: Market, topics_covered: set[str],
                now: datetime | None = None) -> float:
    """Composite priority: reward pot x coverage x freshness."""
    return (market.reward_pot
            * coverage_score(market, topics_covered)
            * freshness_score(market, now))


def rank_markets(markets: list[Market], topics_covered: set[str],
                 now: datetime | None = None) -> list[Market]:
    return sorted(markets,
                  key=lambda m: value_score(m, topics_covered, now),
                  reverse=True)

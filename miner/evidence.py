"""Evidence compilation, dedup, and submission composition.

Competition rules that shape this module:
- Repeats earn zero. Facts already known to the forecaster earn zero.
- The judge fetches cited URLs once; X/Reddit/paywalls fail, so the
  note must carry the key text and a screenshot file (URL + date).
- Submissions cannot be edited or retracted. Compose carefully.
"""
import hashlib
import re
from dataclasses import dataclass, field


@dataclass
class Source:
    url: str
    published: str          # ISO date of the underlying fact
    key_text: str           # verbatim text pasted for the judge
    screenshot: str | None = None  # path to png/jpg showing URL + date


@dataclass
class Evidence:
    market_id: str
    note: str
    sources: list[Source] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    fact_key: str = ""      # filled by compose()

    def normalized_fact(self) -> str:
        words = [w for s in self.sources for w in s.key_text.lower().split()]
        base = " ".join(sorted(words)) if words else self.note.lower()
        return re.sub(r"[^a-z0-9 ]", "", base)


def fact_key(ev: Evidence) -> str:
    ev.fact_key = hashlib.sha256(ev.normalized_fact().encode()).hexdigest()[:16]
    return ev.fact_key


class FactIndex:
    """What we (and the forecaster, via our public briefs) already know."""

    def __init__(self):
        self.known: set[str] = set()

    def add(self, ev: Evidence) -> None:
        self.known.add(fact_key(ev))

    def is_repeat(self, ev: Evidence) -> bool:
        return fact_key(ev) in self.known


def compose_note(headline: str, sources: list[Source]) -> str:
    """Note format: claim + dated, sourced facts with key text inline."""
    parts = [headline.strip()]
    for s in sources:
        parts.append(f"[{s.published}] {s.key_text.strip()} ({s.url})")
    return "\n\n".join(p for p in parts if p)

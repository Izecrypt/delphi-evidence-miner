import unittest
from datetime import datetime, timezone, timedelta

from miner.markets import Market, rank_markets, value_score
from miner.evidence import Evidence, Source, FactIndex, compose_note, fact_key
from miner.ledger import Ledger, Receipt
from miner.submissions import Submitter
from miner.config import Config


NOW = datetime(2026, 11, 20, tzinfo=timezone.utc)


def mk_market(**kw):
    base = dict(id="m", question="q?", category="crypto", yes_odds=0.5,
                close_time=NOW + timedelta(days=5),
                evidence_cutoff=NOW + timedelta(days=4), reward_pot=100.0)
    base.update(kw)
    return Market(**base)


def mk_evidence(key_text="the filing states the launch moved to q1"):
    srcs = [Source("https://example.gov/x", "2026-11-19", key_text)]
    return Evidence(market_id="m", note=compose_note("Claim.", srcs),
                    sources=srcs, fact_key="")


class TestScoring(unittest.TestCase):
    def test_fresh_beats_drained(self):
        fresh = mk_market(evidence_cutoff=NOW + timedelta(days=3))
        drained = mk_market(evidence_cutoff=NOW + timedelta(hours=6))
        self.assertGreater(value_score(fresh, {"crypto"}, NOW),
                           value_score(drained, {"crypto"}, NOW))

    def test_covered_topic_beats_uncovered(self):
        covered = mk_market(category="crypto")
        uncovered = mk_market(category="sports")
        self.assertGreater(value_score(covered, {"crypto"}, NOW),
                           value_score(uncovered, {"crypto"}, NOW))

    def test_closed_market_scores_zero(self):
        closed = mk_market(evidence_cutoff=NOW - timedelta(hours=1))
        self.assertEqual(value_score(closed, {"crypto"}, NOW), 0.0)


class TestDedup(unittest.TestCase):
    def test_same_fact_repeats_regardless_of_url(self):
        a = mk_evidence()
        b = mk_evidence()
        b.sources[0].url = "https://another-site.example/x"
        self.assertEqual(fact_key(a), fact_key(b))

    def test_index_blocks_repeat(self):
        idx = FactIndex()
        ev = mk_evidence()
        self.assertFalse(idx.is_repeat(ev))
        idx.add(ev)
        self.assertTrue(idx.is_repeat(mk_evidence()))

    def test_different_fact_different_key(self):
        a, b = mk_evidence(), mk_evidence("completely different fact entirely")
        self.assertNotEqual(fact_key(a), fact_key(b))


class TestLedger(unittest.TestCase):
    def test_append_and_totals(self, ):
        import tempfile, os
        with tempfile.TemporaryDirectory() as d:
            led = Ledger(os.path.join(d, "l.jsonl"))
            led.record(Receipt(1.0, "m", "s1", "k1", "judged", "moved", 2.5, 0.0))
            led.record(Receipt(2.0, "m", "s2", "k2", "judged", "settled", 1.0, 4.0))
            t = led.totals()
            self.assertEqual(t["submissions"], 2)
            self.assertEqual(t["judgment_usdc"], 3.5)
            self.assertEqual(t["settlement_usdc"], 4.0)


class TestSubmitter(unittest.TestCase):
    def test_market_limit_enforced(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as d:
            sub = Submitter(Config(), Ledger(os.path.join(d, "l.jsonl")))
            for _ in range(3):
                self.assertTrue(sub.can_submit("m"))
                sub.submit(mk_evidence(), "m")
            self.assertFalse(sub.can_submit("m"))

    def test_dry_run_records_receipt(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as d:
            led = Ledger(os.path.join(d, "l.jsonl"))
            sub = Submitter(Config(), led)
            ev = mk_evidence()
            fact_key(ev)
            r = sub.submit(ev, "m")
            self.assertEqual(r.status, "dry-run")
            self.assertEqual(led.totals()["submissions"], 1)


if __name__ == "__main__":
    unittest.main()

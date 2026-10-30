from __future__ import annotations

import unittest

from evaluation.run_evaluation import actionable_steps, classify_repository, ratio, supported_findings


def packet(*, archived: bool = False, days_inactive: int | None = 10):
    return {
        "repository": {"archived": archived},
        "statistics": {"days_inactive": days_inactive},
    }


class EvaluationTests(unittest.TestCase):
    def test_classifies_archived_before_inactivity(self):
        self.assertEqual(classify_repository(packet(archived=True, days_inactive=1)), "archived")

    def test_classifies_inactive_and_active_repositories(self):
        self.assertEqual(classify_repository(packet(days_inactive=365)), "inactive")
        self.assertEqual(classify_repository(packet(days_inactive=364)), "active")

    def test_support_and_actionability_require_valid_evidence(self):
        valid = {"E-001"}
        findings = [
            {"evidence_ids": ["E-001"]},
            {"evidence_ids": ["E-999"]},
            {"evidence_ids": []},
        ]
        steps = [
            {"action": "Verify", "effort": "1 hour", "evidence_ids": ["E-001"]},
            {"action": "Guess", "effort": "1 hour", "evidence_ids": ["E-999"]},
        ]
        self.assertEqual(supported_findings(findings, valid), 1)
        self.assertEqual(actionable_steps(steps, valid), 1)
        self.assertEqual(ratio(1, 2), 0.5)


if __name__ == "__main__":
    unittest.main()

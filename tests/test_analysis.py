from __future__ import annotations

import unittest

from core.claim_validator import validate_findings
from core.resurrection import build_resurrection_plan


PACKET = {"repository":{"full_name":"ghost/example","archived":False},"statistics":{"days_inactive":800,"open_items":12,"stars":90},"evidence":[{"id":"E-001","claim":"Repository archival state","value":False},{"id":"E-002","claim":"Days since the last recorded push","value":800},{"id":"E-003","claim":"Open issue and pull-request count","value":12},{"id":"E-004","claim":"Primary language by bytes","value":"Python"}]}


class ClaimValidatorTests(unittest.TestCase):
    def test_removes_unsupported_claim(self):
        result = {"findings":[{"finding":"Invented","evidence_ids":["E-999"],"confidence":1,"uncertainties":[],"recommended_action":"None"}]}
        validated, warnings = validate_findings(result, PACKET)
        self.assertEqual(validated["findings"], [])
        self.assertTrue(any("removed" in warning for warning in warnings))

    def test_clamps_confidence_and_keeps_valid_evidence(self):
        result = {"findings":[{"finding":"Observed","evidence_ids":["E-002"],"confidence":4.2,"uncertainties":["Motive unknown"],"recommended_action":"Verify"}]}
        validated, _ = validate_findings(result, PACKET)
        self.assertEqual(validated["findings"][0]["confidence"], 1.0)

    def test_resurrection_plan_is_actionable(self):
        analysis = {"findings":[{"recommended_action":"Reproduce issue 1","evidence_ids":["E-003"]}]}
        plan = build_resurrection_plan(PACKET, analysis)
        self.assertGreaterEqual(len(plan), 5)
        self.assertTrue(all(step.get("action") and step.get("effort") for step in plan))


if __name__ == "__main__":
    unittest.main()

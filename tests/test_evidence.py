from __future__ import annotations

import unittest
from unittest.mock import patch

from core.evidence_builder import build_evidence_packet
from core.github_client import parse_public_github_url


def github_fixture():
    return {"repository":{"full_name":"ghost/example","html_url":"https://github.com/ghost/example","description":"A forgotten example","archived":True,"pushed_at":"2020-01-01T00:00:00Z","open_issues_count":7,"stargazers_count":42,"forks_count":3,"license":{"spdx_id":"MIT"},"default_branch":"main","topics":["example"]},"languages":{"Python":1200,"HTML":300},"issues":[{"title":"Document install failure","state":"open","html_url":"https://github.com/ghost/example/issues/1"}],"contributors":[{"login":"octocat"}]}


class URLTests(unittest.TestCase):
    def test_parses_public_github_url(self):
        self.assertEqual(parse_public_github_url("https://github.com/openai/openai-python.git").slug, "openai/openai-python")

    def test_rejects_non_github_host(self):
        with self.assertRaises(ValueError):
            parse_public_github_url("https://evil.example/openai/openai-python")

    def test_rejects_nested_paths(self):
        with self.assertRaises(ValueError):
            parse_public_github_url("https://github.com/openai/openai-python/issues")


class EvidenceTests(unittest.TestCase):
    @patch("core.evidence_builder.datetime")
    def test_builds_stable_linked_records(self, mocked_datetime):
        from datetime import datetime, timezone
        mocked_datetime.now.return_value = datetime(2026, 10, 29, tzinfo=timezone.utc)
        mocked_datetime.fromisoformat.side_effect = datetime.fromisoformat
        packet = build_evidence_packet(github_fixture())
        self.assertEqual(packet["repository"]["full_name"], "ghost/example")
        self.assertEqual(packet["evidence"][0]["id"], "E-001")
        self.assertEqual(packet["evidence"][5]["value"], "Python")
        self.assertTrue(all(record["source_url"].startswith("https://github.com/") for record in packet["evidence"]))
        self.assertFalse(packet["analysis_policy"]["code_executed"])


if __name__ == "__main__":
    unittest.main()

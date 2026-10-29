from __future__ import annotations

import unittest
from unittest.mock import Mock

import requests

from core.github_client import GitHubClient, GitHubClientError, RepositoryRef


class GitHubFailureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = GitHubClient(token="test-token", timeout=1)
        self.ref = RepositoryRef("ghost", "example")

    def test_connection_failure_becomes_actionable_error(self):
        self.client.session.get = Mock(side_effect=requests.ConnectionError("DNS failed"))

        with self.assertRaisesRegex(GitHubClientError, "internet or DNS"):
            self.client.repository(self.ref)

    def test_timeout_becomes_actionable_error(self):
        self.client.session.get = Mock(side_effect=requests.Timeout("too slow"))

        with self.assertRaisesRegex(GitHubClientError, "did not respond in time"):
            self.client.repository(self.ref)

    def test_missing_repository_is_reported(self):
        response = Mock(status_code=404, headers={})
        self.client.session.get = Mock(return_value=response)

        with self.assertRaisesRegex(GitHubClientError, "not found"):
            self.client.repository(self.ref)

    def test_rate_limit_is_reported(self):
        response = Mock(status_code=403, headers={"X-RateLimit-Remaining": "0"})
        self.client.session.get = Mock(return_value=response)

        with self.assertRaisesRegex(GitHubClientError, "rate limit"):
            self.client.repository(self.ref)

    def test_malformed_json_is_reported(self):
        response = Mock(status_code=200, headers={})
        response.raise_for_status.return_value = None
        response.json.side_effect = ValueError("not JSON")
        self.client.session.get = Mock(return_value=response)

        with self.assertRaisesRegex(GitHubClientError, "unreadable repository"):
            self.client.repository(self.ref)

    def test_unexpected_json_shape_is_reported(self):
        response = Mock(status_code=200, headers={})
        response.raise_for_status.return_value = None
        response.json.return_value = ["not", "metadata"]
        self.client.session.get = Mock(return_value=response)

        with self.assertRaisesRegex(GitHubClientError, "unexpected repository"):
            self.client.repository(self.ref)


if __name__ == "__main__":
    unittest.main()

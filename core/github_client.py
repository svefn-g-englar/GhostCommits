"""Read-only GitHub REST client with strict public-repository validation."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests


GITHUB_HOSTS = {"github.com", "www.github.com"}
REPO_PART = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")


class GitHubClientError(RuntimeError):
    """Raised when GitHub cannot provide a safe, usable response."""


@dataclass(frozen=True)
class RepositoryRef:
    owner: str
    name: str

    @property
    def slug(self) -> str:
        return f"{self.owner}/{self.name}"

    @property
    def url(self) -> str:
        return f"https://github.com/{self.slug}"


def parse_public_github_url(value: str) -> RepositoryRef:
    """Accept owner/repo or an HTTPS github.com URL and reject ambiguous hosts."""
    raw = value.strip().removesuffix(".git").rstrip("/")
    if "://" not in raw:
        parts = raw.split("/")
    else:
        parsed = urlparse(raw)
        if parsed.scheme != "https" or parsed.hostname not in GITHUB_HOSTS:
            raise ValueError("Only HTTPS URLs for public github.com repositories are accepted.")
        if parsed.username or parsed.password or parsed.port:
            raise ValueError("Credentials and custom ports are not accepted in repository URLs.")
        parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 2 or not all(REPO_PART.fullmatch(part) for part in parts):
        raise ValueError("Use a repository URL such as https://github.com/owner/project.")
    return RepositoryRef(parts[0], parts[1])


class GitHubClient:
    """Minimal GitHub API client; all operations are read-only and time-bounded."""

    def __init__(self, token: Optional[str] = None, timeout: int = 20) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "GhostCommits/1.0",
            }
        )
        token = token or os.getenv("GITHUB_TOKEN")
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        response = self.session.get(
            f"https://api.github.com{path}", params=params, timeout=self.timeout
        )
        if response.status_code == 404:
            raise GitHubClientError("Repository not found or not publicly accessible.")
        if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
            raise GitHubClientError("GitHub API rate limit reached. Add GITHUB_TOKEN and retry.")
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise GitHubClientError(f"GitHub returned HTTP {response.status_code}.") from exc
        return response

    def repository(self, ref: RepositoryRef) -> Dict[str, Any]:
        data = self._get(f"/repos/{ref.slug}").json()
        if data.get("private"):
            raise GitHubClientError("Private repositories are intentionally unsupported.")
        return data

    def commits(self, ref: RepositoryRef, limit: int = 100) -> List[Dict[str, Any]]:
        return self._get(
            f"/repos/{ref.slug}/commits", {"per_page": min(max(limit, 1), 100)}
        ).json()

    def issues(self, ref: RepositoryRef, limit: int = 40) -> List[Dict[str, Any]]:
        records = self._get(
            f"/repos/{ref.slug}/issues",
            {"state": "open", "sort": "updated", "per_page": min(limit, 100)},
        ).json()
        return [item for item in records if "pull_request" not in item]

    def contributors(self, ref: RepositoryRef, limit: int = 100) -> List[Dict[str, Any]]:
        response = self._get(
            f"/repos/{ref.slug}/contributors", {"anon": "true", "per_page": min(limit, 100)}
        )
        return response.json()

    def languages(self, ref: RepositoryRef) -> Dict[str, int]:
        return self._get(f"/repos/{ref.slug}/languages").json()

    def collect(self, value: str) -> Tuple[RepositoryRef, Dict[str, Any]]:
        ref = parse_public_github_url(value)
        repo = self.repository(ref)
        commits = self.commits(ref)
        return ref, {
            "repository": repo,
            "commits": commits,
            "issues": self.issues(ref),
            "contributors": self.contributors(ref),
            "languages": self.languages(ref),
        }

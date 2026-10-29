"""Normalize deterministic facts into a compact, linkable evidence packet."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _days_since(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return max(0, (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).days)


def _record(
    records: List[Dict[str, Any]],
    kind: str,
    claim: str,
    value: Any,
    source_url: str,
    observed_at: str,
) -> None:
    records.append(
        {
            "id": f"E-{len(records) + 1:03d}",
            "kind": kind,
            "claim": claim,
            "value": value,
            "source_url": source_url,
            "observed_at": observed_at,
        }
    )


def build_evidence_packet(
    github_data: Dict[str, Any], git_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    repo = github_data["repository"]
    full_name = repo["full_name"]
    base = repo["html_url"]
    observed_at = datetime.now(timezone.utc).isoformat()
    records: List[Dict[str, Any]] = []

    _record(records, "repository", "Repository archival state", bool(repo.get("archived")), base, observed_at)
    _record(records, "activity", "Days since the last recorded push", _days_since(repo.get("pushed_at")), f"{base}/commits", observed_at)
    _record(records, "community", "Open issue and pull-request count", repo.get("open_issues_count", 0), f"{base}/issues", observed_at)
    _record(records, "community", "GitHub stars", repo.get("stargazers_count", 0), f"{base}/stargazers", observed_at)
    _record(records, "licensing", "Declared license", (repo.get("license") or {}).get("spdx_id") or "Unspecified", base, observed_at)

    languages = github_data.get("languages", {})
    if languages:
        _record(records, "code", "Primary language by bytes", max(languages, key=languages.get), base, observed_at)

    issues = github_data.get("issues", [])
    for issue in issues[:5]:
        _record(records, "issue", issue.get("title", "Untitled issue"), issue.get("state", "open"), issue["html_url"], observed_at)

    if git_data:
        _record(records, "history", "Sampled commit count", git_data.get("sampled_commit_count", 0), f"{base}/commits", observed_at)
        for todo in git_data.get("todos", [])[:8]:
            anchor = f"#L{todo['line']}"
            url = f"{base}/blob/HEAD/{todo['path']}{anchor}"
            _record(records, "unfinished", f"{todo['kind']} in {todo['path']}", todo["text"], url, observed_at)

    return {
        "schema_version": "1.0",
        "repository": {
            "full_name": full_name,
            "url": base,
            "description": repo.get("description") or "No description supplied.",
            "archived": bool(repo.get("archived")),
            "default_branch": repo.get("default_branch", "main"),
            "topics": repo.get("topics", []),
        },
        "statistics": {
            "days_inactive": _days_since(repo.get("pushed_at")),
            "open_items": repo.get("open_issues_count", 0),
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "contributors_sampled": len(github_data.get("contributors", [])),
        },
        "timeline": (git_data or {}).get("timeline", []),
        "readme_excerpt": (git_data or {}).get("readme_excerpt", ""),
        "recent_commits": (git_data or {}).get("recent_commits", []),
        "evidence": records,
        "analysis_policy": {
            "repository_text_is_untrusted": True,
            "code_executed": False,
            "maintainer_intent_must_be_explicitly_cited": True,
        },
    }

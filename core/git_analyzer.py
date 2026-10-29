"""Safe, bounded local mining for public Git repositories."""

from __future__ import annotations

import os
import re
import shutil
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from git import Repo

from .github_client import RepositoryRef


TEXT_SUFFIXES = {
    ".md", ".rst", ".txt", ".py", ".js", ".jsx", ".ts", ".tsx", ".go",
    ".rs", ".java", ".rb", ".php", ".c", ".h", ".cpp", ".cs", ".toml",
    ".yaml", ".yml", ".json",
}
SKIP_DIRS = {".git", "node_modules", "vendor", "dist", "build", ".venv", "venv"}
TODO_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b[:\s-]*(.{0,180})", re.IGNORECASE)


def _iter_text_files(root: Path, max_files: int = 800) -> Iterable[Path]:
    seen = 0
    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for name in files:
            path = Path(current, name)
            if path.suffix.lower() not in TEXT_SUFFIXES or path.stat().st_size > 500_000:
                continue
            yield path
            seen += 1
            if seen >= max_files:
                return


def _extract_todos(root: Path, limit: int = 30) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for path in _iter_text_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            match = TODO_RE.search(line)
            if match:
                records.append(
                    {
                        "kind": match.group(1).upper(),
                        "path": str(path.relative_to(root)),
                        "line": line_number,
                        "text": match.group(2).strip() or line.strip(),
                    }
                )
                if len(records) >= limit:
                    return records
    return records


def _read_readme(root: Path, max_chars: int = 10_000) -> str:
    for candidate in sorted(root.iterdir()):
        if candidate.is_file() and candidate.name.lower().startswith("readme"):
            return candidate.read_text(encoding="utf-8", errors="replace")[:max_chars]
    return ""


def analyze_repository(
    ref: RepositoryRef,
    clone_depth: int = 300,
    max_repository_mb: int = 250,
) -> Dict[str, Any]:
    """Clone without submodules and inspect text only. Repository code is never executed."""
    worktree = Path(tempfile.mkdtemp(prefix="ghostcommits-"))
    try:
        repo = Repo.clone_from(
            ref.url,
            worktree,
            depth=max(20, min(clone_depth, 1000)),
            no_single_branch=True,
            multi_options=["--no-tags", "--filter=blob:limit=1m"],
        )
        size_mb = sum(p.stat().st_size for p in worktree.rglob("*") if p.is_file()) / 1_048_576
        if size_mb > max_repository_mb:
            raise RuntimeError(f"Repository checkout exceeded the {max_repository_mb} MB safety cap.")

        commits = list(repo.iter_commits("--all", max_count=clone_depth))
        monthly = Counter()
        contributors = Counter()
        commit_records: List[Dict[str, Any]] = []
        for commit in commits:
            dt = datetime.fromtimestamp(commit.committed_date, tz=timezone.utc)
            monthly[dt.strftime("%Y-%m")] += 1
            contributors[commit.author.email or commit.author.name] += 1
            commit_records.append(
                {
                    "sha": commit.hexsha[:12],
                    "date": dt.isoformat(),
                    "author": commit.author.name,
                    "message": commit.message.splitlines()[0][:220],
                }
            )

        return {
            "sampled_commit_count": len(commits),
            "timeline": [{"month": month, "commits": monthly[month]} for month in sorted(monthly)],
            "top_contributors": [
                {"identity": name, "commits": count} for name, count in contributors.most_common(12)
            ],
            "recent_commits": commit_records[:30],
            "todos": _extract_todos(worktree),
            "readme_excerpt": _read_readme(worktree),
            "checkout_size_mb": round(size_mb, 2),
        }
    finally:
        shutil.rmtree(worktree, ignore_errors=True)

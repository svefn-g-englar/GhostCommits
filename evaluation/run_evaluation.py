"""Run the documented three-repository GhostCommits evaluation."""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List
from urllib.parse import urldefrag

import requests
from dotenv import load_dotenv

from core.claim_validator import validate_findings
from core.evidence_builder import build_evidence_packet
from core.gemma_engine import analyze_with_gemma
from core.git_analyzer import analyze_repository
from core.github_client import GitHubClient
from core.resurrection import build_resurrection_plan


load_dotenv()


CASES = [
    {
        "url": "https://github.com/jquery-archive/jquery-mobile",
        "expected_classification": "archived",
        "selection_reason": "GitHub explicitly marks the repository as archived.",
    },
    {
        "url": "https://github.com/nvbn/thefuck",
        "expected_classification": "inactive",
        "selection_reason": "Not archived, with no recorded push for more than one year at evaluation time.",
    },
    {
        "url": "https://github.com/pallets/flask",
        "expected_classification": "active",
        "selection_reason": "Not archived, with a recorded push within the last year at evaluation time.",
    },
]


def classify_repository(packet: Dict[str, Any], inactive_days: int = 365) -> str:
    if packet["repository"].get("archived"):
        return "archived"
    days = packet["statistics"].get("days_inactive")
    if days is not None and days >= inactive_days:
        return "inactive"
    return "active"


def ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def supported_findings(findings: Iterable[Dict[str, Any]], valid_ids: set[str]) -> int:
    supported = 0
    for finding in findings:
        citations = finding.get("evidence_ids", [])
        if citations and set(citations).issubset(valid_ids):
            supported += 1
    return supported


def actionable_steps(steps: Iterable[Dict[str, Any]], valid_ids: set[str]) -> int:
    actionable = 0
    for step in steps:
        citations = step.get("evidence_ids", [])
        if step.get("action") and step.get("effort") and citations and set(citations).issubset(valid_ids):
            actionable += 1
    return actionable


def validate_source_urls(records: Iterable[Dict[str, Any]], timeout: int = 15) -> Dict[str, Any]:
    session = requests.Session()
    session.headers.update({"User-Agent": "GhostCommits-Evaluation/1.0"})
    token = os.getenv("GITHUB_TOKEN")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    checked: List[Dict[str, Any]] = []
    for record in records:
        original = str(record.get("source_url", ""))
        url, _ = urldefrag(original)
        status: int | None = None
        error: str | None = None
        attempts = 0
        for attempts in range(1, 4):
            try:
                response = session.get(url, allow_redirects=True, timeout=timeout, stream=True)
                status = response.status_code
                response.close()
                error = None
                break
            except (requests.Timeout, requests.ConnectionError) as exc:
                error = type(exc).__name__
                if attempts < 3:
                    time.sleep(0.5 * attempts)
            except requests.RequestException as exc:
                error = type(exc).__name__
                break
        checked.append(
            {
                "evidence_id": record.get("id"),
                "url": original,
                "status": status,
                "valid": status is not None and status < 400,
                "error": error,
                "attempts": attempts,
            }
        )
    valid = sum(1 for item in checked if item["valid"])
    return {
        "valid": valid,
        "total": len(checked),
        "rate": ratio(valid, len(checked)),
        "failures": [item for item in checked if not item["valid"]],
    }


def run_case(
    case: Dict[str, str],
    clone_depth: int,
    max_repository_mb: int,
    allow_fallback: bool,
    check_urls: bool,
) -> Dict[str, Any]:
    started = time.perf_counter()
    client = GitHubClient()
    ref, github_data = client.collect(case["url"])
    git_data = analyze_repository(
        ref,
        clone_depth=clone_depth,
        max_repository_mb=max_repository_mb,
    )
    packet = build_evidence_packet(github_data, git_data)
    raw_analysis = analyze_with_gemma(packet, allow_fallback=allow_fallback)
    analysis, warnings = validate_findings(raw_analysis, packet)
    plan = build_resurrection_plan(packet, analysis)

    evidence = packet["evidence"]
    valid_ids = {record["id"] for record in evidence}
    findings = analysis.get("findings", [])
    supported = supported_findings(findings, valid_ids)
    actionable = actionable_steps(plan, valid_ids)
    source_check = (
        validate_source_urls(evidence)
        if check_urls
        else {"valid": None, "total": len(evidence), "rate": None, "failures": []}
    )
    observed = classify_repository(packet)

    return {
        "repository": ref.slug,
        "url": case["url"],
        "selection_reason": case["selection_reason"],
        "expected_classification": case["expected_classification"],
        "observed_classification": observed,
        "classification_correct": observed == case["expected_classification"],
        "archived": packet["repository"]["archived"],
        "days_inactive": packet["statistics"]["days_inactive"],
        "sampled_commits": git_data["sampled_commit_count"],
        "evidence_records": len(evidence),
        "source_validity": source_check,
        "findings": len(findings),
        "supported_findings": supported,
        "claim_support_rate": ratio(supported, len(findings)),
        "roadmap_steps": len(plan),
        "actionable_steps": actionable,
        "recommendation_actionability_rate": ratio(actionable, len(plan)),
        "duration_seconds": round(time.perf_counter() - started, 2),
        "model": analysis.get("model"),
        "used_ai": bool(analysis.get("used_ai")),
        "validator_warnings": warnings,
        "epitaph": analysis.get("epitaph"),
        "analysis": findings,
        "resurrection_plan": plan,
        "evidence": evidence,
    }


def aggregate(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_sources = sum(case["source_validity"]["total"] for case in cases)
    valid_sources = sum(case["source_validity"]["valid"] or 0 for case in cases)
    total_findings = sum(case["findings"] for case in cases)
    supported = sum(case["supported_findings"] for case in cases)
    total_steps = sum(case["roadmap_steps"] for case in cases)
    actionable = sum(case["actionable_steps"] for case in cases)
    return {
        "repositories_completed": len(cases),
        "classifications_correct": sum(1 for case in cases if case["classification_correct"]),
        "classification_accuracy": ratio(
            sum(1 for case in cases if case["classification_correct"]), len(cases)
        ),
        "valid_source_urls": valid_sources,
        "source_urls_checked": total_sources,
        "evidence_validity_rate": ratio(valid_sources, total_sources),
        "supported_findings": supported,
        "findings_checked": total_findings,
        "claim_support_rate": ratio(supported, total_findings),
        "actionable_steps": actionable,
        "roadmap_steps_checked": total_steps,
        "recommendation_actionability_rate": ratio(actionable, total_steps),
        "all_runs_used_ai": all(case["used_ai"] for case in cases),
        "total_duration_seconds": round(sum(case["duration_seconds"] for case in cases), 2),
        "average_duration_seconds": round(
            sum(case["duration_seconds"] for case in cases) / len(cases), 2
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="evaluation/results.json")
    parser.add_argument("--clone-depth", type=int, default=120)
    parser.add_argument("--max-repository-mb", type=int, default=250)
    parser.add_argument("--allow-fallback", action="store_true")
    parser.add_argument("--skip-url-checks", action="store_true")
    args = parser.parse_args()

    started_at = datetime.now(timezone.utc)
    results = [
        run_case(
            case,
            clone_depth=args.clone_depth,
            max_repository_mb=args.max_repository_mb,
            allow_fallback=args.allow_fallback,
            check_urls=not args.skip_url_checks,
        )
        for case in CASES
    ]
    report = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "method": {
            "repositories": len(CASES),
            "inactive_threshold_days": 365,
            "clone_depth": args.clone_depth,
            "max_repository_mb": args.max_repository_mb,
            "model": os.getenv("GHOSTCOMMITS_MODEL", "gemma3:1b"),
            "fallback_allowed": args.allow_fallback,
            "live_source_url_checks": not args.skip_url_checks,
            "started_at": started_at.isoformat(),
        },
        "aggregate": aggregate(results),
        "cases": results,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2))
    print(f"Saved measured results to {output}")


if __name__ == "__main__":
    main()

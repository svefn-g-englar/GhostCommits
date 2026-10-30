"""Reject unsupported model claims before they reach the interface."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple


EVIDENCE_ID = re.compile(r"^E-(\d{1,3})$", re.IGNORECASE)


def _canonical_evidence_id(value: Any) -> str:
    text = str(value).strip().upper()
    match = EVIDENCE_ID.fullmatch(text)
    if not match:
        return text
    return f"E-{int(match.group(1)):03d}"


def validate_findings(result: Dict[str, Any], packet: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    valid_ids = {item["id"] for item in packet.get("evidence", [])}
    accepted: List[Dict[str, Any]] = []
    warnings: List[str] = []

    for index, finding in enumerate(result.get("findings", []), 1):
        cited = [_canonical_evidence_id(item) for item in finding.get("evidence_ids", [])]
        supported = [evidence_id for evidence_id in cited if evidence_id in valid_ids]
        missing = sorted(set(cited) - valid_ids)
        if missing:
            warnings.append(f"Finding {index} referenced unknown evidence: {', '.join(missing)}")
        if not supported:
            warnings.append(f"Finding {index} was removed because it had no valid evidence.")
            continue
        confidence = finding.get("confidence", 0.5)
        try:
            confidence = min(1.0, max(0.0, float(confidence)))
        except (TypeError, ValueError):
            confidence = 0.5
            warnings.append(f"Finding {index} used an invalid confidence score; reset to 0.5.")
        accepted.append(
            {
                "finding": str(finding.get("finding", "")).strip(),
                "evidence_ids": supported,
                "confidence": confidence,
                "uncertainties": [str(item) for item in finding.get("uncertainties", [])][:5],
                "recommended_action": str(finding.get("recommended_action", "")).strip(),
            }
        )

    validated = dict(result)
    validated["findings"] = accepted
    validated["validation"] = {
        "accepted_claims": len(accepted),
        "warnings": len(warnings),
        "evidence_ids_checked": len(valid_ids),
    }
    return validated, warnings

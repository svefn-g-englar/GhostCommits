"""Turn evidence and validated findings into a prioritized recovery plan."""

from __future__ import annotations

from typing import Any, Dict, List


def build_resurrection_plan(packet: Dict[str, Any], analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    repo = packet["repository"]
    stats = packet["statistics"]
    language = next(
        (item["value"] for item in packet["evidence"] if item["claim"] == "Primary language by bytes"),
        "the project language",
    )
    steps = [
        {"phase":"Preserve","title":"Snapshot the surviving evidence","action":"Fork the repository, record licensing, releases, installation notes, and the current default branch.","effort":"30–45 min","risk":"Low","evidence_ids":["E-001","E-005"]},
        {"phase":"Reproduce","title":"Reconstruct an isolated toolchain","action":f"Identify the last documented {language} runtime and dependency lockfiles. Work only inside a disposable environment.","effort":"1–2 hr","risk":"Medium","evidence_ids":["E-006"] if len(packet["evidence"]) >= 6 else ["E-002"]},
        {"phase":"Verify","title":"Establish one clean baseline","action":"Run only reviewed, documented checks; capture missing dependencies and failures without silently fixing them.","effort":"1–3 hr","risk":"Medium","evidence_ids":["E-002"]},
        {"phase":"Triage","title":"Choose one bounded recovery target","action":f"Review the {stats['open_items']} open items and select a reproducible issue with a small, observable outcome.","effort":"45–60 min","risk":"Low","evidence_ids":["E-003"]},
        {"phase":"Revive","title":"Publish a contributor-ready brief","action":f"Document compatibility findings, unresolved risks, and the smallest useful change for {repo['full_name']} before broad modernization.","effort":"45 min","risk":"Low","evidence_ids":["E-002","E-003"]},
    ]
    model_actions = [f.get("recommended_action") for f in analysis.get("findings", []) if f.get("recommended_action")]
    if model_actions:
        steps.append({"phase":"Model insight","title":"Test the strongest evidence-backed suggestion","action":model_actions[0],"effort":"Variable","risk":"Review","evidence_ids":analysis["findings"][0]["evidence_ids"]})
    return steps

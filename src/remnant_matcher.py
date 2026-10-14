"""Synthetic remnant eligibility demo; not a production nesting system."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _pair_allowed(source_project: str, target_project: str,
                  allowed_pairs: list[list[str]]) -> bool:
    return source_project == target_project or [source_project, target_project] in allowed_pairs


def _plate_fit(offcut: dict[str, Any], part: dict[str, Any], trim: float,
               kerf: float) -> tuple[bool, float, str]:
    # Simplified single rectangular part fit. Subtract trim at both ends and
    # a kerf allowance; does not perform multi-part nesting or irregular geometry.
    avail_w = float(offcut["width_mm"]) - 2 * trim
    avail_l = float(offcut["length_mm"]) - 2 * trim
    req_w = float(part["width_mm"]) + kerf
    req_l = float(part["length_mm"]) + kerf
    orientations = [(req_w, req_l, "normal")]
    if part.get("allow_rotation", True):
        orientations.append((req_l, req_w, "rotated"))
    fits = [(w, l, label) for w, l, label in orientations if w <= avail_w and l <= avail_l]
    if not fits:
        return False, 0.0, "dimensions_do_not_fit"
    # Choose orientation with minimum remaining area as a simple best-fit score.
    best = min(fits, key=lambda x: (avail_w * avail_l - x[0] * x[1], x[2]))
    residual = max(0.0, avail_w * avail_l - best[0] * best[1])
    return True, residual, f"fits_{best[2]}"


def _profile_fit(offcut: dict[str, Any], part: dict[str, Any], trim: float,
                 kerf: float) -> tuple[bool, float, str]:
    available = float(offcut["length_mm"]) - 2 * trim
    required = float(part["length_mm"]) + kerf
    if required > available:
        return False, 0.0, "length_does_not_fit"
    return True, available - required, "fits_lengthwise"


def candidate_result(offcut: dict[str, Any], part: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    """Return a scored eligibility result for one offcut/part pair."""
    reasons: list[str] = []
    if part.get("revision_status") != "released":
        reasons.append("part_revision_not_released")
    if not part.get("traceable_spec", False) or not offcut.get("traceable", False):
        reasons.append("traceability_incomplete")
    if offcut.get("status") != "available":
        reasons.append("offcut_not_available")
    if offcut.get("form") != part.get("form"):
        reasons.append("form_mismatch")
    if offcut.get("material_grade") != part.get("material_grade"):
        reasons.append("material_grade_mismatch")
    if part.get("form") == "plate" and offcut.get("thickness_mm") != part.get("thickness_mm"):
        reasons.append("thickness_mismatch")
    if part.get("form") == "profile" and offcut.get("profile_family") != part.get("profile_family"):
        reasons.append("profile_family_mismatch")

    transfers = policy.get("authorised_project_transfers", [])
    if not _pair_allowed(offcut.get("project_id", ""), part.get("project_id", ""), transfers):
        reasons.append("project_transfer_not_authorised")

    score = None
    fit_reason = "not_evaluated"
    if not reasons:
        trim = float(policy.get("edge_trim_mm", 0))
        kerf = float(policy.get("kerf_mm", 0))
        if part["form"] == "plate":
            fits, score, fit_reason = _plate_fit(offcut, part, trim, kerf)
        elif part["form"] == "profile":
            fits, score, fit_reason = _profile_fit(offcut, part, trim, kerf)
        else:
            fits, score, fit_reason = False, 0.0, "unsupported_form"
        if not fits:
            reasons.append(fit_reason)

    return {
        "offcut_id": offcut.get("offcut_id"),
        "part_id": part.get("part_id"),
        "eligible": not reasons,
        "score_remaining_area_mm2_or_length_mm": round(score, 2) if score is not None else None,
        "reason": fit_reason if not reasons else ";".join(reasons),
    }


def match_remnants(data: dict[str, Any]) -> dict[str, Any]:
    """Greedy best-fit assignment; each remnant and part can be assigned once."""
    offcuts = list(data.get("offcuts", []))
    requirements = data.get("requirements", [])
    policy = data.get("policy", {})
    matches: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    used: set[str] = set()

    # Smaller parts first is a demo heuristic, not a claim of global optimality.
    def size_key(p: dict[str, Any]) -> float:
        if p.get("form") == "plate":
            return float(p.get("width_mm", 0)) * float(p.get("length_mm", 0))
        return float(p.get("length_mm", 0))

    for part in sorted(requirements, key=size_key):
        qty = int(part.get("quantity", 1))
        for index in range(qty):
            unit_part = dict(part)
            if qty > 1:
                unit_part["part_id"] = f"{part['part_id']}#{index + 1}"
            candidates = [candidate_result(o, unit_part, policy) for o in offcuts if o["offcut_id"] not in used]
            feasible = [c for c in candidates if c["eligible"]]
            decisions.extend(c for c in candidates if not c["eligible"])
            if not feasible:
                unmatched.append({"part_id": unit_part["part_id"], "reason": "no_eligible_remnant"})
                continue
            best = min(feasible, key=lambda c: c["score_remaining_area_mm2_or_length_mm"])
            used.add(best["offcut_id"])
            matches.append(best)
    return {"matches": matches, "unmatched_parts": unmatched, "rejected_candidate_examples": decisions}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to synthetic JSON case file")
    args = parser.parse_args()
    with Path(args.input).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    print(json.dumps(match_remnants(data), indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OPERATIONS_DIR = SCRIPT_DIR.parent
REPO_ROOT = OPERATIONS_DIR.parent
WORKSPACE_ROOT = REPO_ROOT.parent
OBJECTIVES_DIR = REPO_ROOT / "OBJECTIVES"
CANONICAL_JSON = WORKSPACE_ROOT / "manamaths-tasks" / "canonical" / "year-9-learning-objectives.json"
TRACKER_JSON = OPERATIONS_DIR / "data" / "lo-tracker.json"


def load_json(path: Path):
    return json.loads(path.read_text())


def topic_number_from_objective_id(objective_id: str) -> int | None:
    parts = objective_id.split("-")
    for part in parts:
        if part.startswith("topic") and part[5:].isdigit():
            return int(part[5:])
    return None


def is_explicit_lo(objective_id: str) -> bool:
    return "-lo" in objective_id and "-ex" not in objective_id


def main() -> int:
    parser = argparse.ArgumentParser(description="Return the next missing Mana Maths LO from tracker order.")
    parser.add_argument("--topic", type=int, help="Optional topic number filter, e.g. 2")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    tracker = load_json(TRACKER_JSON)
    canonical = load_json(CANONICAL_JSON)

    canonical_titles = {}
    for topic in canonical.get("topics", []):
        for section in ("learning_objectives", "extensions"):
            for item in topic.get(section, []):
                title = item.get("display_title") or item.get("title") or ""
                source_code = (item.get("source_code") or "").lower()
                topic_id = (topic.get("topic_id") or "").lower().replace("t", "topic")
                objective_id = f"y9-{topic_id}-{source_code}-" + "-".join(
                    "".join(ch.lower() if ch.isalnum() else " " for ch in title).split()
                )
                canonical_titles[objective_id] = {
                    "displayTitle": item.get("display_title") or item.get("title") or "",
                    "internalCode": item.get("internal_code") or "",
                }

    for item in tracker.get("learningObjectives", []):
        objective_id = item.get("objectiveId", "")
        if not is_explicit_lo(objective_id):
            continue
        if args.topic is not None and topic_number_from_objective_id(objective_id) != args.topic:
            continue
        if item.get("status") != "not_started":
            continue
        result = {
            "objectiveId": objective_id,
            "slug": item.get("slug"),
            "displayTitle": canonical_titles.get(objective_id, {}).get("displayTitle", ""),
            "internalCode": canonical_titles.get(objective_id, {}).get("internalCode", ""),
        }
        if args.json:
            print(json.dumps(result))
        else:
            print(f"{result['objectiveId']}\t{result['slug']}\t{result['displayTitle']}\t{result['internalCode']}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

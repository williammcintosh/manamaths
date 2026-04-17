#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OPERATIONS_DIR = SCRIPT_DIR.parent
REPO_ROOT = OPERATIONS_DIR.parent
WORKSPACE_ROOT = REPO_ROOT.parent
OBJECTIVES_DIR = REPO_ROOT / "OBJECTIVES"
CANONICAL_JSON = WORKSPACE_ROOT / "lesson-builder" / "canonical" / "year-9-learning-objectives.json"
TRACKER_JSON = OPERATIONS_DIR / "data" / "lo-tracker.json"
TEMPLATE_PATH = OPERATIONS_DIR / "templates" / "lo-template.tex"
LEVELS = ["foundation", "proficient", "excellence"]
LEVEL_LABELS = {
    "foundation": "Foundation",
    "proficient": "Proficient",
    "excellence": "Excellence",
}
COUNTS = {
    "foundation": 14,
    "proficient": 12,
    "excellence": 16,
}


def slugify(text: str) -> str:
    return "lo-yr9-" + re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def find_canonical_by_tracker_objective_id(objective_id: str) -> dict | None:
    raw = load_json(CANONICAL_JSON)
    for topic in raw.get("topics", []):
        for section in ("learning_objectives", "extensions"):
            for item in topic.get(section, []):
                title = item.get("display_title") or item.get("title") or ""
                source_code = (item.get("source_code") or "").lower()
                topic_id = (topic.get("topic_id") or "").lower().replace("t", "topic")
                inferred = f"y9-{topic_id}-{source_code}-{re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')}"
                if inferred == objective_id:
                    return item
    return None


def find_tracker_record(slug: str | None, objective_id: str | None) -> dict | None:
    raw = load_json(TRACKER_JSON)
    for item in raw.get("learningObjectives", []):
        if slug and item.get("slug") == slug:
            return item
        if objective_id and item.get("objectiveId") == objective_id:
            return item
    return None


def make_placeholder_tasks(level: str, count: int, sample_questions: list[str]) -> str:
    prompts: list[str] = []
    if sample_questions:
        cleaned = [re.sub(r"\s+", " ", q).strip() for q in sample_questions if str(q).strip()]
    else:
        cleaned = []

    for i in range(count):
        if cleaned:
            base = cleaned[i % len(cleaned)]
            prompt = f"TODO: {base}"
        else:
            prompt = f"TODO: write {level} question {i+1}."
        prompts.append(r"\task {" + prompt + "}")
    return "\n".join(prompts)


def build_tex(title: str, level: str, sample_questions: list[str]) -> str:
    template = TEMPLATE_PATH.read_text()
    template = template.replace("INSERT HEADER HERE", f"{title} — {LEVEL_LABELS[level]}")
    template = template.replace(r"\task ", make_placeholder_tasks(level, COUNTS[level], sample_questions), 1)
    return template


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold a new Mana Maths LO folder from the repo template.")
    parser.add_argument("--slug", help="Existing repo slug, e.g. lo-yr9-capacity")
    parser.add_argument("--objective-id", help="Tracker objectiveId, e.g. y9-topic1-lo13-capacity")
    parser.add_argument("--force", action="store_true", help="Overwrite existing tex files")
    args = parser.parse_args()

    if not args.slug and not args.objective_id:
        raise SystemExit("Pass --slug or --objective-id")

    tracker = find_tracker_record(args.slug, args.objective_id)
    if tracker is None:
        raise SystemExit("Tracker record not found. Use an existing tracker objectiveId or slug.")

    canonical = find_canonical_by_tracker_objective_id(tracker["objectiveId"])
    if canonical is None:
        raise SystemExit(f"Canonical record not found for {tracker['objectiveId']}")

    slug = tracker["slug"]
    title = canonical.get("display_title") or canonical.get("title") or slug
    sample_questions = canonical.get("sample_questions") or []

    lo_dir = OBJECTIVES_DIR / slug
    lo_dir.mkdir(exist_ok=True)

    for level in LEVELS:
        path = lo_dir / f"{level}-questions.tex"
        if path.exists() and not args.force:
            continue
        path.write_text(build_tex(title, level, sample_questions))
        print(f"Wrote {path.relative_to(REPO_ROOT)}")

    print(f"Scaffolded {slug} from template using canonical metadata.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

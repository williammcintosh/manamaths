#!/usr/bin/env python3
from __future__ import annotations

import difflib
import json
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OPERATIONS_DIR = SCRIPT_DIR.parent
REPO_ROOT = OPERATIONS_DIR.parent
WORKSPACE_ROOT = REPO_ROOT.parent
OBJECTIVES_DIR = REPO_ROOT / "OBJECTIVES"
CANONICAL_JSON = WORKSPACE_ROOT / "lesson-builder" / "canonical" / "year-9-learning-objectives.json"
OUTPUT_JSON = OPERATIONS_DIR / "data" / "lo-tracker.json"
LEVELS = ["foundation", "proficient", "excellence"]


def slugify(text: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return f"lo-yr9-{text}"


def path_or_none(path: Path) -> str | None:
    return str(path.relative_to(WORKSPACE_ROOT)) if path.exists() else None


STOPWORDS = {"and", "a", "of", "the", "by", "formerly", "quantity"}


def normalize_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def tokenise(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t]


def canonicalise_tokens(text: str) -> tuple[str, ...]:
    return tuple(t for t in tokenise(text) if t not in STOPWORDS)


def existing_slug_map() -> dict[tuple[str, ...], str]:
    slug_map: dict[tuple[str, ...], str] = {}
    for path in OBJECTIVES_DIR.glob("lo-yr9-*"):
        if not path.is_dir():
            continue
        slug = path.name
        titleish = slug.removeprefix("lo-yr9-").replace("-", " ")
        slug_map.setdefault(canonicalise_tokens(titleish), slug)
    for path in (REPO_ROOT / "SITE" / "objectives").glob("lo-yr9-*.html"):
        slug = path.stem
        titleish = slug.removeprefix("lo-yr9-").replace("-", " ")
        slug_map.setdefault(canonicalise_tokens(titleish), slug)
    return slug_map


def compatible_tokens(source_tokens: tuple[str, ...], candidate_tokens: tuple[str, ...]) -> bool:
    source_set = set(source_tokens)
    candidate_set = set(candidate_tokens)
    numberish = {t for t in source_set | candidate_set if any(ch.isdigit() for ch in t)}
    for token in numberish:
        if (token in source_set) != (token in candidate_set):
            return False
    protected = {"single", "double", "fractions", "fraction", "expressions", "equations", "brackets"}
    for token in protected:
        if (token in source_set) != (token in candidate_set):
            return False
    return True


def resolve_slug(title: str, slug_map: dict[tuple[str, ...], str]) -> str:
    direct = slugify(title)
    direct_tokens = canonicalise_tokens(title)
    if direct_tokens in slug_map:
        return slug_map[direct_tokens]
    if (OBJECTIVES_DIR / direct).exists() or (REPO_ROOT / "SITE" / "objectives" / f"{direct}.html").exists():
        return direct

    best_slug: str | None = None
    best_score = 0.0
    direct_joined = " ".join(direct_tokens)
    for candidate_tokens, candidate_slug in slug_map.items():
        if not compatible_tokens(direct_tokens, candidate_tokens):
            continue
        candidate_joined = " ".join(candidate_tokens)
        score = difflib.SequenceMatcher(a=direct_joined, b=candidate_joined).ratio()
        overlap = len(set(direct_tokens) & set(candidate_tokens))
        score += min(overlap * 0.03, 0.12)
        if score > best_score:
            best_score = score
            best_slug = candidate_slug
    return best_slug if best_slug and best_score >= 0.93 else direct


def source_code_number(source_code: str | None) -> int | None:
    match = re.search(r"(LO|EX)0*(\d+)$", source_code or "")
    return int(match.group(2)) if match else None


def build_objective_id(topic_num: int | None, topic_title: str, item: dict) -> str:
    topic_id = str(item.get("topic_id") or "").strip().upper()
    internal_code = str(item.get("internal_code") or "").strip().upper()
    if topic_id and internal_code:
        return f"YR9_{internal_code}"

    source_code = str(item.get("source_code") or "").strip().upper()
    number = source_code_number(source_code)
    if isinstance(topic_num, int) and number is not None:
        kind = "EX" if source_code.startswith("EX") else "LO"
        return f"YR9_T{topic_num}_{kind}{number}"

    topic_slug = re.sub(r"[^A-Z0-9]+", "_", (topic_title or "OTHER").upper()).strip("_")
    slug_tail = re.sub(r"[^A-Z0-9]+", "_", source_code or "UNTITLED").strip("_") or "UNTITLED"
    return f"YR9_{topic_slug}_{slug_tail}"


def build_legacy_objective_id(topic_num: int | None, topic_title: str, item: dict) -> str:
    source_code = item.get("source_code") or ""
    number = source_code_number(source_code)
    title = item.get("display_title") or item.get("title") or "untitled"
    slug_tail = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "untitled"

    if isinstance(topic_num, int) and number is not None:
        prefix = f"y9-topic{topic_num}"
        if source_code.startswith("EX"):
            return f"{prefix}-ex{number}-{slug_tail}"
        return f"{prefix}-lo{number}-{slug_tail}"

    topic_slug = re.sub(r"[^a-z0-9]+", "-", (topic_title or "other").lower()).strip("-")
    return f"y9-{topic_slug}-{slug_tail}"


def build_lesson_ref(topic_num: int | None, item: dict) -> dict:
    source_code = item.get("source_code") or ""
    number = source_code_number(source_code)
    ref: dict[str, object] = {}
    if isinstance(topic_num, int):
        ref["topic"] = topic_num
    if number is not None:
        if source_code.startswith("EX"):
            ref["ex"] = number
        else:
            ref["lo"] = number
    if item.get("source_page") is not None:
        ref["evidence"] = f"canonical source page {item['source_page']}"
    return ref


def canonical_records() -> list[dict]:
    data = json.loads(CANONICAL_JSON.read_text())
    records: list[dict] = []

    for topic_index, topic in enumerate(data.get("topics", []), start=1):
        topic_id = topic.get("topic_id") or ""
        topic_title = topic.get("topic_title") or f"Topic {topic_index}"
        topic_num = None
        topic_match = re.search(r"T(\d+)$", topic_id)
        if topic_match:
            topic_num = int(topic_match.group(1))

        for section_name, objective_type in (("learning_objectives", "explicit_learning_objective"), ("extensions", "extension_learning_objective")):
            for item in topic.get(section_name, []):
                title = item.get("display_title") or item.get("title") or "Untitled"
                records.append(
                    {
                        "objectiveId": build_objective_id(topic_num, topic_title, {**item, "topic_id": topic_id}),
                        "legacyObjectiveId": build_legacy_objective_id(topic_num, topic_title, item),
                        "canonicalTopicId": topic_id,
                        "canonicalInternalCode": item.get("internal_code"),
                        "canonicalSourceCode": item.get("source_code"),
                        "canonicalTitle": item.get("title") or title,
                        "canonicalDisplayTitle": item.get("display_title") or item.get("title") or title,
                        "internal_code": item.get("internal_code"),
                        "sourceId": "yr9-learning-objectives-canonical",
                        "unitId": f"y9-topic-{topic_num}-{re.sub(r'[^a-z0-9]+', '-', topic_title.lower()).strip('-')}" if isinstance(topic_num, int) else None,
                        "lessonRef": build_lesson_ref(topic_num, item),
                        "subject": "mathematics",
                        "yearLevel": "Year 9",
                        "topic": f"Topic {topic_num}" if isinstance(topic_num, int) else topic_title,
                        "topicTitle": topic_title,
                        "subtopic": title,
                        "originalSourceText": f"{item.get('source_code')}: {title}" if item.get("source_code") else title,
                        "normalizedObjective": item.get("normalized_objective") or item.get("learning_objective") or title,
                        "objectiveType": objective_type,
                        "source_page": item.get("source_page"),
                        "resources": item.get("resources", {}),
                        "terminology": item.get("terminology", []),
                        "teaching_notes": item.get("teaching_notes", []),
                        "sample_questions": item.get("sample_questions", []),
                    }
                )

    return records


def collect_lo_record(item: dict, slug_map: dict[str, str]) -> dict:
    subtopic = item.get("subtopic") or item.get("normalizedObjective") or item.get("originalSourceText") or "untitled"
    slug = resolve_slug(subtopic, slug_map)
    lo_dir = OBJECTIVES_DIR / slug
    objective_page = REPO_ROOT / "SITE" / "objectives" / f"{slug}.html"

    tex_files = {level: lo_dir / f"{level}-questions.tex" for level in LEVELS}
    pdf_files = {level: lo_dir / f"{level}-questions.pdf" for level in LEVELS}

    has_any_tex = any(path.exists() for path in tex_files.values())
    all_tex = all(path.exists() for path in tex_files.values())
    all_pdfs = all(path.exists() for path in pdf_files.values())
    has_folder = lo_dir.is_dir()
    website = objective_page.exists()

    if all_tex and all_pdfs and website:
        status = "complete"
    elif has_any_tex or website or has_folder:
        status = "partial"
    else:
        status = "not_started"

    return {
        "objectiveId": item.get("objectiveId"),
        "legacyObjectiveId": item.get("legacyObjectiveId"),
        "canonicalTopicId": item.get("canonicalTopicId"),
        "canonicalInternalCode": item.get("canonicalInternalCode"),
        "canonicalSourceCode": item.get("canonicalSourceCode"),
        "canonicalTitle": item.get("canonicalTitle"),
        "canonicalDisplayTitle": item.get("canonicalDisplayTitle"),
        "slug": slug,
        "status": status,
        "paths": {
            "folder": path_or_none(lo_dir),
            "objectivePage": path_or_none(objective_page),
            "levels": {
                level: {
                    "tex": path_or_none(tex_files[level]),
                    "pdf": path_or_none(pdf_files[level]),
                }
                for level in LEVELS
            },
        },
        "evidence": {
            "folder": has_folder,
            "allTex": all_tex,
            "allPdfs": all_pdfs,
            "website": website,
        },
    }


def main() -> int:
    slug_map = existing_slug_map()
    records = [collect_lo_record(item, slug_map) for item in canonical_records() if isinstance(item, dict)]
    payload = {
        "canonicalSource": str(CANONICAL_JSON.relative_to(WORKSPACE_ROOT)),
        "generatedAtRepoPath": str(OUTPUT_JSON.relative_to(WORKSPACE_ROOT)),
        "notes": [
            "This tracker is the generated inventory and build-status file for Year 9 Mana Maths learning objectives.",
            "Worksheet content lives in per-LO TeX files, not in this tracker.",
            "Canonical curriculum/source metadata lives in the canonical JSON file.",
            "This tracker is derived from the canonical JSON plus the actual filesystem state.",
            "Canonical identifiers and titles are copied through here so smaller models can compare tracker and canonical records directly.",
            "objectiveId now uses the shared code form, e.g. YR9_T3_LO20; legacyObjectiveId keeps the old sluggy identifier for compatibility.",
            "Prefer canonicalInternalCode / canonicalSourceCode / canonicalDisplayTitle when matching back to the canonical JSON.",
        ],
        "summary": {
            "totalObjectives": len(records),
            "complete": sum(1 for r in records if r["status"] == "complete"),
            "partial": sum(1 for r in records if r["status"] == "partial"),
            "notStarted": sum(1 for r in records if r["status"] == "not_started"),
        },
        "learningObjectives": records,
    }
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Wrote {OUTPUT_JSON.relative_to(WORKSPACE_ROOT)} with {len(records)} objectives")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

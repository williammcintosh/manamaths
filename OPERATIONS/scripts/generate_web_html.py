#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import tempfile
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
OPERATIONS_DIR = SCRIPT_DIR.parent
REPO_ROOT = OPERATIONS_DIR.parent
WORKSPACE_ROOT = REPO_ROOT.parent
OBJECTIVES_DIR = REPO_ROOT / "OBJECTIVES"
SITE_DIR = REPO_ROOT / "SITE"
CANONICAL_JSON = WORKSPACE_ROOT / "lesson-builder" / "canonical" / "year-9-learning-objectives.json"
LO_TRACKER_JSON = OPERATIONS_DIR / "data" / "lo-tracker.json"
TE_REO_TRACKER_JSON = WORKSPACE_ROOT / "te-reo-maori-terms" / "tracking" / "te-reo-progress.json"
OUTPUT_DIR = SITE_DIR / "objectives"
TITLE = "Mana Maths"
DESCRIPTION = "Helping maths teachers save time. We make maths curriculum content resources easy to find."
LEVELS = [
    ("foundation", "Foundation"),
    ("proficient", "Proficient"),
    ("excellence", "Excellence"),
]
MATH_RE = re.compile(r"\$(.+?)\$", re.DOTALL)
COMMAND_REPLACEMENTS = {
    r"\\frac": "frac",
    r"\\times": "times",
    r"\\div": "div",
    r"\\square": "square",
    r"\\pi": "pi",
    r"\\theta": "theta",
    r"\\alpha": "alpha",
    r"\\beta": "beta",
    r"\\gamma": "gamma",
    r"\\leq": "leq",
    r"\\geq": "geq",
    r"\\neq": "neq",
    r"\\left": "left",
    r"\\right": "right",
}
TEXT_REPLACEMENTS = {
    r"\\%": "%",
    r"\\&": "&",
    r"\\#": "#",
    r"\\_": "_",
    r"\\,": " ",
    r"\\ ": " ",
    r"\\quad": " ",
    r"\\qquad": " ",
}
MATHJAX = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"
TASKS_RE = re.compile(r"\\begin\{tasks\}\((\d+)\)")
ITEM_SKIP_RE = re.compile(r"after-item-skip=([0-9.]+)em")
CHROMIUM = "chromium-browser"
WEB_DIAGRAM_DIRNAME = "web-diagrams"
TEX_REFERENCE_RE = re.compile(r"^See\s+(.+?-questions\.tex)\s*$")
ITEM_OR_TASK_SPLIT_RE = re.compile(r"(?=\\item\b|\\task\b)")
INCLUDEGRAPHICS_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
MINIPAGE_QUESTION_RE = re.compile(r"\\textbf\{(\d+)\.\}\s*(.*?)(?=\\end\{minipage\})", re.DOTALL)
INLINE_QUESTION_RE = re.compile(r"\\textbf\{(\d+)\.\}\s*(.*?)(?=(?:\\hfill|\\par|$))", re.DOTALL)
META_DESCRIPTION_RE = re.compile(r'<meta\s+name="description"\s+content="([^"]*)"', re.IGNORECASE)
LEAD_RE = re.compile(r'<p\s+class="lead">(.*?)</p>', re.IGNORECASE | re.DOTALL)


def sanitize_yaml_text(raw_text: str) -> str:
    raw_text = raw_text.replace("\r\n", "\n")
    raw_text = raw_text.replace("\r", r"\r")
    raw_text = raw_text.replace("\t", r"\t")
    raw_text = raw_text.replace("\x0c", r"\f")
    raw_text = raw_text.replace(".''", ".'")
    raw_text = raw_text.replace("?''", "?'")
    raw_text = raw_text.replace("\nule{", "\\rule{")
    raw_text = raw_text.replace("$\f rac{", "$\\frac{")
    raw_text = raw_text.replace("$\fr ac{", "$\\frac{")
    raw_text = raw_text.replace("$\frac{", "$\\frac{")
    raw_text = raw_text.replace("\f\frac", "\\frac")
    return raw_text


def read_yaml(path: Path):
    raw_text = sanitize_yaml_text(path.read_text(errors="replace"))
    return yaml.safe_load(raw_text)


def normalize_question(question: object) -> str:
    if isinstance(question, dict) and question:
        key, value = next(iter(question.items()))
        return f"{key}: {value}"
    return str(question)


def extract_questions_from_tex(tex_path: Path) -> list[str]:
    tex = tex_path.read_text(errors="replace")
    blocks: list[str] = []
    for begin, end in [(r"\begin{enumerate}", r"\end{enumerate}"), (r"\begin{tasks}", r"\end{tasks}")]:
        start = tex.find(begin)
        if start == -1:
            continue
        end_idx = tex.find(end, start)
        if end_idx == -1:
            continue
        block = tex[start:end_idx]
        blocks.append(block)

    if not blocks:
        questions: list[str] = []
        for pattern in (MINIPAGE_QUESTION_RE, INLINE_QUESTION_RE):
            matches = pattern.findall(tex)
            if matches:
                for _num, chunk in matches:
                    cleaned = chunk.strip()
                    cleaned = re.sub(r"\\\\\[[^\]]*\]", "", cleaned)
                    cleaned = re.sub(r"\s+", " ", cleaned).strip()
                    questions.append(cleaned)
                if questions:
                    return questions
        return []

    questions: list[str] = []
    for block in blocks:
        for chunk in ITEM_OR_TASK_SPLIT_RE.split(block):
            chunk = chunk.strip()
            if not chunk or not (chunk.startswith("\\item") or chunk.startswith("\\task")):
                continue
            chunk = re.sub(r"^(\\item|\\task)\s*", "", chunk, count=1).strip()
            questions.append(chunk)
    return questions


def resolve_questions(raw_questions: object) -> list[object]:
    if isinstance(raw_questions, str):
        match = TEX_REFERENCE_RE.match(raw_questions.strip())
        if match:
            tex_ref = match.group(1).strip()
            tex_path = (WORKSPACE_ROOT / tex_ref.replace("manamaths/", "manamaths/", 1)).resolve()
            if tex_path.exists():
                extracted = extract_questions_from_tex(tex_path)
                if extracted:
                    return extracted
        return [raw_questions]
    if isinstance(raw_questions, list):
        return raw_questions
    return list(raw_questions or [])


def slugify_topic(text: str) -> str:
    return f"lo-yr9-{re.sub(r'[^a-z0-9]+', '-', str(text).lower()).strip('-')}"


def normalize_lookup_key(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', str(text).lower())


def load_tracker_order() -> dict[str, dict]:
    if not LO_TRACKER_JSON.exists():
        return {}

    try:
        raw = json.loads(LO_TRACKER_JSON.read_text())
    except Exception:
        return {}

    items = raw.get("learningObjectives") or []
    order: dict[str, dict] = {}
    for index, item in enumerate(items):
        slug = item.get("slug")
        if not slug:
            continue
        order[slug] = {
            "tracker_sort": index,
            "objective_id": item.get("objectiveId", ""),
        }
    return order


def load_source_metadata() -> tuple[dict[str, dict], dict[str, dict], dict[str, dict], dict[int, str]]:
    if not CANONICAL_JSON.exists():
        return {}, {}, {}, {}

    try:
        raw = json.loads(CANONICAL_JSON.read_text())
    except Exception:
        return {}, {}, {}, {}

    metadata: dict[str, dict] = {}
    metadata_by_name: dict[str, dict] = {}
    metadata_by_objective_id: dict[str, dict] = {}
    topic_titles_by_number: dict[int, str] = {}
    source_index = 0

    for topic_index, topic in enumerate(raw.get("topics", []), start=1):
        topic_label = topic.get("topic_title") or f"Topic {topic_index}"
        topic_match = re.search(r"T(\d+)$", topic.get("topic_id") or "")
        topic_number = int(topic_match.group(1)) if topic_match else None
        topic_sort = topic_number if isinstance(topic_number, int) else topic_index
        if isinstance(topic_number, int):
            topic_titles_by_number[topic_number] = str(topic_label)

        for section_name in ("learning_objectives", "extensions"):
            for item in topic.get(section_name, []):
                title = item.get("display_title") or item.get("title") or ""
                slug = slugify_topic(title)
                source_code = item.get("source_code") or ""
                number_match = re.search(r"(LO|EX)0*(\d+)$", source_code)
                objective_sort = int(number_match.group(2)) if number_match else source_index + 1
                if source_code.startswith("EX"):
                    objective_sort += 1000
                entry = {
                    "topic_label": str(topic_label),
                    "topic_number": topic_number,
                    "topic_sort": topic_sort,
                    "objective_sort": objective_sort,
                    "source_sort": source_index,
                    "internal_code": item.get("internal_code") or "",
                    "source_code": source_code,
                    "title": title,
                }
                metadata[slug] = entry
                objective_id = item.get("objectiveId") or item.get("objective_id")
                if objective_id:
                    metadata_by_objective_id[str(objective_id)] = entry
                for candidate in [title, item.get("title"), item.get("internal_code"), source_code]:
                    key = normalize_lookup_key(candidate or "")
                    if key and key not in metadata_by_name:
                        metadata_by_name[key] = entry
                source_index += 1

    return metadata, metadata_by_name, metadata_by_objective_id, topic_titles_by_number


def extract_existing_instruction(page_path: Path) -> str:
    if not page_path.exists():
        return ""
    text = page_path.read_text(errors="replace")
    for pattern in (META_DESCRIPTION_RE, LEAD_RE):
        match = pattern.search(text)
        if match:
            return html.unescape(re.sub(r"\s+", " ", match.group(1))).strip()
    return ""


def latex_to_html(text: str) -> str:
    text = text.strip()
    if text.startswith("__RAWHTML__"):
        return text[len("__RAWHTML__"):]
    text = re.sub(r"^\\item\s*", "", text)
    while text.startswith("{") and text.endswith("}"):
        inner = text[1:-1].strip()
        if not inner:
            break
        text = inner
    if "\\begin{tikzpicture}" in text or any(token in text for token in ["\\hscale{", "\\thermo{", "\\cylinder{", "\\speedo{", "\\simplepie{", "\\picto{", "\\barchart{", "\\histogram{", "\\begin{tabular}"]):
        cleaned = re.sub(r"\\\[[^\]]*\]", "", text)
        cleaned = re.sub(r"\\(hscale|thermo|cylinder|speedo|simplepie|picto|barchart|histogram)\{[^\n]*", "", cleaned)
        cleaned = re.sub(r"\\begin\{tabular\}.*?\\end\{tabular\}", "", cleaned, flags=re.S)
        cleaned = cleaned.replace("\\", "").strip()
        cleaned_html = html.escape(cleaned) if cleaned else "Question uses a diagram."
        return f'{cleaned_html} <span class="question-diagram-note">Diagram version available in the PDF.</span>'

    text = text.replace(r"\f\frac", r"\frac")
    text = text.replace(r"\fr\frac", r"\frac")

    for old, new in TEXT_REPLACEMENTS.items():
        text = text.replace(old, new)

    placeholders: list[str] = []

    def stash_placeholder(value: str, kind: str) -> str:
        placeholders.append(value)
        return f"@@{kind}{len(placeholders)-1}@@"

    text = re.sub(
        r"\\rule\{[^}]+\}\{[^}]+\}",
        lambda _: stash_placeholder('<span class="blank-line"></span>', "HTML"),
        text,
    )
    text = re.sub(r"\\text\{([^}]*)\}", lambda m: html.escape(m.group(1)), text)
    text = re.sub(r"\\mathrm\{([^}]*)\}", lambda m: html.escape(m.group(1)), text)
    text = re.sub(r"\\mbox\{(\$.*?\$)\}", lambda m: m.group(1), text)
    text = re.sub(r"\\mbox\{([^}]*)\}", lambda m: m.group(1), text)

    def stash_math(match: re.Match[str]) -> str:
        return stash_placeholder(match.group(0), "MATH")

    text = MATH_RE.sub(stash_math, text)
    text = html.escape(text)

    for old, new in COMMAND_REPLACEMENTS.items():
        text = text.replace(html.escape(old), html.escape(new))

    text = text.replace("\\n", "<br />")

    for idx, original in enumerate(placeholders):
        text = text.replace(f"@@MATH{idx}@@", original)
        text = text.replace(f"@@HTML{idx}@@", original)

    for idx, original in enumerate(placeholders):
        text = text.replace(f"@@HTML{idx}@@", original)

    return text


def extract_layout_settings(tex_path: Path) -> dict:
    columns = 1
    row_gap = 1.2
    if tex_path.exists():
        tex = tex_path.read_text(errors="replace")
        match = TASKS_RE.search(tex)
        if match:
            columns = max(1, int(match.group(1)))
        skip_match = ITEM_SKIP_RE.search(tex)
        if skip_match:
            row_gap = max(0.8, float(skip_match.group(1)) * 0.42)
    return {"columns": columns, "row_gap": row_gap}


def svg_line(x1: float, y1: float, x2: float, y2: float, label: str | None = None, label_dx: float = 0, label_dy: float = -10) -> str:
    parts = [f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" />']
    if label:
        mx = (x1 + x2) / 2 + label_dx
        my = (y1 + y2) / 2 + label_dy
        parts.append(f'<text x="{mx}" y="{my}" class="branch-label">{html.escape(label)}</text>')
    return "".join(parts)


def svg_text(x: float, y: float, text: str, klass: str = "node-label", anchor: str = "start") -> str:
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" class="{klass}">{html.escape(text)}</text>'


def build_tree_svg(name: str) -> tuple[str, int, int]:
    stroke = "#1d3b2a"
    if name == "twocointree":
        width, height = 520, 280
        lines = [
            svg_line(60, 140, 190, 80, "H"),
            svg_line(60, 140, 190, 200, "T", 0, 16),
            svg_line(190, 80, 340, 40, "H"),
            svg_line(190, 80, 340, 110, "T", 0, 16),
            svg_line(190, 200, 340, 160, "H"),
            svg_line(190, 200, 340, 230, "T", 0, 16),
        ]
        labels = [
            svg_text(50, 145, "Start", anchor="end"),
            svg_text(355, 45, "HH"), svg_text(355, 115, "HT"), svg_text(355, 165, "TH"), svg_text(355, 235, "TT"),
        ]
    elif name == "coindietree":
        width, height = 600, 360
        lines = [svg_line(60, 180, 180, 100, "H"), svg_line(60, 180, 180, 260, "T", 0, 16)]
        h_targets = [(320, 40, "1", "H1"), (320, 85, "2", "H2"), (320, 130, "3", "H3"), (320, 175, "4", "H4"), (320, 220, "5", "H5"), (320, 265, "6", "H6")]
        t_targets = [(320, 95, "1", "T1"), (320, 140, "2", "T2"), (320, 185, "3", "T3"), (320, 230, "4", "T4"), (320, 275, "5", "T5"), (320, 320, "6", "T6")]
        for x, y, n, lab in h_targets:
            lines.append(svg_line(180, 100, x, y, n))
        for x, y, n, lab in t_targets:
            lines.append(svg_line(180, 260, x, y, n, 0, 16))
        labels = [svg_text(50, 185, "Start", anchor="end")]
        labels.extend(svg_text(335, y + 5, lab) for x, y, n, lab in h_targets + t_targets)
    elif name == "threetwothreetree":
        width, height = 560, 360
        starts = [(180, 70, "1"), (180, 180, "2"), (180, 290, "3")]
        lines = [svg_line(60, 180, x, y, lab) for x, y, lab in starts]
        second = [
            ((180, 70), (330, 40), "1", "11"), ((180, 70), (330, 70), "2", "12"), ((180, 70), (330, 100), "3", "13"),
            ((180, 180), (330, 150), "1", "21"), ((180, 180), (330, 180), "2", "22"), ((180, 180), (330, 210), "3", "23"),
            ((180, 290), (330, 260), "1", "31"), ((180, 290), (330, 290), "2", "32"), ((180, 290), (330, 320), "3", "33"),
        ]
        for (x1, y1), (x2, y2), n, lab in second:
            lines.append(svg_line(x1, y1, x2, y2, n))
        labels = [svg_text(50, 185, "Start", anchor="end")]
        labels.extend(svg_text(x2 + 15, y2 + 5, lab) for (_, _), (x2, y2), _, lab in second)
    elif name == "threecointree":
        width, height = 840, 420
        lines = [
            svg_line(60, 200, 180, 110, "H"), svg_line(60, 200, 180, 290, "T", 0, 16),
            svg_line(180, 110, 360, 70, "H"), svg_line(180, 110, 360, 150, "T", 0, 16),
            svg_line(180, 290, 360, 250, "H"), svg_line(180, 290, 360, 330, "T", 0, 16),
            svg_line(360, 70, 560, 40, "H"), svg_line(360, 70, 560, 100, "T", 0, 16),
            svg_line(360, 150, 560, 130, "H"), svg_line(360, 150, 560, 190, "T", 0, 16),
            svg_line(360, 250, 560, 220, "H"), svg_line(360, 250, 560, 280, "T", 0, 16),
            svg_line(360, 330, 560, 320, "H"), svg_line(360, 330, 560, 380, "T", 0, 16),
        ]
        labels = [
            svg_text(50, 205, "Start", anchor="end"),
            svg_text(170, 30, "1st toss", "small-note", "middle"), svg_text(360, 30, "2nd toss", "small-note", "middle"), svg_text(560, 30, "3rd toss", "small-note", "middle"),
            svg_text(575, 45, "HHH"), svg_text(575, 105, "HHT"), svg_text(575, 135, "HTH"), svg_text(575, 195, "HTT"),
            svg_text(575, 225, "THH"), svg_text(575, 285, "THT"), svg_text(575, 325, "TTH"), svg_text(575, 385, "TTT"),
        ]
    elif name == "twodicetree":
        width, height = 760, 460
        starts = [(180, 60, "1"), (180, 120, "2"), (180, 180, "3"), (180, 240, "4"), (180, 300, "5"), (180, 360, "6")]
        lines = [svg_line(60, 210, x, y, lab) for x, y, lab in starts]
        labels = [svg_text(50, 215, "Start", anchor="end")]
        end_rows = [
            ["11", "12", "13", "14", "15", "16"],
            ["21", "22", "23", "24", "25", "26"],
            ["31", "32", "33", "34", "35", "36"],
        ]
        start_points = starts[:3]
        for row_idx, ((sx, sy, _), labs) in enumerate(zip(start_points, end_rows)):
            for col_idx, lab in enumerate(labs, start=1):
                x2 = 360
                y2 = 40 + row_idx * 90 + (col_idx - 1) * 28
                lines.append(svg_line(sx, sy, x2, y2, str(col_idx)))
                labels.append(svg_text(x2 + 15, y2 + 5, lab))
    else:
        raise ValueError(f"Unknown tree diagram: {name}")

    svg = f"""<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{width}\" height=\"{height}\" viewBox=\"0 0 {width} {height}\">\n  <style>\n    .tree-frame {{ fill: white; }}\n    line {{ stroke: {stroke}; stroke-width: 4; stroke-linecap: round; }}\n    text {{ fill: {stroke}; font-family: Arial, sans-serif; font-size: 24px; }}\n    .branch-label {{ font-size: 22px; font-weight: 700; }}\n    .small-note {{ font-size: 18px; font-weight: 700; }}\n  </style>\n  <rect class=\"tree-frame\" width=\"100%\" height=\"100%\" />\n  {''.join(lines)}\n  {''.join(labels)}\n</svg>"""
    return svg, width, height


def render_svg_to_png(svg: str, png_path: Path, width: int, height: int) -> None:
    png_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        svg_path = tmpdir_path / "diagram.svg"
        html_path = tmpdir_path / "diagram.html"
        svg_path.write_text(svg)
        html_path.write_text(
            f"""<!DOCTYPE html><html><head><meta charset=\"utf-8\" /><style>html,body{{margin:0;padding:0;background:white;}}body{{width:{width}px;height:{height}px;overflow:hidden;}}img{{display:block;width:{width}px;height:{height}px;}}</style></head><body><img src=\"diagram.svg\" alt=\"diagram\" /></body></html>"""
        )
        subprocess.run(
            [
                CHROMIUM,
                "--headless",
                "--disable-gpu",
                "--hide-scrollbars",
                f"--window-size={width},{height}",
                f"--screenshot={png_path}",
                html_path.as_uri(),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def ensure_tree_diagram_png(name: str, slug: str) -> str:
    png_path = OBJECTIVES_DIR / slug / WEB_DIAGRAM_DIRNAME / f"{name}.png"
    if not png_path.exists():
        svg, width, height = build_tree_svg(name)
        render_svg_to_png(svg, png_path, width, height)
    return f"../{slug}/{WEB_DIAGRAM_DIRNAME}/{name}.png"


def inject_tree_diagrams(slug: str, level_key: str, questions: list[str]) -> list[str]:
    if slug != "lo-yr9-trees-combined-events":
        return questions

    diagram_map = {
        "foundation": {0: "twocointree", 5: "coindietree"},
        "proficient": {0: "coindietree", 2: "twocointree", 4: "threetwothreetree"},
        "excellence": {0: "threecointree", 4: "twodicetree"},
    }
    level_map = diagram_map.get(level_key, {})
    enriched: list[str] = []
    for index, question in enumerate(questions):
        if index in level_map:
            image_path = ensure_tree_diagram_png(level_map[index], slug)
            question = (
                "__RAWHTML__"
                + latex_to_html(question)
                + f' <div class="web-diagram-wrap"><img class="web-diagram" src="{image_path}" alt="Tree diagram for this question." /></div>'
            )
        enriched.append(question)
    return enriched


def inject_embedded_images(slug: str, questions: list[str]) -> list[str]:
    enriched: list[str] = []
    for question in questions:
        match = INCLUDEGRAPHICS_RE.search(question)
        if not match:
            enriched.append(question)
            continue

        image_ref = match.group(1).strip()
        image_name = Path(image_ref).name
        image_path = f"../../OBJECTIVES/{slug}/web-diagrams/{image_name}"
        cleaned = INCLUDEGRAPHICS_RE.sub("", question)
        cleaned = cleaned.replace("\\\\[0.4em]", "").strip()
        if cleaned.startswith("{") and cleaned.endswith("}"):
            cleaned = cleaned[1:-1].strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        enriched.append(
            "__RAWHTML__"
            + latex_to_html(cleaned)
            + f' <div class="web-diagram-wrap"><img class="web-diagram" src="{image_path}" alt="Worksheet image for this question." /></div>'
        )
    return enriched


def composite_media_html(slug: str, level_key: str) -> str:
    composite_map = {
        "lo-yr9-estimating-lengths-from-scale-drawings-and-photos": {
            "foundation": "foundation-composite.png",
            "proficient": "proficient-composite.png",
            "excellence": "excellence-composite.png",
        },
        "lo-yr9-time": {
            "proficient": "proficient-time-composite.png",
            # page2 composite if present
            "proficient_page2": "proficient-time-page2-diff.png",
        }
    }
    # first, prefer a local manifest next to the LO images
    manifest_path = OBJECTIVES_DIR / slug / "web-diagrams" / "images.json"
    if manifest_path.exists():
        try:
            import json
            m = json.loads(manifest_path.read_text())
            image_name = m.get(level_key) or m.get(f"{level_key}_page2")
            if image_name:
                image_path = f"../../OBJECTIVES/{slug}/web-diagrams/{image_name}"
                return (
                    '<div class="web-diagram-wrap">'
                    f'<img class="web-diagram" src="{image_path}" alt="Worksheet composite image for this level." />'
                    '</div>'
                )
        except Exception:
            pass

    image_name = composite_map.get(slug, {}).get(level_key)
    if not image_name:
        return ""
    image_path = f"../../OBJECTIVES/{slug}/web-diagrams/{image_name}"
    return (
        '<div class="web-diagram-wrap">'
        f'<img class="web-diagram" src="{image_path}" alt="Worksheet composite image for this level." />'
        '</div>'
    )


def load_te_reo_terms() -> dict[str, list[dict]]:
    if not TE_REO_TRACKER_JSON.exists():
        return {}

    try:
        raw = json.loads(TE_REO_TRACKER_JSON.read_text())
    except Exception:
        return {}

    out: dict[str, list[dict]] = {}
    for topic in raw.get("topics", []):
        for item in topic.get("items", []):
            if not isinstance(item, dict):
                continue
            selected_terms = item.get("selected_terms") or []
            if not selected_terms:
                continue
            key = str(item.get("internal_code") or "").strip()
            if key:
                out[key] = [term for term in selected_terms if isinstance(term, dict)]
    return out


def load_objectives() -> list[dict]:
    source_metadata, source_metadata_by_name, source_metadata_by_objective_id, topic_titles_by_number = load_source_metadata()
    te_reo_terms = load_te_reo_terms()
    objectives: list[dict] = []

    if not LO_TRACKER_JSON.exists():
        return objectives

    try:
        tracker_items = (json.loads(LO_TRACKER_JSON.read_text()).get("learningObjectives") or [])
    except Exception:
        return objectives

    for fallback_index, tracker_item in enumerate(tracker_items):
        if not isinstance(tracker_item, dict):
            continue

        slug = str(tracker_item.get("slug") or "").strip()
        if not slug:
            continue

        objective_id = str(tracker_item.get("objectiveId") or "")
        objective_dir = OBJECTIVES_DIR / slug
        objective_page = OUTPUT_DIR / f"{slug}.html"
        level_data = []
        has_any_material = objective_dir.is_dir() or objective_page.exists()

        for key, label in LEVELS:
            tex_path = objective_dir / f"{key}-questions.tex"
            pdf_path = objective_dir / f"{key}-questions.pdf"
            questions = extract_questions_from_tex(tex_path) if tex_path.exists() else []
            normalized_questions = [normalize_question(question) for question in questions]
            normalized_questions = inject_tree_diagrams(slug, key, normalized_questions)
            normalized_questions = inject_embedded_images(slug, normalized_questions)
            if tex_path.exists() or pdf_path.exists():
                has_any_material = True
            level_data.append(
                {
                    "key": key,
                    "label": label,
                    "questions": normalized_questions,
                    "pdf": f"../../OBJECTIVES/{slug}/{key}-questions.pdf",
                    "pdf_exists": pdf_path.exists(),
                    "layout": extract_layout_settings(tex_path),
                    "media_html": composite_media_html(slug, key),
                }
            )

        if not has_any_material:
            continue

        meta = source_metadata.get(slug, {})
        if not meta and objective_id:
            meta = source_metadata_by_objective_id.get(objective_id, {})
        if not meta and objective_id:
            match = re.search(r"topic(\d+)-(lo|ex)(\d+)", objective_id, re.IGNORECASE)
            if match:
                topic_number = int(match.group(1))
                kind = match.group(2).upper()
                objective_sort = int(match.group(3))
                source_code = f"{kind}{objective_sort}"
                meta = {
                    "title": slug.removeprefix("lo-yr9-").replace("-", " ").title(),
                    "topic_label": topic_titles_by_number.get(topic_number, "Other"),
                    "topic_number": topic_number,
                    "topic_sort": topic_number,
                    "objective_sort": objective_sort,
                    "source_sort": fallback_index,
                    "internal_code": f"T{topic_number}_{kind}{objective_sort}",
                    "source_code": source_code,
                }
        if not meta:
            meta = source_metadata_by_name.get(normalize_lookup_key(slug.removeprefix("lo-yr9-").replace("-", " ")), {})

        topic_title = str(meta.get("title") or slug.removeprefix("lo-yr9-").replace("-", " ").title())
        instruction = extract_existing_instruction(objective_page)
        if not instruction and topic_title:
            instruction = f"Explore {topic_title}."

        objectives.append(
            {
                "id": objective_id,
                "topic": topic_title,
                "slug": slug,
                "instruction": instruction,
                "levels": level_data,
                "is_built": objective_dir.exists(),
                "topic_group": meta.get("topic_label", "Other"),
                "topic_number": meta.get("topic_number"),
                "topic_sort": meta.get("topic_sort", 999),
                "objective_sort": meta.get("objective_sort", fallback_index + 1),
                "source_sort": fallback_index,
                "tracker_sort": fallback_index,
                "objective_id": objective_id,
                "internal_code": meta.get("internal_code", ""),
                "source_code": meta.get("source_code", ""),
                "te_reo_terms": te_reo_terms.get(meta.get("internal_code", ""), []),
            }
        )

    objectives.sort(key=lambda obj: (obj["tracker_sort"], obj["topic_sort"], obj["objective_sort"], obj["source_sort"], obj["topic"].lower()))
    return objectives


def render_level(level: dict) -> str:
    questions = level["questions"]
    layout = level.get("layout", {"columns": 1, "row_gap": 1.2})
    media_html = level.get("media_html", "")
    items = "".join(f"<li>{latex_to_html(str(question))}</li>" for question in questions)
    download = (
        f'<a class="button button-secondary" href="{level["pdf"]}">Download PDF</a>'
        if level.get("pdf_exists")
        else '<span class="button button-secondary button-disabled">PDF coming soon</span>'
    )
    return f"""
      <section class=\"worksheet-panel\">
        <div class=\"worksheet-panel-head\">
          <div>
            <h3>{html.escape(level['label'])}</h3>
            <p>{len(questions)} web questions</p>
          </div>
          {download}
        </div>
        {media_html}
        <ol class=\"question-list\" style=\"--worksheet-columns: {layout['columns']}; --worksheet-row-gap: {layout['row_gap']:.2f}rem;\">
          {items}
        </ol>
      </section>
    """


def render_te_reo_terms(terms: list[dict]) -> str:
    if not terms:
        return ""

    items = []
    for term in terms:
        english = html.escape(str(term.get("english_term") or ""))
        maori = html.escape(str(term.get("te_reo_maori_term") or ""))
        url = html.escape(str(term.get("te_aka_word_url") or ""))
        link_html = f'<a class="te-reo-link" href="{url}" target="_blank" rel="noopener noreferrer">Open in Te Aka</a>' if url else ""
        meta_html = f'''<div class="te-reo-meta"><h3>{english}</h3>{link_html}</div>'''
        items.append(
            f'''<article class="te-reo-card">
        <p class="te-reo-word">{maori}</p>
        {meta_html}
      </article>'''
        )

    return f"""
      <section class=\"worksheet-panel te-reo-panel\">
        <div class=\"worksheet-panel-head\">
          <div>
            <h3>Te reo Māori terms</h3>
          </div>
        </div>
        <div class=\"te-reo-grid\">
          {''.join(items)}
        </div>
      </section>
    """


def render_objective_page(obj: dict) -> str:
    te_reo_terms = render_te_reo_terms(obj.get("te_reo_terms", []))
    levels = "".join(render_level(level) for level in obj["levels"])
    page_title = html.escape(obj['topic'])
    page_description = html.escape(obj['instruction'] or DESCRIPTION)
    return f"""<!DOCTYPE html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>{page_title} · {TITLE}</title>
    <meta name=\"description\" content=\"{page_description}\" />
    <meta property=\"og:title\" content=\"{page_title} · {TITLE}\" />
    <meta property=\"og:description\" content=\"{page_description}\" />
    <meta name=\"twitter:card\" content=\"summary\" />
    <link rel=\"icon\" type=\"image/png\" href=\"../favicon.png\" />
    <link rel=\"stylesheet\" href=\"../styles.css\" />
    <script>
      window.MathJax = {{ tex: {{ inlineMath: [['$', '$'], ['\\(', '\\)']] }} }};
    </script>
    <script defer src="../assets/js/page-seps.js"></script>
    <script defer src=\"{MATHJAX}\"></script>
  </head>
  <body>
    <header class=\"hero hero-subpage\">
      <div class=\"hero-inner\">
        <div class=\"hero-brand\">
          <img class=\"hero-logo\" src=\"../header-logo.png\" alt=\"Mana Maths jade twist logo\" />
          <div class=\"hero-copy\">
            <h1>{html.escape(obj['topic'])}</h1>
            <p class=\"lead\">{html.escape(obj['instruction'])}</p>
          </div>
        </div>
        <a class=\"button\" href=\"../index.html\">All objectives</a>
      </div>
    </header>

    <main class=\"page-shell page-shell-detail\">
      {te_reo_terms}
      {levels}
    </main>
  </body>
</html>
"""


def render_index(objectives: list[dict]) -> str:
    grouped: dict[str, list[dict]] = {}
    ordered_groups: list[str] = []
    for obj in objectives:
        group = obj.get("topic_group") or "Other"
        if group not in grouped:
            grouped[group] = []
            ordered_groups.append(group)
        grouped[group].append(obj)

    menu_sections = []
    card_sections = []
    for group_name in ordered_groups:
        group_objectives = grouped[group_name]
        menu_links = "".join(
            f'<a href="./objectives/{obj["slug"]}.html">{html.escape(obj["topic"])}</a>' for obj in group_objectives
        )
        menu_sections.append(
            f'<div class="header-dropdown-group"><div class="header-dropdown-heading">{html.escape(group_name)}</div>{menu_links}</div>'
        )

        cards = []
        for obj in group_objectives:
            debug_code = obj.get("internal_code") or obj.get("source_code") or ""
            if debug_code and not debug_code.startswith("YR9_"):
                debug_code = f"YR9_{debug_code}"
            debug_markup = (
                f'<span class="objective-debug-code" title="Canonical learning objective code">{html.escape(debug_code)}</span>'
                if debug_code
                else ""
            )
            cards.append(
                f"""
      <article class="objective-card">
        <div class="objective-card-top">
          <h2>{html.escape(obj['topic'])}</h2>
          <p class="card-copy">{html.escape(obj['instruction'])}</p>
        </div>
        <div class="objective-card-meta">
          <span>{sum(len(level['questions']) for level in obj['levels'])} questions</span>
          <span>3 levels</span>
          {debug_markup}
        </div>
        <div class="objective-card-actions">
          <a class="button" href="./objectives/{obj['slug']}.html">Open worksheet</a>
        </div>
      </article>
                """
            )

        card_sections.append(
            f"""
      <section class="topic-group">
        <div class="topic-group-header">
          <h2>{html.escape(group_name)}</h2>
        </div>
        <div class="objective-card-grid">
          {''.join(cards)}
        </div>
      </section>
            """
        )

    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{TITLE}</title>
    <meta name="description" content="{DESCRIPTION}" />
    <meta property="og:title" content="{TITLE}" />
    <meta property="og:description" content="{DESCRIPTION}" />
    <meta property="og:url" content="https://manamaths.co.nz/" />
    <meta name="twitter:card" content="summary" />
    <link rel="icon" type="image/png" href="./favicon.png" />
    <link rel="stylesheet" href="./styles.css" />
    <script>
      (function() {{
        const params = new URLSearchParams(window.location.search);
        if (params.has('debug') || params.get('mode') === 'debug') {{
          document.documentElement.dataset.debug = '1';
        }}
      }})();
    </script>
  </head>
  <body>
    <header class="hero">
      <div class="hero-inner">
        <div class="hero-brand">
          <img class="hero-logo" src="./header-logo.png" alt="Mana Maths jade twist logo" />
          <div class="hero-copy">
            <h1>Mana Maths</h1>
          </div>
        </div>

        <details class="header-menu">
          <summary aria-label="Open learning objectives menu">
            <span></span>
            <span></span>
            <span></span>
          </summary>
          <nav class="header-dropdown" aria-label="Learning objectives">
            {''.join(menu_sections)}
          </nav>
        </details>
      </div>
    </header>

    <main class="page-shell">
      {''.join(card_sections)}
    </main>
  </body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Mana Maths website HTML.")
    parser.add_argument(
        "--slug",
        action="append",
        dest="slugs",
        help="Generate only the specified objective slug(s). Index is still refreshed unless --skip-index is used.",
    )
    parser.add_argument(
        "--skip-index",
        action="store_true",
        help="Do not rewrite index.html.",
    )
    args = parser.parse_args()

    objectives = load_objectives()
    OUTPUT_DIR.mkdir(exist_ok=True)

    selected = objectives
    if args.slugs:
        wanted = set(args.slugs)
        selected = [obj for obj in objectives if obj["slug"] in wanted]
        missing = sorted(wanted - {obj["slug"] for obj in selected})
        if missing:
            print(f"Unknown slug(s): {', '.join(missing)}")
            return 1

    for obj in selected:
        page = render_objective_page(obj)
        (OUTPUT_DIR / f"{obj['slug']}.html").write_text(page)

    if not args.skip_index:
        (SITE_DIR / "index.html").write_text(render_index(objectives))
        print(f"Wrote {len(selected)} objective page(s) and index.html")
    else:
        print(f"Wrote {len(selected)} objective page(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

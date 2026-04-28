#!/usr/bin/env python3
"""Generate Mana Maths website HTML — dashboard-style with PDF preview images."""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
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
PREVIEWS_DIR = SITE_DIR / "previews"
CANONICAL_JSON = WORKSPACE_ROOT / "manamaths-tasks" / "canonical" / "year-9-learning-objectives.json"
LO_TRACKER_JSON = OPERATIONS_DIR / "data" / "lo-tracker.json"
TE_REO_TRACKER_JSON = OPERATIONS_DIR / "data" / "te-reo-progress.json"
NOTES_TRACKER_JSON = WORKSPACE_ROOT / "manamaths-notes" / "OPERATIONS" / "data" / "notes-tracker.json"
OUTPUT_DIR = SITE_DIR / "objectives"
NOTES_PDF_OUTPUT_DIR = SITE_DIR / "notes-pdfs"
SOLUTIONS_REPO = WORKSPACE_ROOT / "manamaths-solutions"
SOLUTIONS_OUTPUT_DIR = SITE_DIR / "solutions-pdfs"
TITLE = "Mana Maths"
DESCRIPTION = "Helping maths teachers save time. We make maths curriculum content resources easy to find."
LEVELS = [
    ("foundation", "Foundation"),
    ("proficient", "Proficient"),
    ("excellence", "Excellence"),
]
MATHJAX = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"
CHROMIUM = "chromium-browser"
WEB_DIAGRAM_DIRNAME = "web-diagrams"
META_DESCRIPTION_RE = re.compile(r'<meta\s+name="description"\s+content="([^"]*)"', re.IGNORECASE)
LEAD_RE = re.compile(r'<p\s+class="lead">(.*?)</p>', re.IGNORECASE | re.DOTALL)

# Level descriptions — one sentence per module, sourced from the actual content
LEVEL_DESCRIPTIONS = {
    "foundation": "Build confidence with basic digit values, reading and writing numbers, comparing values, and partitioning into tens and ones.",
    "proficient": "Tackle larger numbers, decimals to thousandths, inequality comparisons, ordering multiple values, and full partitioning.",
    "excellence": "Explain misconceptions, justify reasoning, handle 3 d.p. ordering, build numbers from place-value parts, and reason about equivalence.",
}
LEVEL_ACCENT = {
    "foundation": "#85b24a",
    "proficient": "#5d8a56",
    "excellence": "#3e6f3f",
}

PREVIEW_CACHE: dict[str, list[str]] = {}


def load_cached_previews(slug: str) -> dict[str, list[str]]:
    """Return a dict mapping prefix to list of preview URLs for each page."""
    preview_dir = PREVIEWS_DIR / slug
    if not preview_dir.exists():
        return {}
    result: dict[str, list[str]] = {}
    for f in sorted(preview_dir.iterdir()):
        if f.suffix not in (".png", ".webp"):
            continue
        # prefix is everything before -p001
        name = f.stem
        parts = name.rsplit("-p", 1)
        if len(parts) != 2:
            continue
        prefix = parts[0]
        if prefix not in result:
            result[prefix] = []
        result[prefix].append(f"../previews/{slug}/{f.name}")
    return result


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


def load_notes_index() -> dict[str, dict]:
    if not NOTES_TRACKER_JSON.exists():
        return {}
    try:
        raw = json.loads(NOTES_TRACKER_JSON.read_text())
    except Exception:
        return {}
    out: dict[str, dict] = {}
    for item in raw.get("learningObjectives", []):
        if not isinstance(item, dict):
            continue
        slug = str(item.get("slug") or "").strip()
        if not slug:
            continue
        if str(item.get("notesStatus") or "") != "complete":
            continue
        pdf_source = WORKSPACE_ROOT / "manamaths-notes" / "OBJECTIVES" / slug / "build" / "main.pdf"
        pdf_target = NOTES_PDF_OUTPUT_DIR / f"{slug}.pdf"
        pdf_url = ""
        if pdf_source.exists():
            pdf_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(pdf_source, pdf_target)
            pdf_url = f"../notes-pdfs/{slug}.pdf"
        out[slug] = {
            "title": str(item.get("canonicalDisplayTitle") or item.get("canonicalTitle") or slug),
            "page_url": f"/objectives/{slug}.html#notes",
            "pdf_url": pdf_url,
        }
    return out


def load_objectives() -> list[dict]:
    source_metadata, source_metadata_by_name, source_metadata_by_objective_id, topic_titles_by_number = load_source_metadata()
    te_reo_terms = load_te_reo_terms()
    notes_index = load_notes_index()
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
            pdf_path = objective_dir / f"{key}-questions.pdf"
            if pdf_path.exists() or (objective_dir / f"{key}-questions.tex").exists():
                has_any_material = True
            level_data.append({
                "key": key,
                "label": label,
                "pdf": f"../../OBJECTIVES/{slug}/{key}-questions.pdf",
                "pdf_exists": pdf_path.exists(),
                "desc": LEVEL_DESCRIPTIONS.get(key, ""),
                "accent": LEVEL_ACCENT.get(key, "#85b24a"),
            })

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

        tracker_topic_id = str(tracker_item.get("canonicalTopicId") or "")
        tracker_topic_match = re.search(r"T(\d+)$", tracker_topic_id)
        tracker_topic_number = int(tracker_topic_match.group(1)) if tracker_topic_match else None
        topic_title = str(meta.get("title") or slug.removeprefix("lo-yr9-").replace("-", " ").title())
        instruction = extract_existing_instruction(objective_page)
        if not instruction and topic_title:
            instruction = f"Explore {topic_title}."
        internal_code = str(meta.get("internal_code") or tracker_item.get("canonicalInternalCode") or "")
        source_code = str(meta.get("source_code") or tracker_item.get("canonicalSourceCode") or "")
        topic_number = meta.get("topic_number")
        if topic_number is None:
            topic_number = tracker_topic_number
        topic_sort = meta.get("topic_sort", topic_number if isinstance(topic_number, int) else 999)
        topic_group = meta.get("topic_label") or (topic_titles_by_number.get(topic_number) if isinstance(topic_number, int) else None) or "Other"

        # Skills — derive sensible skill names from the instruction
        raw_instruction = instruction.strip().rstrip(".").lower()
        skill_keywords = {
            "Digit values": ["digit", "value", "identify", "place"],
            "Reading and writing numbers": ["read", "write"],
            "Comparing and ordering": ["compare", "order"],
            "Partitioning numbers": ["partition", "part"],
            "Reasoning &amp; explaining": ["explain", "justify"],
            "Working with decimals": ["decimal", "decimals"],
        }
        skills = []
        seen = set()
        for display, keywords in skill_keywords.items():
            if any(k in raw_instruction for k in keywords):
                if display not in seen:
                    skills.append(display)
                    seen.add(display)


        objectives.append({
            "id": objective_id,
            "topic": topic_title,
            "slug": slug,
            "instruction": instruction,
            "skills": skills,
            "levels": level_data,
            "is_built": objective_dir.exists(),
            "topic_group": topic_group,
            "topic_number": topic_number,
            "topic_sort": topic_sort,
            "objective_sort": meta.get("objective_sort", fallback_index + 1),
            "source_sort": fallback_index,
            "tracker_sort": fallback_index,
            "objective_id": objective_id,
            "internal_code": internal_code,
            "source_code": source_code,
            "te_reo_terms": te_reo_terms.get(internal_code, []),
            "notes": notes_index.get(slug),
        })

    objectives.sort(key=lambda obj: (obj["tracker_sort"], obj["topic_sort"], obj["objective_sort"], obj["source_sort"], obj["topic"].lower()))
    return objectives


def render_te_reo_panel(terms: list[dict], slug: str) -> str:
    """Render te reo Māori terms — shows PDF preview only, no HTML cards."""
    if not terms:
        return ""

    previews = load_cached_previews(slug)
    te_reo_preview = previews.get("te-reo", [])
    preview_html = ""
    if te_reo_preview and len(te_reo_preview) > 0:
        preview_html = f'<div class="preview-figure"><a href="../te-reo-pdfs/{slug}.pdf" target="_blank" rel="noopener"><img class="pdf-preview-thumb" src="{te_reo_preview[0]}" alt="" loading="lazy" /></a></div>'

    return f'''
      <section class="module-card" style="--card-accent: #85b24a;">
        {preview_html}
        <div class="module-card-actions">
          <a class="button button-secondary" href="../te-reo-pdfs/{slug}.pdf" target="_blank" rel="noopener">Open terms PDF</a>
        </div>
      </section>
    '''


def render_notes_panel(notes: dict | None, slug: str) -> str:
    if not notes:
        return ""
    title = html.escape(str(notes.get("title") or "Notes"))
    pdf_url = html.escape(str(notes.get("pdf_url") or ""))

    previews = load_cached_previews(slug)
    notes_pages = previews.get("notes", [])

    preview_html = ""
    if notes_pages and len(notes_pages) > 0:
        preview_html = f'<div class="preview-figure"><a href="{pdf_url}" target="_blank" rel="noopener"><img class="pdf-preview-thumb" src="{notes_pages[0]}" alt="" loading="lazy" /></a></div>'

    pdf_button = f'<a class="button" href="{pdf_url}" target="_blank" rel="noopener">Open notes PDF</a>' if pdf_url else ""
    return f'''
      <section id="notes" class="module-card" style="--card-accent: #3e6f3f;">
        {preview_html}
        <div class="module-card-actions">
          {pdf_button}
        </div>
      </section>
    '''


def render_module_card(level: dict, slug: str) -> str:
    """Render a single module card with PDF preview and action buttons."""
    key = level["key"]
    label = level["label"]
    desc = level["desc"]
    accent = level["accent"]
    tasks_pdf = level["pdf"]
    pdf_exists = level["pdf_exists"]

    icon_count = {"foundation": 1, "proficient": 2, "excellence": 3}.get(key, 1)
    icon_html = "".join(
        "" for _ in range(icon_count)
    )

    solutions_pdf = f"../solutions-pdfs/{slug}/{key}-answers.pdf"
    solutions_exists = (SOLUTIONS_OUTPUT_DIR / slug / f"{key}-answers.pdf").exists()

    # Preview — just the first page of the tasks PDF
    previews = load_cached_previews(slug)
    tasks_pages = previews.get(f"{key}-tasks", [])
    preview_thumbnails = ""
    if tasks_pages and len(tasks_pages) > 0:
        preview_thumbnails = f'<div class="preview-figure"><a href="{tasks_pdf}" target="_blank" rel="noopener"><img class="pdf-preview-thumb" src="{tasks_pages[0]}" alt="" loading="lazy" /></a></div>'

    tasks_button = (
        f'<a class="button" href="{tasks_pdf}" target="_blank" rel="noopener">Open tasks PDF</a>'
        if pdf_exists
        else '<span class="button button-disabled">Tasks coming soon</span>'
    )
    solutions_button = (
        f'<a class="button button-secondary" href="{solutions_pdf}" target="_blank" rel="noopener">Open solutions PDF</a>'
        if solutions_exists
        else ""
    )

    return f'''
      <section class="module-card" style="--card-accent: {accent};">
        {icon_html}
        {preview_thumbnails}
        <div class="module-card-actions">
          {tasks_button}
          {solutions_button}
        </div>
      </section>
    '''


def render_skills_section(obj: dict) -> str:
    skills = obj.get("skills", [])
    if not skills:
        return ""

    total_qs = sum(
        27 if l["pdf_exists"] else 0 for l in obj["levels"]
    )
    chips = "".join(f"<li>{html.escape(s)}</li>" for s in skills)
    return f'''
      <section class="lo-panel lo-details">
        <div class="detail-grid">
          <div class="detail-group">
            <h3>Key skills</h3>
            <ul class="chip-list">
              {chips}
            </ul>
          </div>
          <div class="detail-group">
            <h3>Quick stats</h3>
            <ul class="chip-list">
              <li>{total_qs} total questions</li>
              <li>3 difficulty levels</li>
              <li>Answers included</li>
            </ul>
          </div>
        </div>
      </section>
    '''


def render_objective_page(obj: dict) -> str:
    skills_section = render_skills_section(obj)
    te_reo = render_te_reo_panel(obj.get("te_reo_terms", []), obj["slug"])
    notes = render_notes_panel(obj.get("notes"), obj["slug"])
    cards = "".join(render_module_card(level, obj["slug"]) for level in obj["levels"])
    # Wrap te reo and notes in a module-card grid for side-by-side layout
    extras_panels = []
    if te_reo:
        extras_panels.append(te_reo)
    if notes:
        extras_panels.append(notes)
    extras_grid = ""
    if extras_panels:
        extras_grid = '<div class="module-card-grid module-card-grid-extra">\n' + "\n".join(extras_panels) + '\n      </div>'
    page_title = html.escape(obj['topic'])
    page_description = html.escape(obj['instruction'] or DESCRIPTION)

    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{page_title} · {TITLE}</title>
    <meta name="description" content="{page_description}" />
    <meta property="og:title" content="{page_title} · {TITLE}" />
    <meta property="og:description" content="{page_description}" />
    <meta name="twitter:card" content="summary" />
    <link rel="icon" type="image/png" href="../favicon.png" />
    <link rel="stylesheet" href="../styles.css" />
    <script defer src="{MATHJAX}"></script>
  </head>
  <body>
    <header class="hero hero-subpage">
      <div class="hero-inner">
        <div class="hero-brand">
          <img class="hero-logo" src="../header-logo.png" alt="Mana Maths jade twist logo" />
          <div class="hero-copy">
            <h1>{page_title}</h1>
            <p class="lead">{page_description}</p>
          </div>
        </div>
        <a class="button" href="../index.html">All objectives</a>
      </div>
    </header>

    <main class="page-shell page-shell-detail">
      {skills_section}
      {extras_grid}
      <div class="module-card-grid">
        {cards}
      </div>
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
            total_qs = sum(27 if l["pdf_exists"] else 0 for l in obj["levels"])
            cards.append(f'''
      <article class="objective-card">
        <div class="objective-card-top">
          <h2>{html.escape(obj['topic'])}</h2>
          <p class="card-copy">{html.escape(obj['instruction'])}</p>
        </div>
        <div class="objective-card-meta">
          <span>{total_qs} questions</span>
          <span>3 levels</span>
          {debug_markup}
        </div>
        <div class="objective-card-actions">
          <a class="button" href="./objectives/{obj['slug']}.html">Open worksheet</a>
        </div>
      </article>''')

        card_sections.append(f'''
      <section class="topic-group">
        <div class="topic-group-header">
          <h2>{html.escape(group_name)}</h2>
        </div>
        <div class="objective-card-grid">
          {''.join(cards)}
        </div>
      </section>''')

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
        if (params.get('debug') === 'true') {{
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
    parser = argparse.ArgumentParser(description="Generate Mana Maths website HTML — dashboard layout.")
    parser.add_argument("--slug", action="append", dest="slugs", help="Generate only the specified objective slug(s).")
    parser.add_argument("--skip-index", action="store_true", help="Do not rewrite index.html.")
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
        solutions_src = SOLUTIONS_REPO / "OBJECTIVES" / obj["slug"] if SOLUTIONS_REPO.exists() else None
        if solutions_src and solutions_src.is_dir():
            solutions_dst = SOLUTIONS_OUTPUT_DIR / obj["slug"]
            solutions_dst.mkdir(parents=True, exist_ok=True)
            for pdf in solutions_src.glob("*-answers.pdf"):
                shutil.copy2(pdf, solutions_dst / pdf.name)

    if not args.skip_index:
        (SITE_DIR / "index.html").write_text(render_index(objectives))
        print(f"Wrote {len(selected)} objective page(s) and index.html")
    else:
        print(f"Wrote {len(selected)} objective page(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

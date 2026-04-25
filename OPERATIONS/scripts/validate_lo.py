#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OPERATIONS_DIR = SCRIPT_DIR.parent
REPO_ROOT = OPERATIONS_DIR.parent
OBJECTIVES_DIR = REPO_ROOT / "OBJECTIVES"
SITE_DIR = REPO_ROOT / "SITE"
LEVELS = ["foundation", "proficient", "excellence"]
BAD_HTML_SNIPPETS = [
    "@@HTML",
    r"\mbox",
    "<li>S</li><li>e</li><li>e</li>",
    "See manamaths/",
]
PDF_NOTE_CLASS = 'question-diagram-note'
PAGE_SEPS_JS = SITE_DIR / 'assets' / 'js' / 'page-seps.js'


def check_tex(tex_path: Path) -> list[str]:
    errors: list[str] = []
    if not tex_path.exists():
        errors.append(f"Missing worksheet file: {tex_path.relative_to(REPO_ROOT)}")
        return errors

    text = tex_path.read_text(errors="replace")
    uses_tasks = "\\begin{tasks}" in text and "\\usepackage{tasks}" in text
    uses_custom_visual_layout = "\\includegraphics" in text and "\\begin{minipage}" in text
    uses_beamer_cards = "\\documentclass[aspectratio=169,12pt]{beamer}" in text and "\\MMProblem" in text
    if not uses_tasks and not uses_custom_visual_layout and not uses_beamer_cards:
        errors.append(f"Worksheet is not using an approved layout: {tex_path.relative_to(REPO_ROOT)}")
    if "\\begin{enumerate}" in text:
        errors.append(f"Worksheet still contains enumerate layout: {tex_path.relative_to(REPO_ROOT)}")
    return errors


def check_html(slug: str, html_path: Path) -> list[str]:
    errors: list[str] = []
    if not html_path.exists():
        errors.append(f"Missing web page: {html_path.relative_to(REPO_ROOT)}")
        return errors

    text = html_path.read_text(errors="replace")
    if not PAGE_SEPS_JS.exists():
        errors.append(f"Missing beautify asset: {PAGE_SEPS_JS.relative_to(REPO_ROOT)}")
    for snippet in BAD_HTML_SNIPPETS:
        if snippet in text:
            errors.append(f"Web page still contains broken render content `{snippet}`: {html_path.relative_to(REPO_ROOT)}")
    expected_pdf = f"../../OBJECTIVES/{slug}/foundation-questions.pdf"
    if expected_pdf not in text:
        errors.append(f"Web page is missing expected PDF links for {slug}: {html_path.relative_to(REPO_ROOT)}")
    if '../assets/js/page-seps.js' not in text:
        errors.append(f"Web page is missing page-seps.js beautify script: {html_path.relative_to(REPO_ROOT)}")

    # Additional web checks to prevent regressions
    # 1) Detect literal visible braces inside question lists
    ol_blocks = []
    for part in text.split('<ol'):
        if 'class="question-list"' in part:
            # approximate extract of block up to closing </ol>
            ol_blocks.append(part.split('</ol>', 1)[0])
    for block in ol_blocks:
        visible_block = re.sub(r"\$.*?\$", "", block, flags=re.S)
        visible_block = re.sub(r"<[^>]+>", "", visible_block)
        if '{' in visible_block or '}' in visible_block:
            errors.append(f"Found literal brace characters in web questions (possible LaTeX leak): {html_path.relative_to(REPO_ROOT)}")

        # 2) ensure separators (row-separator) appear only after multiples of 9 items
        # Build a token stream: count <li> occurrences and check positions of row-separator
        tokens = block.split('<')
        li_count = 0
        for t in tokens:
            if t.startswith('li'):
                li_count += 1
            if 'class="row-separator"' in t:
                # separator found; li_count should be multiple of 9
                if li_count % 9 != 0:
                    errors.append(f"row-separator found after non-9n item ({li_count}) in {html_path.relative_to(REPO_ROOT)}")

    # 3) check that numeric markers are present (either question-list-reflow or CSS counter usage)
    if 'question-list-reflow' not in text and 'question-row' not in text:
        # also accept standard ol with markers; check ol has visible list-style
        if 'class="question-list"' in text and 'counter-reset' not in (SITE_DIR / 'styles.css').read_text(errors='replace'):
            errors.append(f"No reflow grouping or CSS counters found for web questions in {html_path.relative_to(REPO_ROOT)}")

    return errors


def check_index(slug: str, index_path: Path) -> list[str]:
    errors: list[str] = []
    if not index_path.exists():
        return [f"Missing index.html: {index_path.relative_to(REPO_ROOT)}"]
    text = index_path.read_text(errors="replace")
    if f"./objectives/{slug}.html" not in text:
        errors.append(f"index.html is missing link to {slug}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate one Mana Maths LO for layout and web-render issues.")
    parser.add_argument("slug", help="LO slug, e.g. lo-yr9-solving-1-step-equations")
    args = parser.parse_args()

    slug = args.slug
    lo_dir = OBJECTIVES_DIR / slug
    html_path = SITE_DIR / "objectives" / f"{slug}.html"
    index_path = SITE_DIR / "index.html"

    errors: list[str] = []
    if not lo_dir.is_dir():
        errors.append(f"LO folder not found: {lo_dir.relative_to(REPO_ROOT)}")
    else:
        for level in LEVELS:
            errors.extend(check_tex(lo_dir / f"{level}-questions.tex"))

    errors.extend(check_html(slug, html_path))
    errors.extend(check_index(slug, index_path))

    if errors:
        print("Validation failed:\n")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Validation OK: {slug}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

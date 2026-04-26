#!/usr/bin/env python3
"""
Generate PNG preview images for all PDF pages in an LO or across all LOs.

Output: SITE/previews/lo-yr9-<slug>/*.png

Each PDF gets one preview per page. The first page (000.png) is the
thumbnail shown in the module card. Subsequent pages can be shown in
a lightbox or as scrollable strips later.

Usage:
  python3 OPERATIONS/scripts/generate_previews.py [--slug lo-yr9-place-values-and-decimals]
  python3 OPERATIONS/scripts/generate_previews.py  # all LOs
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OPERATIONS_DIR = SCRIPT_DIR.parent
REPO_ROOT = OPERATIONS_DIR.parent
SITE_DIR = REPO_ROOT / "SITE"
OBJECTIVES_DIR = REPO_ROOT / "OBJECTIVES"
SOLUTIONS_DIR = SITE_DIR / "solutions-pdfs"
NOTES_DIR = SITE_DIR / "notes-pdfs"
PREVIEWS_DIR = SITE_DIR / "previews"

LO_TRACKER_JSON = OPERATIONS_DIR / "data" / "lo-tracker.json"

# Use virtualenv python with pymupdf
PYTHON = "/tmp/pdfenv/bin/python3"

PREVIEW_DPI = 96  # good quality, ~600px wide for beamer slides


def slug_order() -> list[dict]:
    """Load slugs from tracker."""
    if not LO_TRACKER_JSON.exists():
        return []
    raw = json.loads(LO_TRACKER_JSON.read_text())
    return raw.get("learningObjectives", [])


def generate_lo_previews(slug: str) -> int:
    """Generate all preview images for one LO slug. Returns count of images generated."""
    count = 0

    # Sources: tasks PDFs, solutions PDFs, notes PDF
    sources: list[tuple[str, Path, bool]] = []

    # Tasks PDFs
    for level in ("foundation", "proficient", "excellence"):
        p = OBJECTIVES_DIR / slug / f"{level}-questions.pdf"
        if p.exists():
            sources.append((f"{level}-tasks", p, True))

    # Solutions PDFs (in SITE/solutions-pdfs/)
    for level in ("foundation", "proficient", "excellence"):
        p = SOLUTIONS_DIR / slug / f"{level}-answers.pdf"
        if p.exists():
            sources.append((f"{level}-solutions", p, True))

    # Notes PDF
    notes_pdf = NOTES_DIR / f"{slug}.pdf"
    if notes_pdf.exists():
        sources.append(("notes", notes_pdf, False))

    if not sources:
        return 0

    preview_dir = PREVIEWS_DIR / slug
    preview_dir.mkdir(parents=True, exist_ok=True)

    import subprocess
    script = f"""
import fitz, sys
slug = '{slug}'
sources = {[(name, str(path), multi) for name, path, multi in sources]}
outdir = '{preview_dir}'
for name, path, multi in sources:
    doc = fitz.open(path)
    pages = doc.page_count if multi else 1
    for i in range(pages):
        page = doc[i]
        pix = page.get_pixmap(dpi={PREVIEW_DPI})
        outpath = f"{{outdir}}/{{name}}-p{{i+1:03d}}.png"
        pix.save(outpath)
        print(outpath)
    doc.close()
"""
    result = subprocess.run(
        [PYTHON, "-c", script],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        print(f"  ERROR generating previews for {slug}: {result.stderr.strip()}", file=sys.stderr)
        return 0
    lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
    for line in lines:
        print(f"  {line}")
    return len(lines)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Generate PDF preview images.")
    parser.add_argument("--slug", help="Process only this LO slug")
    args = parser.parse_args()

    if args.slug:
        slugs = [args.slug]
    else:
        items = slug_order()
        slugs = [item["slug"] for item in items if item.get("slug")]

    total = 0
    for slug in slugs:
        print(f"Generating previews for {slug}...")
        n = generate_lo_previews(slug)
        total += n
        print(f"  → {n} images")

    print(f"\nDone: {total} preview images")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

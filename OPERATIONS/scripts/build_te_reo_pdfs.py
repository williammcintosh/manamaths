#!/usr/bin/env python3
"""
Generate a clean te reo Māori terms PDF for each LO that has terms.

The PDF uses the same beamer template style as worksheets — one
projectable page with term cards.

Output: SITE/te-reo-pdfs/lo-yr9-<slug>.pdf
Preview: SITE/previews/lo-yr9-<slug>/te-reo-p001.png
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OPERATIONS_DIR = SCRIPT_DIR.parent
REPO_ROOT = OPERATIONS_DIR.parent
SITE_DIR = REPO_ROOT / "SITE"
TEMPLATE_PATH = OPERATIONS_DIR / "templates" / "te-reo-template.tex"
TE_REO_TRACKER_JSON = OPERATIONS_DIR / "data" / "te-reo-progress.json"
LO_TRACKER_JSON = OPERATIONS_DIR / "data" / "lo-tracker.json"
TE_REO_PDF_DIR = SITE_DIR / "te-reo-pdfs"
PREVIEWS_DIR = SITE_DIR / "previews"

TECTONIC = "/home/debid/bin/tectonic"

# Map internal codes to slugs via tracker
def load_slug_map() -> dict[str, str]:
    slugs: dict[str, str] = {}
    if not LO_TRACKER_JSON.exists():
        return slugs
    try:
        raw = json.loads(LO_TRACKER_JSON.read_text())
    except Exception:
        return slugs
    for item in raw.get("learningObjectives", []):
        code = item.get("canonicalInternalCode") or ""
        slug = item.get("slug") or ""
        if code and slug:
            slugs[code] = slug
    return slugs


def load_all_terms() -> dict[str, list[dict]]:
    """Return dict mapping internal_code -> list of term dicts."""
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
            selected = item.get("selected_terms") or []
            if not selected:
                continue
            key = str(item.get("internal_code") or "").strip()
            if key:
                out[key] = [t for t in selected if isinstance(t, dict)]
    return out


def slug_for_code(code: str, slug_map: dict[str, str]) -> str | None:
    return slug_map.get(code)


def build_tex(terms: list[dict]) -> str:
    """Build LaTeX for the term cards — 3 per row, each with Te Aka link."""
    template = TEMPLATE_PATH.read_text()

    def escape(s: str) -> str:
        return s.replace("&", r"\&").replace("#", r"\#").replace("%", r"\%").replace("_", r"\_").replace("$", r"\$")

    cards = []
    for t in terms:
        maori = escape(t.get("te_reo_maori_term", ""))
        english = escape(t.get("english_term", ""))
        url = escape(t.get("te_aka_word_url", ""))
        cards.append(f"\\TermCard{{{maori}}}{{{english}}}{{{url}}}")

    # Arrange 2 per row using a tabular for clean, wide columns
    cols_per_row = 2
    rows = []
    for i in range(0, len(cards), cols_per_row):
        chunk = cards[i:i+cols_per_row]
        cells = " & ".join(chunk)
        if len(chunk) < cols_per_row:
            cells += " & \\hfill"
        rows.append(cells)
    
    all_cards_text = "\\begin{tabular}{c@{\\hskip 1.5em}c}\n"
    all_cards_text += " \\\\[2.5em]\n".join(rows)
    all_cards_text += " \\\\"
    all_cards_text += "\n\\end{tabular}"
    latex = template.replace("TERM_CARDS", all_cards_text.strip())
    return latex


def build_te_reo_pdf(slug: str, terms: list[dict]) -> int:
    """Generate the te reo PDF for this LO. Returns 0 on success."""
    TE_REO_PDF_DIR.mkdir(parents=True, exist_ok=True)
    out_path = TE_REO_PDF_DIR / f"{slug}.pdf"
    preview_dir = PREVIEWS_DIR / slug
    preview_dir.mkdir(parents=True, exist_ok=True)

    build_dir = Path("/tmp") / f"te-reo-{slug}"
    build_dir.mkdir(parents=True, exist_ok=True)

    try:
        tex_content = build_tex(terms)
        tex_path = build_dir / "te-reo.tex"
        tex_path.write_text(tex_content)
        # Copy logo so the PDF can reference it
        logo_src = REPO_ROOT / "SITE" / "header-logo.png"
        logo_dst = build_dir / "header-logo.png"
        if logo_src.exists():
            import shutil
            shutil.copy2(logo_src, logo_dst)
        # Debug: save the tex content
        (build_dir / "debug.tex").write_text(tex_content)

        result = subprocess.run(
            [TECTONIC, "-p", "te-reo.tex"],
            capture_output=True, text=True, timeout=60,
            cwd=str(build_dir)
        )
        if result.returncode != 0:
            print(f"  tectonic error for {slug}: {result.stderr[-300:]}", file=sys.stderr)
            return 1

        # tectonic outputs to build_dir/te-reo.pdf
        built_pdf = build_dir / "te-reo.pdf"
        if built_pdf.exists():
            import shutil
            shutil.copy2(built_pdf, out_path)
            # Generate preview
            PYTHON = "/tmp/pdfenv/bin/python3"
            pf_result = subprocess.run(
                [PYTHON, "-c", f"""
import fitz
doc = fitz.open(r'{out_path}')
if doc.page_count > 0:
    pix = doc[0].get_pixmap(dpi=96)
    pix.save(r'{preview_dir / "te-reo-p001.png"}')
doc.close()
"""],
                capture_output=True, text=True, timeout=30
            )
            if pf_result.returncode != 0:
                print(f"  preview error for {slug}: {pf_result.stderr}", file=sys.stderr)
            print(f"  → {out_path}")
            return 0
        else:
            print(f"  No PDF produced for {slug}", file=sys.stderr)
            return 1
    finally:
        import shutil
        # Keep build artifacts for debugging:
        print(f"  Build dir: {build_dir}", file=sys.stderr)
        # shutil.rmtree(build_dir, ignore_errors=True)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Generate te reo Māori terms PDFs.")
    parser.add_argument("--slug", help="Process only this LO slug")
    args = parser.parse_args()

    slug_map = load_slug_map()
    all_terms = load_all_terms()

    if args.slug:
        # Find the internal code for this slug
        code = None
        for c, s in slug_map.items():
            if s == args.slug:
                code = c
                break
        if code and code in all_terms:
            targets = [(args.slug, all_terms[code])]
        else:
            print(f"No te reo terms found for slug: {args.slug}")
            return 1
    else:
        targets = []
        for code, slug in slug_map.items():
            if code in all_terms:
                targets.append((slug, all_terms[code]))

    if not targets:
        print("No te reo terms found.")
        return 0

    success = 0
    for slug, terms in targets:
        print(f"Building te reo PDF for {slug} ({len(terms)} terms)...")
        rc = build_te_reo_pdf(slug, terms)
        if rc == 0:
            success += 1

    print(f"\nDone: {success}/{len(targets)} te reo PDFs generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

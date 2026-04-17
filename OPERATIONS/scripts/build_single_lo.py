#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OPERATIONS_DIR = SCRIPT_DIR.parent
REPO_ROOT = OPERATIONS_DIR.parent
OBJECTIVES_DIR = REPO_ROOT / "OBJECTIVES"
LEVELS = ["foundation", "proficient", "excellence"]


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=REPO_ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely build and publish one Mana Maths LO.")
    parser.add_argument("slug", help="LO slug, e.g. lo-yr9-solving-1-step-equations")
    parser.add_argument("--skip-pdfs", action="store_true", help="Skip PDF rebuild")
    parser.add_argument("--skip-site", action="store_true", help="Skip website HTML generation")
    args = parser.parse_args()

    lo_dir = OBJECTIVES_DIR / args.slug
    if not lo_dir.is_dir():
        raise SystemExit(f"LO folder not found: {lo_dir}")

    tex_files = [str(lo_dir / f"{level}-questions.tex") for level in LEVELS if (lo_dir / f"{level}-questions.tex").exists()]
    if not tex_files:
        raise SystemExit(f"No worksheet tex files found in {lo_dir}")

    if not args.skip_pdfs:
        # Intentionally keep automatic layout normalization ON.
        # This repairs common small-model mistakes such as old enumerate layout,
        # wrong preambles, and non-projector-friendly spacing before compile.
        run(["python3", "OPERATIONS/scripts/build_pdfs.py", *tex_files])

    if not args.skip_site:
        run(["python3", "OPERATIONS/scripts/generate_web_html.py", "--slug", args.slug])

    run(["python3", "OPERATIONS/scripts/validate_lo.py", args.slug])

    print(f"Built single LO safely: {args.slug}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

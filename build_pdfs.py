#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_GLOB = "lo-yr9-*/**/*-questions.tex"
CLEAN_SUFFIXES = [".aux", ".log", ".fls", ".fdb_latexmk", ".out", ".synctex.gz"]


def find_engine() -> list[str] | None:
    latexmk = shutil.which("latexmk")
    if latexmk:
        return [latexmk, "-pdf", "-interaction=nonstopmode", "-halt-on-error"]

    pdflatex = shutil.which("pdflatex")
    if pdflatex:
        return [pdflatex, "-interaction=nonstopmode", "-halt-on-error"]

    tectonic = shutil.which("tectonic")
    if tectonic:
        return [tectonic, "--keep-logs", "--keep-intermediates"]

    return None


def compile_tex(tex_path: Path, engine: list[str]) -> int:
    command = [*engine, tex_path.name]
    result = subprocess.run(command, cwd=tex_path.parent)
    if result.returncode != 0:
        return result.returncode

    # pdflatex usually needs a second pass for stable output; harmless for simple files.
    if Path(engine[0]).name == "pdflatex":
        result = subprocess.run(command, cwd=tex_path.parent)
        if result.returncode != 0:
            return result.returncode

    return 0


def clean_intermediates(tex_path: Path) -> None:
    stem = tex_path.with_suffix("")
    for suffix in CLEAN_SUFFIXES:
        candidate = stem.with_suffix(suffix)
        if candidate.exists():
            candidate.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build worksheet PDFs beside their TeX files.")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional TeX files to build. Defaults to all worksheet TeX files.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep LaTeX intermediate files like .aux and .log.",
    )
    args = parser.parse_args()

    engine = find_engine()
    if engine is None:
        print(
            "No TeX engine found. Install one of: latexmk, pdflatex, or tectonic.",
            file=sys.stderr,
        )
        return 2

    if args.paths:
        tex_files = [Path(path).resolve() for path in args.paths]
    else:
        tex_files = sorted(ROOT.glob(DEFAULT_GLOB))

    tex_files = [path for path in tex_files if path.is_file()]

    if not tex_files:
        print("No worksheet .tex files found.", file=sys.stderr)
        return 1

    print(f"Using engine: {Path(engine[0]).name}")
    failures: list[Path] = []

    for tex_path in tex_files:
        rel = tex_path.relative_to(ROOT)
        print(f"Building {rel} ...")
        code = compile_tex(tex_path, engine)
        if code != 0:
            failures.append(tex_path)
            print(f"Failed: {rel}", file=sys.stderr)
            continue

        pdf_path = tex_path.with_suffix(".pdf")
        if not pdf_path.exists():
            failures.append(tex_path)
            print(f"Missing PDF after build: {rel}", file=sys.stderr)
            continue

        if not args.keep_temp:
            clean_intermediates(tex_path)

    if failures:
        print("\nBuild finished with failures:", file=sys.stderr)
        for path in failures:
            print(f"- {path.relative_to(ROOT)}", file=sys.stderr)
        return 1

    print(f"\nBuilt {len(tex_files)} PDF(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

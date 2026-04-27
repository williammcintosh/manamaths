#!/usr/bin/env python3
"""Migrate old extarticle-based .tex files to the new beamer template."""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OBJECTIVES_DIR = REPO_ROOT / "OBJECTIVES"
TEMPLATE_PATH = REPO_ROOT / "OPERATIONS" / "templates" / "lo-template.tex"
TEMPLATE_TEXT = TEMPLATE_PATH.read_text()

MODULE_LABELS = {1: "Start Tasks", 2: "Build Tasks", 3: "Push Tasks"}

# Map count to filename stem
LEVEL_FILE = {("foundation", 1), ("proficient", 2), ("excellence", 3)}


def extract_tasks(text: str) -> list[str]:
    """Extract task content from old extarticle format.

    Handles both:
    \task{content}
    \task \mbox{...} (or any content until next \task or \end{tasks})
    """
    tasks = []

    # Find \begin{tasks}...\end{tasks} block first
    bt = text.find(r"\begin{tasks}")
    et = text.find(r"\end{tasks}", bt) if bt != -1 else -1
    if bt == -1 or et == -1:
        return tasks

    body = text[bt:et]
    pos = 0
    while True:
        # Find \task (possibly with { or space)
        idx = -1
        for pattern in [r"\task{", r"\task "]:
            p = body.find(pattern, pos)
            if p != -1 and (idx == -1 or p < idx):
                idx = p
        if idx == -1:
            break

        # Find where this task's content ends
        brace_start = body.find("{", idx)
        if brace_start != -1 and brace_start < idx + 10:
            # \task{content} form — parse with brace matching
            depth = 0
            end = brace_start
            for i in range(brace_start, len(body)):
                if body[i] == "{":
                    depth += 1
                elif body[i] == "}":
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            content = body[brace_start + 1 : end].strip()
            pos = end + 1
        else:
            # \task content form — content until next \task or \end
            next_task = body.find(r"\task", idx + 5)
            end_pos = next_task if next_task != -1 else len(body)
            # Also check for \end{tasks}
            end_tasks = body.find(r"\end{tasks}", idx)
            if end_tasks != -1 and end_tasks < end_pos:
                end_pos = end_tasks
            content = body[idx + 5 : end_pos].strip()
            pos = end_pos

        if content:
            tasks.append(content)

    return tasks


def build_beamer_tex(tasks: list[str], level_count: int) -> str:
    """Build new beamer .tex from extracted tasks."""
    label = MODULE_LABELS[level_count]

    # Start from template, replace the header placeholder
    tex = TEMPLATE_TEXT.replace("INSERT HEADER HERE", label)

    # Replace the \MMProblem{N}{} lines with actual questions
    # The template has \MMProblem{1}{} through \MMProblem{9}{}
    # We need to handle multiple pages (3 sets of 9 problems = 27 questions)
    # Old format may have 14/12/16 questions — we just slot them in

    # Build all pages
    pages = []
    num_tasks = len(tasks)
    for page_start in range(0, num_tasks, 9):
        page_tasks = tasks[page_start : page_start + 9]
        page = rf"""\begin{{frame}}[t]
\WorksheetTitle{{{label}}}
\vspace{{-0.18em}}
\begin{{columns}}[T,onlytextwidth]
\begin{{column}}{{0.32\textwidth}}\MMProblem{{1}}{{{_escape_problem(page_tasks[0]) if len(page_tasks) > 0 else ""}}}\end{{column}}
\begin{{column}}{{0.32\textwidth}}\MMProblem{{2}}{{{_escape_problem(page_tasks[1]) if len(page_tasks) > 1 else ""}}}\end{{column}}
\begin{{column}}{{0.32\textwidth}}\MMProblem{{3}}{{{_escape_problem(page_tasks[2]) if len(page_tasks) > 2 else ""}}}\end{{column}}
\end{{columns}}
\vspace{{0.45em}}
\begin{{columns}}[T,onlytextwidth]
\begin{{column}}{{0.32\textwidth}}\MMProblem{{4}}{{{_escape_problem(page_tasks[3]) if len(page_tasks) > 3 else ""}}}\end{{column}}
\begin{{column}}{{0.32\textwidth}}\MMProblem{{5}}{{{_escape_problem(page_tasks[4]) if len(page_tasks) > 4 else ""}}}\end{{column}}
\begin{{column}}{{0.32\textwidth}}\MMProblem{{6}}{{{_escape_problem(page_tasks[5]) if len(page_tasks) > 5 else ""}}}\end{{column}}
\end{{columns}}
\vspace{{0.45em}}
\begin{{columns}}[T,onlytextwidth]
\begin{{column}}{{0.32\textwidth}}\MMProblem{{7}}{{{_escape_problem(page_tasks[6]) if len(page_tasks) > 6 else ""}}}\end{{column}}
\begin{{column}}{{0.32\textwidth}}\MMProblem{{8}}{{{_escape_problem(page_tasks[7]) if len(page_tasks) > 7 else ""}}}\end{{column}}
\begin{{column}}{{0.32\textwidth}}\MMProblem{{9}}{{{_escape_problem(page_tasks[8]) if len(page_tasks) > 8 else ""}}}\end{{column}}
\end{{columns}}
\end{{frame}}"""
        pages.append(page)

    # Replace everything after \begin{document}
    doc_end = tex.find(r"\begin{document}")
    if doc_end == -1:
        raise ValueError("Template missing \\begin{document}")

    preamble = tex[:doc_end]
    return preamble + r"\begin{document}" + "\n".join(pages) + "\n\end{document}\n"


def _escape_problem(content: str) -> str:
    """Escape special chars for LaTeX context inside MMProblem."""
    return content.strip()


def main() -> int:
    migrated = 0
    skipped = 0

    for lo_dir in sorted(OBJECTIVES_DIR.iterdir()):
        if not lo_dir.is_dir() or not lo_dir.name.startswith("lo-yr9-"):
            continue

        for fname, count in [("foundation-questions.tex", 1),
                              ("proficient-questions.tex", 2),
                              ("excellence-questions.tex", 3)]:
            path = lo_dir / fname
            if not path.exists():
                continue

            text = path.read_text()

            # Skip if already beamer
            if r"\documentclass[" in text and "beamer" in text:
                skipped += 1
                continue

            tasks = extract_tasks(text)
            if not tasks:
                print(f"  No tasks found in {path.relative_to(REPO_ROOT)} — skipping")
                skipped += 1
                continue

            new_text = build_beamer_tex(tasks, count)
            path.write_text(new_text)
            migrated += 1
            print(f"  Migrated {path.relative_to(REPO_ROOT)} ({len(tasks)} tasks)")

    print(f"\nMigrated: {migrated}, Skipped (already beamer): {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

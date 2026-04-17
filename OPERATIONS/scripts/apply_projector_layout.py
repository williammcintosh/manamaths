#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OPERATIONS_DIR = SCRIPT_DIR.parent
REPO_ROOT = OPERATIONS_DIR.parent
OBJECTIVES_DIR = REPO_ROOT / "OBJECTIVES"
TARGET_GLOB = 'lo-yr9-*/**/*-questions.tex'

WORDY_MARKERS = {
    'write', 'explain', 'which', 'complete', 'student', 'diagram', 'fraction',
    'equivalent', 'because', 'correct', 'real-life', 'represented', 'simpler',
    'remaining', 'present', 'empty', 'total', 'belong', 'blank', 'identify',
    'find', 'show', 'state', 'whether'
}

TARGET_PREAMBLE = """\\documentclass[17pt,a4paper,landscape]{extarticle}
\\usepackage[margin=2.35cm,top=0.12cm,left=1.05cm]{geometry}
\\usepackage{amsmath}
\\usepackage{amssymb}
\\usepackage{tasks}
\\usepackage{tikz}
\\usepackage{xcolor}
\\usepackage[sfdefault,lf]{FiraSans}
\\renewcommand{\\familydefault}{\\sfdefault}
\\setlength{\\parindent}{0pt}
\\pagestyle{empty}
\\settasks{label=\\textbf{\\arabic*.}, label-width=2.2em, item-indent=2.95em, column-sep=2.1cm, after-item-skip=3.6em}
\\renewcommand{\\arraystretch}{1.15}
\\everymath{\\displaystyle}
"""


def strip_latex(text: str) -> str:
    text = re.sub(r'%.*', '', text)
    text = re.sub(r'\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}', ' diagram ', text, flags=re.S)
    text = re.sub(r'\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^{}]*\})?', ' ', text)
    text = re.sub(r'\$[^$]*\$', ' math ', text)
    text = re.sub(r'[^A-Za-z0-9? ]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip().lower()


def extract_items(tex: str) -> list[str]:
    parts = re.split(r'\\(?:item|task)\s*', tex)
    return [part.strip() for part in parts[1:] if part.strip()]


def classify_layout(tex: str) -> tuple[int, str, str]:
    items = extract_items(tex)
    if not items:
        return 3, '7.8em', 'fallback-no-items'

    score = 0
    for item in items:
        plain = strip_latex(item)
        words = plain.split()
        word_count = len(words)
        marker_hits = sum(1 for word in words if word in WORDY_MARKERS)
        has_question = '?' in item
        has_blank = '\\rule' in item or '\\square' in item
        has_diagram = '\\begin{tikzpicture}' in item

        if word_count >= 8:
            score += 2
        elif word_count >= 5:
            score += 1

        if marker_hits:
            score += marker_hits
        if has_question:
            score += 1
        if has_blank:
            score += 1
        if has_diagram:
            score += 2

    word_counts = [len(strip_latex(item).split()) for item in items]
    average_score = score / len(items)
    average_words = sum(word_counts) / len(items)
    max_words = max(word_counts) if word_counts else 0
    long_item_count = sum(1 for count in word_counts if count >= 6)

    if average_score >= 2.2 or average_words >= 5.2 or max_words >= 6 or long_item_count >= max(4, len(items) // 4):
        return 3, '4.7em', f'wordy avg_score={average_score:.2f} avg_words={average_words:.2f} max_words={max_words} long_items={long_item_count}'
    return 4, '9.8em', f'numeric avg_score={average_score:.2f} avg_words={average_words:.2f} max_words={max_words} long_items={long_item_count}'


def normalize_preamble(tex: str) -> str:
    if '\\begin{document}' not in tex:
        return tex
    preamble, rest = tex.split('\\begin{document}', 1)
    rest = rest.lstrip()
    rest = re.sub(r'^(\\sffamily\s*)+', '', rest)
    return TARGET_PREAMBLE + '\n\\begin{document}\n\\sffamily\n\\boldmath\n\n' + rest


def unbox_task_lines(tex: str) -> str:
    return re.sub(r'(?m)^\\task\s+\\mbox\{(.*)\}$', r'\\task \1', tex)


def normalize_inline_math_boxes(text: str) -> str:
    text = text.replace('\\\\mbox{', '\\mbox{')
    while True:
        updated = re.sub(r'\\mbox\{\$([^$]+)\$\}', r'$\1$', text)
        if updated == text:
            return text
        text = updated


def protect_inline_math(tex: str) -> str:
    def protect_task_line(match: re.Match[str]) -> str:
        content = match.group(1)
        if '\\begin{' in content or '\\parbox{' in content:
            return match.group(0)

        content = normalize_inline_math_boxes(content)
        protected = re.sub(
            r'\$([^$]+)\$',
            lambda m: '\\mbox{$' + m.group(1) + '$}',
            content,
        )
        return f'\\task {protected}'

    tex = unbox_task_lines(tex)
    return re.sub(r'(?m)^\\task\s+([^\n]+)$', protect_task_line, tex)


def apply_to_file(path: Path) -> tuple[int, str]:
    original = path.read_text(encoding='utf-8')
    if '\\includegraphics' in original and '\\begin{minipage}' in original and '\\begin{tasks}' not in original:
        return 3, 'preserve-custom-visual-layout'
    updated = normalize_preamble(original)
    updated = re.sub(r'\{\\LARGE \\textbf\{[^}]*\}\}\\\\\[0\.35em\]\s*\n\{\\large \\textbf\{[^}]*\}\}\s*\n\s*\\vspace\{[^}]+\}\s*\n', '', updated, count=1)

    columns, itemsep, reason = classify_layout(updated)
    updated = re.sub(r'\\begin\{multicols\}\{\d+\}\s*\\begin\{enumerate\}\[.*?\]\s*', rf'\\begin{{tasks}}({columns})\n', updated, flags=re.S)
    updated = re.sub(r'\\end\{enumerate\}\s*\\end\{multicols\}', r'\\end{tasks}', updated, flags=re.S)
    updated = re.sub(r'(?m)^\\item\b', r'\\task', updated)
    updated = re.sub(r'\\begin\{tasks\}\((\d+)\)', rf'\\begin{{tasks}}({columns})', updated)
    updated = re.sub(r'after-item-skip=([0-9.]+)em', f'after-item-skip={itemsep[:-2]}em', updated)
    updated = re.sub(r'\{\\Huge \\textbf\{([^}]*)\}\}', r'{\\LARGE \\textbf{\1}}', updated)
    updated = re.sub(r'(?m)^\\LARGE (.*)$', r'\1', updated, count=1)
    updated = protect_inline_math(updated)

    if updated != original:
        path.write_text(updated, encoding='utf-8')

    return columns, reason


def main() -> int:
    parser = argparse.ArgumentParser(description='Apply projector-friendly worksheet layout rules.')
    parser.add_argument('paths', nargs='*', help='Optional worksheet .tex paths relative to repo root.')
    args = parser.parse_args()

    if args.paths:
        tex_files = [Path(path).resolve() for path in args.paths]
    else:
        tex_files = sorted(path for path in OBJECTIVES_DIR.glob(TARGET_GLOB) if path.is_file())

    tex_files = [path for path in tex_files if path.is_file()]
    if not tex_files:
        print('No worksheet .tex files found.')
        return 1

    for path in tex_files:
        columns, reason = apply_to_file(path)
        print(f'{path.relative_to(REPO_ROOT)} -> {columns} columns ({reason})')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())

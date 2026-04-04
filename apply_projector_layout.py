#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET_GLOB = 'lo-yr9-*/**/*-questions.tex'

WORDY_MARKERS = {
    'write', 'explain', 'which', 'complete', 'student', 'diagram', 'fraction',
    'equivalent', 'because', 'correct', 'real-life', 'represented', 'simpler',
    'remaining', 'present', 'empty', 'total', 'belong', 'blank', 'identify',
    'find', 'show', 'state', 'whether'
}

TARGET_PREAMBLE = """\\documentclass[17pt,a4paper,landscape]{extarticle}
\\usepackage[margin=1.2cm]{geometry}
\\usepackage{amsmath}
\\usepackage{amssymb}
\\usepackage{multicol}
\\usepackage{enumitem}
\\usepackage{tikz}
\\usepackage{xcolor}
\\usepackage[sfdefault,lf]{FiraSans}
\\renewcommand{\\familydefault}{\\sfdefault}
\\setlength{\\parindent}{0pt}
\\pagestyle{empty}
\\setlength{\\columnsep}{1.4cm}
\\setlength{\\columnseprule}{0pt}
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
    parts = re.split(r'\\item\s*', tex)
    return [part.strip() for part in parts[1:] if part.strip()]


def classify_layout(tex: str) -> tuple[int, str, str]:
    items = extract_items(tex)
    if not items:
        return 3, '6.4em', 'fallback-no-items'

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

    average_score = score / len(items)
    average_words = sum(len(strip_latex(item).split()) for item in items) / len(items)

    if average_score >= 2.2 or average_words >= 5.2:
        return 3, '7.4em', f'wordy avg_score={average_score:.2f} avg_words={average_words:.2f}'
    return 3, '6.6em', f'numeric avg_score={average_score:.2f} avg_words={average_words:.2f}'


def normalize_preamble(tex: str) -> str:
    if '\\begin{document}' not in tex:
        return tex
    preamble, rest = tex.split('\\begin{document}', 1)
    rest = rest.lstrip()
    rest = re.sub(r'^(\\sffamily\s*)+', '', rest)
    return TARGET_PREAMBLE + '\n\\begin{document}\n\\sffamily\n\\boldmath\n\n' + rest


def apply_to_file(path: Path) -> tuple[int, str]:
    original = path.read_text(encoding='utf-8')
    updated = normalize_preamble(original)
    updated = re.sub(r'\\vspace\{[^}]+\}', r'\\vspace{2.6em}', updated, count=1)

    columns, itemsep, reason = classify_layout(updated)
    updated = re.sub(r'\\begin\{multicols\}\{\d+\}', rf'\\begin{{multicols}}{{{columns}}}', updated)
    updated = re.sub(r'itemsep=([0-9.]+)em,', f'itemsep={itemsep},', updated)
    updated = re.sub(r'label=\\arabic\*\.,', r'label=\\textbf{\\arabic*.},', updated)
    updated = re.sub(r'labelwidth=([0-9.]+)em,', 'labelwidth=2.2em,', updated)
    updated = re.sub(r'labelsep=([0-9.]+)em,', 'labelsep=0.75em,', updated)
    updated = re.sub(r'\{\\Huge \\textbf\{([^}]*)\}\}\\\\\[0\.45em\]', r'{\\LARGE \\textbf{\1}}\\\\[0.35em]', updated)
    updated = re.sub(r'\{\\Huge \\textbf\{([^}]*)\}\}', r'{\\LARGE \\textbf{\1}}', updated)
    updated = re.sub(r'(?m)^\\LARGE (.*)$', r'\1', updated, count=1)

    if updated != original:
        path.write_text(updated, encoding='utf-8')

    return columns, reason


def main() -> int:
    parser = argparse.ArgumentParser(description='Apply projector-friendly worksheet layout rules.')
    parser.add_argument('paths', nargs='*', help='Optional worksheet .tex paths relative to repo root.')
    args = parser.parse_args()

    if args.paths:
        tex_files = [ROOT / path for path in args.paths]
    else:
        tex_files = sorted(path for path in ROOT.glob(TARGET_GLOB) if path.is_file())

    tex_files = [path for path in tex_files if path.is_file()]
    if not tex_files:
        print('No worksheet .tex files found.')
        return 1

    for path in tex_files:
        columns, reason = apply_to_file(path)
        print(f'{path.relative_to(ROOT)} -> {columns} columns ({reason})')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())

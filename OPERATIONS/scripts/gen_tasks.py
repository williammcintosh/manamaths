#!/usr/bin/env python3
"""
Generate a full Mana Maths beamer worksheet for one LO.
Usage: python3 gen_tasks.py <slug> <title> <foundation_qs.json> <proficient_qs.json> <excellence_qs.json>

Each JSON file should be a list of 27 question strings.
"""

import json, sys, re
from pathlib import Path

ROOT = Path('/home/debid/.openclaw/workspace/manamaths')

PREAMBLE = r'''\documentclass[aspectratio=169,12pt]{beamer}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage[most]{tcolorbox}
\usepackage{tikz}
\usepackage{graphicx}
\usepackage[sfdefault,lf]{FiraSans}
\renewcommand{\familydefault}{\sfdefault}
\setlength{\parindent}{0pt}
\everymath{\displaystyle}

\setbeamertemplate{navigation symbols}{}
\setbeamertemplate{footline}{}
\setbeamertemplate{headline}{}

\definecolor{mmpageWhite}{HTML}{FCFBF7}
\definecolor{mmtanSoft}{HTML}{F7F5EF}
\definecolor{mmgreenDeep}{HTML}{244B2C}
\definecolor{mmgreenLeaf}{HTML}{5D8A56}
\definecolor{mmgreenSoft}{HTML}{E4EFD9}
\definecolor{mmtext}{HTML}{163221}

\setbeamercolor{background canvas}{bg=mmpageWhite}
\setbeamercolor{normal text}{fg=mmtext,bg=mmpageWhite}

\newtcolorbox{MMProblemCard}[1][]{enhanced,breakable=false,colback=white,colframe=black,boxrule=1.0pt,arc=5pt,left=3pt,right=3pt,top=2pt,bottom=2pt,before skip=0pt,after skip=0pt,height=0.26\textheight,valign=top,#1}
\newcommand{\KoruIcon}{\raisebox{-0.2em}{\includegraphics[height=1.05em]{../../SITE/header-logo.png}}}
\newcommand{\HoeIcon}{\raisebox{-0.2em}{\includegraphics[height=1.05em]{../../SITE/hoe.png}}}
\newcommand{\ScaffoldIcons}[1]{\ifcase#1\or \HoeIcon\or \HoeIcon\hspace{0.22em}\HoeIcon\or \HoeIcon\hspace{0.22em}\HoeIcon\hspace{0.22em}\HoeIcon\fi}
\newcommand{\WorksheetTitle}[2]{%
  {\colorbox{mmtanSoft}{\parbox[c][2.0em][c]{0.975\linewidth}{%
    \hspace{0.25em}{\Large\bfseries\textcolor{mmgreenDeep}{#1}\hfill\ScaffoldIcons{#2}}}}
  \par\vspace{0.08em}{\color{mmgreenLeaf}\rule{\linewidth}{2.0pt}}\par\vspace{0.04em}}
}
\newcommand{\MMProblem}[2]{\begin{MMProblemCard}\raggedright\small\textbf{#1.} #2\par\end{MMProblemCard}}

\setbeamertemplate{background}{
 \begin{tikzpicture}[remember picture,overlay]
 \draw[black,line width=1.5pt,rounded corners=10pt]
 ([xshift=0.45cm,yshift=-0.45cm]current page.north west)
 rectangle
 ([xshift=-0.45cm,yshift=0.45cm]current page.south east);
 \end{tikzpicture}
}

'''

def make_frame(title, icon, start_num, qs):
    lines = [f'\\begin{{frame}}[t]', f'\\WorksheetTitle{{{title}}}{{{icon}}}', '\\vspace{-0.18em}']
    n = start_num
    for r in range(3):
        lines.append('\\begin{columns}[T,onlytextwidth]')
        for c in range(3):
            q = qs[r*3+c]
            lines.append(f'\\begin{{column}}{{0.32\\textwidth}}\\MMProblem{{{n}}}{{{q}}}\\end{{column}}')
            n += 1
        lines.append('\\end{columns}')
        if r < 2:
            lines.append('\\vspace{0.45em}')
    lines.append('\\end{frame}')
    return '\n'.join(lines)

def gen_document(title, icon, questions):
    assert len(questions) == 27
    return PREAMBLE + '\\begin{document}\n' + '\n\n'.join([
        make_frame(title, icon, 1, questions[:9]),
        make_frame(title, icon, 10, questions[9:18]),
        make_frame(title, icon, 19, questions[18:]),
    ]) + '\n\\end{document}\n'

if __name__ == '__main__':
    slug = sys.argv[1]
    display_title = sys.argv[2]
    qs_f = json.load(open(sys.argv[3]))
    qs_p = json.load(open(sys.argv[4]))
    qs_e = json.load(open(sys.argv[5]))

    folder = ROOT / 'OBJECTIVES' / slug
    folder.mkdir(parents=True, exist_ok=True)

    for level, questions, icon, title in [
        ('foundation', qs_f, 1, 'Start Tasks'),
        ('proficient', qs_p, 2, 'Build Tasks'),
        ('excellence', qs_e, 3, 'Push Tasks'),
    ]:
        tex = folder / f'{level}-questions.tex'
        tex.write_text(gen_document(title, icon, questions))

    # Build
    import subprocess
    for level in ['foundation', 'proficient', 'excellence']:
        r = subprocess.run([
            '/home/debid/bin/tectonic',
            '--outdir', str(folder),
            str(folder / f'{level}-questions.tex')
        ], capture_output=True, text=True)
        if r.returncode != 0:
            print(f'FAIL {slug}/{level}: {r.stderr[-200:]}')
            sys.exit(1)

    print(f'DONE {slug}')

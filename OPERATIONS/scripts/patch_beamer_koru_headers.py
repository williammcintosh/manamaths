#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OBJECTIVES_DIR = REPO_ROOT / "OBJECTIVES"
TEMPLATE_PATH = REPO_ROOT / "OPERATIONS" / "templates" / "lo-template.tex"

TITLE_RE = re.compile(r"\\WorksheetTitle\{([^{}]+?)\\hfill\s*(Foundation|Proficient|Excellence)\}")

FILES = [
    *OBJECTIVES_DIR.glob("**/foundation-questions.tex"),
    *OBJECTIVES_DIR.glob("**/proficient-questions.tex"),
    *OBJECTIVES_DIR.glob("**/excellence-questions.tex"),
]

MACRO_OLD = r'''\usepackage{tikz}
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

\newtcolorbox{MMProblemCard}[1][]{enhanced,breakable=false,colback=white,colframe=black,boxrule=1.5pt,arc=8pt,left=5pt,right=5pt,top=4pt,bottom=4pt,before skip=0pt,after skip=0pt,height=0.245\textheight,valign=top,#1}
\newcommand{\WorksheetTitle}[1]{{\colorbox{mmtanSoft}{\parbox{0.975\linewidth}{\vspace{0.10em}\hspace{0.25em}{\LARGE\bfseries\textcolor{mmgreenDeep}{#1}}\vspace{0.10em}}}\par\vspace{0.10em}{\color{mmgreenLeaf}\rule{\linewidth}{2.0pt}}\par\vspace{0.04em}}}
\newcommand{\MMProblem}[2]{\begin{MMProblemCard}\raggedright\small\textbf{#1.} #2\par\end{MMProblemCard}}
'''

MACRO_NEW = r'''\usepackage{tikz}
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

\newtcolorbox{MMProblemCard}[1][]{enhanced,breakable=false,colback=white,colframe=black,boxrule=1.5pt,arc=8pt,left=5pt,right=5pt,top=4pt,bottom=4pt,before skip=0pt,after skip=0pt,height=0.245\textheight,valign=top,#1}
\newcommand{\KoruIcon}{\raisebox{-0.2em}{\includegraphics[height=1.05em]{../../SITE/header-logo.png}}}
\newcommand{\ScaffoldIcons}[1]{\ifcase#1\or \KoruIcon\or \KoruIcon\hspace{0.22em}\KoruIcon\or \KoruIcon\hspace{0.22em}\KoruIcon\hspace{0.22em}\KoruIcon\fi}
\newcommand{\WorksheetTitle}[2]{%
  {\colorbox{mmtanSoft}{\parbox[c][2.0em][c]{0.975\linewidth}{%
    \hspace{0.25em}{\Large\bfseries\textcolor{mmgreenDeep}{#1}\hfill\ScaffoldIcons{#2}}}}
  \par\vspace{0.08em}{\color{mmgreenLeaf}\rule{\linewidth}{2.0pt}}\par\vspace{0.04em}}
}
\newcommand{\MMProblem}[2]{\begin{MMProblemCard}\raggedright\small\textbf{#1.} #2\par\end{MMProblemCard}}
'''


def convert_title(match: re.Match[str]) -> str:
    title = match.group(1).strip()
    level = match.group(2).lower()
    count = {"foundation": 1, "proficient": 2, "excellence": 3}[level]
    return f"\\WorksheetTitle{{{title}}}{{{count}}}"


def patch_text(text: str) -> str:
    if "\\newcommand{\\KoruIcon}" not in text:
        text = text.replace(MACRO_OLD, MACRO_NEW)
    text = TITLE_RE.sub(convert_title, text)
    return text


def main() -> int:
    patched = 0
    for path in FILES:
        text = path.read_text()
        new_text = patch_text(text)
        if new_text != text:
            path.write_text(new_text)
            patched += 1

    template_text = TEMPLATE_PATH.read_text()
    new_template_text = patch_text(template_text)
    if new_template_text != template_text:
        TEMPLATE_PATH.write_text(new_template_text)
        patched += 1

    print(f"Patched {patched} beamer template file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

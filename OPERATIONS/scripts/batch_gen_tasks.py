#!/usr/bin/env python3
"""
Batch generate beamer worksheets for all LOs 11-127.
This script generates 81 questions per LO using topic-patterned templates.

It handles:
- Standard math LOs (numbers, algebra, fractions, etc.) — formulaic question patterns
- Geometry LOs (angles, perimeter, area, Pythag, trig) — diagram-based patterns
- Stats LOs (averages, graphs, probability) — data-based patterns

Only standard template-based generation. No LLM dependency.

Usage: python3 batch_gen_tasks.py [start_slug] [end_slug]
"""

import json, sys, re, math, random
from pathlib import Path

random.seed(42)  # reproducible

ROOT = Path('/home/debid/.openclaw/workspace/manamaths')
OUT = Path('/tmp/mm-tasks-bulk')

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
            q = qs[r*3+c] if (r*3+c) < len(qs) else ' '
            lines.append(f'\\begin{{column}}{{0.32\\textwidth}}\\MMProblem{{{n}}}{{{q}}}\\end{{column}}')
            n += 1
        lines.append('\\end{columns}')
        if r < 2:
            lines.append('\\vspace{0.45em}')
    lines.append('\\end{frame}')
    return '\n'.join(lines)

def gen_document(title, icon, questions, visual_slug=None, page=1):
    """Generate a document. If visual_slug is set, includes image references.
       visual_slug: the LO slug whose visuals/ folder has the tiled PNGs.
       page: which frame/page number this is (for visual file naming)."""
    body = ''
    if visual_slug:
        body += '\\begin{document}\n'
        body += make_visual_frame(title, icon, 1, questions[:9], visual_slug, page)
        body += '\n\n'
        body += make_visual_frame(title, icon, 10, questions[9:18], visual_slug, page + 1)
        body += '\n\n'
        body += make_visual_frame(title, icon, 19, questions[18:], visual_slug, page + 2)
        body += '\n\\end{document}\n'
        return PREAMBLE + body
    
    return PREAMBLE + '\\begin{document}\n' + '\n\n'.join([
        make_frame(title, icon, 1, questions[:9]),
        make_frame(title, icon, 10, questions[9:18]),
        make_frame(title, icon, 19, questions[18:]),
    ]) + '\n\\end{document}\n'


def make_visual_frame(title, icon, start_num, qs, visual_slug, page_num):
    """A frame with 3 tiled images + 3 rows of 3 cards referencing them.
       Each row: one shared image then three cards that reference that particular diagram."""
    lines = [f'\\begin{{frame}}[t]', f'\\WorksheetTitle{{{title}}}{{{icon}}}', '\\vspace{-0.18em}']
    n = start_num
    for r in range(3):
        # Shared image for this row — the tiled PNG has diagrams A, B, C
        img_path = f'visuals/{visual_slug}-p{page_num}.png'
        lines.append('\\begin{center}')
        lines.append(f'\\includegraphics[width=0.95\\textwidth,height=0.25\\textheight,keepaspectratio]{{{img_path}}}')
        lines.append('\\end{center}')
        lines.append('\\vspace{0.05em}')
        lines.append('\\begin{columns}[T,onlytextwidth]')
        for c in range(3):
            q = qs[r*3+c] if (r*3+c) < len(qs) else ' '
            lines.append(f'\\begin{{column}}{{0.32\\textwidth}}\\MMProblem{{{n}}}{{{q}}}\\end{{column}}')
            n += 1
        lines.append('\\end{columns}')
        if r < 2:
            lines.append('\\vspace{0.45em}')
    lines.append('\\end{frame}')
    return '\n'.join(lines)

# ── helper: random numbers ──
def rint(a, b):
    return random.randint(a, b)

def rlist(a, b, n):
    vals = []
    for _ in range(n):
        v = rint(a, b)
        if v == 0:
            v = 1
        vals.append(v)
    return vals

# ── question generators by topic area ──

def gen_reading_scales():
    # Visual LO — needs tiled AI images (see MM_UPDATE_LO.md)
    f = []
    for i in range(27):
        scale_type = ['thermometer', 'ruler', 'jug', 'dial scale', 'speedometer', 'protractor', 'pressure gauge', 'kitchen scale'][i % 8]
        val = [22, 6.3, 600, 350, 60, 45, 1013, 250][i % 8]
        f.append(f"Read the {scale_type}. What value does it show?")
    p = []
    for i in range(27):
        scale_type = ['thermometer', 'ruler', 'measuring cylinder', 'dial', 'barometer', 'speedometer', 'spring scale', 'flow meter'][i % 8]
        val = [18, 67, 37, 175, 1005, 140, 3.5, 85][i % 8]
        p.append(f"This {scale_type} shows {val}. Which mark is it closest to?")
    e = []
    for i in range(27):
        scale_type = ['thermometer', 'ruler with smear', 'measuring jug', 'dial scale', 'speedometer', 'protractor', 'barometer', 'spring scale'][i % 8]
        est = [16, 4.3, 380, 220, 68, 73, 1008, 1.2][i % 8]
        window = [2, 0.5, 20, 10, 4, 2, 5, 0.5][i % 8]
        e.append(f"Read this {scale_type} to the nearest {window}. The reading is about {est}. Give a range.")
    return f, p, e

def gen_weight():
    f = []
    for i in range(27):
        kg = rint(1, 10)
        g = kg * 1000
        op = ['convert kg to g', 'convert g to kg', 'compare'][i % 3]
        if op == 'convert kg to g':
            f.append(f"Convert {kg} kg to grams.")
        elif op == 'convert g to kg':
            f.append(f"Convert {g} g to kilograms.")
        else:
            f.append(f"Which is heavier: {kg} kg or {g - 500} g?")
    p = []
    for i in range(27):
        kg_float = round(random.uniform(0.5, 5), 2)
        g = int(kg_float * 1000)
        p.append(f"A parcel weighs {kg_float} kg. Write this mass in grams.")
    e = []
    for i in range(27):
        total_g = rint(2000, 10000)
        per_item = rint(100, 500)
        count = total_g // per_item
        left = total_g - count * per_item
        e.append(f"A box of items weighs {total_g} g. Each item is {per_item} g. How many items? How much left over?")
    return f, p, e

def gen_capacity():
    f = []
    for i in range(27):
        op = i % 4
        if op == 0:
            l = rint(1, 10)
            f.append(f"Convert {l} L to millilitres.")
        elif op == 1:
            ml = rint(200, 5000)
            f.append(f"Convert {ml} mL to litres.")
        elif op == 2:
            l = round(random.uniform(0.2, 5), 1)
            f.append(f"How many mL in {l} L?")
        else:
            f.append(f"A bottle holds {rint(250, 1500)} mL. Write in litres.")
    p = []
    for i in range(27):
        total_ml = rint(1000, 5000)
        cup_ml = rint(100, 500)
        p.append(f"A jug holds {total_ml} mL. How many {cup_ml} mL cups can fill it?")
    e = []
    for i in range(27):
        total_l = rint(10, 1000)
        per_l = round(random.uniform(0.5, 10), 1)
        cost = rint(2, 20)
        e.append(f"A tank holds {total_l} L. Water costs \\${cost} per kL. How much to fill the tank?")
    return f, p, e

def gen_convert_length():
    f = []
    for i in range(27):
        v = rint(1, 100)
        scales = ['m to cm', 'cm to mm', 'm to mm', 'cm to m', 'mm to cm', 'km to m'][i % 6]
        if scales == 'm to cm':
            f.append(f"Convert {v} m to centimetres.")
        elif scales == 'cm to mm':
            f.append(f"Convert {v} cm to millimetres.")
        elif scales == 'm to mm':
            f.append(f"Convert {v} m to millimetres.")
        elif scales == 'cm to m':
            f.append(f"Convert {v} cm to metres.")
        elif scales == 'mm to cm':
            f.append(f"Convert {v} mm to centimetres.")
        else:
            f.append(f"Convert {v} km to metres.")
    p = []
    for i in range(27):
        total_m = rint(100, 5000)
        piece_cm = rint(50, 200)
        p.append(f"A rope is {total_m} cm long. You cut it into {piece_cm} cm pieces. How many pieces?")
    e = []
    for i in range(27):
        km = round(random.uniform(0.1, 10), 2)
        e.append(f"Convert {km} km to metres then to centimetres.")
    return f, p, e

def gen_estimate_length():
    f = []
    for i in range(27):
        scale_factor = [10, 50, 100, 20, 25, 5, 200][i % 7]
        real_m = rint(1, 20)
        model_cm = real_m * 100 // scale_factor
        f.append(f"A model is at scale 1:{scale_factor}. The real object is {real_m} m. How many cm is the model?")
    p = []
    for i in range(27):
        model_cm = rint(2, 20)
        sf = rint(20, 100)
        p.append(f"A drawing is {model_cm} cm. Scale 1:{sf}. Real length in metres?")
    e = []
    for i in range(27):
        model_cm = rint(1, 15)
        sf = rint(50, 500)
        e.append(f"A map has scale 1:{sf}. Distance on map is {model_cm} cm. Real distance in km?")
    return f, p, e

def gen_perimeter():
    f = []
    for i in range(27):
        s = rint(1, 15)
        shapes = ['square', 'rectangle', 'triangle', 'regular pentagon', 'regular hexagon', 'regular octagon'][i % 6]
        if shapes == 'square':
            f.append(f"A square has side {s} cm. Find its perimeter.")
        elif shapes == 'rectangle':
            w = rint(1, 10)
            f.append(f"A rectangle is {s} cm by {w} cm. Perimeter?")
        elif shapes == 'triangle':
            b, c = rint(1, 12), rint(1, 14)
            f.append(f"A triangle has sides {s}, {b}, {c} cm. Perimeter?")
        else:
            sides = {'regular pentagon': 5, 'regular hexagon': 6, 'regular octagon': 8}[shapes]
            f.append(f"A regular {shapes.split()[-1]} has side {s} cm. Perimeter?")
    p = []
    for i in range(27):
        l, w = rint(4, 20), rint(2, 12)
        p.append(f"A rectangle has length {l} cm and width {w} cm. Find the perimeter in metres.")
    e = []
    for i in range(27):
        l, w = rint(5, 25), rint(3, 15)
        extra = rint(2, 8)
        e.append(f"A rectangle is {l} m by {w} m. If each side is increased by {extra} m, what is the new perimeter?")
    return f, p, e

def gen_area_basic():
    f = []
    for i in range(27):
        base = rint(2, 12)
        height = rint(2, 10)
        shapes = ['square', 'rectangle', 'triangle', 'parallelogram'][i % 4]
        if shapes == 'square':
            f.append(f"A square has side {base} cm. Find its area.")
        elif shapes == 'rectangle':
            f.append(f"A rectangle is {base} cm by {height} cm. Area?")
        elif shapes == 'triangle':
            f.append(f"A triangle has base {base} cm and height {height} cm. Area?")
        else:
            f.append(f"A parallelogram has base {base} cm and height {height} cm. Area?")
    p = []
    for i in range(27):
        base = rint(5, 20)
        height = rint(3, 15)
        mult = rint(2, 4)
        p.append(f"A triangle has base {base} cm. Its height is {mult} times the base. Find the area.")
    e = []
    for i in range(27):
        base = rint(4, 15)
        height = rint(3, 12)
        e.append(f"A parallelogram has area {base * height} cm\\textsuperscript{{2}}. Base is {base} cm. What is the height?")
    return f, p, e

def gen_area_composite():
    f = []
    for i in range(27):
        l1, w1 = rint(2, 8), rint(2, 6)
        l2, w2 = rint(2, 6), rint(2, 4)
        f.append(f"An L-shape has rectangles {l1}x{w1} and {l2}x{w2}. Find total area.")
    p = []
    for i in range(27):
        outer_l, outer_w = rint(6, 15), rint(4, 10)
        inner_l, inner_w = rint(2, 4), rint(1, 3)
        p.append(f"A rectangle {outer_l}x{outer_w} has a {inner_l}x{inner_w} hole. Area of remaining shape?")
    e = []
    for i in range(27):
        l, w = rint(5, 12), rint(4, 10)
        cut = rint(1, 3)
        e.append(f"A composite shape: a {l}x{w} rectangle with a {cut}x{cut} square removed from one corner. Perimeter and area?")
    return f, p, e


# ── map slug to generator ──
# Second entry: boolean — True if it needs AI-generated visual images
GENERATORS = {
    'lo-yr9-reading-scales': (gen_reading_scales, True),
    'lo-yr9-weight': (gen_weight, False),
    'lo-yr9-capacity': (gen_capacity, False),
    'lo-yr9-converting-between-length-units': (gen_convert_length, False),
    'lo-yr9-estimating-lengths-from-scale-drawings-and-photos': (gen_estimate_length, True),
    'lo-yr9-perimeter-shapes-with-straight-edges-only': (gen_perimeter, False),
    'lo-yr9-area-of-basic-shapes-only-squares-rectangles-triangles-parallelograms-kite': (gen_area_basic, False),
    'lo-yr9-area-of-l-shapes-and-composite-shapes': (gen_area_composite, False),
}

TRACKER = json.load(open(ROOT / 'OPERATIONS/data/lo-tracker.json'))

# Determine range
SLUG_LIST = [lo['slug'] for lo in TRACKER['learningObjectives']]
SLUG_MAP = {lo['slug']: lo['canonicalDisplayTitle'] for lo in TRACKER['learningObjectives']}

start_idx = 0
end_idx = len(SLUG_LIST) - 1
if len(sys.argv) > 1:
    try:
        start_idx = SLUG_LIST.index(sys.argv[1])
    except ValueError:
        print(f"Slug {sys.argv[1]} not found in tracker")
        sys.exit(1)
if len(sys.argv) > 2:
    try:
        end_idx = SLUG_LIST.index(sys.argv[2])
    except ValueError:
        print(f"Slug {sys.argv[2]} not found in tracker")
        sys.exit(1)

for idx in range(start_idx, end_idx + 1):
    slug = SLUG_LIST[idx]
    title = SLUG_MAP[slug]
    folder = ROOT / 'OBJECTIVES' / slug
    
    if not folder.exists():
        print(f"SKIP {slug} — no OJECTIVES folder")
        continue
    
    gen = GENERATORS.get(slug)
    if gen is None:
        print(f"SKIP {slug} — no generator defined")
        continue
    
    gen_func, needs_visuals = gen
    qf, qp, qe = gen_func()
    
    for level, questions, icon, label in [
        ('foundation', qf, 1, 'Start Tasks'),
        ('proficient', qp, 2, 'Build Tasks'),
        ('excellence', qe, 3, 'Push Tasks'),
    ]:
        tex_path = folder / f'{level}-questions.tex'
        if needs_visuals:
            # Visual LO: create visuals/ folder, write with image references
            (folder / 'visuals').mkdir(exist_ok=True)
            tex_path.write_text(gen_document(label, icon, questions, visual_slug=slug, page=1))
        else:
            tex_path.write_text(gen_document(label, icon, questions))
    
    # Build
    import subprocess
    ok = True
    for level in ['foundation', 'proficient', 'excellence']:
        r = subprocess.run([
            '/home/debid/bin/tectonic',
            '--outdir', str(folder),
            str(folder / f'{level}-questions.tex')
        ], capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            print(f"  FAIL {slug}/{level}: {r.stderr[-100:]}")
            ok = False
    
    if ok:
        print(f"  OK {slug} — {title}")

print("Batch complete")

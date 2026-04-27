#!/usr/bin/env python3
"""Replace all WorksheetTitle headers with just the module name."""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OBJECTIVES_DIR = REPO_ROOT / "OBJECTIVES"

# Map count to module label
COUNT_LABEL = {1: "Start Tasks", 2: "Build Tasks", 3: "Push Tasks"}

# Match \WorksheetTitle{anything}{count}
TITLE_RE = re.compile(r"\\WorksheetTitle\{[^}]*\}\{(\d)\}")

FILES = list(OBJECTIVES_DIR.glob("**/foundation-questions.tex"))
FILES += list(OBJECTIVES_DIR.glob("**/proficient-questions.tex"))
FILES += list(OBJECTIVES_DIR.glob("**/excellence-questions.tex"))

patched = 0
for path in FILES:
    text = path.read_text()
    new_text = TITLE_RE.sub(lambda m: f"\\WorksheetTitle{{{COUNT_LABEL[int(m.group(1))]}}}{{{m.group(1)}}}", text)
    if new_text != text:
        path.write_text(new_text)
        patched += 1

print(f"Patched {patched} .tex file(s).")

# Mana Maths — Reference LO Guide

**Reference objective**: YR9_T1_LO1 — Place Values and Decimals
**Slug**: `lo-yr9-place-values-and-decimals`
**Status**: meets_expectation

This document is the single source of truth for "what does a complete LO look like".
Future threads create new complete LOs by copying this pattern exactly.

---

## Module 1: Te Reo Māori Terms

**Where**: `manamaths/SITE/te-reo-pdfs/<slug>.tex` → built into PDF in same dir
**Template**: `manamaths/OPERATIONS/templates/te-reo-template.tex`

**Structure**:
- Landscape beamer (16:9), white background, black rounded border
- Title: "Te reo Māori terms" with green underline + koru icon
- TermCard macro: card per term with Māori word (bold/LARGE), English translation, link to Te Aka
- Terms arranged in 2-column grid
- Font: Fira Sans

**How to create**:
```bash
# 1. Write the .tex file in SITE/te-reo-pdfs/
# 2. Build with tectonic from SITE/te-reo-pdfs/
tectonic --outdir . SITE/te-reo-pdfs/<slug>.tex
# 3. Convert PDF first page to PNG preview
convert SITE/te-reo-pdfs/<slug>.pdf[0] SITE/previews/<slug>/te-reo-p001.png
```

**Terms source**: `manamaths/OPERATIONS/data/te-reo-progress.json`

---

## Module 2: Notes

**Where**: `manamaths-notes/OBJECTIVES/<slug>/main.tex` → builds to PDF in `<slug>/build/main.pdf`
**Template**: `manamaths-notes/TEMPLATES/notes-template.tex`
**Tracker**: `manamaths-notes/OPERATIONS/data/notes-tracker.json`

**Structure**:
- Landscape beamer (16:9), tan/warm background, black rounded border
- Two-column layout with `\begin{columns}[T,onlytextwidth]`
- Left column: key idea + steps
- Right column: worked examples + common mistake + try these
- Commands:
  - `\NotesTitle{Notes & Steps}` — top header bar
  - `\KeyIdea{...}` — green-bordered card 
  - `\SectionTitle{...}` — green section heading
  - `\StepLine{n}{...}` — numbered step
  - `\WorkedExample{title}{content}` — sample problem
  - `\CommonMistake{...}` — red-warning card
  - `\TryThese{...}` — tiny practice
  - `\GreenDivider` — full-width green separator
- Content should be first-teach focused: light, clear, illustrative
- ~1-2 slides max per LO

**How to create**:
```bash
# 1. Write main.tex in manamaths-notes/OBJECTIVES/<slug>/
# 2. Build
tectonic --outdir manamaths-notes/OBJECTIVES/<slug>/build manamaths-notes/OBJECTIVES/<slug>/main.tex
# 3. Copy PDF to main site
cp manamaths-notes/OBJECTIVES/<slug>/build/main.pdf manamaths/SITE/notes-pdfs/<slug>.pdf
# 4. Refresh tracker
python3 manamaths-notes/OPERATIONS/scripts/generate_notes_tracker.py
```

---

## Module 3: Tasks (3 levels)

**Where**: `manamaths/OBJECTIVES/<slug>/{foundation,proficient,excellence}-questions.tex`
**Template**: `manamaths/OPERATIONS/templates/lo-template.tex`
**Tracker**: `manamaths/OPERATIONS/data/lo-tracker.json`

**Structure**:
- Landscape beamer (16:9), white background, black rounded border
- Header: scaffold icons (hoe for Foundation, hoe+koru for Proficient, 3x koru for Excellence)
- 3 rows of problem cards per page, ~2 pages per level
- Cards are `MMProblemCard` tcolorbox with height=0.26\textheight
- Each card has a number (1-9 per page) + question content
- Foundation: basic/steps, Proficient: applied, Excellence: extended/word problems
- Total: ~27-36 questions per level (3 pages × 9 cards or 2 pages × ~15 smaller)

**How to create**:
```bash
# 1. Write the three .tex files
# 2. Build with tectonic from manamaths root
tectonic --outdir OBJECTIVES/<slug> OBJECTIVES/<slug>/foundation-questions.tex
tectonic --outdir OBJECTIVES/<slug> OBJECTIVES/<slug>/proficient-questions.tex
tectonic --outdir OBJECTIVES/<slug> OBJECTIVES/<slug>/excellence-questions.tex
# 3. Generate preview images
# 4. Update LO tracker and site page
```

---

## Module 4: Solutions (3 levels)

**Where**: `manamaths-solutions/OBJECTIVES/<slug>/{foundation,proficient,excellence}-answers.tex`
**No separate template** — mirrors the task template but adds answers inside cards
**Tracker**: none yet (create if needed)

**Structure**:
- Same layout as task PDFs, but cards have answers shown (e.g. `\textbf{Answer: }42`)
- Foundation, Proficient, Excellence — one answer PDF per level
- Answers projected in class, so should be clear and well-spaced

**How to create**:
```bash
# 1. Copy the task .tex files, add answers inside problem cards
# 2. Build with tectonic
tectonic --outdir . manamaths-solutions/OBJECTIVES/<slug>/foundation-answers.tex
tectonic --outdir . manamaths-solutions/OBJECTIVES/<slug>/proficient-answers.tex
tectonic --outdir . manamaths-solutions/OBJECTIVES/<slug>/excellence-answers.tex
# 3. Copy to main site
mkdir -p manamaths/SITE/solutions-pdfs/<slug>/
cp manamaths-solutions/OBJECTIVES/<slug>/*-answers.pdf manamaths/SITE/solutions-pdfs/<slug>/
```

---

## Site Page Integration

**Where**: `manamaths/SITE/objectives/<slug>.html`
**Generator**: `manamaths/OPERATIONS/scripts/generate_web_html.py`

The site page pulls in all 4 modules as section cards:
1. Te reo terms PDF button (green accent)
2. Notes PDF button (green accent, with notes anchor #notes)
3. Task PDF buttons (3 cards, Foundation/Proficient/Excellence)
4. Solution PDF buttons (paired with each task card)

---

## Pipeline (in order for a new LO)

1. Create task PDFs (Foundation → Proficient → Excellence)
2. Create te reo Māori terms PDF
3. Create notes module in `manamaths-notes`
4. Create solution PDFs in `manamaths-solutions`
5. Copy solutions + notes PDFs into main site
6. Regenerate site page for the LO slug
7. Regenerate index page
8. Build all PNG preview images
9. Update lo-tracker.json + notes-tracker.json
10. Run `update-lo-status.py --sync-from-fs`
11. Visually inspect all PDFs
12. Push all repos

## Visual verification checklist

- [ ] Tasks: 2 pages, 3 rows per page, readable when projected
- [ ] Solutions: match task layout exactly, answers visible in cards
- [ ] Notes: 1-2 slides, clear key idea + steps + worked examples
- [ ] Te reo: terms match the LO's vocabulary, 2-column grid
- [ ] Site page: all module buttons present and linked correctly
- [ ] Preview PNGs: generated from PDF page 1 for each module

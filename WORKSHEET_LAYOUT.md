# Mana Maths worksheet layout system

Use this when generating or rebuilding worksheet PDFs.

## Goal

Make worksheets readable when projected in a classroom.

Default priority order:
1. readability from the back of the room
2. clear spacing between questions
3. sensible column count for the question type
4. fit as many questions as possible only after the first three are satisfied

## Projector-friendly defaults

All worksheet PDFs should use these defaults unless there is a strong reason not to:

- larger base font than the original template
- sans-serif body text for cleaner projection
- tighter header gap so more space goes to questions
- wider column gap
- more vertical space between items

## Column rules

Use these automatic rules:

- **4 columns** for sheets that are mostly numeric or very short prompts
- **3 columns** for wordier sheets

Treat a sheet as **wordy** if many items include things like:
- full-sentence prompts
- explanation language
- comparison language
- blanks to fill in
- error-checking
- student reasoning
- diagram instructions

Examples:
- `5 of 12 shaded` -> usually 4 columns
- `Explain whether 14/21 and 2/3 are equivalent.` -> 3 columns

## Counts and density

Do not cram the page.

If a sheet starts to feel crowded, prefer this order of fixes:
1. reduce columns
2. increase item spacing
3. reduce question count
4. split across more than one page if needed

## Build workflow

Before publishing worksheet updates:
1. update the question counts in YAML first
2. rebuild the matching `.tex` files from YAML if needed
3. run `apply_projector_layout.py`
4. run `build_pdfs.py`
5. visually inspect the rendered PDFs page by page
6. if page 2 still has obvious empty slots, add more questions in YAML and rebuild
7. if a third page appears or the sheet feels cramped, remove questions or reduce density
8. sync the finished PDFs to the public website copy

`build_pdfs.py` already runs the layout step automatically unless `--skip-layout` is passed.

Do not stop at "it compiles" or "it has two pages". The target is that page 2 should look intentionally filled, with only normal bottom whitespace left over.

For short, mostly numeric sheets, assume there is often room for 1 to 3 more questions on page 2 even after the PDF first reaches two pages.

When checking density, prefer the rendered PDF over the LaTeX source. A sparse second page means the YAML should usually gain more questions.

Current public review target:
- `wmm.co.nz/manamaths/`

Current website sync script:
- `/home/debid/.openclaw/workspace/williammcintosh.github.io/scripts/sync_manamaths.py`

## Files

- `convert_learning_objectives_json.py` = JSON to YAML converter
- `JSON_TO_YAML.md` = JSON conversion workflow
- `lo-template.tex` = base worksheet template
  - should always assume inline maths stays together as a unit while words still wrap normally
- `apply_projector_layout.py` = automatic layout classifier and restyler
- `build_pdfs.py` = PDF build script

## Current heuristic

The layout script currently decides between 3 and 4 columns based on worksheet wordiness.

- higher wordiness -> 3 columns
- mostly numeric / short prompts -> 4 columns

The heuristic looks at:
- average word count per item
- reasoning words like `explain`, `which`, `complete`, `whether`
- blanks like `\rule` or `\square`
- diagram-heavy prompts
- question-style punctuation and phrasing

## Inline maths wrapping rule

Keep the maths expression together, not the whole sentence.

Use this for prompts like:
- `Are $\frac{6}{9}$ and $\frac{10}{15}$ equivalent?`
- `Fill in the blank: $\frac{5}{6} = \frac{\square}{18}$`
- `Simplify $\frac{12}{16}$ and state a fraction equivalent to it.`

Goal:
- allow the words in a prompt to wrap normally
- prevent the maths expression itself from being split awkwardly across lines
- if a line break is needed, the full maths expression should move as a unit
- preserve generous projected row spacing so pages visually land around 3 rows / about 9 problems where appropriate

Do not box the entire task line. If an older file already has a full-line `\\mbox{...}`, remove it before rebuilding.
Only protect inline maths fragments.
Do not force this on long wordy questions or diagram tasks.

## Visual density rule

After every rebuild, inspect the actual rendered pages.

Use this decision rule:
- if page 2 has space that could clearly fit another full row or about 2 more short problems, add more questions in YAML
- if page 2 has only a small tail of whitespace, leave it
- if page 3 appears with only a few problems on it, reduce the count or tighten layout
- prefer fixing the content count in YAML, not by hand-editing only the compiled `.tex`

This is now part of the standard worksheet workflow, not an optional final polish step.

## Future direction

Keep extending the system so the agent can:
- render PDFs to images
- review actual page density visually
- decide when to increase or reduce question count
- detect when 2 columns is better than 3
- spot overflow, cramped diagrams, and weak projection readability
- feed the visual result back into YAML question-count decisions

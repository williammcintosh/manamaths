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

Before building PDFs:
1. run `apply_projector_layout.py`
2. then run `build_pdfs.py`

`build_pdfs.py` already runs the layout step automatically unless `--skip-layout` is passed.

## Files

- `lo-template.tex` = base worksheet template
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

## Future direction

Once visual PDF inspection is available, extend this system so the agent can:
- render PDFs to images
- review actual page density visually
- decide when to reduce question count
- detect when 2 columns is better than 3
- spot overflow, cramped diagrams, and weak projection readability

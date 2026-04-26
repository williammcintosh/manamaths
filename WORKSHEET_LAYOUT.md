# Mana Maths worksheet layout system

Use this when generating or rebuilding worksheet PDFs.

## Relevant files

- `OPERATIONS/templates/lo-template.tex`
- `OPERATIONS/scripts/apply_projector_layout.py`
- `OPERATIONS/scripts/build_pdfs.py`
- `OBJECTIVES/lo-yr9-<slug>/*-questions.tex`

## Goal

Make worksheets readable when projected.

Priority order:
1. readability from the back of the room
2. clear spacing between questions
3. sensible column count
4. fit more content only after the first three are satisfied

## Default rules

- use larger projected text
- keep generous row spacing
- default target: 27 questions per scaffold as 3 sets of 9 when the sheet can carry that cleanly
- worksheet headers should show the learning objective title only plus the scaffold label
- do not print internal LO codes like `Topic 1 LO1`
- do not print set labels like `Set 1`, `Set 2`, or `Set 3`
- use ragged-right card text to avoid stretched gaps after the question number
- avoid hard fixed card heights when they cause overflow; prefer tighter padding and natural card height first
- allow wide cards for wordier prompts; one wide card may span two card slots
- if a wide card is used, a page can carry 8 or fewer problems instead of forcing 9
- prefer 3 columns for wordier sheets
- use 4 columns only for short, mostly numeric sheets
- avoid cramped pages

## Build workflow

1. update question content in `OBJECTIVES/`
2. run `python3 OPERATIONS/scripts/build_pdfs.py`
3. visually inspect the PDFs
4. if page 2 is too sparse, add more questions and rebuild
5. if the sheet spills awkwardly to page 3, trim or simplify and rebuild

`build_pdfs.py` already runs `apply_projector_layout.py` unless `--skip-layout` is passed.

## Inline maths rule

Keep the maths expression together, not the whole sentence.

Do not wrap full prompt lines in `\mbox{...}`.
Only protect inline maths fragments when needed.

## Visual density rule

After every rebuild, inspect the rendered PDF.

Decision rule:
- obvious empty room on page 2 -> add more questions, usually toward the 27-question target
- small normal bottom whitespace -> leave it
- weak third page -> reduce density or question count

Prefer fixing the source question count in `OBJECTIVES/`, not patching only the compiled output.

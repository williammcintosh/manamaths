# Mana Maths pipeline

Use this workflow when building a full learning-objective pack for Year 9.

## Goal

For each learning objective:
1. write original Foundation questions
2. write original Proficient questions
3. write original Excellence questions
4. save those questions in YAML
5. assemble LaTeX worksheets from the template
6. apply projector-friendly layout rules automatically before building PDFs

## Source files

- `lo-template.tex` = page template
- `lo-yr9.yaml` = master Year 9 source

## Output structure

For each learning objective, create a folder:

- `lo-yr9-<slug>/foundation-questions.tex`
- `lo-yr9-<slug>/proficient-questions.tex`
- `lo-yr9-<slug>/excellence-questions.tex`

Keep the master YAML as the source of truth.

## YAML shape

Each learning objective should contain:

```yaml
- id: L01
  topic: Forming fractions
  instruction: Write each as a fraction.
  terminology: []
  skills: []
  question_types: []
  foundation_questions: []
  proficient_questions: []
  excellence_questions: []
```

Question entries should be LaTeX-ready items, usually beginning with `\item`.
Use YAML block style `|` for multiline TikZ or larger LaTeX blocks.

## Question-writing rules

### Foundation
- make questions direct and accessible
- focus on one skill at a time
- use clean numbers and familiar contexts
- include straightforward visual fraction prompts where useful
- avoid traps, ambiguity, and heavy reading load

### Proficient
- increase variety and independence
- mix numeric, visual, and short context questions
- require students to recognise the fraction without the wording always being identical
- use slightly less friendly numbers where appropriate

### Excellence
- use richer reasoning
- include inference, comparison, error-checking, and multi-step interpretation
- allow unit conversion or whole-part reasoning where suitable
- keep the task solvable without becoming wordy

## Quality bar

For every learning objective:
- Foundation should feel easier than Proficient
- Proficient should feel easier than Excellence
- all questions must match the stated learning objective
- wording must be student-facing and concise
- LaTeX must compile cleanly
- TikZ blocks must stay self-contained inside each `\item`
- worksheets must remain readable when projected
- do not cram wordy prompts into 4 columns

## LaTeX assembly rules

When creating each worksheet file:
1. copy the structure from `lo-template.tex`
2. insert the learning objective line
3. insert the student instruction line
4. insert the section header: `Foundation`, `Proficient`, or `Excellence`
5. insert the matching questions from YAML into the `enumerate` block
6. save into the correct `lo-yr9-<slug>/` folder
7. run the projector layout pass before final PDF build

See `WORKSHEET_LAYOUT.md` for the durable layout system.

## Naming

Convert the topic to a simple slug.

Examples:
- `Forming fractions` -> `lo-yr9-forming-fractions`
- `Equivalent fractions` -> `lo-yr9-equivalent-fractions`
- `Solving 1-step equations` -> `lo-yr9-solving-1-step-equations`

## Working order

For each learning objective:
1. inspect or create the YAML entry
2. write Foundation questions
3. write Proficient questions
4. write Excellence questions
5. create the three `.tex` files from the template
6. sanity-check for obvious LaTeX issues
7. commit in the `manamaths` repo

## Default counts

Unless told otherwise:
- Foundation: 12 to 16 questions
- Proficient: 12 questions
- Excellence: 16 to 20 questions

Use fewer questions if the items are diagram-heavy or too wordy for comfortable projection.

## If a learning objective needs visuals

Prefer:
- circles split into equal parts
- rectangles or grids
- simple polygons or region shading

Keep diagrams uncluttered and printable.

## Delivery style

Build the content first.
Then build the worksheet files.
Then run the automatic layout pass and build PDFs.
Keep the YAML clean enough that future worksheet generation can be automated.

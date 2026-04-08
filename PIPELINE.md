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
7. sync the finished PDFs to the public website copy so they can be reviewed in-browser

## Source files

- `lo-template.tex` = page template
  - base rule: inline maths should stay together as a unit, but full prompt lines must still wrap normally
  - base rule: projected worksheets should default to generous row gaps, aiming for about 3 rows / roughly 9 problems per page where appropriate
- `lo-yr9.yaml` = master Year 9 source
- `convert_learning_objectives_json.py` = JSON to YAML converter when objectives arrive as JSON
- `JSON_TO_YAML.md` = durable JSON conversion workflow

## Output structure

For each learning objective, create a folder:

- `lo-yr9-<slug>/foundation-questions.tex`
- `lo-yr9-<slug>/proficient-questions.tex`
- `lo-yr9-<slug>/excellence-questions.tex`

Keep the master YAML as the source of truth.
If learning objectives arrive as JSON, convert them first and then continue from YAML.

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

For each learning objective set:
1. if the source arrives as JSON, convert it to YAML first
2. inspect or create the YAML entry
3. write Foundation questions
4. write Proficient questions
5. write Excellence questions
6. create the three `.tex` files from the template
7. run the projector-friendly PDF build flow
8. add the new learning objective section and jump-link to `index.html`
9. visually inspect the rendered PDFs and confirm there are enough rows/problems to cover at least 2 pages; if not, adjust YAML counts first, then rebuild
10. sync the PDFs to the website copy
11. commit in the `manamaths` repo

## Rinse-and-repeat rule

When asked for the next learning objective, assume the same end-to-end workflow unless told otherwise:
- locate the next LO source in project JSON/YAML
- create a new `lo-yr9-<slug>/` directory
- create Foundation / Proficient / Excellence worksheet source files
- build the PDFs
- add the new section to the website and the jump-links nav
- visually inspect rendered PDFs, especially page fill and prompt wrapping, and confirm there are enough rows/problems to cover at least 2 pages
- push when done

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

If the source starts as JSON, convert JSON to YAML first.
Then build or refine the content in YAML.
Then build the worksheet files.
Then run the automatic layout pass and build PDFs.
Then sync the generated PDFs to the website copy so they can be checked on `wmm.co.nz/manamaths/`.
Keep the YAML clean enough that future worksheet generation can be automated.

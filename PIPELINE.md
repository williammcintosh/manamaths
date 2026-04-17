# Mana Maths pipeline

Use this workflow when building one Year 9 learning objective end to end.

## Repo shape

- `OBJECTIVES/` = worksheet source + PDFs + LO-specific media
- `SITE/` = generated website pages and shared site assets
- `OPERATIONS/scripts/` = build and validation scripts
- `OPERATIONS/data/lo-tracker.json` = generated status inventory
- `OPERATIONS/templates/` = worksheet templates

## Inputs

- `../lesson-builder/canonical/year-9-learning-objectives.json`
- `../lesson-builder/source/year-9-learning-objectives.pdf`
- `../lesson-builder/source/9MAT-master-teaching-guide.pdf`
- `OPERATIONS/data/lo-tracker.json`
- actual files under `OBJECTIVES/` and `SITE/`

## Definition of done

An LO is done only when all of these are true:
- `OBJECTIVES/lo-yr9-<slug>/` exists
- `foundation-questions.tex` exists
- `proficient-questions.tex` exists
- `excellence-questions.tex` exists
- all three PDFs build cleanly
- `SITE/objectives/lo-yr9-<slug>.html` exists
- `SITE/index.html` links to it
- the PDFs were visually checked
- tracker was regenerated
- changes were committed
- changes were pushed unless Will said not to

## Standard one-LO flow

1. choose the next LO from canonical + tracker + filesystem
2. confirm the slug
3. write Foundation questions
4. write Proficient questions
5. write Excellence questions
6. save them in `OBJECTIVES/lo-yr9-<slug>/`
7. run the single-LO build
8. visually inspect the rendered PDFs
9. regenerate the tracker
10. commit and push

## Preferred commands

Choose and scaffold the next missing LO:

```bash
python3 OPERATIONS/scripts/start_next_lo.py --json
```

Or manually:

```bash
python3 OPERATIONS/scripts/next_missing_lo.py --json
python3 OPERATIONS/scripts/scaffold_lo_tex.py --objective-id <objective-id>
```

Build one LO:

```bash
python3 OPERATIONS/scripts/build_single_lo.py lo-yr9-<slug>
```

That will:
- apply projector layout
- build PDFs
- regenerate that LO page plus `SITE/index.html`
- validate the LO

Refresh tracker:

```bash
python3 OPERATIONS/scripts/generate_lo_tracker.py
```

## Source-of-truth rule

- canonical wins for identity, order, wording, and metadata
- filesystem wins for what actually exists
- tracker is generated evidence only

## Guardrails

- do one LO at a time unless asked otherwise
- keep worksheet content in `OBJECTIVES/`
- keep generated website output in `SITE/`
- keep scripts/templates/tracker in `OPERATIONS/`
- do not reintroduce loose root clutter
- before asking Will for any git URL, first verify whether the current `manamaths/` copy is already a git repo/worktree
- if git metadata is missing, say that plainly and treat it as an environment mismatch in this filesystem copy

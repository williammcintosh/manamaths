# Mana Maths pipeline

Use this workflow when building one Year 9 learning objective end to end.

**Read `VISION.md` first** — it explains the project's long-term goal, architecture principles, and how the website vs PDFs fit together. All work should align with that vision.

## Repo shape

- `OBJECTIVES/` = worksheet source + PDFs + LO-specific media
- `SITE/` = generated website pages and shared site assets
- `OPERATIONS/scripts/` = build and validation scripts
- `OPERATIONS/data/lo-tracker.json` = generated status inventory
- `OPERATIONS/data/te-reo-progress.json` = local te reo Māori term tracker used for website term cards
- `OPERATIONS/templates/` = worksheet templates

## Inputs

- local repo files under `OBJECTIVES/`, `SITE/`, and `OPERATIONS/`
- `OPERATIONS/data/lo-tracker.json`
- `OPERATIONS/data/te-reo-progress.json`
- actual files under `OBJECTIVES/` and `SITE/`

## Definition of done

An LO is done only when all of these are true:
- `OBJECTIVES/lo-yr9-<slug>/` exists
- `foundation-questions.tex` exists
- `proficient-questions.tex` exists
- `excellence-questions.tex` exists
- each scaffold targets 27 problems by default (3 sets of 9) unless the task explicitly calls for a different count
- worksheet print headers show the module name only (Start Tasks / Build Tasks / Push Tasks) with hoe icons — no LO title in header; the LO title belongs on a combined title page
- worksheet print headers use the compact beamer spacing defaults so the first 3x3 page does not clip at the bottom
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
3. write Start Tasks (foundation) questions
4. write Build Tasks (proficient) questions
5. write Push Tasks (excellence) questions
6. make each scaffold 27 questions by default (3 sets of 9) unless told otherwise
7. save them in `OBJECTIVES/lo-yr9-<slug>/`
8. run the single-LO build
9. visually inspect the rendered PDFs
10. regenerate the tracker
11. commit and push

A full LO also includes **solutions** (answer PDFs via `mm-solutions` skill in `manamaths-solutions/`) and **notes** (teaching notes via `mm-notes` skill in `manamaths-notes/`). The site shows all available modules: scaffold panels have koru-only headings (no text labels) with both "Download tasks" and "Download solutions" buttons when the answer PDF exists.

## Per-module skills

- **Tasks** (worksheets): `mm-tasks` skill  
- **Solutions** (answer PDFs): `mm-solutions` skill  
- **Notes** (teaching notes): `mm-notes` skill  
- **Te reo** (Māori terms): `mm-te-reo` skill. Generated via `build_te_reo_pdfs.py` — reads `OPERATIONS/data/te-reo-progress.json`, writes both `.tex` and `.pdf` to `SITE/te-reo-pdfs/`. The `.tex` is committed to the repo alongside the PDF so it can be hand-edited and recompiled directly. Template at `OPERATIONS/templates/te-reo-template.tex`.
- **Resources**: `mm-resources` skill

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
- canonical website repo: `https://github.com/williammcintosh/manamaths`
- canonical internal docs repo: `https://github.com/williammcintosh/manamaths-tasks`
- before asking Will for any git URL, first verify whether the current `manamaths/` copy is already a git repo/worktree
- if git metadata is missing, say that plainly and treat it as an environment mismatch in this filesystem copy
- if the current workspace copy is detached, reattach or reclone from the canonical repos above instead of asking Will to repeat them

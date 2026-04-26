# Mana Maths

## Layout

`manamaths/` is now split into three clear areas:

- `OBJECTIVES/` — one folder per learning objective, including the worksheet `.tex`, PDFs, and any LO-specific web diagrams
- `SITE/` — generated website output and shared site assets
- `OPERATIONS/` — scripts, tracker data, templates, and build plumbing

Root should stay lean: a few all-caps docs plus those three folders.

## Source of truth

Use these in order:
- local repo content under `OBJECTIVES/`, `SITE/`, and `OPERATIONS/`
- generated tracker: `OPERATIONS/data/lo-tracker.json`
- te reo term tracker: `OPERATIONS/data/te-reo-progress.json`
- actual built files: `OBJECTIVES/` and `SITE/`

Quick decision guide:
- current local working state -> files in this repo
- what exists / what is missing -> `OPERATIONS/data/lo-tracker.json`
- edit worksheet content -> `OBJECTIVES/lo-yr9-<slug>/*-questions.tex`
- inspect generated website output -> `SITE/objectives/lo-yr9-<slug>.html`
- Notes panel presence on objective pages -> driven by `../manamaths-notes/OPERATIONS/data/notes-tracker.json` during site generation

Do not hand-edit the LO tracker JSON.

If te reo Māori term blocks need maintenance:
- local tracker data now lives in `OPERATIONS/data/te-reo-progress.json`
- reference PDF now lives in `OPERATIONS/reference/NZQAMathematicsTermsMao-Eng.pdf`
- site generation reads that te reo tracker directly from `manamaths/`

If older workflows mention local `tasks/` inputs, treat them as stale unless Will explicitly restores that repo.

## Core commands

Refresh tracker:

```bash
python3 OPERATIONS/scripts/generate_lo_tracker.py
```

Find next missing LO:

```bash
python3 OPERATIONS/scripts/next_missing_lo.py --json
```

Scaffold the next LO:

```bash
python3 OPERATIONS/scripts/start_next_lo.py --json
```

Build one LO safely:

```bash
python3 OPERATIONS/scripts/build_single_lo.py lo-yr9-solving-1-step-equations
```

Validate one LO:

```bash
python3 OPERATIONS/scripts/validate_lo.py lo-yr9-solving-1-step-equations
```

Generate site pages:

```bash
python3 OPERATIONS/scripts/generate_web_html.py
```

## Build notes

Worksheet PDF builds use:

```bash
python3 OPERATIONS/scripts/build_pdfs.py
```

The default beamer worksheet template now uses compact header spacing to protect the bottom row on 3x3 projector pages.

Supported TeX engines:
- `latexmk`
- `pdflatex`
- `tectonic`

On this machine, the intended fallback is:
- `/home/debid/bin/tectonic`

## Smaller-model safe path

For autonomous or smaller-model work, prefer this exact flow:

```bash
python3 OPERATIONS/scripts/start_next_lo.py --json
python3 OPERATIONS/scripts/build_single_lo.py lo-yr9-<slug>
python3 OPERATIONS/scripts/generate_lo_tracker.py
```

That path keeps the repo constrained to one LO at a time.

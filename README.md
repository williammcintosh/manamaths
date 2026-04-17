# Mana Maths

## Layout

`manamaths/` is now split into three clear areas:

- `OBJECTIVES/` — one folder per learning objective, including the worksheet `.tex`, PDFs, and any LO-specific web diagrams
- `SITE/` — generated website output and shared site assets
- `OPERATIONS/` — scripts, tracker data, templates, and build plumbing

Root should stay lean: a few all-caps docs plus those three folders.

## Source of truth

Use these in order:
- canonical list: `../lesson-builder/canonical/year-9-learning-objectives.json`
- generated tracker: `OPERATIONS/data/lo-tracker.json`
- actual built files: `OBJECTIVES/` and `SITE/`

Quick decision guide:
- official LO title/order/metadata -> canonical JSON
- what exists / what is missing -> `OPERATIONS/data/lo-tracker.json`
- edit worksheet content -> `OBJECTIVES/lo-yr9-<slug>/*-questions.tex`
- inspect generated website output -> `SITE/objectives/lo-yr9-<slug>.html`

Do not hand-edit the tracker JSON.

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

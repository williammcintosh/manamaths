# Mana Maths JSON to YAML workflow

Use this when the source learning objectives arrive as JSON instead of YAML.

## Goal

Turn a learning objectives JSON file into the Mana Maths YAML source of truth.

After that, the normal workflow continues:
1. YAML becomes the editable source of truth
2. worksheet `.tex` files are created from that YAML
3. PDFs are built
4. PDFs are synced to `wmm.co.nz/manamaths/`

## Conversion script

- `convert_learning_objectives_json.py`

## Supported JSON shapes

The converter accepts either:

- a top-level JSON array, or
- a top-level object with one of these list keys:
  - `learning_objectives`
  - `learningObjectives`
  - `objectives`
  - `items`

## Preferred objective fields

Each JSON objective should ideally include:

- `id`
- `topic`
- `instruction`
- `terminology`
- `skills`
- `question_types`
- `foundation_questions`
- `proficient_questions`
- `excellence_questions`

The converter also accepts common aliases such as:
- `title` / `name` for `topic`
- `instructions` / `prompt` for `instruction`
- `vocabulary` for `terminology`
- `questionTypes` for `question_types`
- `foundationQuestions`, `proficientQuestions`, `excellenceQuestions`

## Command

Example:

```bash
python3 convert_learning_objectives_json.py input.json -o lo-yr9.yaml
```

## Rules

- YAML becomes the source of truth after conversion.
- Keep slugs simple: `lo-yr9-<topic-slug>`.
- Preserve multiline LaTeX question blocks using YAML block style.
- If input JSON is incomplete, convert what exists, then fill gaps in YAML before worksheet generation.

## Standard pipeline after conversion

1. convert JSON to YAML
2. review and tidy YAML
3. create worksheet `.tex` files
4. run `build_pdfs.py`
5. sync PDFs to the website copy
6. review at `wmm.co.nz/manamaths/`

# Mana Maths objective JSON workflow

Use this when external objective data arrives in JSON and needs to be mapped into the Mana Maths canonical/tracker flow.

## Inputs and outputs

Input source of truth:
- `../lesson-builder/canonical/year-9-learning-objectives.json`

Generated build-state evidence:
- `OPERATIONS/data/lo-tracker.json`

Worksheet source output:
- `OBJECTIVES/lo-yr9-<slug>/`

Generated website output:
- `SITE/objectives/lo-yr9-<slug>.html`

## Rule

After conversion or mapping:
- canonical stays the source of truth
- tracker stays generated evidence
- worksheets live in `OBJECTIVES/`
- website output lives in `SITE/`

## Command shape

If a conversion helper is needed, keep it under `OPERATIONS/scripts/`.

After mapping or conversion, the normal path is:
1. review canonical data
2. choose the next missing LO
3. scaffold worksheet files
4. write/refine the `.tex` in `OBJECTIVES/`
5. run the single-LO build
6. regenerate the tracker
7. review the generated page in `SITE/`

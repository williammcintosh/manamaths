#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / 'lo-yr9.yaml'


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return re.sub(r'-+', '-', text).strip('-')


def pick(source: dict, *keys: str, default=None):
    for key in keys:
        if key in source and source[key] is not None:
            return source[key]
    return default


def ensure_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def yaml_scalar(value: str) -> str:
    value = '' if value is None else str(value)
    if value == '' or re.search(r'[:#\-\n\[\]\{\}]', value):
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'
    return value


def yaml_list(lines: list[str], indent: int = 0) -> str:
    prefix = ' ' * indent
    if not lines:
        return prefix + '[]'

    rendered = []
    for item in lines:
        text = '' if item is None else str(item)
        if '\n' in text:
            rendered.append(prefix + '- |')
            for line in text.splitlines():
                rendered.append(prefix + '  ' + line)
        else:
            rendered.append(prefix + '- ' + yaml_scalar(text))
    return '\n'.join(rendered)


def normalize_objective(raw: dict, index: int) -> dict:
    topic = pick(raw, 'topic', 'title', 'name', default=f'Learning objective {index:02d}')
    objective_id = pick(raw, 'id', 'objective_id', default=f'L{index:02d}')
    instruction = pick(raw, 'instruction', 'instructions', 'prompt', default='')

    normalized = {
        'id': str(objective_id),
        'topic': str(topic),
        'slug': f"lo-yr9-{slugify(str(topic))}",
        'instruction': str(instruction),
        'terminology': ensure_list(pick(raw, 'terminology', 'vocabulary', default=[])),
        'skills': ensure_list(pick(raw, 'skills', default=[])),
        'question_types': ensure_list(pick(raw, 'question_types', 'questionTypes', default=[])),
        'foundation_questions': ensure_list(pick(raw, 'foundation_questions', 'foundationQuestions', default=[])),
        'proficient_questions': ensure_list(pick(raw, 'proficient_questions', 'proficientQuestions', default=[])),
        'excellence_questions': ensure_list(pick(raw, 'excellence_questions', 'excellenceQuestions', default=[])),
    }
    return normalized


def load_json(path: Path):
    data = json.loads(path.read_text(encoding='utf-8'))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ('learning_objectives', 'learningObjectives', 'objectives', 'items'):
            if isinstance(data.get(key), list):
                return data[key]
    raise ValueError('Expected a JSON array or an object containing a learning objectives list.')


def render_yaml(objectives: list[dict], year_level: int) -> str:
    lines = [f'year_level: {year_level}', 'learning_objectives:']
    for objective in objectives:
        lines.extend(
            [
                f"  - id: {yaml_scalar(objective['id'])}",
                f"    topic: {yaml_scalar(objective['topic'])}",
                f"    slug: {yaml_scalar(objective['slug'])}",
                f"    instruction: {yaml_scalar(objective['instruction'])}",
                '    terminology:',
                yaml_list(objective['terminology'], indent=6),
                '    skills:',
                yaml_list(objective['skills'], indent=6),
                '    question_types:',
                yaml_list(objective['question_types'], indent=6),
                '',
                '    foundation_questions:',
                yaml_list(objective['foundation_questions'], indent=6),
                '',
                '    proficient_questions:',
                yaml_list(objective['proficient_questions'], indent=6),
                '',
                '    excellence_questions:',
                yaml_list(objective['excellence_questions'], indent=6),
            ]
        )
    return '\n'.join(lines) + '\n'


def main() -> int:
    parser = argparse.ArgumentParser(description='Convert learning objectives JSON into Mana Maths YAML.')
    parser.add_argument('input_json', help='Path to source JSON file.')
    parser.add_argument('-o', '--output', default=str(DEFAULT_OUTPUT), help='Path to output YAML file.')
    parser.add_argument('--year-level', type=int, default=9, help='Year level to write into the YAML file.')
    args = parser.parse_args()

    input_path = Path(args.input_json).resolve()
    output_path = Path(args.output).resolve()

    raw_objectives = load_json(input_path)
    objectives = [normalize_objective(item, index + 1) for index, item in enumerate(raw_objectives)]
    yaml_text = render_yaml(objectives, args.year_level)
    output_path.write_text(yaml_text, encoding='utf-8')

    print(f'Wrote {len(objectives)} learning objectives to {output_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

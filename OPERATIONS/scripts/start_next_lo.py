#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OPERATIONS_DIR = SCRIPT_DIR.parent
REPO_ROOT = OPERATIONS_DIR.parent
OBJECTIVES_DIR = REPO_ROOT / "OBJECTIVES"


def run_json(cmd: list[str]) -> dict:
    result = subprocess.run(cmd, cwd=REPO_ROOT.parent, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Pick and scaffold the next missing Mana Maths LO.")
    parser.add_argument("--topic", type=int, help="Optional topic number filter, e.g. 2")
    parser.add_argument("--force", action="store_true", help="Overwrite existing tex files when scaffolding")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary")
    args = parser.parse_args()

    next_cmd = ["python3", "manamaths/OPERATIONS/scripts/next_missing_lo.py", "--json"]
    if args.topic is not None:
        next_cmd = ["python3", "manamaths/OPERATIONS/scripts/next_missing_lo.py", "--topic", str(args.topic), "--json"]

    info = run_json(next_cmd)

    scaffold_cmd = [
        "python3",
        "manamaths/OPERATIONS/scripts/scaffold_lo_tex.py",
        "--objective-id",
        info["objectiveId"],
    ]
    if args.force:
        scaffold_cmd.append("--force")

    subprocess.run(scaffold_cmd, cwd=REPO_ROOT.parent, check=True)

    result = {
        "objectiveId": info["objectiveId"],
        "slug": info["slug"],
        "displayTitle": info.get("displayTitle", ""),
        "internalCode": info.get("internalCode", ""),
        "nextStep": f"Edit manamaths/OBJECTIVES/{info['slug']}/{{foundation,proficient,excellence}}-questions.tex then run: python3 manamaths/OPERATIONS/scripts/build_single_lo.py {info['slug']}",
    }

    if args.json:
        print(json.dumps(result))
    else:
        print(f"objectiveId: {result['objectiveId']}")
        print(f"slug: {result['slug']}")
        print(f"displayTitle: {result['displayTitle']}")
        print(f"internalCode: {result['internalCode']}")
        print(result['nextStep'])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

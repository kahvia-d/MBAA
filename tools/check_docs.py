#!/usr/bin/env python3
"""Validate MBAA documentation links and JSON/JSONC examples."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

from check_pipeline import ROOT, strip_json_comments


DOCS = [ROOT / "README.md", ROOT / "docs" / "zh_cn" / "develop" / "pipeline_best_practices.md"]
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
FENCE_RE = re.compile(r"```(?:json|jsonc)\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def main() -> int:
    errors: list[str] = []
    example_count = 0
    link_count = 0
    for path in DOCS:
        text = path.read_text(encoding="utf-8")
        for target in LINK_RE.findall(text):
            target = target.strip().split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            link_count += 1
            resolved = (path.parent / unquote(target)).resolve()
            if not resolved.exists():
                errors.append(f"{path.relative_to(ROOT)}: broken local link {target}")
        if path.name == "pipeline_best_practices.md":
            for index, block in enumerate(FENCE_RE.findall(text), start=1):
                example_count += 1
                try:
                    json.loads(strip_json_comments(block))
                except (json.JSONDecodeError, ValueError) as exc:
                    errors.append(f"{path.relative_to(ROOT)}: JSON example {index} is invalid: {exc}")

    if errors:
        print("Documentation checks failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(f"Documentation checks passed: {link_count} local links, {example_count} JSON examples.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

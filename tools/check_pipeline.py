#!/usr/bin/env python3
"""Static graph and resource checks for MBAA Pipeline v1 files."""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
PIPELINE_DIR = ROOT / "assets" / "resource" / "pipeline"
IMAGE_DIR = ROOT / "assets" / "resource" / "image"
INTERFACE_PATH = ROOT / "assets" / "interface.json"
FULLSCREEN_TEMPLATE_ALLOWLIST = {"nav/loading.png"}


def strip_json_comments(text: str) -> str:
    out: list[str] = []
    index = 0
    in_string = False
    escaped = False
    while index < len(text):
        char = text[index]
        if in_string:
            out.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            out.append(char)
            index += 1
            continue
        if text.startswith("//", index):
            end = text.find("\n", index)
            if end == -1:
                break
            out.append("\n")
            index = end + 1
            continue
        if text.startswith("/*", index):
            end = text.find("*/", index + 2)
            if end == -1:
                raise ValueError("unterminated block comment")
            out.extend("\n" for char in text[index : end + 2] if char == "\n")
            index = end + 2
            continue
        out.append(char)
        index += 1
    return "".join(out)


def load_jsonc(path: Path, duplicate_errors: list[str]) -> Any:
    def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                duplicate_errors.append(f"{path.relative_to(ROOT)}: duplicate JSON key {key}")
            result[key] = value
        return result

    return json.loads(strip_json_comments(path.read_text(encoding="utf-8")), object_pairs_hook=pairs_hook)


def normalize_route(route: str) -> str:
    while route.startswith("["):
        match = re.match(r"^\[[^\]]+\]", route)
        if not match:
            break
        route = route[match.end() :]
    return route


def collect_routes(node: dict[str, Any]) -> list[tuple[str, str]]:
    routes: list[tuple[str, str]] = []
    for field in ("next", "on_error"):
        for route in node.get(field, []):
            if isinstance(route, str):
                routes.append((field, route))
    for field in ("any_of", "all_of"):
        for route in node.get(field, []):
            if isinstance(route, str):
                routes.append((field, route))
    return routes


def visit_recognition_objects(value: Any, callback: Any) -> None:
    if isinstance(value, list):
        for item in value:
            visit_recognition_objects(item, callback)
    elif isinstance(value, dict):
        if value.get("recognition") in {"TemplateMatch", "FeatureMatch"}:
            callback(value)
        for child in value.values():
            visit_recognition_objects(child, callback)


def iter_override_nodes(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, list):
        for item in value:
            found.extend(iter_override_nodes(item))
    elif isinstance(value, dict):
        override = value.get("pipeline_override")
        if isinstance(override, dict):
            found.extend(override)
        for child in value.values():
            found.extend(iter_override_nodes(child))
    return found


def main() -> int:
    errors: list[str] = []
    duplicates: list[str] = []
    nodes: dict[str, dict[str, Any]] = {}
    owners: dict[str, Path] = {}

    for path in sorted(PIPELINE_DIR.glob("*.json")):
        data = load_jsonc(path, duplicates)
        if not isinstance(data, dict):
            errors.append(f"{path.relative_to(ROOT)}: pipeline root must be an object")
            continue
        for name, node in data.items():
            if name in nodes:
                errors.append(
                    f"duplicate node {name}: {owners[name].relative_to(ROOT)} and {path.relative_to(ROOT)}"
                )
                continue
            if not isinstance(node, dict):
                errors.append(f"{path.relative_to(ROOT)}: node {name} must be an object")
                continue
            nodes[name] = node
            owners[name] = path

    if list(nodes).count("Stop") != 1 or "Stop" not in nodes:
        errors.append("the pipeline graph must define exactly one Stop node")

    edges: dict[str, set[str]] = defaultdict(set)
    for name, node in nodes.items():
        next_routes = {normalize_route(route) for route in node.get("next", []) if isinstance(route, str)}
        error_routes = {normalize_route(route) for route in node.get("on_error", []) if isinstance(route, str)}
        overlap = sorted(next_routes & error_routes)
        if overlap:
            errors.append(f"{name}: next/on_error overlap: {', '.join(overlap)}")

        for _field, raw_route in collect_routes(node):
            target = normalize_route(raw_route)
            if target not in nodes:
                errors.append(f"{name}: undefined route {raw_route}")
            else:
                edges[name].add(target)
            if target == name and "max_hit" not in node:
                errors.append(f"{name}: unlimited direct self-loop {raw_route}")

        def check_template(recognition: dict[str, Any]) -> None:
            recognition_type = recognition.get("recognition")
            raw_templates = recognition.get("template", [])
            templates = raw_templates if isinstance(raw_templates, list) else [raw_templates]
            for template in templates:
                if not isinstance(template, str):
                    errors.append(f"{name}: non-string template value")
                    continue
                template_path = IMAGE_DIR / template
                if template_path.is_dir():
                    if not any(template_path.glob("*.png")):
                        errors.append(f"{name}: empty template directory {template}")
                elif not template_path.is_file():
                    errors.append(f"{name}: missing template {template}")
                if "roi" not in recognition and template not in FULLSCREEN_TEMPLATE_ALLOWLIST:
                    errors.append(f"{name}: {recognition_type} {template} has no ROI")

        visit_recognition_objects(node, check_template)

    interface = load_jsonc(INTERFACE_PATH, duplicates)
    errors.extend(duplicates)
    tasks = interface.get("task", []) if isinstance(interface, dict) else []
    roots = {"Start"}
    for task in tasks:
        entry = task.get("entry") if isinstance(task, dict) else None
        if not isinstance(entry, str) or entry not in nodes:
            errors.append(f"UI task {task.get('name', '<unknown>')}: undefined entry {entry}")
        else:
            roots.add(entry)
    for override_node in iter_override_nodes(interface):
        if override_node not in nodes:
            errors.append(f"interface pipeline_override references undefined node {override_node}")

    reachable: set[str] = set()
    queue = deque(root for root in roots if root in nodes)
    while queue:
        current = queue.popleft()
        if current in reachable:
            continue
        reachable.add(current)
        queue.extend(edges[current] - reachable)
    for name in sorted(set(nodes) - reachable):
        errors.append(f"unreachable node {name} ({owners[name].relative_to(ROOT)})")

    if errors:
        print("Pipeline checks failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(f"Pipeline checks passed: {len(nodes)} nodes, all reachable, {len(roots) - 1} UI tasks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

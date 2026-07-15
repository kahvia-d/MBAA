#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = (
    ROOT / "tests" / "fixtures" / "reference_templates" / "schedule_special_students"
)
ACTUAL_SIZE_SOURCE_DIR = (
    ROOT
    / "tests"
    / "fixtures"
    / "reference_templates"
    / "schedule_special_students_actual"
)
OUTPUT_DIR = ROOT / "assets" / "resource" / "image" / "schedule" / "special_students"
SCHEDULE_IMAGE_DIR = ROOT / "assets" / "resource" / "image" / "schedule"
HEART_SOURCE = ROOT / "tests" / "fixtures" / "screenshots" / "当前地区全体课程表.png"
OUTPUT_SIZE = (43, 52)
MASK_COLOR = (0, 255, 0)
HEART_BOX = (258, 273, 31, 40)
DEPRECATED_HEART_TEMPLATES = {"heart_wide.png"}
REQUIRED_TEMPLATES = {
    "Kei.png",
    "佳世子(正月).png",
    "彌香.png",
    "愛麗絲(武裝).png",
    "星野(泳裝).png",
    "聖亞.png",
    "花子(泳裝).png",
    "莉央.png",
    "陽奈(禮服).png",
}


def render_student_template(source: Path) -> Image.Image:
    actual_size_source = ACTUAL_SIZE_SOURCE_DIR / source.name
    selected_source = actual_size_source if actual_size_source.exists() else source
    with Image.open(selected_source) as image:
        output = image.convert("RGB")
        if output.size != OUTPUT_SIZE:
            output = output.resize(OUTPUT_SIZE, Image.Resampling.LANCZOS)

    draw = ImageDraw.Draw(output)
    width, height = OUTPUT_SIZE
    draw.rectangle((0, 0, width - 1, 2), fill=MASK_COLOR)
    draw.rectangle((0, height - 3, width - 1, height - 1), fill=MASK_COLOR)
    draw.rectangle((0, 0, 2, height - 1), fill=MASK_COLOR)
    draw.rectangle((width - 3, 0, width - 1, height - 1), fill=MASK_COLOR)
    # Rio's white hair clips are her strongest discriminator from other dark-haired
    # students. A completed Rio may stop matching, which is fine because completed
    # students should be skipped anyway.
    if source.name != "莉央.png":
        draw.rectangle((29, 0, 42, 17), fill=MASK_COLOR)
    draw.rectangle((30, 35, 42, 51), fill=MASK_COLOR)
    return output


def render_heart_template() -> Image.Image:
    with Image.open(HEART_SOURCE) as image:
        x, y, width, height = HEART_BOX
        output = image.convert("RGB").crop((x, y, x + width, y + height))

    pixels = output.load()
    for y in range(output.height):
        for x in range(output.width):
            red, green, blue = pixels[x, y]
            is_pink = red > 180 and blue > 120 and red - green > 15
            is_stem_or_body = y >= 17 or 18 <= x <= 27
            is_number = 7 <= x <= 25 and 22 <= y <= 34
            is_heart_tip = y < 37 or 14 <= x <= 21
            if not (is_pink and is_stem_or_body and not is_number and is_heart_tip):
                pixels[x, y] = MASK_COLOR
    return output


def source_templates() -> list[Path]:
    sources = sorted(SOURCE_DIR.glob("*.png"), key=lambda path: path.name)
    names = {path.name for path in sources}
    missing = sorted(REQUIRED_TEMPLATES - names)
    if missing:
        raise RuntimeError(f"Missing schedule source templates: {', '.join(missing)}")
    return sources


def image_matches(path: Path, expected: Image.Image) -> bool:
    try:
        with Image.open(path) as actual:
            actual_rgb = actual.convert("RGB")
            return actual_rgb.size == expected.size and actual_rgb.tobytes() == expected.tobytes()
    except (FileNotFoundError, OSError):
        return False


def write_templates(sources: list[Path]) -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    expected_names = {path.name for path in sources}
    for stale in OUTPUT_DIR.glob("*.png"):
        if stale.name not in expected_names:
            stale.unlink()

    updated = 0
    for source in sources:
        destination = OUTPUT_DIR / source.name
        expected = render_student_template(source)
        if image_matches(destination, expected):
            continue
        expected.save(destination, format="PNG", compress_level=9)
        updated += 1

    SCHEDULE_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    heart_destination = SCHEDULE_IMAGE_DIR / "heart.png"
    expected_heart = render_heart_template()
    if not image_matches(heart_destination, expected_heart):
        expected_heart.save(heart_destination, format="PNG", compress_level=9)
        updated += 1

    for name in DEPRECATED_HEART_TEMPLATES:
        stale = SCHEDULE_IMAGE_DIR / name
        if stale.exists():
            stale.unlink()
            updated += 1
    return updated


def check_templates(sources: list[Path]) -> list[str]:
    expected_names = {path.name for path in sources}
    problems = [
        f"unexpected output: {path.relative_to(ROOT)}"
        for path in sorted(OUTPUT_DIR.glob("*.png"), key=lambda item: item.name)
        if path.name not in expected_names
    ]
    for source in sources:
        destination = OUTPUT_DIR / source.name
        if not image_matches(destination, render_student_template(source)):
            problems.append(f"stale or missing output: {destination.relative_to(ROOT)}")
    heart_destination = SCHEDULE_IMAGE_DIR / "heart.png"
    if not image_matches(heart_destination, render_heart_template()):
        problems.append(f"stale or missing output: {heart_destination.relative_to(ROOT)}")
    for name in DEPRECATED_HEART_TEMPLATES:
        stale = SCHEDULE_IMAGE_DIR / name
        if stale.exists():
            problems.append(f"deprecated output: {stale.relative_to(ROOT)}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate schedule student templates.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="Write generated templates.")
    mode.add_argument("--check", action="store_true", help="Check generated templates.")
    args = parser.parse_args()

    try:
        sources = source_templates()
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1

    if args.write:
        updated = write_templates(sources)
        print(f"Schedule templates updated: {updated}; total: {len(sources) + 1}.")
        return 0

    problems = check_templates(sources)
    if problems:
        print("Schedule template generation is out of date:", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1
    print(f"Schedule templates are up to date: {len(sources) + 1} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

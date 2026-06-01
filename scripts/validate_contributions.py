"""Validate every contribution manifest. CI-friendly (no Blender, no rendering).

Walks contributions/<category>/<contribution>/manifest.yaml recursively, checks
required fields, enum values, and that referenced files exist. Exits non-zero on
any error so it can gate pull requests.

    python scripts/validate_contributions.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONTRIB = ROOT / "contributions"

REQUIRED = ["title", "author", "type", "entry", "preview", "license"]
TYPES = {"figure", "animation", "report", "model", "universe"}
ENGINES = {"cycles", "eevee", "matplotlib", "html", "none"}


def _manifest_dirs():
    for mf in CONTRIB.rglob("manifest.yaml"):
        parts = mf.relative_to(CONTRIB).parts
        if any(p in {"_TEMPLATE", "schema"} or p.startswith("_") for p in parts):
            continue
        yield mf.parent


def validate_one(folder: Path) -> list[str]:
    rel = folder.relative_to(CONTRIB)
    m = yaml.safe_load((folder / "manifest.yaml").read_text())
    errs = []
    for key in REQUIRED:
        if not m.get(key):
            errs.append(f"{rel}: missing required field '{key}'")
    if m.get("type") and m["type"] not in TYPES:
        errs.append(f"{rel}: type must be one of {sorted(TYPES)}")
    if m.get("engine") and m["engine"] not in ENGINES:
        errs.append(f"{rel}: engine must be one of {sorted(ENGINES)}")
    for ref in ("entry", "preview"):
        if m.get(ref) and not (folder / m[ref]).exists():
            errs.append(f"{rel}: {ref} file '{m[ref]}' not found")
    return errs


def main() -> None:
    folders = sorted(_manifest_dirs())
    all_errs = []
    for folder in folders:
        all_errs += validate_one(folder)
    if all_errs:
        print("Contribution validation FAILED:")
        for e in all_errs:
            print("  -", e)
        sys.exit(1)
    print(f"OK — {len(folders)} contribution(s) valid.")


if __name__ == "__main__":
    main()

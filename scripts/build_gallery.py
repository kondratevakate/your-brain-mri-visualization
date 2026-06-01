"""Regenerate gallery/README.md from all contribution manifests, grouped by
category (the folder directly under contributions/).

    python scripts/build_gallery.py
"""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONTRIB = ROOT / "contributions"
GALLERY = ROOT / "gallery"
COLS = 3

CATEGORY_TITLES = {
    "reports": "📊 Reports",
    "anatomical-models": "🧠 Anatomical Models (3D-printable)",
    "3d-art": "🎨 3D Art",
    "anime": "🌀 Anime",
    "universes": "🌌 Universes",
}


def collect():
    by_cat: dict[str, list[dict]] = {}
    for mf in CONTRIB.rglob("manifest.yaml"):
        parts = mf.relative_to(CONTRIB).parts
        if any(p in {"_TEMPLATE", "schema"} or p.startswith("_") for p in parts):
            continue
        m = yaml.safe_load(mf.read_text())
        m["_folder"] = mf.parent
        category = parts[0] if len(parts) > 1 else "uncategorized"
        by_cat.setdefault(category, []).append(m)
    return by_cat


def cell(m: dict) -> str:
    folder = m["_folder"]
    rel = (folder / m.get("preview", "")).relative_to(ROOT).as_posix()
    return (f"<td align='center' width='33%'>"
            f"<img src='../{rel}' width='240'><br>"
            f"<b>{m.get('title', folder.name)}</b><br>"
            f"<sub>@{m.get('author', '?')} · {m.get('type', '')}</sub></td>")


def main() -> None:
    by_cat = collect()
    GALLERY.mkdir(exist_ok=True)
    total = sum(len(v) for v in by_cat.values())
    lines = ["# Gallery", "",
             f"{total} community contribution(s) across {len(by_cat)} "
             "categor(ies). Add yours — see [CONTRIBUTING.md](../CONTRIBUTING.md).",
             ""]
    for cat in sorted(by_cat, key=lambda c: list(CATEGORY_TITLES).index(c)
                      if c in CATEGORY_TITLES else 99):
        items = by_cat[cat]
        lines += [f"## {CATEGORY_TITLES.get(cat, cat)}", "", "<table>"]
        for i in range(0, len(items), COLS):
            lines.append("<tr>")
            lines += [cell(m) for m in items[i:i + COLS]]
            lines.append("</tr>")
        lines += ["</table>", ""]
    (GALLERY / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {GALLERY / 'README.md'} — {total} item(s), "
          f"{len(by_cat)} categor(ies)")


if __name__ == "__main__":
    main()

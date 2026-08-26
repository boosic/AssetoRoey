"""Module 2 — Project Hierarchy Generation.

Builds the strict Assetto Corsa car content folder hierarchy::

    <location>/<car_id>/
        <car_id>.kn5            (placeholder)
        collider.kn5            (placeholder)
        logo.png                (placeholder)
        data/                   (physics .ini templates + .lut tables)
        sfx/                    (<car_id>.bank + GUIDs.txt placeholders)
        skins/00_default/       (livery/preview placeholders + ui_skin.json)
        ui/                     (ui_car.json + badge placeholder)

and populates it from the Module 1 template dictionaries.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from string import Template

from templates import (
    CONFIG_TEMPLATES,
    LUT_FILES,
    PLACEHOLDER_FILES,
    REQUIRED_DIRS,
    build_ui_car_json,
    build_ui_skin_json,
)


def sanitize_car_id(raw: str) -> str:
    """Normalise a user-typed name into a safe AC folder id
    (lowercase letters, digits and underscores)."""
    slug = re.sub(r"[^a-z0-9_]+", "_", raw.strip().lower())
    return slug.strip("_")


def _render(template_text: str, mapping: dict) -> str:
    return Template(template_text).safe_substitute(mapping)


def generate_car_project(location: Path | str, car_id: str, *,
                         screen_name: str | None = None,
                         brand: str = "Unknown",
                         author: str = "AC Mod Studio",
                         year: int = 2026,
                         overwrite: bool = False) -> Path:
    """Create ``<location>/<car_id>`` with the full AC car mod skeleton.

    Existing files are never overwritten (missing ones are added), so it is
    safe to re-run over a project when ``overwrite=True`` is passed for an
    existing folder. Returns the project root path."""
    car_id = sanitize_car_id(car_id)
    if not car_id:
        raise ValueError("car_id must contain at least one letter or digit")
    screen_name = screen_name or car_id.replace("_", " ").title()

    root = Path(location) / car_id
    if root.exists() and not overwrite:
        raise FileExistsError(f"{root} already exists")

    mapping = {"car": car_id, "screen_name": screen_name, "brand": brand,
               "author": author, "year": year}

    # 1. strict folder hierarchy -------------------------------------------
    for rel in REQUIRED_DIRS:
        (root / _render(rel, mapping)).mkdir(parents=True, exist_ok=True)

    def write(rel_path: str, content: str):
        target = root / _render(rel_path, mapping)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text(content, encoding="utf-8")

    # 2. mandatory binary-asset placeholders (3D models, audio, images) ----
    for rel_path, content in PLACEHOLDER_FILES.items():
        write(rel_path, _render(content, mapping))

    # 3. physics configuration templates + lookup tables -------------------
    for filename, content in CONFIG_TEMPLATES.items():
        write(f"data/{filename}", _render(content, mapping))
    for filename, content in LUT_FILES.items():
        write(f"data/{filename}", content)

    # 4. UI JSON files ------------------------------------------------------
    write("ui/ui_car.json",
          json.dumps(build_ui_car_json(car_id, screen_name, brand,
                                       author=author, year=year),
                     indent=2, ensure_ascii=False) + "\n")
    write("skins/00_default/ui_skin.json",
          json.dumps(build_ui_skin_json("Default"), indent=2,
                     ensure_ascii=False) + "\n")

    return root

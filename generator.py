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
    MINIMAL_CONFIG_FILES,
    MINIMAL_LUT_FILES,
    MINIMAL_PLACEHOLDER_FILES,
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


# File types AC Mod Studio writes as real text — everything else is a
# binary-asset placeholder eligible for the optional '.txt' name suffix.
_TEXT_SUFFIXES = {".txt", ".ini", ".json", ".lut", ".rto"}

_LUT_REF = re.compile(r"[A-Za-z0-9_.]+\.lut")


def _luts_referenced_by(config_files) -> set:
    """LUT filenames mentioned by the given config templates — generating
    them alongside avoids dangling references (a missing physics LUT is a
    crash in AC)."""
    needed = set()
    for filename in config_files:
        needed.update(_LUT_REF.findall(CONFIG_TEMPLATES.get(filename, "")))
    return needed


def generate_car_project(location: Path | str, car_id: str, *,
                         screen_name: str | None = None,
                         brand: str = "Unknown",
                         author: str = "AC Mod Studio",
                         year: int = 2026,
                         overwrite: bool = False,
                         minimal: bool = False,
                         config_files=None,
                         placeholder_files=None,
                         placeholder_txt_suffix: bool = False) -> Path:
    """Create ``<location>/<car_id>`` with the AC car mod skeleton.

    * ``minimal=True`` — only the files the sim needs to load and drive the
      car (no setup screen, driver aids, shadows, badges, DRS stubs).
    * ``config_files`` / ``placeholder_files`` — explicit custom selections
      of data templates and asset placeholders; the LUTs the chosen
      templates reference are added automatically. ``None`` means "decide
      from the minimal flag".
    * ``placeholder_txt_suffix=True`` — binary-asset placeholders get a
      ``.txt`` appended to their name (``my_car.kn5.txt``) so they open in
      any text editor and the real asset name stays free.

    Existing files are never overwritten (missing ones are added), so it is
    safe to re-run over a project when ``overwrite=True`` is passed for an
    existing folder. Returns the project root path."""
    car_id = sanitize_car_id(car_id)
    if not car_id:
        raise ValueError("car_id must contain at least one letter or digit")
    screen_name = screen_name or car_id.replace("_", " ").title()

    custom = config_files is not None or placeholder_files is not None
    if config_files is None:
        config_files = MINIMAL_CONFIG_FILES if minimal \
            else set(CONFIG_TEMPLATES)
    else:
        config_files = set(config_files) & set(CONFIG_TEMPLATES)
    if placeholder_files is None:
        placeholder_files = MINIMAL_PLACEHOLDER_FILES if minimal \
            else set(PLACEHOLDER_FILES)
    else:
        placeholder_files = (set(placeholder_files) & set(PLACEHOLDER_FILES))
        placeholder_files.add("_README_PLACEHOLDERS.txt")
    if minimal or custom:
        lut_files = set(LUT_FILES) & _luts_referenced_by(config_files)
    else:
        lut_files = set(LUT_FILES)   # full set: components need them too

    root = Path(location) / car_id
    if root.exists() and not overwrite:
        raise FileExistsError(f"{root} already exists")

    mapping = {"car": car_id, "screen_name": screen_name, "brand": brand,
               "author": author, "year": year}

    # 1. strict folder hierarchy -------------------------------------------
    for rel in REQUIRED_DIRS:
        (root / _render(rel, mapping)).mkdir(parents=True, exist_ok=True)

    def write(rel_path: str, content: str, is_placeholder: bool = False):
        target = root / _render(rel_path, mapping)
        if is_placeholder and placeholder_txt_suffix and \
                target.suffix.lower() not in _TEXT_SUFFIXES:
            target = target.with_name(target.name + ".txt")
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text(content, encoding="utf-8")

    # 2. mandatory binary-asset placeholders (3D models, audio, images) ----
    for rel_path, content in PLACEHOLDER_FILES.items():
        if rel_path in placeholder_files:
            write(rel_path, _render(content, mapping), is_placeholder=True)

    # 3. physics configuration templates + lookup tables -------------------
    for filename, content in CONFIG_TEMPLATES.items():
        if filename in config_files:
            write(f"data/{filename}", _render(content, mapping))
    for filename, content in LUT_FILES.items():
        if filename in lut_files:
            write(f"data/{filename}", content)

    # 4. UI JSON files ------------------------------------------------------
    write("ui/ui_car.json",
          json.dumps(build_ui_car_json(car_id, screen_name, brand,
                                       author=author, year=year),
                     indent=2, ensure_ascii=False) + "\n")
    if not minimal and any(str(p).startswith("skins/")
                           for p in placeholder_files):
        write("skins/00_default/ui_skin.json",
              json.dumps(build_ui_skin_json("Default"), indent=2,
                         ensure_ascii=False) + "\n")

    return root

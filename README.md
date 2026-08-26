# AC Mod Studio

A desktop toolkit for **generating, managing and tuning Assetto Corsa car
mods** — pure Python standard library (`tkinter`/`ttk`), zero external
dependencies.

```
python main.py
```

Requires Python 3.10+ with tkinter (included in the python.org installers;
on Debian/Ubuntu: `sudo apt install python3-tk`).

## Features

- **Project generator** — creates the strict AC `content/cars/<car_id>`
  hierarchy (`data`, `sfx`, `skins/00_default`, `ui`) with:
  - Kunos-style physics templates (`car.ini`, `engine.ini`,
    `suspensions.ini`, `aero.ini`) whose keys and default values follow real
    extracted Kunos car data,
  - lookup tables (`power.lut`, wing AoA LUTs),
  - a valid `ui/ui_car.json` + `ui_skin.json`,
  - placeholder text files for every mandatory binary asset (`.kn5` models,
    FMOD `.bank` + `GUIDs.txt`, previews, badges, blob shadows) explaining
    how to produce the real thing.
- **Split-screen shell** — file-explorer tree on the left, tabbed editor
  workspace on the right, with closable tabs, a status bar and a persisted
  **dark mode** (Ctrl+D).
- **Visual config editor** — every `.ini` opens in a 2-tab notebook
  (*Visual* / *Raw Text*). The visual tab renders a bordered box per
  `[SECTION]` with a clean 2-column key/value grid; edits update the raw
  text live, hand-edits to the raw text flow back into the grid. Comments
  and file layout are preserved on save (Ctrl+S — nothing touches disk
  until you save).
- **Suspension tuning editor** — `suspensions.ini` opens a BeamNG-style
  editor: `TYPE` renders as a dropdown of the vanilla AC suspension types
  (DWB, STRUT, AXLE, ML) and picking one injects that geometry's default
  sub-option keys (wishbone pickups, strut mounts, `[AXLE]` links,
  multilink joints). Every numeric value gets a slider with two-way
  binding — drag to type, type to move — and typing a value beyond the
  current limit stretches the slider range instead of clamping.
- **ADD COMPONENT ▾** — injects Kunos-accurate template variants straight
  into the active editor's memory and refreshes the grid instantly:
  - *engine.ini*: street/race/80s-F1 turbos, twin-turbo pair, overboost
    damage,
  - *aero.ini*: rear wing, front splitter, body aero, DRS flap,
  - *suspensions.ini*: street/sport/race anti-roll bars, formula heave
    (3rd element), suspension damage,
  - plus a one-click "Add ALL variants" per group.

## Architecture

| Module | Responsibility |
| --- | --- |
| `templates.py` | Data storage: placeholder texts, Kunos config templates, LUTs, component library, suspension type data, slider hints. No UI code. |
| `generator.py` | Project hierarchy generation from the templates. |
| `editors.py` | Editing engine: order/comment-preserving INI model, `RawTextEditor`, `ConfigEditor` (Visual + Raw Text), `SuspensionEditor` (dropdown + sliders). |
| `app.py` | Application shell: theming/dark mode, file explorer, closable tab workspace, routing, ADD COMPONENT menu, dialogs. |
| `main.py` | Entry point. |

### Editor routing

| File | Editor |
| --- | --- |
| `suspensions.ini` (any `*suspension*.ini`) | `SuspensionEditor` |
| any other `.ini` | `ConfigEditor` |
| `.json`, `.lut`, `.txt`, everything else | `RawTextEditor` (with a Format-JSON button for JSON) |

Real binary files (containing NUL bytes) are refused with a hint instead of
being opened.

## Notes on the generated car

The `data/` files are genuine, tunable Kunos-style physics. The car will
appear in tools (e.g. Content Manager) immediately, but it drives only after
you replace the placeholder text files with real compiled assets — each
placeholder documents exactly what belongs there. See
`_README_PLACEHOLDERS.txt` inside a generated project.

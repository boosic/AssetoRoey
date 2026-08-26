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
  - Kunos-style physics templates whose keys and default values follow real
    extracted Kunos car data: the four core files (`car.ini`, `engine.ini`,
    `suspensions.ini`, `aero.ini`) plus the rest of the minimum drivable
    set (`drivetrain.ini`, `tyres.ini` v10, `brakes.ini`,
    `electronics.ini`, `colliders.ini`, `ai.ini`, `lods.ini`,
    `driver3d.ini`, `setup.ini`, `fuel_cons.ini`, and zero-byte
    `drs.ini`/`wing_animations.ini`),
  - lookup tables (`power.lut`, wing AoA + ground-height LUTs, tyre
    wear/thermal curves) — every LUT referenced by an ini exists on disk,
  - a valid `ui/ui_car.json` + `ui_skin.json`,
  - placeholder text files for every mandatory binary asset (`.kn5` models,
    FMOD `.bank` + `GUIDs.txt`, previews, badges, blob shadows) explaining
    how to produce the real thing.
  Choose **Full car**, **Minimal** (only what the sim needs to load and
  drive), or a **Custom selection** — pick exactly which `data/` templates
  and asset placeholders to create; the LUTs they reference are added
  automatically.
- **Split-screen shell** — file-explorer tree on the left, tabbed editor
  workspace on the right, with closable tabs (the ✕ stays visible however
  many tabs are open; right-click a tab for Close / Close Others /
  Close All) and a status bar.
- **Settings menu** — theme (Dark / Regular / **Follow system colors**,
  the default; Ctrl+D quick-toggles dark/light), always-visible LUT point
  labels (on by default), whether to reopen the last project on startup,
  and an option to append `.txt` to binary placeholder names
  (`my_car.kn5.txt`) so they open in any text editor. All persisted.
- **Visual config editor** — every `.ini` opens in a 2-tab notebook
  (*Visual* / *Raw Text*). The visual tab renders a bordered box per
  `[SECTION]` with a clean 2-column key/value grid; edits update the raw
  text live, hand-edits to the raw text flow back into the grid. Comments
  and file layout are preserved on save (Ctrl+S — nothing touches disk
  until you save). 3-component vector values render as labelled **X/Y/Z
  fields**, and every row/section carries a small options menu
  (right-click a row, or the ⋮ on a section box): remove this key, remove
  any key via a submenu, add a key, add a section, remove the section —
  more actions can slot in later. A "＋ Section" toolbar button (and an
  empty-state button) creates sections even after all were removed.
- **Suspension tuning editor** — `suspensions.ini` opens a BeamNG-style
  editor: `TYPE` renders as a dropdown of the vanilla AC suspension types
  (DWB, STRUT, AXLE, ML). Switching type updates the file properly:
  the old type's geometry keys are removed, the new type's are inserted,
  and the `[AXLE]` helper section is created or dropped as needed.
  Removed values are stashed per project until the project is closed, so
  switching back restores your tuned numbers instead of defaults. For
  live axles, changing `LINK_COUNT` regenerates the `J{i}_CAR`/`J{i}_AXLE`
  link pairs (extra links are stashed too). Every numeric value gets a
  slider with two-way binding — drag to type, type to move — typing beyond
  the current limit stretches the slider range, and integer keys snap to
  whole numbers.
- **LUT graph viewer** — `.lut` lookup tables open in a 2-tab editor with
  a live line graph (grid, tick labels, zero axis, hover readout, and
  per-point value labels shown by default) next to the raw text; the plot
  re-renders as you type and warns about malformed or non-ascending rows.
- **ADD COMPONENT ▾** — injects Kunos-accurate template variants straight
  into the active editor's memory and refreshes the grid instantly:
  - *engine.ini*: street/race/80s-F1 turbos, twin-turbo pair, overboost
    damage,
  - *aero.ini*: rear wing, front splitter, body aero, DRS flap,
  - *suspensions.ini*: street/sport/race anti-roll bars, formula heave
    (3rd element), suspension damage,
  - *drs.ini* / *wing_animations.ini*: F1-style or road-car DRS, flap
    animation binding,
  - *drivetrain.ini*: differential presets, RWD/FWD/AWD traction,
  - *electronics.ini*: ABS/TC presets, electronic diff lock,
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
| `.lut` | `LutEditor` (live graph + raw text) |
| `.json`, `.txt`, everything else | `RawTextEditor` (with a Format-JSON button for JSON) |

Real binary files (containing NUL bytes) are refused with a hint instead of
being opened.

## Notes on the generated car

The `data/` files are genuine, tunable Kunos-style physics. The car will
appear in tools (e.g. Content Manager) immediately, but it drives only after
you replace the placeholder text files with real compiled assets — each
placeholder documents exactly what belongs there. See
`_README_PLACEHOLDERS.txt` inside a generated project.

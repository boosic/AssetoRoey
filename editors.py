"""Module 3 — Dynamic UI Editing Engine.

Contains:
  * A comment/order-preserving parser + serializer for Kunos-style INI files
    (``ConfigDocument`` / ``Section`` / ``Entry``).
  * ``RawTextEditor``      — plain text editor with save support.
  * ``ConfigEditor``       — 2-tab (Visual / Raw Text) editor for .ini files.
  * ``SuspensionEditor``   — BeamNG-style subclass with TYPE dropdowns and
                             slider-bound numeric fields.

Everything is pure stdlib (tkinter / ttk).
"""

from __future__ import annotations

import json
import re
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import messagebox, ttk

from templates import (
    SLIDER_HINTS,
    SUSPENSION_TYPES,
    SUSPENSION_TYPE_DEFAULTS,
)

MONO_FONT = ("Consolas", 10)
_COMMENT_MARKS = (";", "//", "#")


# ---------------------------------------------------------------------------
#  INI document model (order + comment preserving)
# ---------------------------------------------------------------------------

class Entry:
    """One line inside a section: a key/value pair, a comment, or a blank."""

    __slots__ = ("kind", "key", "value", "comment")

    def __init__(self, kind: str, key: str = "", value: str = "", comment: str = ""):
        self.kind = kind          # "kv" | "comment" | "blank"
        self.key = key
        self.value = value
        self.comment = comment    # inline comment, including its ';' marker


class Section:
    def __init__(self, name: str, comment: str = ""):
        self.name = name
        self.comment = comment    # inline comment on the [SECTION] line
        self.entries: list[Entry] = []

    # -- key helpers --------------------------------------------------------
    def kv_entries(self) -> list[Entry]:
        return [e for e in self.entries if e.kind == "kv"]

    def has(self, key: str) -> bool:
        return any(e.key.upper() == key.upper() for e in self.kv_entries())

    def get(self, key: str, default: str = "") -> str:
        for e in self.kv_entries():
            if e.key.upper() == key.upper():
                return e.value
        return default

    def set(self, key: str, value: str) -> Entry:
        """Update an existing key (case-insensitive) or append a new one."""
        for e in self.kv_entries():
            if e.key.upper() == key.upper():
                e.value = value
                return e
        entry = Entry("kv", key, value)
        self.entries.append(entry)
        return entry


def _split_inline_comment(raw: str) -> tuple[str, str]:
    """Split ``80000  ; wheel rate`` into ``('80000', '; wheel rate')``."""
    best = -1
    for mark in _COMMENT_MARKS:
        pos = raw.find(mark)
        if pos != -1 and (best == -1 or pos < best):
            best = pos
    if best == -1:
        return raw.strip(), ""
    return raw[:best].strip(), raw[best:].rstrip()


class ConfigDocument:
    """A parsed Kunos-style INI file. Preserves section/key order, comments
    and blank lines so that a Visual-tab edit round-trips cleanly."""

    def __init__(self):
        self.preamble: list[str] = []      # verbatim lines before first section
        self.sections: list[Section] = []

    # -- parsing ------------------------------------------------------------
    @classmethod
    def parse(cls, text: str) -> "ConfigDocument":
        doc = cls()
        current: Section | None = None
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if line.startswith("["):
                end = line.find("]")
                if end == -1:
                    name, rest = line[1:].strip(), ""
                else:
                    name, rest = line[1:end].strip(), line[end + 1:].strip()
                current = Section(name, rest)
                doc.sections.append(current)
                continue
            if current is None:
                doc.preamble.append(raw_line)
                continue
            if not line:
                current.entries.append(Entry("blank"))
            elif line.startswith(_COMMENT_MARKS):
                current.entries.append(Entry("comment", comment=raw_line.rstrip()))
            elif "=" in line:
                key, _, rest = line.partition("=")
                value, comment = _split_inline_comment(rest)
                current.entries.append(Entry("kv", key.strip(), value, comment))
            else:
                # Malformed line — keep it verbatim so nothing is lost.
                current.entries.append(Entry("comment", comment=raw_line.rstrip()))
        return doc

    # -- serialisation ------------------------------------------------------
    def serialize(self) -> str:
        if not self.sections and not any(l.strip() for l in self.preamble):
            # Keep genuinely empty files zero-byte: AC treats the mere
            # presence of a non-empty drs.ini as "car has DRS".
            return ""
        out: list[str] = list(self.preamble)
        for i, sec in enumerate(self.sections):
            header = f"[{sec.name}]"
            if sec.comment:
                header += f"\t{sec.comment}"
            out.append(header)
            for e in sec.entries:
                if e.kind == "kv":
                    line = f"{e.key}={e.value}"
                    if e.comment:
                        line += f"\t{e.comment}"
                    out.append(line)
                elif e.kind == "comment":
                    out.append(e.comment)
                else:
                    out.append("")
            # keep exactly one blank line between sections
            if i < len(self.sections) - 1 and (not out or out[-1] != ""):
                out.append("")
        return "\n".join(out).rstrip("\n") + "\n"

    # -- section helpers ----------------------------------------------------
    def section(self, name: str) -> Section | None:
        for s in self.sections:
            if s.name.upper() == name.upper():
                return s
        return None

    def add_section(self, name: str) -> Section:
        sec = Section(name)
        self.sections.append(sec)
        return sec

    def next_numbered(self, prefix: str) -> str:
        """Return the next free ``PREFIX_N`` style name, e.g. ``WING_2``."""
        pattern = re.compile(re.escape(prefix) + r"(\d+)$", re.IGNORECASE)
        taken = [int(m.group(1)) for s in self.sections
                 if (m := pattern.match(s.name))]
        return f"{prefix}{max(taken) + 1 if taken else 0}"

    def merge_component(self, sections: list[tuple[str, dict]]) -> list[str]:
        """Inject a component template (list of ``(section_name, {key: value})``).

        A section name ending in ``#`` (e.g. ``TURBO_#``) is auto-numbered to
        the next free index.  A fixed-name section that already exists gets its
        keys merged (template values win, extra user keys survive).
        Returns the names of the sections that were created/updated."""
        touched: list[str] = []
        for name, keys in sections:
            if name.endswith("#"):
                name = self.next_numbered(name[:-1])
                sec = self.add_section(name)
            else:
                sec = self.section(name) or self.add_section(name)
            for key, value in keys.items():
                sec.set(key, str(value))
            touched.append(sec.name)
        return touched


# ---------------------------------------------------------------------------
#  Small helpers shared by the editors
# ---------------------------------------------------------------------------

def _as_float(value: str):
    """Return the float for a plain scalar value, else None (vectors, text,
    inline LUTs and lut file names are not sliderable)."""
    v = value.strip()
    if not v or "," in v or "(" in v or "|" in v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _fmt_num(v: float) -> str:
    """Format a slider value the way a human would type it."""
    if v == int(v) and abs(v) >= 1:
        return str(int(v))
    if abs(v) >= 1000:
        return str(int(round(v)))
    if abs(v) >= 100:
        return f"{v:.1f}".rstrip("0").rstrip(".")
    if abs(v) >= 1:
        return f"{v:.2f}".rstrip("0").rstrip(".")
    s = f"{v:.5f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-") else "0"


def _nice_ceil(x: float) -> float:
    """Round *up* to a 'nice' 1/2/5×10^k number for slider limits."""
    if x <= 0:
        return 1.0
    import math
    exp = math.floor(math.log10(x))
    for mult in (1, 2, 5, 10):
        candidate = mult * (10 ** exp)
        if candidate >= x:
            return float(candidate)
    return float(10 ** (exp + 1))


class ScrollableFrame(ttk.Frame):
    """Canvas-based vertically scrollable frame.

    Mousewheel handling is a single application-wide binding that walks up
    from the widget under the pointer to the nearest ScrollableFrame — this
    keeps the wheel working over the entries/sliders that cover the grid,
    and multiple open editors never fight over ``bind_all``."""

    _wheel_installed = False

    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self.vbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vbar.set)
        self.vbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.interior = ttk.Frame(self.canvas)
        self._win = self.canvas.create_window((0, 0), window=self.interior, anchor="nw")
        self.interior.bind("<Configure>", self._on_interior_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self._install_wheel_binding()

    def _on_interior_configure(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self._win, width=event.width)

    # -- mousewheel (Windows / macOS / X11) ---------------------------------
    def _install_wheel_binding(self):
        if ScrollableFrame._wheel_installed:
            return
        ScrollableFrame._wheel_installed = True
        root = self.winfo_toplevel()
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            root.bind_all(seq, ScrollableFrame._on_wheel_global, add="+")

    @staticmethod
    def _on_wheel_global(event):
        widget = event.widget
        if not isinstance(widget, tk.Misc):        # e.g. already destroyed
            return
        try:
            # Scroll what is under the pointer (on Windows the event goes to
            # the focus widget, so event.widget alone is not enough).
            under = widget.winfo_containing(event.x_root, event.y_root)
        except (KeyError, tk.TclError):
            under = None
        target = under or widget
        while target is not None:
            if isinstance(target, ScrollableFrame):
                break
            target = target.master
        if target is None:
            return
        if getattr(event, "num", None) == 4 or getattr(event, "delta", 0) > 0:
            target.canvas.yview_scroll(-2, "units")
        elif getattr(event, "num", None) == 5 or getattr(event, "delta", 0) < 0:
            target.canvas.yview_scroll(2, "units")


# ---------------------------------------------------------------------------
#  Base editor
# ---------------------------------------------------------------------------

class BaseEditor(ttk.Frame):
    """Common behaviour for every editor hosted in the workspace notebook."""

    def __init__(self, master, path: Path, app):
        super().__init__(master)
        self.path = Path(path)
        self.app = app
        self.dirty = False

    # -- dirty tracking -----------------------------------------------------
    def mark_dirty(self):
        if not self.dirty:
            self.dirty = True
            self.app.on_editor_dirty_changed(self)

    def mark_clean(self):
        if self.dirty:
            self.dirty = False
            self.app.on_editor_dirty_changed(self)

    @property
    def display_name(self) -> str:
        return self.path.name

    def save(self):  # pragma: no cover - overridden
        raise NotImplementedError

    # -- toolbar ------------------------------------------------------------
    def _build_toolbar(self, extra_buttons=()):
        bar = ttk.Frame(self, padding=(6, 4))
        bar.pack(side="top", fill="x")
        ttk.Button(bar, text="\U0001f4be Save", command=self.save,
                   style="Accent.TButton").pack(side="left")
        for text, cmd in extra_buttons:
            ttk.Button(bar, text=text, command=cmd).pack(side="left", padx=(6, 0))
        ttk.Label(bar, text=str(self.path), style="Muted.TLabel",
                  anchor="e").pack(side="right", fill="x", expand=True)
        ttk.Separator(self, orient="horizontal").pack(side="top", fill="x")
        return bar

    def _make_text(self, master) -> tk.Text:
        wrapper = ttk.Frame(master)
        text = tk.Text(wrapper, wrap="none", undo=True, font=MONO_FONT,
                       borderwidth=0, highlightthickness=0, padx=8, pady=6)
        ybar = ttk.Scrollbar(wrapper, orient="vertical", command=text.yview)
        xbar = ttk.Scrollbar(wrapper, orient="horizontal", command=text.xview)
        text.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        ybar.pack(side="right", fill="y")
        xbar.pack(side="bottom", fill="x")
        text.pack(side="left", fill="both", expand=True)
        self.app.theme.register_text(text)
        wrapper.text = text
        return wrapper


# ---------------------------------------------------------------------------
#  Raw text editor (JSON / LUT / txt / anything else)
# ---------------------------------------------------------------------------

class RawTextEditor(BaseEditor):
    def __init__(self, master, path: Path, app):
        super().__init__(master, path, app)
        extra = []
        if self.path.suffix.lower() == ".json":
            extra.append(("{ } Format JSON", self._format_json))
        self._build_toolbar(extra)
        wrapper = self._make_text(self)
        wrapper.pack(fill="both", expand=True)
        self.text = wrapper.text
        try:
            content = self.path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = self.path.read_text(encoding="latin-1")
        self.text.insert("1.0", content)
        self.text.edit_reset()
        self.text.edit_modified(False)
        self.text.bind("<<Modified>>", self._on_modified)

    def _on_modified(self, _event=None):
        if self.text.edit_modified():
            self.mark_dirty()
            self.text.edit_modified(False)

    def _format_json(self):
        raw = self.text.get("1.0", "end-1c")
        try:
            pretty = json.dumps(json.loads(raw), indent=2, ensure_ascii=False)
        except ValueError as exc:
            messagebox.showerror("Invalid JSON", f"Cannot format: {exc}",
                                 parent=self)
            return
        self.text.delete("1.0", "end")
        self.text.insert("1.0", pretty)
        self.mark_dirty()

    def save(self):
        self.path.write_text(self.text.get("1.0", "end-1c"), encoding="utf-8")
        self.mark_clean()
        self.app.set_status(f"Saved {self.path.name}")


# ---------------------------------------------------------------------------
#  Configuration editor — Visual + Raw Text notebook
# ---------------------------------------------------------------------------

class ConfigEditor(BaseEditor):
    """Base editor for Kunos .ini physics files.

    Two-way flow:
      * Visual edits update the parsed document immediately and re-render the
        Raw Text tab (debounced).
      * Hand edits in the Raw Text tab are re-parsed into the document when
        switching back to the Visual tab (or when saving / injecting a
        component), so both views never fight over a keystroke.
    """

    def __init__(self, master, path: Path, app):
        super().__init__(master, path, app)
        try:
            text = self.path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = self.path.read_text(encoding="latin-1")
        self.doc = ConfigDocument.parse(text)

        self._rows = []               # per-row state (see _RowBinding)
        self._raw_dirty = False       # raw tab has edits not yet in self.doc
        self._sync_guard = False      # suppress <<Modified>> during programmatic set
        self._pending_sync = None     # debounce id for visual->raw sync

        self._build_toolbar([("↻ Reload", self.reload_from_disk)])
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # -- Visual tab
        self.visual_tab = ScrollableFrame(self.notebook)
        self.notebook.add(self.visual_tab, text="  Visual  ")

        # -- Raw text tab
        raw_wrapper_host = ttk.Frame(self.notebook)
        self.notebook.add(raw_wrapper_host, text="  Raw Text  ")
        wrapper = self._make_text(raw_wrapper_host)
        wrapper.pack(fill="both", expand=True)
        self.raw_text = wrapper.text
        self.raw_text.bind("<<Modified>>", self._on_raw_modified)

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self.rebuild_visual()
        self._set_raw(self.doc.serialize())

    # ------------------------------------------------------------------ raw
    def _set_raw(self, content: str):
        self._sync_guard = True
        try:
            yview = self.raw_text.yview()
            self.raw_text.delete("1.0", "end")
            self.raw_text.insert("1.0", content)
            self.raw_text.edit_modified(False)
            self.raw_text.yview_moveto(yview[0])
        finally:
            self._sync_guard = False
        self._raw_dirty = False

    def _on_raw_modified(self, _event=None):
        if not self.raw_text.edit_modified():
            return
        self.raw_text.edit_modified(False)
        if self._sync_guard:
            return
        self._raw_dirty = True
        self.mark_dirty()

    def _schedule_raw_sync(self):
        """Visual edit happened → refresh the raw tab shortly afterwards."""
        if self._pending_sync is not None:
            self.after_cancel(self._pending_sync)
        self._pending_sync = self.after(150, self._sync_raw_from_doc)

    def _sync_raw_from_doc(self):
        self._pending_sync = None
        self._set_raw(self.doc.serialize())

    def _flush_raw_edits(self):
        """If the user hand-edited the raw tab, fold it back into the model."""
        if self._pending_sync is not None:      # visual edits still queued
            self.after_cancel(self._pending_sync)
            self._sync_raw_from_doc()
        if self._raw_dirty:
            self.doc = ConfigDocument.parse(self.raw_text.get("1.0", "end-1c"))
            self._raw_dirty = False
            self.rebuild_visual()

    def _on_tab_changed(self, _event=None):
        try:
            active = self.notebook.index(self.notebook.select())
        except tk.TclError:
            return
        if active == 0:        # Visual selected → absorb raw edits
            self._flush_raw_edits()
        else:                  # Raw selected → make sure it shows latest model
            if self._pending_sync is not None:
                self.after_cancel(self._pending_sync)
                self._sync_raw_from_doc()

    # --------------------------------------------------------------- saving
    def reload_from_disk(self):
        if self.dirty and not messagebox.askyesno(
                "Reload", f"Discard unsaved changes to {self.path.name}?",
                parent=self):
            return
        try:
            text = self.path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = self.path.read_text(encoding="latin-1")
        self.doc = ConfigDocument.parse(text)
        self.rebuild_visual()
        self._set_raw(self.doc.serialize())
        self.mark_clean()
        self.app.set_status(f"Reloaded {self.path.name}")

    def save(self):
        if self._raw_dirty:
            # Raw tab holds the newest edits — save it verbatim.
            content = self.raw_text.get("1.0", "end-1c")
            self.doc = ConfigDocument.parse(content)
            self._raw_dirty = False
            self.rebuild_visual()
        else:
            if self._pending_sync is not None:
                self.after_cancel(self._pending_sync)
                self._sync_raw_from_doc()
            content = self.doc.serialize()
            self._set_raw(content)
        self.path.write_text(content, encoding="utf-8")
        self.mark_clean()
        self.app.set_status(f"Saved {self.path.name}")

    # ------------------------------------------------------- component menu
    def inject_component(self, label: str, sections: list[tuple[str, dict]]):
        """ADD COMPONENT hook: merge template sections into the in-memory
        document and refresh both tabs. Nothing touches the disk until the
        user hits Save / Ctrl+S."""
        self._flush_raw_edits()
        touched = self.doc.merge_component(sections)
        self.rebuild_visual()
        self._sync_raw_from_doc()
        self.mark_dirty()
        pretty = ", ".join(f"[{t}]" for t in touched)
        self.app.set_status(f"Injected '{label}' → {pretty}  (unsaved)")

    # --------------------------------------------------------------- visual
    def rebuild_visual(self):
        for child in self.visual_tab.interior.winfo_children():
            child.destroy()
        self._rows.clear()
        host = self.visual_tab.interior
        host.columnconfigure(0, weight=1)
        for row, sec in enumerate(self.doc.sections):
            box = ttk.LabelFrame(host, text=f" [{sec.name}] ", padding=(10, 6))
            box.grid(row=row, column=0, sticky="ew", padx=10, pady=(8, 2))
            self._build_section_body(sec, box)
        if not self.doc.sections:
            ttk.Label(host, text="No [SECTION] blocks found — use the Raw Text "
                                 "tab to start one.",
                      style="Muted.TLabel").grid(padx=14, pady=14)
        self.visual_tab._on_interior_configure()

    def _build_section_body(self, sec: Section, box: ttk.Frame):
        """Default layout: clean 2-column grid of key labels + value entries."""
        box.columnconfigure(1, weight=1)
        r = 0
        for entry in sec.kv_entries():
            ttk.Label(box, text=entry.key).grid(
                row=r, column=0, sticky="w", padx=(2, 12), pady=2)
            var = tk.StringVar(value=entry.value)
            widget = ttk.Entry(box, textvariable=var)
            widget.grid(row=r, column=1, sticky="ew", pady=2)
            self._bind_var(var, entry)
            if entry.comment:
                r += 1
                ttk.Label(box, text=entry.comment.lstrip(";/# ").strip(),
                          style="Muted.TLabel").grid(
                    row=r, column=1, sticky="w", padx=2)
            r += 1

    def _bind_var(self, var: tk.StringVar, entry: Entry):
        # Keep a hard reference: a StringVar only referenced from closures is
        # a collectible cycle, and its finalizer would unset the Tcl variable.
        self._rows.append(var)

        def on_write(*_):
            entry.value = var.get()
            self.mark_dirty()
            self._schedule_raw_sync()
        var.trace_add("write", on_write)


# ---------------------------------------------------------------------------
#  Suspension editor — BeamNG-style tuning layout
# ---------------------------------------------------------------------------

class _SliderRow:
    """2-way binding between one Entry and one Scale, loop-protected."""

    def __init__(self, editor: "SuspensionEditor", box, row: int,
                 entry: Entry, sec: Section):
        self.editor = editor
        self.entry = entry
        self._guard = False

        value = _as_float(entry.value)
        lo, hi = editor.slider_range(sec.name, entry.key, value)
        self.var = tk.StringVar(value=entry.value)

        ttk.Label(box, text=entry.key).grid(
            row=row, column=0, sticky="w", padx=(2, 12), pady=3)
        self.field = ttk.Entry(box, textvariable=self.var, width=12)
        self.field.grid(row=row, column=1, sticky="w", pady=3)
        self.scale = ttk.Scale(box, orient="horizontal", from_=lo, to=hi,
                               command=self._on_slider)
        self.scale.grid(row=row, column=2, sticky="ew", padx=(10, 4), pady=3)
        self.bounds = ttk.Label(box, text=self._bounds_text(lo, hi),
                                style="Muted.TLabel", width=16, anchor="e")
        self.bounds.grid(row=row, column=3, sticky="e", padx=(0, 2))

        if value is not None:
            self._guard = True
            self.scale.set(value)
            self._guard = False
        self.var.trace_add("write", self._on_typed)

    @staticmethod
    def _bounds_text(lo, hi):
        return f"{_fmt_num(lo)} ↔ {_fmt_num(hi)}"

    # -- slider moved → push into the text box (guarded) --------------------
    def _on_slider(self, raw):
        if self._guard:
            return
        self._guard = True
        try:
            self.var.set(_fmt_num(float(raw)))   # trace fires: model updates,
        finally:                                  # slider write-back is skipped
            self._guard = False

    # -- text typed → update model, stretch limits, move slider -------------
    def _on_typed(self, *_):
        self.entry.value = self.var.get()
        self.editor.mark_dirty()
        self.editor._schedule_raw_sync()
        if self._guard:
            return
        v = _as_float(self.var.get())
        if v is None:
            return
        lo = float(self.scale.cget("from"))
        hi = float(self.scale.cget("to"))
        stretched = False
        # Dynamic stretching: typing a value outside the current range grows
        # the slider instead of clamping the user's number.
        if v > hi:
            hi = _nice_ceil(v * 1.25)
            stretched = True
        if v < lo:
            lo = -_nice_ceil(abs(v) * 1.25) if v < 0 else 0.0
            stretched = True
        if stretched:
            self.scale.configure(from_=lo, to=hi)
            self.bounds.configure(text=self._bounds_text(lo, hi))
        self._guard = True
        try:
            self.scale.set(v)
        finally:
            self._guard = False


class SuspensionEditor(ConfigEditor):
    """Specialised editor for suspensions.ini.

    * ``TYPE`` keys render as a dropdown of the standard AC suspension types;
      choosing one injects that geometry's default sub-option keys.
    * Numeric values get an interactive slider with 2-way binding.
    """

    def _build_section_body(self, sec: Section, box: ttk.Frame):
        box.columnconfigure(2, weight=1)
        r = 0
        for entry in sec.kv_entries():
            if entry.key.upper() == "TYPE":
                r = self._build_type_row(sec, box, r, entry)
            elif _as_float(entry.value) is not None:
                self._rows.append(_SliderRow(self, box, r, entry, sec))
                r += 1
            else:
                ttk.Label(box, text=entry.key).grid(
                    row=r, column=0, sticky="w", padx=(2, 12), pady=3)
                var = tk.StringVar(value=entry.value)
                ttk.Entry(box, textvariable=var).grid(
                    row=r, column=1, columnspan=3, sticky="ew", pady=3,
                    padx=(0, 4))
                self._bind_var(var, entry)
                r += 1

    # -- TYPE dropdown -------------------------------------------------------
    def _build_type_row(self, sec: Section, box, r: int, entry: Entry) -> int:
        ttk.Label(box, text=entry.key).grid(
            row=r, column=0, sticky="w", padx=(2, 12), pady=3)
        var = tk.StringVar(value=entry.value)
        self._rows.append(var)
        values = list(SUSPENSION_TYPES)
        if entry.value and entry.value not in values:
            values.insert(0, entry.value)
        combo = ttk.Combobox(box, textvariable=var, values=values,
                             state="readonly", width=12)
        combo.grid(row=r, column=1, sticky="w", pady=3)
        hint = ttk.Label(box, text=self._type_hint(entry.value),
                         style="Muted.TLabel")
        hint.grid(row=r, column=2, columnspan=2, sticky="w", padx=(10, 2))

        def on_pick(_event=None):
            entry.value = var.get()
            self.mark_dirty()
            added = self._apply_type_defaults(sec, var.get())
            if added:
                # Sub-option keys were injected → the grid must be rebuilt.
                self.rebuild_visual()
                self._sync_raw_from_doc()
                self.app.set_status(
                    f"[{sec.name}] TYPE={var.get()} — added default sub-options: "
                    + ", ".join(added))
            else:
                hint.configure(text=self._type_hint(var.get()))
                self._schedule_raw_sync()
                self.app.set_status(f"[{sec.name}] TYPE={var.get()}")
        combo.bind("<<ComboboxSelected>>", on_pick)
        return r + 1

    @staticmethod
    def _type_hint(type_name: str) -> str:
        spec = SUSPENSION_TYPE_DEFAULTS.get(type_name.upper())
        return spec.get("hint", "") if spec else ""

    def _apply_type_defaults(self, sec: Section, type_name: str) -> list[str]:
        """Inject the missing geometry keys for the selected suspension type.
        Existing keys are never overwritten. Returns the added key names."""
        spec = SUSPENSION_TYPE_DEFAULTS.get(type_name.upper())
        if not spec:
            return []
        added: list[str] = []
        for key, value in spec.get("keys", {}).items():
            if not sec.has(key):
                sec.set(key, str(value))
                added.append(key)
        for sec_name, keys in spec.get("sections", {}).items():
            target = self.doc.section(sec_name)
            if target is None:
                target = self.doc.add_section(sec_name)
                for key, value in keys.items():
                    target.set(key, str(value))
                added.append(f"[{sec_name}]")
            else:
                for key, value in keys.items():
                    if not target.has(key):
                        target.set(key, str(value))
                        added.append(f"[{sec_name}] {key}")
        return added

    # -- slider ranges -------------------------------------------------------
    def slider_range(self, section: str, key: str, value):
        hint = (SLIDER_HINTS.get(f"{section.upper()}/{key.upper()}")
                or SLIDER_HINTS.get(key.upper()))
        v = 0.0 if value is None else value
        if hint:
            lo, hi = float(hint[0]), float(hint[1])
        elif v > 0:
            lo, hi = 0.0, _nice_ceil(v * 2)
        elif v < 0:
            m = _nice_ceil(abs(v) * 2)
            lo, hi = -m, m
        else:
            lo, hi = 0.0, 1.0
        # Never start with the current value already off the rails.
        if v > hi:
            hi = _nice_ceil(v * 1.25)
        if v < lo:
            lo = -_nice_ceil(abs(v) * 1.25) if v < 0 else 0.0
        return lo, hi

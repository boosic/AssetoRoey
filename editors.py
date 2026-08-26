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
import math
import re
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import messagebox, ttk

from templates import (
    ALL_SUSPENSION_TYPE_KEYS,
    SLIDER_HINTS,
    SLIDER_INT_KEYS,
    SUSPENSION_TYPES,
    SUSPENSION_TYPE_DEFAULTS,
    axle_link_default,
)

MONO_FONT = ("Consolas", 10)
# AC's own INI reader treats ';' and '//' as comments — NOT '#', which can be
# real data ("SCREEN_NAME=Car #12").
_COMMENT_MARKS = (";", "//")


def read_text_any(path: Path) -> tuple[str, str]:
    """Read a config file with encoding detection. Returns (text, encoding)
    where encoding is what should be used to write the file back, so a
    cp1252 file is not silently transcoded to UTF-8 on save. A UTF-8 BOM is
    stripped (AC dislikes BOMs)."""
    data = path.read_bytes()
    for enc, write_enc in (("utf-8-sig", "utf-8"), ("cp1252", "cp1252"),
                           ("latin-1", "latin-1")):
        try:
            return data.decode(enc), write_enc
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1", errors="replace"), "latin-1"


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
        """Update an existing key (case-insensitive) or append a new one.
        With duplicate keys, the LAST one wins in AC's reader, so that is
        the one updated."""
        for e in reversed(self.kv_entries()):
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
        # Split only on real line endings: splitlines() would also break on
        # U+0085/U+000C, which appear as data after a latin-1 fallback read.
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        if lines and lines[-1] == "":
            lines.pop()
        for raw_line in lines:
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
        keys merged (template values win, extra user keys survive).  A value
        may be a ``(value, "; comment")`` tuple to attach an inline comment.
        Returns the names of the sections that were created/updated."""
        touched: list[str] = []
        for name, keys in sections:
            if name.endswith("#"):
                name = self.next_numbered(name[:-1])
                sec = self.add_section(name)
            else:
                sec = self.section(name) or self.add_section(name)
            for key, value in keys.items():
                if isinstance(value, tuple):
                    entry = sec.set(key, str(value[0]))
                    entry.comment = value[1]
                else:
                    sec.set(key, str(value))
            touched.append(sec.name)
        return touched


# ---------------------------------------------------------------------------
#  Small helpers shared by the editors
# ---------------------------------------------------------------------------

def _as_float(value: str):
    """Return the float for a plain scalar value, else None (vectors, text,
    inline LUTs, lut file names, and non-finite/absurd numbers like 'nan',
    'inf' or '1e999' are not sliderable)."""
    v = value.strip()
    if not v or "," in v or "(" in v or "|" in v:
        return None
    try:
        f = float(v)
    except ValueError:
        return None
    if not math.isfinite(f) or abs(f) > 1e12:
        return None
    return f


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
    if not math.isfinite(x) or x <= 0:
        return 1.0
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
        self.encoding = "utf-8"

    def _write_to_disk(self, content: str) -> bool:
        """Write with the encoding the file was read in. Returns False (and
        tells the user) on failure so callers can abort close/exit flows."""
        try:
            self.path.write_text(content, encoding=self.encoding)
        except (OSError, UnicodeError) as exc:
            messagebox.showerror(
                "Save failed", f"Could not save {self.path}:\n{exc}",
                parent=self)
            return False
        return True

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
        content, self.encoding = read_text_any(self.path)
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

    def save(self) -> bool:
        if not self._write_to_disk(self.text.get("1.0", "end-1c")):
            return False
        self.mark_clean()
        self.app.set_status(f"Saved {self.path.name}")
        return True


# ---------------------------------------------------------------------------
#  LUT editor — live graph + raw text
# ---------------------------------------------------------------------------

def _parse_lut(text: str) -> tuple[list[tuple[float, float]], list[str]]:
    """Parse ``input|output`` lines. Returns (points, warnings)."""
    points: list[tuple[float, float]] = []
    warnings: list[str] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith(_COMMENT_MARKS):
            continue
        left, sep, right = line.partition("|")
        if not sep:
            warnings.append(f"line {lineno}: no '|' separator")
            continue
        try:
            x, y = float(left.strip()), float(right.strip())
        except ValueError:
            warnings.append(f"line {lineno}: not numeric")
            continue
        # inf/nan (or absurd magnitudes) would blow up the axis math
        if not all(math.isfinite(v) and abs(v) <= 1e15 for v in (x, y)):
            warnings.append(f"line {lineno}: value out of plottable range")
            continue
        points.append((x, y))
    if any(points[i][0] >= points[i + 1][0] for i in range(len(points) - 1)):
        warnings.append("⚠ inputs are not strictly ascending — AC "
                        "interpolation expects ascending inputs")
    return points, warnings


def _tick_step(span: float) -> float:
    """A 'nice' tick step producing ~5 divisions."""
    if span <= 0 or not math.isfinite(span):
        return 1.0
    raw = span / 5
    mag = 10.0 ** math.floor(math.log10(raw))
    for mult in (1, 2, 2.5, 5, 10):
        if mult * mag >= raw:
            return mult * mag
    return 10 * mag


class LutEditor(BaseEditor):
    """Editor for AC .lut lookup tables: a live line graph of the
    ``input|output`` points next to the editable raw text."""

    PAD_L, PAD_R, PAD_T, PAD_B = 58, 18, 16, 34

    def __init__(self, master, path: Path, app):
        super().__init__(master, path, app)
        self._build_toolbar()
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        graph_tab = ttk.Frame(self.notebook)
        self.notebook.add(graph_tab, text="  Graph  ")
        self.canvas = tk.Canvas(graph_tab, highlightthickness=0,
                                borderwidth=0)
        self.canvas.pack(fill="both", expand=True)
        self.info_var = tk.StringVar()
        ttk.Label(graph_tab, textvariable=self.info_var,
                  style="Muted.TLabel", padding=(8, 3)).pack(
            side="bottom", fill="x")

        raw_host = ttk.Frame(self.notebook)
        self.notebook.add(raw_host, text="  Raw Text  ")
        wrapper = self._make_text(raw_host)
        wrapper.pack(fill="both", expand=True)
        self.text = wrapper.text

        content, self.encoding = read_text_any(self.path)
        self.text.insert("1.0", content)
        self.text.edit_reset()
        self.text.edit_modified(False)
        self.text.bind("<<Modified>>", self._on_modified)

        self.points: list[tuple[float, float]] = []
        self.warnings: list[str] = []
        self._pending_refresh = None
        self._hover_index = None

        self.canvas.bind("<Configure>", lambda e: self._redraw())
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", lambda e: self._set_hover(None))
        self.notebook.bind("<<NotebookTabChanged>>",
                           lambda e: self._redraw())
        self.app.theme.register_redraw(self.canvas, self._redraw)
        self._refresh_from_text()

    # -- text plumbing ------------------------------------------------------
    def _on_modified(self, _event=None):
        if not self.text.edit_modified():
            return
        self.text.edit_modified(False)
        self.mark_dirty()
        if self._pending_refresh is not None:
            self.after_cancel(self._pending_refresh)
        self._pending_refresh = self.after(300, self._refresh_from_text)

    def _refresh_from_text(self):
        self._pending_refresh = None
        self.points, self.warnings = _parse_lut(
            self.text.get("1.0", "end-1c"))
        self._hover_index = None
        self._redraw()

    def save(self) -> bool:
        if not self._write_to_disk(self.text.get("1.0", "end-1c")):
            return False
        self.mark_clean()
        self.app.set_status(f"Saved {self.path.name}")
        return True

    # -- drawing ------------------------------------------------------------
    def _bounds(self):
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)
        if xmax - xmin <= 0:
            xmin, xmax = xmin - 1, xmax + 1
        if ymax - ymin <= 0:
            ymin, ymax = ymin - 1, ymax + 1
        return xmin, xmax, ymin, ymax

    def _to_px(self, x, y, geo):
        xmin, xmax, ymin, ymax, w, h = geo
        px = self.PAD_L + (x - xmin) / (xmax - xmin) * \
            (w - self.PAD_L - self.PAD_R)
        py = h - self.PAD_B - (y - ymin) / (ymax - ymin) * \
            (h - self.PAD_T - self.PAD_B)
        return px, py

    def _geo(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 80 or h < 60:
            return None
        xmin, xmax, ymin, ymax = self._bounds()
        return (xmin, xmax, ymin, ymax, w, h)

    def _redraw(self):
        c = self.canvas
        if not c.winfo_exists():
            return
        p = self.app.theme.palette()
        c.configure(background=p["field"])
        c.delete("all")
        info = f"{len(self.points)} points"
        if not self.points:
            c.create_text(c.winfo_width() // 2 or 100, 40,
                          text="No data points — add input|output lines in "
                               "the Raw Text tab",
                          fill=p["muted"], anchor="center")
            self.info_var.set("  ".join([info] + self.warnings))
            return
        geo = self._geo()
        if geo is None:
            return
        xmin, xmax, ymin, ymax, w, h = geo

        # grid + tick labels
        for step, lo, hi, vertical in (
                (_tick_step(xmax - xmin), xmin, xmax, True),
                (_tick_step(ymax - ymin), ymin, ymax, False)):
            tick = math.ceil(lo / step) * step
            guard = 0
            while tick <= hi + step * 1e-9 and (guard := guard + 1) < 400:
                if vertical:
                    px, _ = self._to_px(tick, ymin, geo)
                    c.create_line(px, self.PAD_T, px, h - self.PAD_B,
                                  fill=p["trough"])
                    c.create_text(px, h - self.PAD_B + 12,
                                  text=_fmt_num(tick), fill=p["muted"],
                                  font=("TkDefaultFont", 8))
                else:
                    _, py = self._to_px(xmin, tick, geo)
                    c.create_line(self.PAD_L, py, w - self.PAD_R, py,
                                  fill=p["trough"])
                    c.create_text(self.PAD_L - 8, py, text=_fmt_num(tick),
                                  fill=p["muted"], anchor="e",
                                  font=("TkDefaultFont", 8))
                tick += step
        # zero axis emphasis
        if ymin < 0 < ymax:
            _, py = self._to_px(xmin, 0, geo)
            c.create_line(self.PAD_L, py, w - self.PAD_R, py,
                          fill=p["muted"])
        c.create_rectangle(self.PAD_L, self.PAD_T, w - self.PAD_R,
                           h - self.PAD_B, outline=p["border"])

        # polyline + markers
        pixels = [self._to_px(x, y, geo) for x, y in self.points]
        if len(pixels) > 1:
            c.create_line(*[v for px in pixels for v in px],
                          fill=p["accent"], width=2)
        for px, py in pixels:
            c.create_oval(px - 3, py - 3, px + 3, py + 3,
                          fill=p["accent"], outline=p["field"])

        # always-visible point value labels (Settings ▸ LUT graphs)
        if self.app.settings.get("lut_point_labels", True):
            if len(self.points) <= 60:
                for (x, y), (px, py) in zip(self.points, pixels):
                    anchor = "s" if py > self.PAD_T + 20 else "n"
                    offset = -7 if anchor == "s" else 7
                    c.create_text(
                        min(max(px, self.PAD_L + 12), w - self.PAD_R - 12),
                        py + offset,
                        text=f"{_fmt_num(x)}|{_fmt_num(y)}",
                        fill=p["muted"], anchor=anchor,
                        font=("TkDefaultFont", 7))
            else:
                info += "  (point labels hidden: >60 points)"

        self._draw_hover(geo)
        rng = (f"X {_fmt_num(xmin)} … {_fmt_num(xmax)}   "
               f"Y {_fmt_num(ymin)} … {_fmt_num(ymax)}")
        self.info_var.set("   ".join([info, rng] + self.warnings))

    # -- hover readout ------------------------------------------------------
    def _on_motion(self, event):
        geo = self._geo()
        if geo is None or not self.points:
            return
        best, best_d = None, 196.0    # 14px radius
        for i, (x, y) in enumerate(self.points):
            px, py = self._to_px(x, y, geo)
            d = (px - event.x) ** 2 + (py - event.y) ** 2
            if d < best_d:
                best, best_d = i, d
        self._set_hover(best)

    def _set_hover(self, index):
        if index == self._hover_index:
            return
        self._hover_index = index
        geo = self._geo()
        if geo is not None:
            self._draw_hover(geo)

    def _draw_hover(self, geo):
        c = self.canvas
        c.delete("hover")
        if self._hover_index is None or \
                self._hover_index >= len(self.points):
            return
        p = self.app.theme.palette()
        x, y = self.points[self._hover_index]
        px, py = self._to_px(x, y, geo)
        c.create_oval(px - 5, py - 5, px + 5, py + 5, outline=p["accent"],
                      width=2, tags="hover")
        label = f"{_fmt_num(x)} | {_fmt_num(y)}"
        tx = min(max(px + 10, self.PAD_L + 30), geo[4] - self.PAD_R - 40)
        ty = max(py - 14, self.PAD_T + 8)
        text_id = c.create_text(tx, ty, text=label, fill=p["fg"],
                                anchor="w", tags="hover",
                                font=("TkDefaultFont", 9, "bold"))
        box = c.bbox(text_id)
        rect = c.create_rectangle(box[0] - 4, box[1] - 2, box[2] + 4,
                                  box[3] + 2, fill=p["panel"],
                                  outline=p["border"], tags="hover")
        c.tag_raise(text_id, rect)


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
        text, self.encoding = read_text_any(self.path)
        self.doc = ConfigDocument.parse(text)

        self._rows = []               # per-row state (see _RowBinding)
        self._raw_dirty = False       # raw tab has edits not yet in self.doc
        self._sync_guard = False      # suppress <<Modified>> during programmatic set
        self._pending_sync = None     # debounce id for visual->raw sync

        self._build_toolbar([("＋ Section", self._add_section_dialog),
                             ("↻ Reload", self.reload_from_disk)])
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
            # Programmatic replaces must never sit on the user's undo stack:
            # otherwise Ctrl+Z on the raw tab could blank the whole buffer.
            self.raw_text.edit_reset()
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
        # Cancel-first so direct callers can never leave an orphaned timer.
        if self._pending_sync is not None:
            self.after_cancel(self._pending_sync)
        self._pending_sync = None
        self._set_raw(self.doc.serialize())

    def _flush_raw_edits(self):
        """If the user hand-edited the raw tab, fold it back into the model."""
        if self._pending_sync is not None:      # visual edits still queued
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
                self._sync_raw_from_doc()

    # --------------------------------------------------------------- saving
    def reload_from_disk(self):
        if self.dirty and not messagebox.askyesno(
                "Reload", f"Discard unsaved changes to {self.path.name}?",
                parent=self):
            return
        text, self.encoding = read_text_any(self.path)
        self.doc = ConfigDocument.parse(text)
        self.rebuild_visual()
        self._set_raw(self.doc.serialize())
        self.mark_clean()
        self.app.set_status(f"Reloaded {self.path.name}")

    def save(self) -> bool:
        if self._raw_dirty:
            # Raw tab holds the newest edits — save it verbatim.
            content = self.raw_text.get("1.0", "end-1c")
            self.doc = ConfigDocument.parse(content)
            self._raw_dirty = False
            self.rebuild_visual()
        else:
            if self._pending_sync is not None:
                self._sync_raw_from_doc()
            content = self.doc.serialize()
            self._set_raw(content)
        if not self._write_to_disk(content):
            return False
        self.mark_clean()
        self.app.set_status(f"Saved {self.path.name}")
        return True

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
        self._vector_vars = {}
        host = self.visual_tab.interior
        host.columnconfigure(0, weight=1)
        for row, sec in enumerate(self.doc.sections):
            box = self._make_section_box(host, sec, row)
            self._build_section_body(sec, box)
        if not self.doc.sections:
            empty = ttk.Frame(host)
            empty.grid(padx=14, pady=14, sticky="w")
            ttk.Label(empty, text="No [SECTION] blocks found.",
                      style="Muted.TLabel").pack(anchor="w")
            ttk.Button(empty, text="＋ Add Section",
                       command=self._add_section_dialog).pack(
                anchor="w", pady=(8, 0))
        self.visual_tab._on_interior_configure()

    def _make_section_box(self, host, sec: Section, row: int) -> ttk.Frame:
        """Bordered section box whose header carries a small ⋮ options menu."""
        head = ttk.Frame(host)
        title = ttk.Label(head, text=f"[{sec.name}]", style="Title.TLabel")
        title.pack(side="left")
        dots = ttk.Button(head, text="⋮", width=2, style="Toolbutton")
        dots.configure(command=lambda: self._post_section_menu(sec, dots))
        dots.pack(side="left", padx=(6, 0))
        box = ttk.LabelFrame(host, labelwidget=head, padding=(10, 6))
        box.grid(row=row, column=0, sticky="ew", padx=10, pady=(8, 2))
        self._attach_context(box, sec, None)
        self._attach_context(title, sec, None)
        return box

    def _build_section_body(self, sec: Section, box: ttk.Frame):
        """Default layout: clean 2-column grid of key labels + value entries.
        3-component numeric values render as labelled X/Y/Z fields."""
        box.columnconfigure(1, weight=1)
        r = 0
        for entry in sec.kv_entries():
            label = ttk.Label(box, text=entry.key)
            label.grid(row=r, column=0, sticky="w", padx=(2, 12), pady=2)
            self._attach_context(label, sec, entry)
            if self._vector_parts(entry.value):
                self._build_vector_row(box, r, sec, entry)
            else:
                var = tk.StringVar(value=entry.value)
                widget = ttk.Entry(box, textvariable=var)
                widget.grid(row=r, column=1, sticky="ew", pady=2)
                self._bind_var(var, entry)
                self._attach_context(widget, sec, entry)
            if entry.comment:
                r += 1
                ttk.Label(box, text=entry.comment.lstrip(";/ ").strip(),
                          style="Muted.TLabel").grid(
                    row=r, column=1, sticky="w", padx=2)
            r += 1
        if not sec.kv_entries():
            self._empty_section_hint(box, sec, span=2)

    def _empty_section_hint(self, box, sec: Section, span: int):
        """A keyless LabelFrame renders ~1px tall — give empty sections a
        visible body that is also a right-click target."""
        hint = ttk.Label(box, text="(empty section — right-click here or "
                                   "use the ⋮ menu to add keys)",
                         style="Muted.TLabel")
        hint.grid(row=0, column=0, columnspan=span, sticky="w",
                  padx=2, pady=4)
        self._attach_context(hint, sec, None)

    # ------------------------------------------------------ vector values
    @staticmethod
    def _vector_parts(value: str):
        """Return ['x','y','z'] when the value is a 3-component numeric
        vector, else None."""
        parts = [p.strip() for p in value.split(",")]
        if len(parts) != 3:
            return None
        for p in parts:
            try:
                float(p)
            except ValueError:
                return None
        return parts

    def _build_vector_row(self, box, r: int, sec: Section, entry: Entry,
                          column: int = 1, span: int = 1):
        parts = self._vector_parts(entry.value)
        holder = ttk.Frame(box)
        holder.grid(row=r, column=column, columnspan=span, sticky="w", pady=2)
        axis_vars: list[tk.StringVar] = []
        for i, (axis, part) in enumerate(zip("XYZ", parts)):
            ttk.Label(holder, text=axis, style="Muted.TLabel").pack(
                side="left", padx=((0 if i == 0 else 10), 3))
            var = tk.StringVar(value=part)
            axis_vars.append(var)
            field = ttk.Entry(holder, textvariable=var, width=10)
            field.pack(side="left")
            self._attach_context(field, sec, entry)
        self._rows.extend(axis_vars)
        # introspection hook (tests/tooling): axis vars by (SECTION, KEY)
        self._vector_vars[(sec.name.upper(), entry.key.upper())] = axis_vars

        def on_write(*_):
            entry.value = ",".join(
                v.get().replace("\n", " ").replace("\r", " ").strip()
                for v in axis_vars)
            self.mark_dirty()
            self._schedule_raw_sync()
        for var in axis_vars:
            var.trace_add("write", on_write)

    # --------------------------------------------- row / section options menu
    def _attach_context(self, widget, sec: Section, entry: Entry | None):
        widget.bind("<Button-3>", lambda e: self._post_menu(
            self._build_options_menu(sec, entry), e.x_root, e.y_root))

    def _post_section_menu(self, sec: Section, button):
        self._post_menu(self._build_options_menu(sec, None),
                        button.winfo_rootx(),
                        button.winfo_rooty() + button.winfo_height())

    def _post_menu(self, menu: tk.Menu, x_root: int, y_root: int):
        try:
            menu.tk_popup(x_root, y_root)
        finally:
            menu.grab_release()

    def _build_options_menu(self, sec: Section, entry: Entry | None) -> tk.Menu:
        """Small options menu (right-click on a row, or the ⋮ button on a
        section box). One reusable Menu per editor, repopulated per post —
        add future actions here."""
        menu = getattr(self, "_options_menu", None)
        if menu is None or not menu.winfo_exists():
            menu = self._options_menu = tk.Menu(self, tearoff=0)
            self.app.theme.register_menu(menu)
        menu.delete(0, "end")
        for child in menu.winfo_children():     # last post's submenus
            child.destroy()
        if entry is not None:
            menu.add_command(
                label=f"Remove  {entry.key}",
                command=lambda: self.remove_key(sec, entry))
        if sec.kv_entries():
            # Discoverable per-key removal, also reachable from the ⋮ button
            sub = tk.Menu(menu, tearoff=0)
            self.app.theme.register_menu(sub)
            for e in sec.kv_entries():
                sub.add_command(
                    label=e.key,
                    command=lambda s=sec, en=e: self.remove_key(s, en))
            menu.add_cascade(label="Remove key from section  ▸", menu=sub)
        menu.add_separator()
        menu.add_command(
            label=f"Add key to [{sec.name}]…",
            command=lambda: self._add_key_dialog(sec))
        menu.add_command(
            label="Add section…",
            command=self._add_section_dialog)
        menu.add_separator()
        menu.add_command(
            label=f"Remove section [{sec.name}]",
            command=lambda: self.remove_section(sec))
        return menu

    def _refresh_after_model_change(self, status: str | None = None):
        self.rebuild_visual()
        self._sync_raw_from_doc()
        self.mark_dirty()
        if status:
            self.app.set_status(status)

    def remove_key(self, sec: Section, entry: Entry):
        try:
            sec.entries.remove(entry)
        except ValueError:
            return
        self._refresh_after_model_change(
            f"Removed {entry.key} from [{sec.name}]  (unsaved)")

    def remove_section(self, sec: Section):
        if sec in self.doc.sections:
            self.doc.sections.remove(sec)
            self._refresh_after_model_change(
                f"Removed section [{sec.name}]  (unsaved)")

    def add_new_section(self, name: str) -> Section | None:
        name = name.strip().strip("[]").strip().upper().replace(" ", "_")
        if not name:
            return None
        existing = self.doc.section(name)
        if existing is not None:
            self.app.set_status(f"[{name}] already exists")
            return existing
        sec = self.doc.add_section(name)
        self._refresh_after_model_change(
            f"Added section [{name}]  (unsaved)")
        # The new section lands at the bottom of the grid — bring it on
        # screen instead of leaving the view at the top.
        self.update_idletasks()
        self.visual_tab.canvas.yview_moveto(1.0)
        return sec

    def _add_section_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Add section")
        dlg.configure(bg=self.app.theme.palette()["bg"])
        dlg.transient(self.winfo_toplevel())
        dlg.resizable(False, False)
        frame = ttk.Frame(dlg, padding=14)
        frame.pack(fill="both", expand=True)
        name_var = tk.StringVar()
        ttk.Label(frame, text="Section name").grid(row=0, column=0,
                                                   sticky="w", padx=(0, 10))
        name_entry = ttk.Entry(frame, textvariable=name_var, width=26)
        name_entry.grid(row=0, column=1)
        ttk.Label(frame, style="Muted.TLabel",
                  text="e.g. TURBO_1, HEAVE_FRONT, WING_2 — brackets "
                       "optional").grid(row=1, column=0, columnspan=2,
                                        sticky="w", pady=(4, 8))

        def ok(_event=None):
            if self.add_new_section(name_var.get()) is not None:
                dlg.destroy()

        buttons = ttk.Frame(frame)
        buttons.grid(row=2, column=0, columnspan=2, sticky="e")
        ttk.Button(buttons, text="Cancel",
                   command=dlg.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(buttons, text="Add", style="Accent.TButton",
                   command=ok).pack(side="right")
        dlg.bind("<Return>", ok)
        dlg.bind("<Escape>", lambda e: dlg.destroy())
        dlg.wait_visibility()
        dlg.grab_set()
        name_entry.focus_set()
        self.app.sync_titlebar(dlg)

    def _add_key_dialog(self, sec: Section):
        dlg = tk.Toplevel(self)
        dlg.title(f"Add key to [{sec.name}]")
        dlg.configure(bg=self.app.theme.palette()["bg"])
        dlg.transient(self.winfo_toplevel())
        dlg.resizable(False, False)
        frame = ttk.Frame(dlg, padding=14)
        frame.pack(fill="both", expand=True)
        key_var, val_var = tk.StringVar(), tk.StringVar()
        ttk.Label(frame, text="Key").grid(row=0, column=0, sticky="w",
                                          padx=(0, 10), pady=3)
        key_entry = ttk.Entry(frame, textvariable=key_var, width=26)
        key_entry.grid(row=0, column=1, pady=3)
        ttk.Label(frame, text="Value").grid(row=1, column=0, sticky="w",
                                            padx=(0, 10), pady=3)
        ttk.Entry(frame, textvariable=val_var, width=26).grid(
            row=1, column=1, pady=3)

        def ok(_event=None):
            key = key_var.get().strip().upper().replace(" ", "_")
            if not key:
                return
            sec.set(key, val_var.get().strip())
            dlg.destroy()
            self._refresh_after_model_change(
                f"Added {key} to [{sec.name}]  (unsaved)")

        buttons = ttk.Frame(frame)
        buttons.grid(row=2, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(buttons, text="Cancel",
                   command=dlg.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(buttons, text="Add", style="Accent.TButton",
                   command=ok).pack(side="right")
        dlg.bind("<Return>", ok)
        dlg.bind("<Escape>", lambda e: dlg.destroy())
        dlg.wait_visibility()
        dlg.grab_set()
        key_entry.focus_set()
        self.app.sync_titlebar(dlg)

    def _bind_var(self, var: tk.StringVar, entry: Entry):
        # Keep a hard reference: a StringVar only referenced from closures is
        # a collectible cycle, and its finalizer would unset the Tcl variable.
        self._rows.append(var)

        def on_write(*_):
            # A pasted newline would shatter the KEY=VALUE line structure.
            entry.value = var.get().replace("\n", " ").replace("\r", " ")
            self.mark_dirty()
            self._schedule_raw_sync()
        var.trace_add("write", on_write)


# ---------------------------------------------------------------------------
#  Suspension editor — BeamNG-style tuning layout
# ---------------------------------------------------------------------------

class _SliderRow:
    """2-way binding between one Entry and one Scale, loop-protected.

    ``on_commit`` (optional) fires when the user finishes an interaction —
    slider release, Enter, or leaving the field — for values that trigger
    structural updates (e.g. LINK_COUNT re-generating axle links)."""

    def __init__(self, editor: "SuspensionEditor", box, row: int,
                 entry: Entry, sec: Section, on_commit=None):
        self.editor = editor
        self.entry = entry
        self._guard = False

        value = _as_float(entry.value)
        lo, hi = editor.slider_range(sec.name, entry.key, value)
        self.var = tk.StringVar(value=entry.value)

        self.label = ttk.Label(box, text=entry.key)
        self.label.grid(row=row, column=0, sticky="w", padx=(2, 12), pady=3)
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
        if on_commit is not None:
            self.scale.bind("<ButtonRelease-1>", lambda e: on_commit())
            self.field.bind("<Return>", lambda e: on_commit())
            self.field.bind("<FocusOut>", lambda e: on_commit())

    @staticmethod
    def _bounds_text(lo, hi):
        return f"{_fmt_num(lo)} ↔ {_fmt_num(hi)}"

    # -- slider moved → push into the text box (guarded) --------------------
    def _on_slider(self, raw):
        if self._guard:
            return
        self._guard = True
        try:
            v = float(raw)
            if self.entry.key.upper() in SLIDER_INT_KEYS:
                text = str(int(round(v)))        # LINK_COUNT=3.37 is nonsense
            else:
                text = _fmt_num(v)
            self.var.set(text)                   # trace fires: model updates,
        finally:                                  # slider write-back is skipped
            self._guard = False

    # -- text typed → update model, stretch limits, move slider -------------
    def _on_typed(self, *_):
        self.entry.value = self.var.get().replace("\n", " ").replace("\r", " ")
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
      switching type removes the old type's geometry keys, injects the new
      type's, and manages the auxiliary [AXLE] section. Removed values are
      stashed (per project, until the project is closed) and restored when
      switching back.
    * ``LINK_COUNT`` in [AXLE] regenerates the J{i}_CAR/J{i}_AXLE link pairs.
    * Numeric values get an interactive slider with 2-way binding; vector
      values get X/Y/Z fields.
    """

    _axle_sync_guard = False

    def _build_section_body(self, sec: Section, box: ttk.Frame):
        box.columnconfigure(2, weight=1)
        is_axle_box = sec.name.upper() == "AXLE"
        r = 0
        for entry in sec.kv_entries():
            if entry.key.upper() == "TYPE":
                r = self._build_type_row(sec, box, r, entry)
                continue
            if _as_float(entry.value) is not None:
                on_commit = None
                if is_axle_box and entry.key.upper() == "LINK_COUNT":
                    on_commit = lambda s=sec: self._sync_axle_links(s)
                row = _SliderRow(self, box, r, entry, sec,
                                 on_commit=on_commit)
                self._rows.append(row)
                self._attach_context(row.label, sec, entry)
                self._attach_context(row.field, sec, entry)
            elif self._vector_parts(entry.value):
                label = ttk.Label(box, text=entry.key)
                label.grid(row=r, column=0, sticky="w", padx=(2, 12), pady=3)
                self._attach_context(label, sec, entry)
                self._build_vector_row(box, r, sec, entry, column=1, span=3)
            else:
                label = ttk.Label(box, text=entry.key)
                label.grid(row=r, column=0, sticky="w", padx=(2, 12), pady=3)
                self._attach_context(label, sec, entry)
                var = tk.StringVar(value=entry.value)
                field = ttk.Entry(box, textvariable=var)
                field.grid(row=r, column=1, columnspan=3, sticky="ew",
                           pady=3, padx=(0, 4))
                self._bind_var(var, entry)
                self._attach_context(field, sec, entry)
            r += 1
        if not sec.kv_entries():
            self._empty_section_hint(box, sec, span=4)

    # -- TYPE dropdown -------------------------------------------------------
    def _build_type_row(self, sec: Section, box, r: int, entry: Entry) -> int:
        label = ttk.Label(box, text=entry.key)
        label.grid(row=r, column=0, sticky="w", padx=(2, 12), pady=3)
        self._attach_context(label, sec, entry)
        var = tk.StringVar(value=entry.value)
        self._rows.append(var)
        values = list(SUSPENSION_TYPES)
        if entry.value and entry.value not in values:
            values.insert(0, entry.value)
        combo = ttk.Combobox(box, textvariable=var, values=values,
                             state="readonly", width=12)
        combo.grid(row=r, column=1, sticky="w", pady=3)
        # The TCombobox class binding spins the value on mouse wheel — over a
        # scrollable grid that would silently change the suspension TYPE.
        # Scroll the grid instead and stop the class binding with "break".
        def wheel_guard(event):
            ScrollableFrame._on_wheel_global(event)
            return "break"
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            combo.bind(seq, wheel_guard)
        self.app.theme.register_combobox(combo)
        hint = ttk.Label(box, text=self._type_hint(entry.value),
                         style="Muted.TLabel")
        hint.grid(row=r, column=2, columnspan=2, sticky="w", padx=(10, 2))

        def on_pick(_event=None):
            new_type = var.get()
            if new_type.upper() == entry.value.strip().upper():
                return
            entry.value = new_type
            added, removed = self._switch_type(sec, entry, new_type)
            parts = [f"[{sec.name}] TYPE={new_type}"]
            if added:
                parts.append("added: " + ", ".join(added))
            if removed:
                parts.append("removed (restorable until the project is "
                             "closed): " + ", ".join(removed))
            self._refresh_after_model_change("  —  ".join(parts))
        combo.bind("<<ComboboxSelected>>", on_pick)
        return r + 1

    @staticmethod
    def _type_hint(type_name: str) -> str:
        spec = SUSPENSION_TYPE_DEFAULTS.get(type_name.upper())
        return spec.get("hint", "") if spec else ""

    # ----------------------------------------------------- type switching
    def _stash(self) -> dict:
        """Per-project stash of removed keys/sections, held on the app so it
        survives tab close and save — cleared when the project is closed."""
        store = getattr(self.app, "type_stash", None)
        if store is None:
            store = self.app.type_stash = {}
        try:
            file_key = str(self.path.resolve())
        except OSError:
            file_key = str(self.path)
        return store.setdefault(file_key, {})

    def _switch_type(self, sec: Section, type_entry: Entry,
                     new_type: str) -> tuple[list[str], list[str]]:
        """Swap [sec] to the new suspension type: remove keys owned by other
        types (stashing their values), insert the new type's keys (restoring
        stashed values over defaults), and create/remove the [AXLE] helper
        section as needed. Returns (added, removed) names."""
        new_type = new_type.strip().upper()
        stash = self._stash()
        spec = SUSPENSION_TYPE_DEFAULTS.get(new_type, {})
        keep = {k.upper() for k in spec.get("keys", {})}
        added: list[str] = []
        removed: list[str] = []

        # 1. remove geometry keys the new type does not use
        for e in list(sec.kv_entries()):
            key_u = e.key.upper()
            if key_u in ALL_SUSPENSION_TYPE_KEYS and key_u not in keep:
                stash[("KEY", sec.name.upper(), key_u)] = \
                    (e.key, e.value, e.comment)
                sec.entries.remove(e)
                removed.append(e.key)

        # 2. insert the new type's keys right after TYPE, stash values first
        try:
            insert_at = sec.entries.index(type_entry) + 1
        except ValueError:
            insert_at = len(sec.entries)
        for key, default in spec.get("keys", {}).items():
            if sec.has(key):
                continue
            stashed = stash.pop(("KEY", sec.name.upper(), key.upper()), None)
            if stashed is not None:
                e = Entry("kv", stashed[0], stashed[1], stashed[2])
            else:
                e = Entry("kv", key, str(default))
            sec.entries.insert(insert_at, e)
            insert_at += 1
            added.append(key)

        # 3. auxiliary sections (the [AXLE] link definition)
        for name, keys in spec.get("sections", {}).items():
            if self.doc.section(name) is not None:
                continue
            pos = self.doc.sections.index(sec) + 1
            stashed_sec = stash.pop(("SECTION", name.upper()), None)
            if stashed_sec is not None:
                self.doc.sections.insert(pos, stashed_sec)
            else:
                new_sec = Section(name)
                for key, value in keys.items():
                    new_sec.set(key, str(value))
                self.doc.sections.insert(pos, new_sec)
            added.append(f"[{name}]")

        # 4. drop [AXLE] once no axle uses TYPE=AXLE any more
        if new_type != "AXLE":
            still_used = any(
                s.get("TYPE", "").strip().upper() == "AXLE"
                for s in self.doc.sections)
            axle_sec = self.doc.section("AXLE")
            if axle_sec is not None and not still_used:
                stash[("SECTION", "AXLE")] = axle_sec
                self.doc.sections.remove(axle_sec)
                removed.append("[AXLE]")
        return added, removed

    # ------------------------------------------------- axle link management
    def _sync_axle_links(self, sec: Section):
        """Make the J{i}_CAR/J{i}_AXLE pairs in [AXLE] match LINK_COUNT.
        Extra links are stashed; restored links get their stashed values."""
        if self._axle_sync_guard:
            return
        count = _as_float(sec.get("LINK_COUNT", ""))
        if count is None:
            return
        n = max(1, min(int(round(count)), 8))
        stash = self._stash()
        j_re = re.compile(r"J(\d+)_(CAR|AXLE)", re.IGNORECASE)

        lc_entry = next((e for e in sec.kv_entries()
                         if e.key.upper() == "LINK_COUNT"), None)
        if lc_entry is None:
            return

        # Pre-check: is any change actually needed? A plain slider click or
        # tab-through must not silently re-splice (reorder) the section.
        present = {(int(m.group(1)), m.group(2).upper())
                   for e in sec.kv_entries()
                   if (m := j_re.fullmatch(e.key))}
        wanted = {(i, suffix) for i in range(n)
                  for suffix in ("CAR", "AXLE")}
        if present == wanted and lc_entry.value.strip() == str(n):
            return
        if present == wanted:       # only LINK_COUNT itself needs normalising
            lc_entry.value = str(n)
            self._refresh_after_model_change(f"[{sec.name}] LINK_COUNT={n}")
            return

        existing: dict[tuple[int, str], Entry] = {}
        for e in list(sec.kv_entries()):
            m = j_re.fullmatch(e.key)
            if m:
                existing[(int(m.group(1)), m.group(2).upper())] = e
                sec.entries.remove(e)

        added, removed = [], []
        block: list[Entry] = []
        for i in range(n):
            for suffix in ("CAR", "AXLE"):
                e = existing.pop((i, suffix), None)
                if e is None:
                    key = f"J{i}_{suffix}"
                    stashed = stash.pop(("KEY", sec.name.upper(), key), None)
                    if stashed is not None:
                        e = Entry("kv", stashed[0], stashed[1], stashed[2])
                    else:
                        car, axle = axle_link_default(i)
                        e = Entry("kv", key,
                                  car if suffix == "CAR" else axle)
                    added.append(key)
                block.append(e)
        for (_i, _suffix), e in existing.items():
            stash[("KEY", sec.name.upper(), e.key.upper())] = \
                (e.key, e.value, e.comment)
            removed.append(e.key)

        normalized = lc_entry.value.strip() != str(n)
        lc_entry.value = str(n)
        idx = sec.entries.index(lc_entry) + 1
        sec.entries[idx:idx] = block

        if added or removed or normalized:
            self._axle_sync_guard = True
            try:
                status = [f"[{sec.name}] LINK_COUNT={n}"]
                if added:
                    status.append("added: " + ", ".join(added))
                if removed:
                    status.append("removed (restorable): "
                                  + ", ".join(removed))
                self._refresh_after_model_change("  —  ".join(status))
            finally:
                self._axle_sync_guard = False

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

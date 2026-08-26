"""Module 4 — Main Application Shell & Styling.

Provides:
  * ``ThemeManager``    — light/dark theming for ttk + classic tk widgets.
  * ``ClosableNotebook``— workspace tabs with a working per-tab close button.
  * ``FileExplorer``    — left-pane project tree.
  * ``ACModStudio``     — the main window: split layout, routing, the
                          "ADD COMPONENT" template injector, dialogs.
"""

from __future__ import annotations

import json
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import subprocess
import sys

from editors import (BaseEditor, ConfigEditor, LutEditor, RawTextEditor,
                     ScrollableFrame, SuspensionEditor)
from generator import generate_car_project, sanitize_car_id
from templates import (APP_TITLE, COMPONENT_LIBRARY, CONFIG_TEMPLATES,
                       MINIMAL_CONFIG_FILES, MINIMAL_PLACEHOLDER_FILES,
                       PLACEHOLDER_FILES)


def _enable_windows_system_menus():
    """Let Windows draw this app's native menu bar and popup menus in the
    system theme (dark menus when Windows is dark). Uses the well-known
    uxtheme ordinals; silently no-ops when unavailable."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        uxtheme = ctypes.WinDLL("uxtheme")
        set_preferred_app_mode = uxtheme[135]
        set_preferred_app_mode.argtypes = [ctypes.c_int]
        set_preferred_app_mode(1)      # 1 = AllowDark: follow the system
        uxtheme[136]()                 # FlushMenuThemes
    except Exception:
        pass


def apply_windows_titlebar(window, dark: bool):
    """Ask DWM for a dark or light native title bar (Windows 10 1809+).
    Tk cannot draw the OS frame itself; elsewhere this is a no-op."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id()) \
            or window.winfo_id()
        value = ctypes.c_int(1 if dark else 0)
        for attribute in (20, 19):     # DWMWA_USE_IMMERSIVE_DARK_MODE
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attribute, ctypes.byref(value),
                    ctypes.sizeof(value)) == 0:
                break
        # SWP_NOSIZE|SWP_NOMOVE|SWP_NOZORDER|SWP_FRAMECHANGED: repaint the
        # frame in place so the change shows immediately.
        ctypes.windll.user32.SetWindowPos(
            hwnd, 0, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0004 | 0x0020)
    except Exception:
        pass


def detect_system_theme() -> str:
    """Best-effort OS dark/light detection (Windows registry, macOS
    defaults, GNOME gsettings). Falls back to light."""
    try:
        if sys.platform == "win32":
            import winreg
            key_path = (r"Software\Microsoft\Windows\CurrentVersion"
                        r"\Themes\Personalize")
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return "light" if value else "dark"
        if sys.platform == "darwin":
            out = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True, text=True, timeout=2)
            return "dark" if "dark" in out.stdout.lower() else "light"
        out = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface",
             "color-scheme"],
            capture_output=True, text=True, timeout=2)
        if "dark" in out.stdout.lower():
            return "dark"
    except Exception:
        pass
    return "light"

SETTINGS_PATH = Path.home() / ".ac_mod_studio.json"

PALETTES = {
    "light": dict(
        bg="#ececec", panel="#dfdfdf", fg="#1d1d1d", muted="#6c6c6c",
        field="#ffffff", border="#b5b5b5", select="#cde4f7",
        accent="#0a5dc2", accent_fg="#ffffff", accent_hover="#2b79d8",
        tab="#d3d3d3", trough="#c9c9c9",
    ),
    "dark": dict(
        bg="#1e1f22", panel="#2b2d31", fg="#e6e6e6", muted="#9aa0a6",
        field="#26282c", border="#3d4046", select="#264f78",
        accent="#4da3ff", accent_fg="#10141a", accent_hover="#6cb4ff",
        tab="#26282c", trough="#37393f",
    ),
}


# ---------------------------------------------------------------------------
#  Theme manager
# ---------------------------------------------------------------------------

class ThemeManager:
    """Applies a palette to every ttk style plus the classic tk widgets
    (Text, Menu) that ttk cannot style. Widgets register themselves so a
    toggle mid-session restyles everything live."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.style = ttk.Style(root)
        self.style.theme_use("clam")
        self.mode = "light"
        self._texts: list[tk.Text] = []
        self._menus: list[tk.Menu] = []
        self._combos: list[ttk.Combobox] = []
        self._redraws: list[tuple] = []     # (widget, callback) pairs

    def palette(self) -> dict:
        """The active palette — for widgets that draw themselves (canvases)."""
        return PALETTES[self.mode]

    def register_redraw(self, widget, callback):
        """Call ``callback`` after every theme change while ``widget`` lives
        (used by canvas-drawn views like the LUT graph)."""
        self._redraws = [(w, f) for w, f in self._redraws
                         if self._alive(w)]
        self._redraws.append((widget, callback))

    @staticmethod
    def _alive(widget) -> bool:
        try:
            return bool(widget.winfo_exists())
        except tk.TclError:
            return False

    @staticmethod
    def _prune(widgets: list) -> list:
        alive = []
        for w in widgets:
            try:
                if w.winfo_exists():
                    alive.append(w)
            except tk.TclError:
                pass
        return alive

    # -- registration -------------------------------------------------------
    def register_text(self, widget: tk.Text):
        self._texts = self._prune(self._texts)
        self._texts.append(widget)
        self._style_text(widget, PALETTES[self.mode])

    def register_menu(self, menu: tk.Menu):
        self._menus = self._prune(self._menus)
        self._menus.append(menu)
        self._style_menu(menu, PALETTES[self.mode])

    def register_combobox(self, combo: ttk.Combobox):
        self._combos = self._prune(self._combos)
        self._combos.append(combo)
        self._style_combo_popdown(combo, PALETTES[self.mode])

    # -- application --------------------------------------------------------
    def apply(self, mode: str):
        self.mode = mode if mode in PALETTES else "light"
        p = PALETTES[self.mode]
        s = self.style
        root = self.root
        root.configure(bg=p["bg"])

        base_font = tkfont.nametofont("TkDefaultFont")
        bold = base_font.copy()
        bold.configure(weight="bold")
        self._bold_font = bold

        s.configure(".", background=p["bg"], foreground=p["fg"],
                    bordercolor=p["border"], lightcolor=p["panel"],
                    darkcolor=p["bg"], troughcolor=p["trough"],
                    fieldbackground=p["field"], selectbackground=p["select"],
                    selectforeground=p["fg"], insertcolor=p["fg"],
                    focuscolor=p["accent"])
        s.configure("TFrame", background=p["bg"])
        s.configure("TLabel", background=p["bg"], foreground=p["fg"])
        s.configure("Muted.TLabel", foreground=p["muted"])
        s.configure("Title.TLabel", font=bold, foreground=p["accent"])
        s.configure("TSeparator", background=p["border"])

        s.configure("TLabelframe", background=p["bg"], bordercolor=p["border"],
                    lightcolor=p["border"], darkcolor=p["border"])
        s.configure("TLabelframe.Label", background=p["bg"],
                    foreground=p["accent"], font=bold)

        s.configure("TButton", background=p["panel"], foreground=p["fg"],
                    bordercolor=p["border"], padding=(8, 3))
        s.map("TButton",
              background=[("pressed", p["tab"]), ("active", p["tab"])],
              foreground=[("disabled", p["muted"])])
        s.configure("Accent.TButton", background=p["accent"],
                    foreground=p["accent_fg"], bordercolor=p["accent"])
        s.map("Accent.TButton",
              background=[("pressed", p["accent_hover"]),
                          ("active", p["accent_hover"])])
        s.configure("TMenubutton", background=p["panel"], foreground=p["fg"],
                    bordercolor=p["border"], arrowcolor=p["fg"],
                    padding=(10, 4))
        s.map("TMenubutton", background=[("active", p["tab"])])

        s.configure("TEntry", fieldbackground=p["field"], foreground=p["fg"],
                    insertcolor=p["fg"], bordercolor=p["border"],
                    lightcolor=p["border"], darkcolor=p["border"],
                    padding=(4, 2))
        s.configure("TCombobox", fieldbackground=p["field"],
                    foreground=p["fg"], background=p["panel"],
                    arrowcolor=p["fg"], bordercolor=p["border"],
                    lightcolor=p["border"], darkcolor=p["border"])
        s.map("TCombobox",
              fieldbackground=[("readonly", p["field"])],
              foreground=[("readonly", p["fg"])],
              selectbackground=[("readonly", p["field"])],
              selectforeground=[("readonly", p["fg"])])
        for opt, val in (("background", p["field"]), ("foreground", p["fg"]),
                         ("selectBackground", p["select"]),
                         ("selectForeground", p["fg"])):
            root.option_add(f"*TCombobox*Listbox.{opt}", val)

        for nb in ("TNotebook", "Closable.TNotebook"):
            s.configure(nb, background=p["bg"], bordercolor=p["border"],
                        tabmargins=(6, 4, 6, 0))
            s.configure(f"{nb}.Tab", background=p["tab"], foreground=p["fg"],
                        bordercolor=p["border"], padding=(12, 5),
                        lightcolor=p["tab"])
            s.map(f"{nb}.Tab",
                  background=[("selected", p["bg"])],
                  foreground=[("selected", p["accent"])],
                  lightcolor=[("selected", p["bg"])],
                  expand=[("selected", (1, 1, 1, 0))])

        s.configure("Treeview", background=p["field"],
                    fieldbackground=p["field"], foreground=p["fg"],
                    bordercolor=p["border"], lightcolor=p["field"],
                    darkcolor=p["field"], rowheight=24)
        s.map("Treeview",
              background=[("selected", p["select"])],
              foreground=[("selected", p["fg"])])
        s.configure("Treeview.Heading", background=p["panel"],
                    foreground=p["fg"], bordercolor=p["border"])

        for sb in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
            s.configure(sb, background=p["panel"], troughcolor=p["bg"],
                        bordercolor=p["border"], arrowcolor=p["fg"],
                        lightcolor=p["panel"], darkcolor=p["panel"])
            s.map(sb, background=[("active", p["tab"])])

        s.configure("Horizontal.TScale", background=p["bg"],
                    troughcolor=p["trough"], bordercolor=p["border"],
                    lightcolor=p["accent"], darkcolor=p["accent"])
        s.configure("TPanedwindow", background=p["bg"])
        s.configure("TCheckbutton", background=p["bg"], foreground=p["fg"])
        s.map("TCheckbutton", background=[("active", p["bg"])])

        self._texts = self._prune(self._texts)
        for w in self._texts:
            self._style_text(w, p)
        self._menus = self._prune(self._menus)
        for m in self._menus:
            self._style_menu(m, p)
        self._combos = self._prune(self._combos)
        for cb in self._combos:
            self._style_combo_popdown(cb, p)
        s.configure("Toolbutton", background=p["bg"], foreground=p["fg"],
                    padding=(4, 0))
        s.map("Toolbutton", background=[("active", p["tab"])])
        # flat toolbar strip below the menu bar
        s.configure("Topbar.TFrame", background=p["panel"])
        s.configure("Topbar.Toolbutton", background=p["panel"],
                    foreground=p["fg"], padding=(10, 4))
        s.map("Topbar.Toolbutton",
              background=[("pressed", p["tab"]), ("active", p["tab"])])
        s.configure("Topbar.TMenubutton", background=p["panel"],
                    foreground=p["fg"], arrowcolor=p["fg"],
                    bordercolor=p["panel"], padding=(10, 4))
        s.map("Topbar.TMenubutton", background=[("active", p["tab"])])
        self.run_redraws()

    def run_redraws(self):
        """Re-invoke every registered canvas redraw (theme or display
        settings changed)."""
        self._redraws = [(w, f) for w, f in self._redraws if self._alive(w)]
        for _w, redraw in self._redraws:
            try:
                redraw()
            except tk.TclError:
                pass

    @staticmethod
    def _style_text(widget: tk.Text, p: dict):
        widget.configure(background=p["field"], foreground=p["fg"],
                         insertbackground=p["fg"],
                         selectbackground=p["select"],
                         selectforeground=p["fg"],
                         inactiveselectbackground=p["select"],
                         highlightthickness=0, borderwidth=0)

    @staticmethod
    def _style_combo_popdown(combo: ttk.Combobox, p: dict):
        """option_add only styles popdown listboxes created afterwards; an
        already-realized popdown must be re-configured directly."""
        try:
            combo.tk.call(f"{combo}.popdown.f.l", "configure",
                          "-background", p["field"],
                          "-foreground", p["fg"],
                          "-selectbackground", p["select"],
                          "-selectforeground", p["fg"])
        except tk.TclError:
            pass    # popdown not created yet — option_add covers it

    @staticmethod
    def _style_menu(menu: tk.Menu, p: dict):
        if sys.platform == "win32":
            # Windows draws menus natively and follows the system theme
            # (via the AllowDark opt-in). Forcing palette colors only
            # half-applies — hover bezels and cascade arrows stay native —
            # so leave menus entirely to the OS there.
            return
        try:
            menu.configure(background=p["panel"], foreground=p["fg"],
                           activebackground=p["select"],
                           activeforeground=p["fg"],
                           disabledforeground=p["muted"], borderwidth=0)
        except tk.TclError:
            pass


# ---------------------------------------------------------------------------
#  Notebook with per-tab close buttons
# ---------------------------------------------------------------------------

class ClosableNotebook(ttk.Notebook):
    """ttk.Notebook whose tabs carry an ✕ button (plus middle-click close)."""

    _style_ready = False

    def __init__(self, master, close_command, **kw):
        if not ClosableNotebook._style_ready:
            self._init_style(master)
            ClosableNotebook._style_ready = True
        kw.setdefault("style", "Closable.TNotebook")
        super().__init__(master, **kw)
        self._close_command = close_command
        self._pressed_index = None
        self.bind("<ButtonPress-1>", self._on_press, True)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Button-2>", self._on_middle)

    # -- style / images -----------------------------------------------------
    @classmethod
    def _init_style(cls, master):
        def make(name, fg, bg=""):
            img = tk.PhotoImage(name=name, width=12, height=12, master=master)
            if bg:
                img.put(bg, to=(0, 0, 12, 12))
            for i in range(3, 9):
                img.put(fg, (i, i))
                img.put(fg, (i, 11 - i))
            return img

        cls._images = (
            make("img_tab_close", "#888888"),
            make("img_tab_close_active", "#ffffff", "#c0392b"),
            make("img_tab_close_pressed", "#ffffff", "#8e2418"),
        )
        style = ttk.Style(master)
        style.element_create(
            "close", "image", "img_tab_close",
            ("active", "pressed", "!disabled", "img_tab_close_pressed"),
            ("active", "!disabled", "img_tab_close_active"),
            border=8, sticky="")
        style.layout("Closable.TNotebook", style.layout("TNotebook"))
        # The close element is packed from the RIGHT and BEFORE the label:
        # when many tabs force compression, Tk clips the last-packed element
        # first — this way the shrinking label absorbs the squeeze and the
        # ✕ stays visible on every tab.
        style.layout("Closable.TNotebook.Tab", [
            ("Notebook.tab", {"sticky": "nswe", "children": [
                ("Notebook.padding", {"side": "top", "sticky": "nswe",
                                      "children": [
                    ("Notebook.focus", {"side": "top", "sticky": "nswe",
                                        "children": [
                        ("close", {"side": "right", "sticky": ""}),
                        ("Notebook.label", {"side": "left", "sticky": ""}),
                    ]})]})]})])

    # -- events -------------------------------------------------------------
    def _index_at(self, event):
        try:
            return self.index(f"@{event.x},{event.y}")
        except tk.TclError:
            return None

    def _on_press(self, event):
        if "close" in self.identify(event.x, event.y):
            self._pressed_index = self._index_at(event)
            if self._pressed_index is not None:
                self.state(["pressed"])
                return "break"
        return None

    def _on_release(self, event):
        if self._pressed_index is None:
            return
        self.state(["!pressed"])
        index = self._index_at(event)
        if index == self._pressed_index and \
                "close" in self.identify(event.x, event.y):
            self._close_command(index)
        self._pressed_index = None

    def _on_middle(self, event):
        index = self._index_at(event)
        if index is not None:
            self._close_command(index)


# ---------------------------------------------------------------------------
#  File explorer (left pane)
# ---------------------------------------------------------------------------

class FileExplorer(ttk.Frame):
    IGNORED = {".git", "__pycache__", ".vs", ".idea"}

    def __init__(self, master, app: "ACModStudio"):
        super().__init__(master, padding=(0, 0))
        self.app = app
        self.root_path: Path | None = None

        header = ttk.Frame(self, padding=(8, 6, 4, 4))
        header.pack(side="top", fill="x")
        self.title = ttk.Label(header, text="PROJECT", style="Title.TLabel")
        self.title.pack(side="left")
        ttk.Button(header, text="Refresh", style="Toolbutton",
                   command=self.refresh).pack(side="right")

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(body, show="tree", selectmode="browse")
        ybar = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=ybar.set)
        ybar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        # Open on click / Enter — NOT on <<TreeviewSelect>>, which fires for
        # every arrow-key step and would open a tab per file passed over.
        self.tree.bind("<ButtonRelease-1>", self._on_click)
        self.tree.bind("<Return>", self._on_activate)

    # -- population ---------------------------------------------------------
    def load(self, root_path: Path | None):
        self.root_path = Path(root_path) if root_path else None
        self.refresh()

    def refresh(self):
        open_state = {iid: self.tree.item(iid, "open")
                      for iid in self._all_items()}
        self.tree.delete(*self.tree.get_children())
        if self.root_path is None or not self.root_path.exists():
            self.title.configure(text="PROJECT — none loaded")
            return
        self.title.configure(text=f"PROJECT — {self.root_path.name}")
        root_iid = str(self.root_path)
        self.tree.insert("", "end", iid=root_iid, open=True,
                         text=self.root_path.name)
        self._insert_children(root_iid, self.root_path)
        for iid, was_open in open_state.items():
            if self.tree.exists(iid):
                self.tree.item(iid, open=was_open)

    def _all_items(self, parent=""):
        for iid in self.tree.get_children(parent):
            yield iid
            yield from self._all_items(iid)

    def _insert_children(self, parent_iid: str, dir_path: Path):
        try:
            entries = sorted(dir_path.iterdir(),
                             key=lambda p: (p.is_file(), p.name.lower()))
        except OSError:
            return
        for p in entries:
            if p.name in self.IGNORED:
                continue
            iid = str(p)
            if self.tree.exists(iid):     # symlink aliases of a seen path
                continue
            if p.is_dir():
                self.tree.insert(parent_iid, "end", iid=iid, open=False,
                                 text=f"{p.name}/")
                # Never descend through a symlinked dir — 'ln -s .. up'
                # style loops would otherwise recurse forever.
                if not p.is_symlink():
                    self._insert_children(iid, p)
            else:
                self.tree.insert(parent_iid, "end", iid=iid, text=p.name)

    # -- interaction --------------------------------------------------------
    def _open_iid(self, iid: str):
        if iid:
            path = Path(iid)
            if path.is_file():
                self.app.open_file(path)

    def _on_click(self, event):
        self._open_iid(self.tree.identify_row(event.y))

    def _on_activate(self, _event=None):
        self._open_iid(self.tree.focus())

    def select_path(self, path: Path):
        iid = str(path)
        if self.tree.exists(iid):
            self.tree.see(iid)


# ---------------------------------------------------------------------------
#  Welcome pane
# ---------------------------------------------------------------------------

class WelcomePane(ttk.Frame):
    display_name = "Welcome"
    dirty = False

    def __init__(self, master, app: "ACModStudio"):
        super().__init__(master, padding=40)
        ttk.Label(self, text="AC Mod Studio", style="Title.TLabel",
                  font=("TkDefaultFont", 20, "bold")).pack(anchor="w")
        ttk.Label(self, style="Muted.TLabel", justify="left", text=(
            "\nGenerate, browse and tune Assetto Corsa car mods.\n\n"
            "  -  File > New Car Project generates the full content/cars "
            "hierarchy\n      (data, sfx, skins/00_default, ui) with physics "
            "templates and placeholders.\n"
            "  -  Click a file on the left to edit it — suspensions.ini opens "
            "the slider-based\n      tuning editor, other .ini files the "
            "visual grid editor, .lut files a live\n      graph, JSON raw "
            "text.\n"
            "  -  'ADD COMPONENT' injects turbos, wings, DRS or anti-roll "
            "bars into the\n      active editor. Ctrl+S saves to disk.\n"
        )).pack(anchor="w")
        row = ttk.Frame(self)
        row.pack(anchor="w", pady=12)
        ttk.Button(row, text="New Car Project", style="Accent.TButton",
                   command=app.new_project_dialog).pack(side="left")
        ttk.Button(row, text="Open Project Folder",
                   command=app.open_project_dialog).pack(side="left", padx=10)


# ---------------------------------------------------------------------------
#  Custom file selection for New Car Project
# ---------------------------------------------------------------------------

class FileSelectionDialog(tk.Toplevel):
    """Checklist of the data templates and asset placeholders to generate.
    Result in ``self.result``: {"configs": set, "placeholders": set} or None
    when cancelled. Referenced LUTs are resolved by the generator."""

    def __init__(self, parent: tk.Toplevel, car_id: str,
                 current: dict | None):
        super().__init__(parent)
        self.app = parent.app
        self.title("Choose files to generate")
        self.configure(bg=self.app.theme.palette()["bg"])
        self.transient(parent)
        self.result: dict | None = None
        car_id = sanitize_car_id(car_id) or "my_car"

        outer = ttk.Frame(self, padding=12)
        outer.pack(fill="both", expand=True)
        columns = ttk.Frame(outer)
        columns.pack(fill="both", expand=True)

        self._config_vars: dict[str, tk.BooleanVar] = {}
        self._ph_vars: dict[str, tk.BooleanVar] = {}

        def build_column(title, items, var_map, selected, required,
                         display=lambda k: k):
            box = ttk.LabelFrame(columns, text=f" {title} ", padding=(8, 6))
            box.pack(side="left", fill="both", expand=True, padx=4)
            scroll = ScrollableFrame(box)
            scroll.pack(fill="both", expand=True)
            scroll.canvas.configure(width=290, height=320)
            for key in items:
                var = tk.BooleanVar(value=key in selected)
                var_map[key] = var
                text = display(key)
                if key in required:
                    text += "   • needed to drive"
                ttk.Checkbutton(scroll.interior, text=text,
                                variable=var).pack(anchor="w")

        current_cfg = (current or {}).get("configs",
                                          set(MINIMAL_CONFIG_FILES))
        current_ph = (current or {}).get("placeholders",
                                         set(MINIMAL_PLACEHOLDER_FILES))
        build_column("data/ physics files", sorted(CONFIG_TEMPLATES),
                     self._config_vars, current_cfg, MINIMAL_CONFIG_FILES)
        build_column("assets & placeholders", sorted(PLACEHOLDER_FILES),
                     self._ph_vars, current_ph, MINIMAL_PLACEHOLDER_FILES,
                     display=lambda k: k.replace("$car", car_id))

        presets = ttk.Frame(outer)
        presets.pack(fill="x", pady=(10, 0))
        ttk.Button(presets, text="Minimal set",
                   command=lambda: self._preset(MINIMAL_CONFIG_FILES,
                                                MINIMAL_PLACEHOLDER_FILES)
                   ).pack(side="left")
        ttk.Button(presets, text="Everything",
                   command=lambda: self._preset(set(CONFIG_TEMPLATES),
                                                set(PLACEHOLDER_FILES))
                   ).pack(side="left", padx=(8, 0))
        ttk.Label(presets, style="Muted.TLabel",
                  text="LUT tables referenced by the chosen files are "
                       "generated automatically.").pack(side="left",
                                                        padx=(12, 0))
        ttk.Button(presets, text="Cancel",
                   command=self.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(presets, text="OK", style="Accent.TButton",
                   command=self._ok).pack(side="right")

        self.bind("<Escape>", lambda e: self.destroy())
        self.wait_visibility()
        self.grab_set()
        self.app.sync_titlebar(self)

    def _preset(self, configs: set, placeholders: set):
        for key, var in self._config_vars.items():
            var.set(key in configs)
        for key, var in self._ph_vars.items():
            var.set(key in placeholders)

    def _ok(self):
        self.result = {
            "configs": {k for k, v in self._config_vars.items() if v.get()},
            "placeholders": {k for k, v in self._ph_vars.items()
                             if v.get()},
        }
        self.destroy()


# ---------------------------------------------------------------------------
#  New-project dialog
# ---------------------------------------------------------------------------

class NewProjectDialog(tk.Toplevel):
    def __init__(self, app: "ACModStudio"):
        super().__init__(app)
        self.app = app
        self.title("New Car Project")
        self.configure(bg=PALETTES[app.theme.mode]["bg"])
        self.transient(app)
        self.resizable(False, False)

        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        self.vars = {
            "location": tk.StringVar(
                value=app.settings.get("last_location", str(Path.home()))),
            "car_id": tk.StringVar(value="my_car"),
            "screen_name": tk.StringVar(value="My Car"),
            "brand": tk.StringVar(value="MyBrand"),
        }
        rows = [("Location (content/cars)", "location"),
                ("Car folder ID", "car_id"),
                ("Screen name", "screen_name"),
                ("Brand", "brand")]
        for r, (label, key) in enumerate(rows):
            ttk.Label(frame, text=label).grid(row=r, column=0, sticky="w",
                                              pady=4, padx=(0, 12))
            ttk.Entry(frame, textvariable=self.vars[key], width=38).grid(
                row=r, column=1, sticky="ew", pady=4)
        ttk.Button(frame, text="Browse…", command=self._browse).grid(
            row=0, column=2, padx=(6, 0))
        scope_box = ttk.LabelFrame(frame, text=" Files to generate ",
                                   padding=(10, 6))
        scope_box.grid(row=len(rows), column=0, columnspan=3, sticky="ew",
                       pady=(8, 2))
        self.scope_var = tk.StringVar(value="full")
        self.custom_selection: dict | None = None
        ttk.Radiobutton(scope_box, text="Full car (all templates)",
                        value="full", variable=self.scope_var,
                        command=self._on_scope_change).pack(anchor="w")
        ttk.Radiobutton(scope_box,
                        text="Minimal — only what the sim needs to load "
                             "and drive the car",
                        value="minimal", variable=self.scope_var,
                        command=self._on_scope_change).pack(anchor="w")
        custom_row = ttk.Frame(scope_box)
        custom_row.pack(anchor="w", fill="x")
        ttk.Radiobutton(custom_row, text="Custom selection",
                        value="custom", variable=self.scope_var,
                        command=self._on_scope_change).pack(side="left")
        self.choose_btn = ttk.Button(custom_row, text="Choose files…",
                                     state="disabled",
                                     command=self._choose_files)
        self.choose_btn.pack(side="left", padx=(10, 0))
        self.scope_info = ttk.Label(scope_box, text="", style="Muted.TLabel")
        self.scope_info.pack(anchor="w", pady=(2, 0))

        ttk.Label(frame, style="Muted.TLabel",
                  text="ID is the folder name — lowercase, digits and "
                       "underscores only.").grid(
            row=len(rows) + 1, column=0, columnspan=3, sticky="w",
            pady=(2, 10))

        buttons = ttk.Frame(frame)
        buttons.grid(row=len(rows) + 2, column=0, columnspan=3, sticky="e")
        ttk.Button(buttons, text="Cancel",
                   command=self.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(buttons, text="Create Project", style="Accent.TButton",
                   command=self._create).pack(side="right")

        self.bind("<Return>", lambda e: self._create())
        self.bind("<Escape>", lambda e: self.destroy())
        self.wait_visibility()      # grab before mapping fails on some X11
        self.grab_set()
        self.focus_set()
        app.sync_titlebar(self)

    def _browse(self):
        chosen = filedialog.askdirectory(
            parent=self, initialdir=self.vars["location"].get() or None,
            title="Choose the folder that will contain the car project")
        if chosen:
            self.vars["location"].set(chosen)

    def _on_scope_change(self):
        custom = self.scope_var.get() == "custom"
        self.choose_btn.configure(state="normal" if custom else "disabled")
        if custom and self.custom_selection is None:
            self._choose_files()
        self._update_scope_info()

    def _update_scope_info(self):
        if self.scope_var.get() == "custom" and self.custom_selection:
            n_cfg = len(self.custom_selection["configs"])
            n_ph = len(self.custom_selection["placeholders"])
            self.scope_info.configure(
                text=f"{n_cfg} data files + {n_ph} asset placeholders "
                     "selected (referenced LUTs are added automatically)")
        else:
            self.scope_info.configure(text="")

    def _choose_files(self):
        dialog = FileSelectionDialog(self, self.vars["car_id"].get(),
                                     self.custom_selection)
        self.wait_window(dialog)
        if dialog.result is not None:
            self.custom_selection = dialog.result
            self.scope_var.set("custom")
            self.choose_btn.configure(state="normal")
        self._update_scope_info()

    def _create(self):
        loc_text = self.vars["location"].get().strip()
        if not loc_text:
            messagebox.showerror("New Car Project",
                                 "Please choose a location folder.",
                                 parent=self)
            return
        # Resolve so stored settings / explorer paths are always absolute.
        location = Path(loc_text).expanduser().resolve()
        car_id = sanitize_car_id(self.vars["car_id"].get())
        screen_name = self.vars["screen_name"].get().strip() or car_id
        brand = self.vars["brand"].get().strip() or "Unknown"
        if not car_id:
            messagebox.showerror("New Car Project",
                                 "Please enter a valid car folder ID.",
                                 parent=self)
            return
        target = location / car_id
        overwrite = False
        if target.exists():
            if not messagebox.askyesno(
                    "New Car Project",
                    f"{target}\nalready exists. Add any missing files into it "
                    f"(existing files are kept)?", parent=self):
                return
            overwrite = True
        gen_kwargs = {}
        scope = self.scope_var.get()
        if scope == "minimal":
            gen_kwargs["minimal"] = True
        elif scope == "custom" and self.custom_selection is not None:
            gen_kwargs["config_files"] = self.custom_selection["configs"]
            gen_kwargs["placeholder_files"] = \
                self.custom_selection["placeholders"]
        gen_kwargs["placeholder_txt_suffix"] = \
            self.app.settings.get("placeholder_txt_suffix", False)
        try:
            project = generate_car_project(location, car_id,
                                           screen_name=screen_name,
                                           brand=brand, overwrite=overwrite,
                                           **gen_kwargs)
        except OSError as exc:
            messagebox.showerror("New Car Project",
                                 f"Could not create the project:\n{exc}",
                                 parent=self)
            return
        self.app.settings["last_location"] = str(location)
        self.app.load_project(project)
        self.app.set_status(f"Created car project at {project}")
        self.destroy()


# ---------------------------------------------------------------------------
#  Main application window
# ---------------------------------------------------------------------------

class ACModStudio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1280x800")
        self.minsize(940, 620)
        self.option_add("*tearOff", False)

        self.settings = self._load_settings()
        self.theme = ThemeManager(self)
        self.project_root: Path | None = None
        self._editors: dict[str, BaseEditor] = {}
        self._closing: set = set()
        # Values/sections removed by suspension type switches, kept per file
        # until the project is closed so switching back restores them.
        self.type_stash: dict[str, dict] = {}

        # theme_mode: "dark" | "light" | "system". Follow-system is the
        # default; the legacy "theme" key is discarded rather than
        # migrated so existing installs also default to system.
        mode = self.settings.get("theme_mode") or "system"
        if mode not in ("dark", "light", "system"):
            mode = "system"
        _enable_windows_system_menus()
        self.theme_mode_var = tk.StringVar(value=mode)
        self.lut_labels_var = tk.BooleanVar(
            value=self.settings.get("lut_point_labels", True))
        self.reopen_var = tk.BooleanVar(
            value=self.settings.get("reopen_last_project", True))
        self.txt_suffix_var = tk.BooleanVar(
            value=self.settings.get("placeholder_txt_suffix", False))

        self._build_menubar()
        self._build_topbar()
        self._build_body()
        self._build_statusbar()

        self._apply_theme_mode()

        # Tk's Text/Entry class bindings claim Ctrl+D (delete char),
        # Ctrl+O (insert newline) and Ctrl+N (next line) — and class bindings
        # fire BEFORE bind_all, so they would edit the buffer on top of our
        # accelerators. Neutralize them; arrow keys/Delete cover the loss.
        for cls in ("Text", "Entry", "TEntry", "TCombobox", "TSpinbox"):
            for seq in ("<Control-d>", "<Control-o>", "<Control-n>"):
                self.bind_class(cls, seq, lambda e: None)

        self.bind_all("<Control-s>", self._accel(self.save_active))
        self.bind_all("<Control-n>", self._accel(self.new_project_dialog))
        self.bind_all("<Control-o>", self._accel(self.open_project_dialog))
        self.bind_all("<Control-w>", self._accel(self.close_active_tab))
        self.bind_all("<Control-d>", self._accel(self.toggle_dark))
        self.bind_all("<F5>", self._accel(lambda: self.explorer.refresh()))
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.workspace.add(WelcomePane(self.workspace, self),
                           text="  Welcome  ")

        last = self.settings.get("last_project")
        if self.settings.get("reopen_last_project", True) and last \
                and Path(last).is_dir():
            self.load_project(Path(last))

    def _accel(self, fn):
        """Wrap a keyboard accelerator: inert while a modal dialog holds the
        grab, and 'break' stops any later bindings."""
        def handler(_event=None):
            if self.grab_current() is not None:
                return None
            fn()
            return "break"
        return handler

    # ------------------------------------------------------------------ ui
    def _build_menubar(self):
        menubar = tk.Menu(self)
        self.theme.register_menu(menubar)

        file_menu = tk.Menu(menubar)
        self.theme.register_menu(file_menu)
        file_menu.add_command(label="New Car Project…", accelerator="Ctrl+N",
                              command=self.new_project_dialog)
        file_menu.add_command(label="Open Project Folder…",
                              accelerator="Ctrl+O",
                              command=self.open_project_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Save", accelerator="Ctrl+S",
                              command=self.save_active)
        file_menu.add_command(label="Close Tab", accelerator="Ctrl+W",
                              command=self.close_active_tab)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close)
        menubar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(menubar)
        self.theme.register_menu(view_menu)
        view_menu.add_command(label="Refresh File Tree", accelerator="F5",
                              command=lambda: self.explorer.refresh())
        menubar.add_cascade(label="View", menu=view_menu)

        settings_menu = tk.Menu(menubar)
        self.theme.register_menu(settings_menu)
        theme_menu = tk.Menu(settings_menu)
        self.theme.register_menu(theme_menu)
        theme_menu.add_radiobutton(
            label="Dark mode", value="dark", variable=self.theme_mode_var,
            command=lambda: self._apply_theme_mode("dark"))
        theme_menu.add_radiobutton(
            label="Regular (light) mode", value="light",
            variable=self.theme_mode_var,
            command=lambda: self._apply_theme_mode("light"))
        theme_menu.add_radiobutton(
            label="Follow system colors  (default)", value="system",
            variable=self.theme_mode_var,
            command=lambda: self._apply_theme_mode("system"))
        settings_menu.add_cascade(label="Theme  (Ctrl+D toggles dark/light)",
                                  menu=theme_menu)
        settings_menu.add_separator()
        settings_menu.add_checkbutton(
            label="Show point values on LUT graphs",
            variable=self.lut_labels_var, command=self._apply_lut_labels)
        settings_menu.add_checkbutton(
            label="Reopen last project on startup",
            variable=self.reopen_var,
            command=lambda: self._set_setting("reopen_last_project",
                                              self.reopen_var.get()))
        settings_menu.add_checkbutton(
            label="Append .txt to binary placeholder names (new projects)",
            variable=self.txt_suffix_var,
            command=lambda: self._set_setting("placeholder_txt_suffix",
                                              self.txt_suffix_var.get()))
        menubar.add_cascade(label="Settings", menu=settings_menu)

        help_menu = tk.Menu(menubar)
        self.theme.register_menu(help_menu)
        help_menu.add_command(
            label="About",
            command=lambda: messagebox.showinfo(
                "About", f"{APP_TITLE}\n\nA pure-stdlib (tkinter) toolkit for "
                         "generating and tuning Assetto Corsa car mods.",
                parent=self))
        menubar.add_cascade(label="Help", menu=help_menu)
        self.configure(menu=menubar)

    def _build_topbar(self):
        """Flat toolbar strip directly below the menu bar."""
        bar = ttk.Frame(self, padding=(6, 3), style="Topbar.TFrame")
        bar.pack(side="top", fill="x")
        ttk.Button(bar, text="New Car Project", style="Topbar.Toolbutton",
                   command=self.new_project_dialog).pack(side="left")
        ttk.Button(bar, text="Open Project", style="Topbar.Toolbutton",
                   command=self.open_project_dialog).pack(side="left",
                                                          padx=(6, 0))
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y",
                                                   padx=10, pady=3)
        self.component_menu = tk.Menu(self)
        self.theme.register_menu(self.component_menu)
        self.component_btn = ttk.Menubutton(
            bar, text="ADD COMPONENT", style="Topbar.TMenubutton",
            menu=self.component_menu)
        self.component_menu.configure(postcommand=self._build_component_menu)
        self.component_btn.pack(side="left")
        ttk.Separator(self, orient="horizontal").pack(side="top", fill="x")

    def _build_body(self):
        self.paned = ttk.PanedWindow(self, orient="horizontal")
        self.paned.pack(fill="both", expand=True)
        self.explorer = FileExplorer(self.paned, self)
        self.paned.add(self.explorer, weight=1)
        self.workspace = ClosableNotebook(self.paned, self.close_tab)
        self.workspace.bind("<Button-3>", self._on_tab_context)
        self.paned.add(self.workspace, weight=4)

    def _build_statusbar(self):
        ttk.Separator(self, orient="horizontal").pack(side="bottom", fill="x")
        self.status_var = tk.StringVar(
            value="Ready — create or open a car project to begin.")
        ttk.Label(self, textvariable=self.status_var, padding=(10, 4),
                  style="Muted.TLabel").pack(side="bottom", fill="x")

    # ------------------------------------------------------------ settings
    def _set_setting(self, key: str, value):
        self.settings[key] = value
        self._save_settings()

    def _apply_theme_mode(self, mode: str | None = None):
        if mode is not None:
            self.theme_mode_var.set(mode)
        mode = self.theme_mode_var.get()
        self._set_setting("theme_mode", mode)
        self.settings.pop("theme", None)        # retire the legacy key
        resolved = detect_system_theme() if mode == "system" else mode
        self.theme.apply(resolved)
        self.sync_titlebar(self)

    def sync_titlebar(self, window):
        """Match a window's native title bar to the active theme (Windows
        only; no-op elsewhere)."""
        apply_windows_titlebar(window, self.theme.mode == "dark")

    def toggle_dark(self):
        """Ctrl+D: quick toggle — switches to the explicit theme opposite
        of what is currently showing."""
        self._apply_theme_mode(
            "light" if self.theme.mode == "dark" else "dark")

    def _apply_lut_labels(self):
        self._set_setting("lut_point_labels", self.lut_labels_var.get())
        self.theme.run_redraws()

    # ------------------------------------------------------------- projects
    def new_project_dialog(self):
        NewProjectDialog(self)

    def open_project_dialog(self):
        chosen = filedialog.askdirectory(
            parent=self, title="Open a car project folder "
                               "(content/cars/<car_id>)")
        if chosen:
            self.load_project(Path(chosen))

    def load_project(self, path: Path):
        if self.project_root != Path(path):
            self.type_stash = {}        # stash lives until project close
        self.project_root = Path(path)
        self.explorer.load(self.project_root)
        self.settings["last_project"] = str(self.project_root)
        self._save_settings()
        self.title(f"{APP_TITLE} — {self.project_root.name}")
        self.set_status(f"Project loaded: {self.project_root}")

    # -------------------------------------------------------------- editors
    @property
    def active_editor(self) -> BaseEditor | None:
        try:
            widget = self.nametowidget(self.workspace.select())
        except (KeyError, tk.TclError):
            return None
        return widget if isinstance(widget, BaseEditor) else None

    def open_file(self, path: Path):
        key = str(Path(path).resolve())
        if key in self._editors:
            editor = self._editors[key]
            if str(editor) in self.workspace.tabs():
                self.workspace.select(editor)
                return
            del self._editors[key]

        path = Path(path)
        try:
            with path.open("rb") as fh:      # never slurp a 300MB .kn5
                head = fh.read(2048)
        except OSError as exc:
            messagebox.showerror("Open file", f"Cannot read {path}:\n{exc}",
                                 parent=self)
            return
        if b"\x00" in head:
            messagebox.showinfo(
                "Binary file",
                f"{path.name} is a real binary asset — this tool edits the "
                "text placeholders and config files. Replace binaries with "
                "your compiled KN5/FMOD/PNG files on disk.", parent=self)
            return

        try:
            editor = self._route(path)
        except Exception as exc:             # noqa: BLE001 - keep shell alive
            messagebox.showerror(
                "Open file", f"Could not open {path.name}:\n{exc}",
                parent=self)
            return
        self._editors[key] = editor
        self.workspace.add(editor, text=self._tab_text(editor))
        self.workspace.select(editor)
        self.set_status(f"Opened {path} [{type(editor).__name__}]")

    @staticmethod
    def _tab_text(editor) -> str:
        name = editor.display_name
        if len(name) > 22:
            name = name[:20] + "…"
        return f"  {name}{' ●' if editor.dirty else ''}  "

    def _route(self, path: Path) -> BaseEditor:
        """Routing rules: suspensions → SuspensionEditor, other .ini physics
        files → ConfigEditor, .lut → graph editor, JSON/text → RawTextEditor."""
        name = path.name.lower()
        if name.endswith(".ini") and "suspension" in name:
            return SuspensionEditor(self.workspace, path, self)
        if name.endswith(".ini"):
            return ConfigEditor(self.workspace, path, self)
        if name.endswith(".lut"):
            return LutEditor(self.workspace, path, self)
        return RawTextEditor(self.workspace, path, self)

    def save_active(self):
        editor = self.active_editor
        if editor is not None:
            editor.save()

    def on_editor_dirty_changed(self, editor: BaseEditor):
        if str(editor) in self.workspace.tabs():
            self.workspace.tab(editor, text=self._tab_text(editor))

    # -- tab closing --------------------------------------------------------
    def close_tab(self, index: int):
        try:
            widget = self.nametowidget(self.workspace.tabs()[index])
        except (IndexError, KeyError, tk.TclError):
            return
        self._close_widget(widget)

    def _close_widget(self, widget):
        """Close by widget, not index: the confirm dialog is modal and other
        close requests can land meanwhile, shifting tab indices."""
        if widget in self._closing:
            return
        self._closing.add(widget)
        try:
            if isinstance(widget, BaseEditor) and widget.dirty:
                answer = messagebox.askyesnocancel(
                    "Unsaved changes",
                    f"Save changes to {widget.display_name} before closing?",
                    parent=self)
                if answer is None:
                    return
                if answer and not widget.save():
                    return              # save failed — keep the tab open
            for key, ed in list(self._editors.items()):
                if ed is widget:
                    del self._editors[key]
            try:
                if str(widget) in self.workspace.tabs():
                    self.workspace.forget(widget)
            except tk.TclError:
                pass
            widget.destroy()
        finally:
            self._closing.discard(widget)

    def close_active_tab(self):
        try:
            widget = self.nametowidget(self.workspace.select())
        except (KeyError, tk.TclError):
            return
        self._close_widget(widget)

    def _tab_widgets(self) -> list:
        widgets = []
        for tab in self.workspace.tabs():
            try:
                widgets.append(self.nametowidget(tab))
            except (KeyError, tk.TclError):
                pass
        return widgets

    def close_other_tabs(self, keep):
        for widget in self._tab_widgets():
            if widget is not keep:
                self._close_widget(widget)

    def close_all_tabs(self):
        for widget in self._tab_widgets():
            self._close_widget(widget)

    def _on_tab_context(self, event):
        """Right-click on a tab: close options (a fallback that always works,
        however many tabs are open)."""
        try:
            index = self.workspace.index(f"@{event.x},{event.y}")
        except tk.TclError:
            return
        try:
            widget = self.nametowidget(self.workspace.tabs()[index])
        except (IndexError, KeyError, tk.TclError):
            return
        menu = getattr(self, "_tab_menu", None)
        if menu is None or not menu.winfo_exists():
            menu = self._tab_menu = tk.Menu(self, tearoff=0)
            self.theme.register_menu(menu)
        menu.delete(0, "end")
        menu.add_command(label="Close", accelerator="Ctrl+W / middle-click",
                         command=lambda: self._close_widget(widget))
        menu.add_command(label="Close Others",
                         command=lambda: self.close_other_tabs(widget))
        menu.add_command(label="Close All", command=self.close_all_tabs)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    # -----------------------------------------------------ADD COMPONENT
    def _build_component_menu(self):
        menu = self.component_menu
        menu.delete(0, "end")
        for child in menu.winfo_children():   # drop last post's submenus
            child.destroy()
        editor = self.active_editor
        if not isinstance(editor, ConfigEditor):
            menu.add_command(
                label="Open a .ini physics file to add components",
                state="disabled")
            return
        library = COMPONENT_LIBRARY.get(editor.path.name.lower())
        if not library:
            menu.add_command(
                label=f"No component templates for {editor.path.name}",
                state="disabled")
            return
        for group, variants in library.items():
            sub = tk.Menu(menu)
            self.theme.register_menu(sub)
            for variant, sections in variants.items():
                sub.add_command(
                    label=variant,
                    command=lambda g=group, v=variant, s=sections:
                        editor.inject_component(f"{g} — {v}", s))
            if len(variants) > 1:
                sub.add_separator()
                all_sections = [pair for sections in variants.values()
                                for pair in sections]
                sub.add_command(
                    label=f"Add ALL {group} variants",
                    command=lambda g=group, s=all_sections:
                        editor.inject_component(f"{g} — all variants", s))
            menu.add_cascade(label=group, menu=sub)

    # -------------------------------------------------------------- helpers
    def set_status(self, message: str):
        self.status_var.set(message)

    def _load_settings(self) -> dict:
        try:
            return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _save_settings(self):
        try:
            SETTINGS_PATH.write_text(json.dumps(self.settings, indent=2),
                                     encoding="utf-8")
        except OSError:
            pass

    def _on_close(self):
        dirty = [e for e in self._editors.values() if e.dirty]
        if dirty:
            names = ", ".join(e.display_name for e in dirty)
            answer = messagebox.askyesnocancel(
                "Unsaved changes",
                f"Save changes to {names} before exiting?", parent=self)
            if answer is None:
                return
            if answer:
                for e in dirty:
                    if not e.save():
                        return      # save failed — stay open, data intact
        self._save_settings()
        self.destroy()


def main():
    app = ACModStudio()
    app.mainloop()


if __name__ == "__main__":
    main()

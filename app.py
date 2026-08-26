"""Module 4 — Main Application Shell & Styling.

Provides:
  * ``ThemeManager``    — light/dark theming for ttk + classic tk widgets.
  * ``ClosableNotebook``— workspace tabs with a working per-tab close button.
  * ``FileExplorer``    — left-pane project tree.
  * ``ACModStudio``     — the main window: split layout, routing, the
                          " ADD COMPONENT ▾" template injector, dialogs.
"""

from __future__ import annotations

import json
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from editors import BaseEditor, ConfigEditor, RawTextEditor, SuspensionEditor
from generator import generate_car_project, sanitize_car_id
from templates import APP_TITLE, COMPONENT_LIBRARY

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

    # -- registration -------------------------------------------------------
    def register_text(self, widget: tk.Text):
        self._texts.append(widget)
        self._style_text(widget, PALETTES[self.mode])

    def register_menu(self, menu: tk.Menu):
        self._menus.append(menu)
        self._style_menu(menu, PALETTES[self.mode])

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

        for w in self._texts:
            if w.winfo_exists():
                self._style_text(w, p)
        for m in self._menus:
            self._style_menu(m, p)

    @staticmethod
    def _style_text(widget: tk.Text, p: dict):
        widget.configure(background=p["field"], foreground=p["fg"],
                         insertbackground=p["fg"],
                         selectbackground=p["select"],
                         selectforeground=p["fg"],
                         inactiveselectbackground=p["select"],
                         highlightthickness=0, borderwidth=0)

    @staticmethod
    def _style_menu(menu: tk.Menu, p: dict):
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
        style.layout("Closable.TNotebook.Tab", [
            ("Notebook.tab", {"sticky": "nswe", "children": [
                ("Notebook.padding", {"side": "top", "sticky": "nswe",
                                      "children": [
                    ("Notebook.focus", {"side": "top", "sticky": "nswe",
                                        "children": [
                        ("Notebook.label", {"side": "left", "sticky": ""}),
                        ("close", {"side": "left", "sticky": ""}),
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
        ttk.Button(header, text="⟳", width=3,
                   command=self.refresh).pack(side="right")

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(body, show="tree", selectmode="browse")
        ybar = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=ybar.set)
        ybar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

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
                         text=f"📁 {self.root_path.name}")
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
            if p.is_dir():
                self.tree.insert(parent_iid, "end", iid=iid, open=False,
                                 text=f"📁 {p.name}")
                self._insert_children(iid, p)
            else:
                self.tree.insert(parent_iid, "end", iid=iid,
                                 text=f"📄 {p.name}")

    # -- interaction --------------------------------------------------------
    def _on_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        path = Path(sel[0])
        if path.is_file():
            self.app.open_file(path)

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
            "  •  File ▸ New Car Project generates the full content/cars "
            "hierarchy\n      (data, sfx, skins/00_default, ui) with physics "
            "templates and placeholders.\n"
            "  •  Click a file on the left to edit it — suspensions.ini opens "
            "the slider-based\n      tuning editor, other .ini files the "
            "visual grid editor, JSON/LUT raw text.\n"
            "  •  ' ADD COMPONENT ▾' injects turbos, wings, DRS or anti-roll "
            "bars into the\n      active editor. Ctrl+S saves to disk.\n"
        )).pack(anchor="w")
        row = ttk.Frame(self)
        row.pack(anchor="w", pady=12)
        ttk.Button(row, text="🆕  New Car Project", style="Accent.TButton",
                   command=app.new_project_dialog).pack(side="left")
        ttk.Button(row, text="📂  Open Project Folder",
                   command=app.open_project_dialog).pack(side="left", padx=10)


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
        ttk.Label(frame, style="Muted.TLabel",
                  text="ID is the folder name — lowercase, digits and "
                       "underscores only.").grid(
            row=len(rows), column=0, columnspan=3, sticky="w", pady=(2, 10))

        buttons = ttk.Frame(frame)
        buttons.grid(row=len(rows) + 1, column=0, columnspan=3, sticky="e")
        ttk.Button(buttons, text="Cancel",
                   command=self.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(buttons, text="Create Project", style="Accent.TButton",
                   command=self._create).pack(side="right")

        self.bind("<Return>", lambda e: self._create())
        self.bind("<Escape>", lambda e: self.destroy())
        self.wait_visibility()      # grab before mapping fails on some X11
        self.grab_set()
        self.focus_set()

    def _browse(self):
        chosen = filedialog.askdirectory(
            parent=self, initialdir=self.vars["location"].get() or None,
            title="Choose the folder that will contain the car project")
        if chosen:
            self.vars["location"].set(chosen)

    def _create(self):
        location = Path(self.vars["location"].get().strip())
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
        try:
            project = generate_car_project(location, car_id,
                                           screen_name=screen_name,
                                           brand=brand, overwrite=overwrite)
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

        self.dark_var = tk.BooleanVar(
            value=self.settings.get("theme", "dark") == "dark")

        self._build_menubar()
        self._build_topbar()
        self._build_body()
        self._build_statusbar()

        self.theme.apply("dark" if self.dark_var.get() else "light")

        self.bind_all("<Control-s>", lambda e: self.save_active())
        self.bind_all("<Control-n>", lambda e: self.new_project_dialog())
        self.bind_all("<Control-o>", lambda e: self.open_project_dialog())
        self.bind_all("<Control-w>", lambda e: self.close_active_tab())
        self.bind_all("<Control-d>", lambda e: self.toggle_dark())
        self.bind_all("<F5>", lambda e: self.explorer.refresh())
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.workspace.add(WelcomePane(self.workspace, self),
                           text="  Welcome  ")

        last = self.settings.get("last_project")
        if last and Path(last).is_dir():
            self.load_project(Path(last))

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
        view_menu.add_checkbutton(label="Dark Mode", accelerator="Ctrl+D",
                                  variable=self.dark_var,
                                  command=self._apply_theme_choice)
        view_menu.add_command(label="Refresh File Tree", accelerator="F5",
                              command=lambda: self.explorer.refresh())
        menubar.add_cascade(label="View", menu=view_menu)

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
        bar = ttk.Frame(self, padding=(8, 6))
        bar.pack(side="top", fill="x")
        ttk.Button(bar, text="🆕 New Car Project", style="Accent.TButton",
                   command=self.new_project_dialog).pack(side="left")
        ttk.Button(bar, text="📂 Open Project",
                   command=self.open_project_dialog).pack(side="left",
                                                          padx=(8, 0))
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y",
                                                   padx=12, pady=2)
        self.component_menu = tk.Menu(self)
        self.theme.register_menu(self.component_menu)
        self.component_btn = ttk.Menubutton(
            bar, text=" ADD COMPONENT ▾", menu=self.component_menu)
        self.component_menu.configure(postcommand=self._build_component_menu)
        self.component_btn.pack(side="left")

        ttk.Checkbutton(bar, text="🌙 Dark Mode", variable=self.dark_var,
                        command=self._apply_theme_choice).pack(side="right")
        ttk.Separator(self, orient="horizontal").pack(side="top", fill="x")

    def _build_body(self):
        self.paned = ttk.PanedWindow(self, orient="horizontal")
        self.paned.pack(fill="both", expand=True)
        self.explorer = FileExplorer(self.paned, self)
        self.paned.add(self.explorer, weight=1)
        self.workspace = ClosableNotebook(self.paned, self.close_tab)
        self.paned.add(self.workspace, weight=4)

    def _build_statusbar(self):
        ttk.Separator(self, orient="horizontal").pack(side="bottom", fill="x")
        self.status_var = tk.StringVar(
            value="Ready — create or open a car project to begin.")
        ttk.Label(self, textvariable=self.status_var, padding=(10, 4),
                  style="Muted.TLabel").pack(side="bottom", fill="x")

    # -------------------------------------------------------------- theming
    def _apply_theme_choice(self):
        self.theme.apply("dark" if self.dark_var.get() else "light")
        self.settings["theme"] = "dark" if self.dark_var.get() else "light"
        self._save_settings()

    def toggle_dark(self):
        self.dark_var.set(not self.dark_var.get())
        self._apply_theme_choice()

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
            head = path.read_bytes()[:2048]
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

        editor = self._route(path)
        self._editors[key] = editor
        self.workspace.add(editor, text=f"  {editor.display_name}  ")
        self.workspace.select(editor)
        self.set_status(f"Opened {path} [{type(editor).__name__}]")

    def _route(self, path: Path) -> BaseEditor:
        """Routing rules: suspensions → SuspensionEditor, other .ini physics
        files → ConfigEditor, JSON/LUT/text → RawTextEditor."""
        name = path.name.lower()
        if name.endswith(".ini") and "suspension" in name:
            return SuspensionEditor(self.workspace, path, self)
        if name.endswith(".ini"):
            return ConfigEditor(self.workspace, path, self)
        return RawTextEditor(self.workspace, path, self)

    def save_active(self):
        editor = self.active_editor
        if editor is not None:
            editor.save()

    def on_editor_dirty_changed(self, editor: BaseEditor):
        if str(editor) in self.workspace.tabs():
            marker = " ●" if editor.dirty else ""
            self.workspace.tab(editor,
                               text=f"  {editor.display_name}{marker}  ")

    # -- tab closing --------------------------------------------------------
    def close_tab(self, index: int):
        try:
            widget = self.nametowidget(self.workspace.tabs()[index])
        except (IndexError, KeyError, tk.TclError):
            return
        if isinstance(widget, BaseEditor) and widget.dirty:
            answer = messagebox.askyesnocancel(
                "Unsaved changes",
                f"Save changes to {widget.display_name} before closing?",
                parent=self)
            if answer is None:
                return
            if answer:
                widget.save()
        for key, ed in list(self._editors.items()):
            if ed is widget:
                del self._editors[key]
        self.workspace.forget(index)
        widget.destroy()

    def close_active_tab(self):
        try:
            self.close_tab(self.workspace.index(self.workspace.select()))
        except tk.TclError:
            pass

    # ----------------------------------------------------- ADD COMPONENT ▾
    def _build_component_menu(self):
        menu = self.component_menu
        menu.delete(0, "end")
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
                    label=f"► Add ALL {group} variants",
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
                    e.save()
        self._save_settings()
        self.destroy()


def main():
    app = ACModStudio()
    app.mainloop()


if __name__ == "__main__":
    main()

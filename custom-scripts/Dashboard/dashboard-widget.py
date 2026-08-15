#!/usr/bin/env python3
"""
dashboard-widget.py

A Conky-style GTK4 Layer Shell desktop widget version of dashboard.py.
Reuses the exact same data-gathering logic (subprocess calls, git checks,
budget-buddy hookup, etc.) but instead of printing ANSI-colored text to a
terminal, it renders the same colors as Pango markup inside a floating,
click-through-able desktop widget - built the same way as conky-widget.py
(Gtk4LayerShell, theme CSS hot-reload, background layer, etc).

Auto-refresh:
  - Clock ticks every 1s (cheap)
  - Full data refresh (updates/cache/git/budget/tasks) runs every
    REFRESH_INTERVAL_MS on a background thread, so slow calls like
    `checkupdates` / `yay -Qua` never freeze the UI.
  - Theme colors (bg/fg) are re-read every 2s, exactly like conky-widget.py,
    so it stays in sync if you switch your color scheme live.
"""

import os
import re
import json
import shutil
import subprocess
import threading
from datetime import datetime
from ctypes import CDLL

# Ensure Gtk4LayerShell is available (same guard as conky-widget.py)
try:
    CDLL("libgtk4-layer-shell.so")
except OSError:
    CDLL("/usr/lib/libgtk4-layer-shell.so")

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')

from gi.repository import Gtk, Gdk, GLib, Gtk4LayerShell

# --- Configuration (unchanged from dashboard.py) ---
VERSION = "1.8.5"
BACKUP_DIR = os.path.expanduser("~/dotfiles")
TASKS_JSON = os.path.expanduser("~/.local/share/arch_task_manager/tasks.json")
SYNC_CACHE = os.path.expanduser("~/.cache/last_synced")

PROJECTS = [
    os.path.expanduser("~/arch-projects/XC-Manager"),
    os.path.expanduser("~/arch-projects/mend"),
    os.path.expanduser("~/arch-projects/RTM"),
    os.path.expanduser("~/arch-projects/Budget-Buddy"),
    os.path.expanduser("~/arch-projects/oversight"),
    os.path.expanduser("~/arch-projects/MIREC"),
    os.path.expanduser("~/arch-projects/MiseBrowser"),
]

LIVE_CONFIGS = [
    os.path.expanduser("~/.config/hypr"),
    os.path.expanduser("~/.config/kitty"),
    os.path.expanduser("~/.config/fastfetch"),
    os.path.expanduser("~/custom-scripts"),
]

# Same theme file conky-widget.py reads --clock-bg/--clock-fg from
THEME_FILE = os.path.expanduser("~/custom-scripts/current-theme.css")

# How often to re-run the (potentially slow) data checks
REFRESH_INTERVAL_MS = 300_000  # 3m - updates/git/yay calls are heavy
CLOCK_INTERVAL_MS = 1_000      # 1s
THEME_INTERVAL_MS = 2_000      # 2s, matches conky-widget.py

# --- ANSI color codes used by the original terminal script ---
CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BOLD = '\033[1m'
RESET = '\033[0m'

# Map ANSI SGR codes -> hex colors used in the widget (Pango markup)
ANSI_TO_HEX = {
    '96': '#89dceb',  # cyan
    '92': '#a6e3a1',  # green
    '93': '#f9e2af',  # yellow
    '91': '#f38ba8',  # red
}


def ansi_to_pango(text: str) -> str:
    """
    Converts a string containing the ANSI escape codes used throughout
    dashboard.py (CYAN/GREEN/YELLOW/RED/BOLD/RESET) into Pango markup so it
    can be dropped straight into a Gtk.Label with set_markup().
    """
    out = []
    open_span = False
    bold = False
    i = 0
    pattern = re.compile(r'\033\[(\d+)m')

    pos = 0
    for m in pattern.finditer(text):
        # escape + append the literal text before this code
        literal = text[pos:m.start()]
        if literal:
            out.append(GLib.markup_escape_text(literal))
        pos = m.end()

        code = m.group(1)
        if code == '0':  # RESET
            if bold:
                out.append('</b>')
                bold = False
            if open_span:
                out.append('</span>')
                open_span = False
        elif code == '1':  # BOLD
            out.append('<b>')
            bold = True
        elif code in ANSI_TO_HEX:
            if open_span:
                out.append('</span>')
            out.append(f'<span foreground="{ANSI_TO_HEX[code]}">')
            open_span = True

    tail = text[pos:]
    if tail:
        out.append(GLib.markup_escape_text(tail))
    if bold:
        out.append('</b>')
    if open_span:
        out.append('</span>')

    return ''.join(out)


# ---------------------------------------------------------------------------
# Data gathering - ported as-is from dashboard.py (still returns ANSI text,
# which ansi_to_pango() converts for display).
# ---------------------------------------------------------------------------

def get_updates():
    try:
        official = subprocess.check_output(["checkupdates"], stderr=subprocess.DEVNULL).decode().count('\n')
    except Exception:
        official = 0
    try:
        aur_output = subprocess.check_output(["yay", "-Qua", "--quiet"], stderr=subprocess.DEVNULL).decode().strip()
        aur = len([line for line in aur_output.split('\n') if line])
    except Exception:
        aur = 0
    total = official + aur
    if total == 0:
        return f"{GREEN}Up-to-date{RESET}"
    color = YELLOW if total < 15 else RED
    if aur > 0:
        return f"{color}{total} Total ({aur} AUR){RESET}"
    return f"{color}{total} Pending{RESET}"


def get_cache_size():
    cache_path = "/var/cache/pacman/pkg/"
    if not os.path.exists(cache_path):
        return "N/A"
    try:
        total = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(cache_path) for f in fs)
        gb = total / (1024 ** 3)
        color = RED if gb > 10 else (YELLOW if gb > 5 else GREEN)
        return f"{color}{gb:.1f} GB{RESET}"
    except Exception:
        return "Error"


def get_pending_tasks():
    if not os.path.exists(TASKS_JSON):
        return f"{YELLOW}No Data{RESET}"
    try:
        with open(TASKS_JSON, 'r') as f:
            tasks = json.load(f)
            pending = sum(1 for t in tasks if not (t.get('completed') or t.get('status') == 'done'))
            return f"{YELLOW}{pending} Pending{RESET}"
    except Exception:
        return f"{RED}Error{RESET}"


def check_live_changes():
    """Checks if live config files are newer than the last dotsync."""
    if not os.path.exists(SYNC_CACHE):
        return True

    last_sync_time = os.path.getmtime(SYNC_CACHE)
    for path in LIVE_CONFIGS:
        if os.path.exists(path):
            for root, _, files in os.walk(path):
                for f in files:
                    try:
                        if os.path.getmtime(os.path.join(root, f)) > last_sync_time:
                            return True
                    except OSError:
                        continue
    return False


def get_git_status():
    def check_repo(path):
        if not os.path.exists(path):
            return "missing"
        try:
            is_dirty = subprocess.check_output(["git", "-C", path, "status", "--porcelain"], stderr=subprocess.DEVNULL).decode().strip()
            ahead = subprocess.check_output(["git", "-C", path, "rev-list", "@{u}..HEAD"], stderr=subprocess.DEVNULL).decode().count('\n')
            if is_dirty:
                return "dirty"
            if ahead > 0:
                return f"ahead:{ahead}"
            return "clean"
        except Exception:
            return "error"

    dirty_projects = []
    ahead_projects = []

    for path in PROJECTS:
        name = os.path.basename(path)
        status = check_repo(path)
        if status == "dirty":
            dirty_projects.append(name)
        elif "ahead" in status:
            ahead_projects.append(name)

    if dirty_projects:
        proj_display = f"{RED}Dirty{RESET} ({', '.join(dirty_projects)})"
    elif ahead_projects:
        proj_display = f"{GREEN}Clean{RESET} {YELLOW}↑ ({', '.join(ahead_projects)}){RESET}"
    else:
        proj_display = f"{GREEN}Clean{RESET}"

    dot_raw = check_repo(BACKUP_DIR)
    dot_status = f"{RED}Dirty{RESET}" if dot_raw == "dirty" else f"{GREEN}Clean{RESET}"
    if "ahead" in dot_raw:
        dot_status = f"{GREEN}Clean{RESET} {YELLOW}↑{RESET}"

    try:
        with open(SYNC_CACHE, 'r') as f:
            sync_date = f.read().strip()
    except Exception:
        sync_date = "Never"

    return {"dots": dot_status, "proj": proj_display, "date": sync_date}


def get_budget_status():
    try:
        path = os.path.expanduser("~/arch-projects/Budget-Buddy/budget-buddy.py")
        result = subprocess.check_output(["python", path, "--stats"], stderr=subprocess.DEVNULL).decode().strip()
        return result
    except Exception:
        return f"{RED}Budget Data Unavailable{RESET}"


def gather_snapshot():
    """Runs all data checks and returns a dict of ANSI-colored strings."""
    git_data = get_git_status()
    needs_sync = check_live_changes()

    dot_status = git_data['dots']
    if needs_sync:
        dot_status = f"{RED}Sync Required{RESET}"

    free_gb = shutil.disk_usage(os.path.expanduser('~')).free // (2 ** 30)

    return {
        "storage": f"{free_gb} GB Free",
        "tasks": get_pending_tasks(),
        "updates": get_updates(),
        "dots": f"{dot_status} ({git_data['date']})",
        "cache": get_cache_size(),
        "proj": git_data['proj'],
        "budget": get_budget_status(),
    }


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------

class DashboardWidget(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.rakosn1cek.dashboard.widget")
        self.css_provider = Gtk.CssProvider()
        self.rows = {}
        self.row_prefixes = {}

    def do_activate(self):
        window = Gtk.ApplicationWindow(application=self)
        window.set_title("dashboard-widget")
        window.set_css_classes(["main-window"])

        # Layer Shell configuration (matching conky-widget.py)
        Gtk4LayerShell.init_for_window(window)
        Gtk4LayerShell.set_layer(window, Gtk4LayerShell.Layer.BACKGROUND)
        Gtk4LayerShell.set_anchor(window, Gtk4LayerShell.Edge.RIGHT, True)
        Gtk4LayerShell.set_anchor(window, Gtk4LayerShell.Edge.TOP, True)

        # Adjust these to place the widget wherever you like on screen
        Gtk4LayerShell.set_margin(window, Gtk4LayerShell.Edge.RIGHT, 5)
        Gtk4LayerShell.set_margin(window, Gtk4LayerShell.Edge.TOP, 500)

        Gtk4LayerShell.set_keyboard_mode(window, Gtk4LayerShell.KeyboardMode.NONE)
        Gtk4LayerShell.set_namespace(window, "dashboard-widget")

        # Hard-lock the window width. Without this, GTK's size negotiation
        # lets a long unbroken line (like Budget) request extra width from
        # the compositor and the window grows to fit it - which, since we're
        # anchored to the RIGHT edge, makes it stretch further left. Setting
        # a fixed, non-resizable size forces every child to wrap/lay out
        # inside exactly this width instead.
        WIDGET_WIDTH = 280
        window.set_default_size(WIDGET_WIDTH, -1)
        window.set_resizable(False)

        # --- UI layout ---
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        outer.set_margin_start(16)
        outer.set_margin_end(16)
        outer.set_margin_top(14)
        outer.set_margin_bottom(14)
        # Match conky-widget.py's clock widget width (265px) so both line up
        outer.set_size_request(WIDGET_WIDTH, -1)
        outer.set_hexpand(False)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title_lbl = Gtk.Label(xalign=0, hexpand=True)
        title_lbl.set_markup(f'<span foreground="{ANSI_TO_HEX["96"]}"><b>󰣇 SYSTEM REPORT</b></span>')
        self.clock_lbl = Gtk.Label(xalign=1)
        self.clock_lbl.set_name("ClockLabel")
        header.append(title_lbl)
        header.append(self.clock_lbl)
        outer.append(header)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        outer.append(sep)

        # Single narrow column - one stat per line, label and value share
        # the same line and wrap together if the value is long.
        rows_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        outer.append(rows_box)

        def make_row(icon, label_text, key, initial=None):
            lbl = Gtk.Label(xalign=0)
            lbl.set_name("MonitorLabel")
            lbl.set_hexpand(False)
            lbl.set_wrap(True)
            lbl.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
            lbl.set_max_width_chars(30)
            lbl.set_justify(Gtk.Justification.LEFT)
            prefix = f"<b>{icon} {label_text}:</b> "
            lbl.set_markup(initial if initial is not None else prefix + "...")
            rows_box.append(lbl)
            self.rows[key] = lbl
            self.row_prefixes[key] = prefix

        make_row("💾", "Storage", "storage")
        make_row("📝", "Tasks", "tasks")
        make_row("📦", "Updates", "updates")
        make_row("󱓞", "Dots", "dots")
        make_row("󰒋", "Cache", "cache")
        make_row("󱚝", "Proj", "proj")
        make_row("󱚝", "Budget", "budget", initial="<b>󱚝 Budget:</b>\n    ...")

        window.set_child(outer)

        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self.load_theme()
        GLib.timeout_add(THEME_INTERVAL_MS, self.load_theme)

        self.update_clock()
        GLib.timeout_add(CLOCK_INTERVAL_MS, self.update_clock)

        # Kick off first data refresh immediately, then on the interval
        self.refresh_data()
        GLib.timeout_add(REFRESH_INTERVAL_MS, self.refresh_data)

        window.present()

    def load_theme(self):
        """Same theme hot-reload approach as conky-widget.py."""
        bg_color = None
        fg_color = None

        if os.path.exists(THEME_FILE):
            try:
                with open(THEME_FILE, "r", encoding="utf-8") as f:
                    content = f.read()
                    bg_match = re.search(r'--clock-bg:\s*([^;\n}]+)', content)
                    fg_match = re.search(r'--clock-fg:\s*([^;\n}]+)', content)
                if bg_match:
                    bg_color = bg_match.group(1).strip()
                if fg_match:
                    fg_color = fg_match.group(1).strip()
            except Exception:
                pass

        if not bg_color or not fg_color:
            GLib.timeout_add(1000, self.load_theme)
            return False

        clean_gtk_css = f"""
            .main-window {{
                background-color: {bg_color};
                border: 1px solid #767b7e;
                border-radius: 4px;
            }}
            #MonitorLabel {{
                font-family: 'JetBrains Mono', monospace;
                font-size: 12px;
                font-weight: 600;
                color: {fg_color};
            }}
            #ClockLabel {{
                font-family: 'JetBrains Mono', monospace;
                font-size: 13px;
                color: {fg_color};
            }}
            separator {{
                background-color: alpha({fg_color}, 0.25);
                min-height: 1px;
            }}
        """
        self.css_provider.load_from_data(clean_gtk_css.encode('utf-8'))
        return True

    def update_clock(self):
        self.clock_lbl.set_markup(datetime.now().strftime('%H:%M:%S'))
        return True

    def refresh_data(self):
        """Runs the (possibly slow) data collection off the GTK main thread."""
        threading.Thread(target=self._refresh_worker, daemon=True).start()
        return True

    def _refresh_worker(self):
        try:
            snapshot = gather_snapshot()
        except Exception as e:
            snapshot = {k: f"{RED}Error{RESET}" for k in
                        ("storage", "tasks", "updates", "dots", "cache", "proj", "budget")}
            snapshot["budget"] = f"{RED}Error: {e}{RESET}"
        GLib.idle_add(self._apply_snapshot, snapshot)

    def _apply_snapshot(self, snapshot):
        for key, value in snapshot.items():
            label = self.rows.get(key)
            if label is None:
                continue
            prefix = self.row_prefixes.get(key, "")
            if key == "budget":
                label.set_markup(self._format_budget(prefix, value))
            else:
                label.set_markup(prefix + ansi_to_pango(value))
        return False

    @staticmethod
    def _format_budget(prefix, ansi_text):
        """
        Splits the single pipe-separated budget-buddy line
        ("Today: X | Month: Y | Bills: Z | Net: W") into its own indented
        line per item, so a long budget string can never force the fixed
        265px-wide window to stretch wider.
        """
        # Header line ("Budget:") on its own, no trailing value
        lines = [prefix.rstrip()]
        segments = [seg.strip() for seg in ansi_text.split('|') if seg.strip()]
        if not segments:
            # e.g. "Budget Data Unavailable" - no pipes to split on
            lines.append("    " + ansi_to_pango(ansi_text))
        else:
            for seg in segments:
                lines.append("    " + ansi_to_pango(seg))
        return "\n".join(lines)


if __name__ == "__main__":
    import sys
    app = DashboardWidget()
    sys.exit(app.run(sys.argv))

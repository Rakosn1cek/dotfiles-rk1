#!/usr/bin/env python3

# ------------------------------------------------------------------------
# Theme Configuration - Standalone styling control for all widgets
# VERSION: 0.1.0
# Author: Lukas Grumlik - Rakosn1cek
# May 2026
# LICENSE: MIT
# ------------------------------------------------------------------------

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk
import os
import subprocess
import re

# --- Core Configuration Paths ---
THEME_FILE = os.path.expanduser("~/custom-scripts/current-theme.css")

# --- Default Fallback State ---
STATE = {
    "bg": "#1d2021",
    "text": "#ffffff",
    "hint": "#aaaaaa",
    "accent": "#9c7321"
}

# --- Background Preset Profiles ---
BG_PROFILES = {
    "dark": {
        "bg": "rgba(53, 53, 54, 0.8)",
        "text": "#ffffff",
        "hint": "#ffffff"
    },
    "d-glass": {
        "bg": "rgba(0, 0, 0, 0.4)",
        "text": "#e0e6ed",
        "hint": "#ffffff"
    },
    "clear": {
        "bg": "rgba(0, 0, 0, 0)",
        "text": "#e0e6ed",
        "hint": "#ffffff"
    },
    "light": {
        "bg": "rgba(247, 247, 247, 0.6)",
        "text": "#000000",
        "hint": "#555555"
    },
    "l-glass": {
        "bg": "rgba(240, 240, 240, 0.2)",
        "text": "#000000",
        "hint": "#202928"
    },
    "teal": {
        "bg": "rgba(0, 128, 129, 0.4)",
        "text": "#000000",
        "hint": "#ffffff"
    },
    "paper": {
        "bg": "rgba(251, 241, 199, 0.8)",
        "text": "#3c3836",
        "hint": "#7c6f64"
    },
    "translucent": {
        "bg": "rgba(74, 74, 74, 0.6)",
        "text": "#ffffff",
        "hint": "#aaaaaa"
    }
    
}

# --- Fixed Accent Color Palette Map ---
ACCENTS = {
    "Red": "#960723",
    "Blue": "#0e5989",
    "Gray": "#b7b7b8",
    "Cyan": "#51fefc",
    "Magenta": "#9d2dc0",
    "Green": "#29e171",
    "Yellow": "#c9a800",
    "Black": "#151515",
    "Fire": "rgba(255, 137, 22, 0.86)",
    "Flames": "#f8541f",
    "Brown": "#352e12",
    "Pink": "#f25bff",
    "White": "#ffffff",
    "Teal": "#008081",
    "Vintage": "#f4dcba"
}

# --- Base Application Styling ---
CSS_TEMPLATE = """
window {{ background-color: transparent; }}
.main-window {{ background-color: {bg}; border: 1px solid {accent}; border-radius: 4px; padding: 10px; }}
.header-title {{ color: {text}; font-family: 'JetBrains Mono'; font-size: 16px; font-weight: bold; padding: 10px; }}
.header-hint {{ color: {hint}; font-family: 'JetBrains Mono'; font-size: 9px; opacity: 0.9; }}
.row-label {{ color: {text}; font-family: 'JetBrains Mono'; font-size: 16px; padding: 5px; margin-right: 8px; }}

/* Mode Choice Selection Elements */
.mode-btn {{ background-color: #282828; color: #ffffff; font-family: 'JetBrains Mono'; font-size: 12px; border: 1px solid #3c3836; padding: 5px 12px; margin-right: 1px; }}
.mode-btn:hover {{ border-color: {accent}; }}

/* Dynamic Accent Dot Base Implementation */
.color-dot {{ border-radius: 164px; min-width: 30px; min-height: 30px; border: 0px solid #3c3836; padding: 0px; margin: 0px; }}
.color-dot:hover {{ border-color: {text}; }}
"""

class ThemeWidget(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("theme-widget")
        self.set_keep_above(True)
        self.set_decorated(False)
        self.set_resizable(False)
        # Increased height to fit multi-row selectors comfortably
        self.set_default_size(550, 340)
        
        # Apply transparency handling capabilities
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)
            
        self.load_current_state()
        self.connect("key-press-event", self._on_key)
        self._init_styles()
        self._build_ui()
        self._position_window()

    def load_current_state(self):
        """Reads the actual properties currently set in the QSS sheet to update the STATE matrix."""
        global STATE
        theme_path = os.path.expanduser("~/custom-scripts/Control-Panel/current-theme.css")
        
        if os.path.exists(theme_path):
            try:
                with open(theme_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Using flexible regex patterns to capture either background or background-color variations
                bg_match = re.search(r"QWidget#MainWidget\s*\{\s*background(?:-color)?:\s*([^;]+);", content)
                text_match = re.search(r"QLabel\s*\{\s*color:\s*([^;]+);", content)
                hint_match = re.search(r"QLabel#DateLabel\s*\{\s*color:\s*([^;]+);", content)
                accent_match = re.search(r"border:\s*2px\s*solid\s*([^;]+);", content)
                
                if bg_match:
                    STATE["bg"] = bg_match.group(1).strip()
                if text_match:
                    STATE["text"] = text_match.group(1).strip()
                if hint_match:
                    STATE["hint"] = hint_match.group(1).strip()
                if accent_match:
                    STATE["accent"] = accent_match.group(1).strip()
                    
            except Exception:
                pass
    
    def _init_styles(self):
        self.prov = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), self.prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self._update_css()

    def _update_css(self):
        raw_css = CSS_TEMPLATE.format(**STATE)
        self.prov.load_from_data(raw_css.encode())

    def _build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.get_style_context().add_class("main-window")
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        main_box.set_margin_start(14)
        main_box.set_margin_end(14)
        self.add(main_box)

        # --- Header Section ---
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        title = Gtk.Label(label="󰏘  THEME CONFIGURATION")
        title.get_style_context().add_class("header-title")
        hint = Gtk.Label(label="ESC to exit")
        hint.get_style_context().add_class("header-hint")
        header.pack_start(title, False, False, 0)
        header.pack_end(hint, False, False, 0)
        main_box.pack_start(header, False, False, 0)

        # Separator Line
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.pack_start(sep, False, False, 0)

        # Size group to enforce uniform width across row label columns
        label_group = Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL)

        # --- Mode Section: Row 1 ---
        row1_1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        row1_lbl = Gtk.Label(label="Mode:")
        row1_lbl.set_xalign(0.0)
        row1_lbl.get_style_context().add_class("row-label")
        label_group.add_widget(row1_lbl)
        row1_1.pack_start(row1_lbl, False, False, 0)

        # --- Mode Section: Row 2 ---
        row1_2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        row1_spacer = Gtk.Label()
        label_group.add_widget(row1_spacer)
        row1_2.pack_start(row1_spacer, False, False, 0)

        modes = list(BG_PROFILES.keys())
        mid_mode = (len(modes) + 1) // 2

        for mode_name in modes[:mid_mode]:
            btn = self._make_mode_button(mode_name)
            row1_1.pack_start(btn, True, True, 0)

        for mode_name in modes[mid_mode:]:
            btn = self._make_mode_button(mode_name)
            row1_2.pack_start(btn, True, True, 0)

        main_box.pack_start(row1_1, False, False, 0)
        main_box.pack_start(row1_2, False, False, 0)

        # Spacer break between structural modules
        main_box.pack_start(Gtk.Box(), False, False, 2)

        # --- Accent Section: Row 1 ---
        row2_1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        row2_lbl = Gtk.Label(label="Accent:")
        row2_lbl.set_xalign(0.0)
        row2_lbl.get_style_context().add_class("row-label")
        label_group.add_widget(row2_lbl)
        row2_1.pack_start(row2_lbl, False, False, 0)

        # --- Accent Section: Row 2 ---
        row2_2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        row2_spacer = Gtk.Label()
        label_group.add_widget(row2_spacer)
        row2_2.pack_start(row2_spacer, False, False, 0)

        accents_list = list(ACCENTS.items())
        mid_accent = (len(accents_list) + 1) // 2

        dots_container1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        for name, hex_code in accents_list[:mid_accent]:
            dot_btn = self._make_accent_dot(name, hex_code)
            dots_container1.pack_start(dot_btn, False, False, 0)
        row2_1.pack_start(dots_container1, True, True, 0)

        dots_container2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        for name, hex_code in accents_list[mid_accent:]:
            dot_btn = self._make_accent_dot(name, hex_code)
            dots_container2.pack_start(dot_btn, False, False, 0)
        row2_2.pack_start(dots_container2, True, True, 0)

        main_box.pack_start(row2_1, False, False, 0)
        main_box.pack_start(row2_2, False, False, 0)

    def _make_mode_button(self, mode_name):
        btn_label = mode_name.capitalize()
        if mode_name == "dark": btn_label = "󰖔 Dark"
        elif mode_name == "d-glass": btn_label = "󰛢 D-Glass"
        elif mode_name == "light": btn_label = "󰖙 Light"
        elif mode_name == "l-glass": btn_label = "󰛢 L-Glass"
        elif mode_name == "teal": btn_label = " Teal"
        elif mode_name == "paper": btn_label = "󰃛 Paper"
        elif mode_name == "translucent": btn_label = " Gray"

        btn = Gtk.Button(label=btn_label)
        btn.get_style_context().add_class("mode-btn")
        btn.connect("clicked", self._set_base_mode, mode_name)
        return btn

    def _make_accent_dot(self, name, hex_code):
        dot_btn = Gtk.Button()
        dot_btn.get_style_context().add_class("color-dot")
        
        dot_prov = Gtk.CssProvider()
        dot_prov.load_from_data(f"button {{ background-color: {hex_code}; background-image: none; }}".encode())
        dot_btn.get_style_context().add_provider(dot_prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        dot_btn.connect("clicked", self._set_accent_mode, hex_code)
        dot_btn.set_tooltip_text(name)
        return dot_btn

    def _position_window(self):
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor() or display.get_monitor(0)
        geo = monitor.get_geometry()
        
        x = geo.x + (geo.width - 550) // 1
        # Adjusted height parameter offset tracking for structural balance
        y = geo.y + geo.height - 340 - 40
        self.move(x, y)

    def _set_base_mode(self, _, mode):
        if mode in BG_PROFILES:
            profile = BG_PROFILES[mode]
            STATE["bg"] = profile["bg"]
            STATE["text"] = profile["text"]
            STATE["hint"] = profile["hint"]
        
        self._update_css()
        self._write_and_reload()

    def _set_accent_mode(self, _, hex_code):
        STATE["accent"] = hex_code
        self._update_css()
        self._write_and_reload()

    def _write_and_reload(self):
        output_qss = (
            "QWidget#MainWidget { background-color: " + STATE["bg"] + "; border: 2px solid " + STATE["accent"] + "; }\n"
            "QFrame#Section { border: 1px solid " + STATE["accent"] + "; border-radius: 4px; background-color: " + STATE["bg"] + "; }\n"
            
            # Label selectors enforcing explicit font styling parameters
            "QLabel { color: " + STATE["text"] + "; font-family: 'JetBrains Mono'; font-size: 14px; font-weight: 900; }\n"
            "QLabel#ClockLabel { color: " + STATE["accent"] + "; font-family: 'JetBrains Mono'; font-size: 36px; font-weight: bold; }\n"
            "QLabel#DateLabel { color: " + STATE["hint"] + "; font-family: 'JetBrains Mono'; font-size: 14px; }\n"
            "QLabel#TempLabel { color: " + STATE["accent"] + "; font-family: 'JetBrains Mono'; }\n"
            "QLabel#TrackerProjectLabel { color: " + STATE["text"] + "; font-family: 'JetBrains Mono'; }\n"
            "QLabel#TrackerStatusIcon { color: " + STATE["accent"] + "; font-family: 'JetBrains Mono'; }\n"
            
            # Form elements and list configurations
            "QLineEdit { background-color: " + STATE["bg"] + "; border: 1px solid " + STATE["accent"] + "; color: " + STATE["text"] + "; padding: 5px; border-radius: 4px; font-family: 'JetBrains Mono'; }\n"
            "QLineEdit:focus { border: 2px solid " + STATE["accent"] + "; outline: none; }\n"
            "QListWidget { background-color: " + STATE["bg"] + "; border: 1px solid " + STATE["accent"] + "; color: " + STATE["text"] + "; outline: none; border-radius: 4px; font-family: 'JetBrains Mono'; }\n"
            "QListWidget::item { padding: 8px; border-bottom: 1px solid #111111; font-family: 'JetBrains Mono'; }\n"
            "QListWidget::item:selected { background-color: " + STATE["accent"] + "; color: " + STATE["bg"] + "; font-weight: bold; font-family: 'JetBrains Mono'; }\n"
            
            # Global button behaviors
            "QPushButton { background-color: " + STATE["bg"] + "; border: 1px solid " + STATE["accent"] + "; color: " + STATE["text"] + "; padding: 8px; font-family: 'JetBrains Mono'; font-size: 14px; border-radius: 4px; }\n"
            "QPushButton:hover { background-color: #222222; border-color: " + STATE["text"] + "; }\n"
            "QPushButton:focus { background-color: #b0b0b0; border: 2px solid " + STATE["text"] + "; outline: none; }\n"
            
            # Contextual panel buttons
            "QPushButton#ActiveProfile, QPushButton#ActiveWorkspace { background-color: " + STATE["accent"] + "; color: " + STATE["bg"] + "; font-weight: bold; border: 1px solid " + STATE["text"] + "; font-family: 'JetBrains Mono'; font-size: 14px; }\n"
            "QPushButton#ActiveWorkspace:focus { border: 2px solid " + STATE["text"] + "; }\n"
            "QPushButton#TaskItem { font-size: 12px; padding: 4px 6px; min-width: 70px; background-color: " + STATE["bg"] + "; border-color: " + STATE["accent"] + "; color: " + STATE["text"] + "; font-family: 'JetBrains Mono'; }\n"
            "QPushButton#TaskItem:focus { border: 2px solid " + STATE["text"] + "; }\n"
            
            # System tools navigation nodes
            "QPushButton#ToolButton { font-size: 16px; padding: 10px; background-color: " + STATE["bg"] + "; border-color: " + STATE["accent"] + "; color: " + STATE["text"] + "; font-family: 'JetBrains Mono'; }\n"
            "QPushButton#ToolButton:focus { border: 2px solid " + STATE["text"] + "; }\n"
            "QPushButton#ToolButton[connected='true'] { color: #52fa69; }\n"
            "QPushButton#ToolButton[objectName='ToolButton'][id='bt'][connected='true'] { color: #3b82f6; }\n"
            "QPushButton#ToolButton[connected='false'] { color: " + STATE["text"] + "; }\n"
            "QPushButton#ToolButton[connected='wifi_on'] { color: #52fa69; }\n"
            "QPushButton#ToolButton[connected='bt_on'] { color: #3b82f6; }\n"
            "QPushButton#ToolButton[connected='wifi'] { color: #52fa69; }\n"
            "QPushButton#ToolButton[connected='bluetooth'] { color: #3b82f6; }\n"
            "QPushButton#ToolButton[connected='none'] { color: " + STATE["text"] + "; }\n"
            
            # Bottom bar session triggers
            "QPushButton#PowerBtn_󰐥 { font-size: 16px; background-color: " + STATE["bg"] + "; border-color: " + STATE["accent"] + "; color: #ff5555; font-family: 'JetBrains Mono'; }\n"
            "QPushButton#PowerBtn_󰑐 { font-size: 16px; background-color: " + STATE["bg"] + "; border-color: " + STATE["accent"] + "; color: #21ab00; font-family: 'JetBrains Mono'; }\n"
            "QPushButton#PowerBtn_󰤄 { font-size: 16px; background-color: " + STATE["bg"] + "; border-color: " + STATE["accent"] + "; color: #bd93f9; font-family: 'JetBrains Mono'; }\n"
            "QPushButton#PowerBtn_󰈆 { font-size: 16px; background-color: " + STATE["bg"] + "; border-color: " + STATE["accent"] + "; color: #8be9fd; font-family: 'JetBrains Mono'; }\n"
            "QPushButton#PowerBtn_󰖔 { font-size: 16px; background-color: " + STATE["bg"] + "; border-color: " + STATE["accent"] + "; color: #ffb86c; font-family: 'JetBrains Mono'; }\n"
            "QPushButton[objectName^='PowerBtn_']:focus { border: 2px solid " + STATE["text"] + "; }\n"
            
            # Sliders, tracking graphics, and scrollbars
            "QProgressBar { border: none; background-color: #111111; height: 4px; border-radius: 5px; color: transparent; }\n"
            "QProgressBar::chunk { background-color: " + STATE["accent"] + "; border-radius: 5px; }\n"
            "QSlider::groove:horizontal { border: none; height: 4px; background: #333333; }\n"
            "QSlider::handle:horizontal { background: " + STATE["accent"] + "; border: 0px solid #ffffff; width: 4px; height: 14px; margin: -7px 0; }\n"
            "QScrollBar { border: none; background: #000000; width: 8px; height: 8px; margin: 0px; }\n"
            "QScrollBar::handle { background: #333333; min-height: 20px; min-width: 20px; border-radius: 4px; }\n"
            "QScrollBar::handle:hover { background: " + STATE["accent"] + "; }\n\n"
            
            f":root {{ --clock-bg: {STATE['bg']}; --clock-fg: {STATE['accent']}; }}\n"
        )

        os.makedirs(os.path.dirname(THEME_FILE), exist_ok=True)
        with open(THEME_FILE, "w", encoding="utf-8") as f:
            f.write(output_qss)

        # subprocess.run(["pkill", "-f", "control-panel.py"])
        # subprocess.Popen(["python3", os.path.expanduser("~/custom-scripts/Control-Panel/control-panel.py")])

    def _on_key(self, _, event):
        if event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()

if __name__ == "__main__":
    win = ThemeWidget()
    win.show_all()
    Gtk.main()

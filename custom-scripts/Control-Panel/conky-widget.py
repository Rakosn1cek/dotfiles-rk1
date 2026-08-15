#!/usr/bin/env python3

import sys
import os
import psutil
import re
from ctypes import CDLL

# Ensure Gtk4LayerShell is available
try:
    CDLL("libgtk4-layer-shell.so")
except OSError:
    CDLL("/usr/lib/libgtk4-layer-shell.so")

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')

from gi.repository import Gtk, Gdk, GLib, Gtk4LayerShell

THEME_FILE = os.path.expanduser("~/custom-scripts/current-theme.css")

class ConkyWidget(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.rakosn1cek.conky.monitor")
        self.css_provider = Gtk.CssProvider()

    def do_activate(self):
        window = Gtk.ApplicationWindow(application=self)
        window.set_title("conky-monitor")
        window.set_css_classes(["main-window"])
        
        # Layer Shell configuration (matching desktop-clock.py)
        Gtk4LayerShell.init_for_window(window)
        Gtk4LayerShell.set_layer(window, Gtk4LayerShell.Layer.BACKGROUND)
        Gtk4LayerShell.set_anchor(window, Gtk4LayerShell.Edge.LEFT, True)
        Gtk4LayerShell.set_anchor(window, Gtk4LayerShell.Edge.TOP, True)
        
        Gtk4LayerShell.set_margin(window, Gtk4LayerShell.Edge.LEFT, 1605)
        Gtk4LayerShell.set_margin(window, Gtk4LayerShell.Edge.TOP, 150)
        
        Gtk4LayerShell.set_keyboard_mode(window, Gtk4LayerShell.KeyboardMode.NONE)
        Gtk4LayerShell.set_namespace(window, "conky-monitor")

        # UI Layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=30)
        vbox.set_margin_start(15)
        vbox.set_margin_end(15)
        vbox.set_margin_top(15)
        vbox.set_margin_bottom(15)
        vbox.set_size_request(280, 300)
        
        self.cpu_lbl = Gtk.Label(label="CPU: --", xalign=0)
        self.cpu_lbl.set_name("MonitorLabel")
        self.cpu_bar = Gtk.ProgressBar()
        
        self.ram_lbl = Gtk.Label(label="RAM: --", xalign=0)
        self.ram_lbl.set_name("MonitorLabel")
        self.ram_bar = Gtk.ProgressBar()
        
        self.temp_lbl = Gtk.Label(label="󰔏 Temp: --", xalign=0)
        self.temp_lbl.set_name("MonitorLabel")
        
        self.bat_lbl = Gtk.Label(label="Battery: Checking...", xalign=0)
        self.bat_lbl.set_name("MonitorLabel")
        self.bat_lbl.set_wrap(True)
        
        vbox.append(self.cpu_lbl)
        vbox.append(self.cpu_bar)
        vbox.append(self.ram_lbl)
        vbox.append(self.ram_bar)
        vbox.append(self.temp_lbl)
        vbox.append(self.bat_lbl)
        
        window.set_child(vbox)

        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.load_theme()
        GLib.timeout_add(2000, self.load_theme)
        
        GLib.timeout_add(2000, self.update_data)
        window.present()

    def load_theme(self):
        """Extracts variables natively to avoid passing incompatible Qt code to GTK."""
        bg_color = None
        fg_color = None

        if os.path.exists(THEME_FILE):
            try:
                with open(THEME_FILE, "r", encoding="utf-8") as f:
                    content = f.read()

                    bg_match = re.search(r'--clock-bg:\s*([^;\n}]+)', content)
                    fg_match = re.search(r'--clock-fg:\s*([^;\n}]+)', content)

                if bg_match: bg_color = bg_match.group(1).strip()
                if fg_match: fg_color = fg_match.group(1).strip()
            except Exception:
                pass

        # If values are blank due to a suspend race condition, queue a retry in 1 second
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
                font-size: 14px;
                font-weight: 800;
                color: {fg_color};
            }}
            progressbar {{
                min-height: 8px;
                border-radius: 4px;
                background-color: transparent;
            }}
            progressbar progress {{
                border-radius: 4px;
                background-color: {bg_color};
            }}
        """
        self.css_provider.load_from_data(clean_gtk_css.encode('utf-8'))
        return True

    def get_battery_info(self):
        BAT = "/sys/class/power_supply/BAT0"
        if not os.path.exists(BAT): return "No Battery"
        def read_sys(file):
            try:
                with open(f"{BAT}/{file}", 'r') as f: return int(f.read().strip())
            except: return 0
        cap = read_sys("capacity")
        pwr_mw = read_sys("power_now")
        pwr = pwr_mw / 1_000_000
        full = read_sys("energy_full") or read_sys("charge_full")
        now = read_sys("energy_now") or read_sys("charge_now")
        design = read_sys("energy_full_design") or read_sys("charge_full_design")
        health = int(100 * full / design) if design > 0 else 0
        status = open(f"{BAT}/status").read().strip()
        icon = "󱐋" if status == "Charging" else "󰁹"
        return f"{icon} {cap}% | {pwr:.1f}W | Health: {health}%"

    def update_data(self):
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        
        self.cpu_bar.set_fraction(cpu / 100)
        self.cpu_lbl.set_text(f"CPU: {cpu}%")
        
        used_gb = mem.used / 1073741824
        total_gb = mem.total / 1073741824
        self.ram_bar.set_fraction(mem.percent / 100)
        self.ram_lbl.set_text(f"RAM: {used_gb:.1f}/{total_gb:.1f}GB ({mem.percent}%)")
        
        try:
            temps = psutil.sensors_temperatures()
            core = temps.get('coretemp', temps.get('cpu_thermal', []))[0].current
            self.temp_lbl.set_text(f"󰔏 Temp: {int(core)}°C")
        except: self.temp_lbl.set_text("󰔏 Temp: N/A")
        
        self.bat_lbl.set_text(self.get_battery_info())
        return True

if __name__ == "__main__":
    app = ConkyWidget()
    sys.exit(app.run(sys.argv))

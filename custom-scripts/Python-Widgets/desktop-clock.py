#!/usr/bin/env python3

import sys
import os
import time
import re
from ctypes import CDLL

try:
    CDLL("libgtk4-layer-shell.so")
except OSError:
    CDLL("/usr/lib/libgtk4-layer-shell.so")

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')

from gi.repository import Gtk, Gdk, GLib, Gtk4LayerShell

THEME_FILE = os.path.expanduser("~/custom-scripts/current-theme.css")

class DesktopClock(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.rakosn1cek.desktop.clock")
        self.css_provider = Gtk.CssProvider()

    def do_activate(self):
        window = Gtk.ApplicationWindow(application=self)
        window.set_title("desktop-clock-widget")
        window.set_css_classes(["main-window"])
        
        Gtk4LayerShell.init_for_window(window)
        Gtk4LayerShell.set_layer(window, Gtk4LayerShell.Layer.BACKGROUND)
        Gtk4LayerShell.set_anchor(window, Gtk4LayerShell.Edge.LEFT, True)
        Gtk4LayerShell.set_anchor(window, Gtk4LayerShell.Edge.TOP, True)
        Gtk4LayerShell.set_margin(window, Gtk4LayerShell.Edge.LEFT, 1605)
        Gtk4LayerShell.set_margin(window, Gtk4LayerShell.Edge.TOP, 5)
        Gtk4LayerShell.set_keyboard_mode(window, Gtk4LayerShell.KeyboardMode.NONE)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        vbox.set_margin_top(15)
        vbox.set_margin_bottom(15)
        vbox.set_margin_start(20)
        vbox.set_margin_end(20)
        
        self.time_label = Gtk.Label()
        self.time_label.set_name("ClockLabel")
        
        self.date_label = Gtk.Label()
        self.date_label.set_name("DateLabel")
        
        vbox.append(self.time_label)
        vbox.append(self.date_label)
        window.set_child(vbox)

        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.load_theme()
        GLib.timeout_add(2000, self.load_theme)
        
        self.update_time()
        GLib.timeout_add(10000, self.update_time)
        
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
                border: none;
                box-shadow: none;
                border-radius: 4px;
            }}
            #ClockLabel {{
                font-family: 'JetBrains Mono', monospace;
                font-size: 56pt;
                font-weight: 900;
                color: {fg_color};
            }}
            #DateLabel {{
                font-family: 'JetBrains Mono', monospace;
                font-size: 14pt;
                font-weight: 700;
                color: {fg_color};
                opacity: 0.7;
            }}
        """
        self.css_provider.load_from_data(clean_gtk_css.encode('utf-8'))
        return True

    def update_time(self):
        """Updates the text content of the clock labels using current system metrics."""
        self.time_label.set_text(time.strftime("%H:%M"))
        self.date_label.set_text(time.strftime("%A, %d %B %Y").upper())
        return True

if __name__ == "__main__":
    app = DesktopClock()
    sys.exit(app.run(sys.argv))

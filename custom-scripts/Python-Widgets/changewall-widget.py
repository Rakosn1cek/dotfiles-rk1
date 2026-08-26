#!/usr/bin/env python3
# changewall-widget.py — Minimalist Wallpaper switcher for Control Panel setup
# Uses awww for transitions and matches Control Panel styling.

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf
import os, subprocess, glob, threading, hashlib, re
from concurrent.futures import ThreadPoolExecutor

# --- Configuration ---
WALLPAPER_DIR = os.path.expanduser("~/Pictures/Wallpapers")
CACHE_DIR     = os.path.expanduser("~/.cache/changewall-widget")
THEME_FILE    = os.path.expanduser("~/custom-scripts/current-theme.css")
THUMB_SIZE    = 160
WIDGET_HEIGHT = 220
WIDGET_MARGIN = 335

def load_control_panel_colors():
    """Extracts raw styling colors directly out of the generated current-theme.css structure."""
    defaults = {
        "bg": "#1d2021",
        "accent": "#767b7e",
        "fg": "#ffffff",
        "fg_dim": "#aaaaaa"
    }
    if os.path.exists(THEME_FILE):
        try:
            with open(THEME_FILE, "r", encoding="utf-8") as f:
                content = f.read()
            bg_match = re.search(r"QWidget#MainWidget\s*\{\s*background-color:\s*([^;]+);", content)
            accent_match = re.search(r"border:\s*2px\s*solid\s*([^;]+);", content)
            text_match = re.search(r"QLabel\s*\{\s*color:\s*([^;]+);", content)
            hint_match = re.search(r"QLabel#DateLabel\s*\{\s*color:\s*([^;]+);", content)
            
            if bg_match:
                defaults["bg"] = bg_match.group(1).strip()
            if accent_match:
                defaults["accent"] = accent_match.group(1).strip()
            if text_match:
                defaults["fg"] = text_match.group(1).strip()
            if hint_match:
                defaults["fg_dim"] = hint_match.group(1).strip()
        except Exception:
            pass
    return defaults

# --- Extract active colors prior to stylesheet compiling ---
THEME_PALETTE = load_control_panel_colors()
BG     = THEME_PALETTE["bg"]
ACCENT = THEME_PALETTE["accent"]
FG     = THEME_PALETTE["fg"]
FG_DIM = THEME_PALETTE["fg_dim"]

CSS = f"""
window {{ background-color: {BG}; border: 0px solid {ACCENT}; border-radius: 4px; }}
.frame {{ background-color: {BG}; border-radius: 4px; border: 1px solid {ACCENT}; margin: 6px; }}
.bar   {{ background-color: transparent; padding: 6px 16px 4px 16px; border-bottom: 1px solid #222222; }}
.title {{ color: {FG}; font-family: 'JetBrains Mono'; font-size: 12px; font-weight: bold; }}
.hint  {{ color: {FG_DIM}; font-family: 'JetBrains Mono'; font-size: 10px; opacity: 0.7; }}
.applying {{ color: {ACCENT}; font-family: 'JetBrains Mono'; font-size: 10px; font-weight: bold; }}
.gallery  {{ background-color: transparent; padding: 4px 12px 8px 12px; }}
.thumb-box {{
    background-color: {BG}; border-radius: 4px;
    border: 1px solid #333333; margin: 2px 5px; padding: 4px;
}}
.thumb-box:hover {{ border-color: {ACCENT}; background-color: #222222; }}
.thumb-active {{
    background-color: {BG}; border-radius: 4px;
    border: 1px solid {ACCENT}; margin: 2px 5px; padding: 4px;
}}
.thumb-name        {{ color: {FG_DIM}; font-family: 'JetBrains Mono'; font-size: 9px; }}
.thumb-name-active {{ color: {FG}; font-family: 'JetBrains Mono'; font-size: 9px; font-weight: bold; }}
"""

os.makedirs(CACHE_DIR, exist_ok=True)

def cache_path(wall_path):
    mtime = int(os.path.getmtime(wall_path))
    key   = hashlib.md5(f"{wall_path}{mtime}{THUMB_SIZE}".encode()).hexdigest()[:12]
    return os.path.join(CACHE_DIR, f"{key}.png")

def load_thumbnail(path):
    cp = cache_path(path)
    if os.path.exists(cp):
        try: 
            return GdkPixbuf.Pixbuf.new_from_file(cp)
        except Exception: 
            pass # Properly indented under except
    try:
        pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, THUMB_SIZE, THUMB_SIZE, True)
        w, h = pb.get_width(), pb.get_height()
        if w != h:
            sq = min(w, h)
            pb = pb.new_subpixbuf((w - sq) // 2, (h - sq) // 2, sq, sq)
            pb = pb.scale_simple(THUMB_SIZE, THUMB_SIZE, GdkPixbuf.InterpType.BILINEAR)
        pb.savev(cp, "png", [], [])
        return pb
    except Exception: 
        return None

def find_wallpapers():
    files = []
    for ext in ('*.jpg', '*.jpeg', '*.png', '*.webp'):
        files.extend(glob.glob(os.path.join(WALLPAPER_DIR, ext)))
        files.extend(glob.glob(os.path.join(WALLPAPER_DIR, '**', ext), recursive=True))
    seen, result = set(), []
    for f in sorted(files):
        if f not in seen:
            seen.add(f); result.append(f)
    return result

def extract_wall_color(path):
    """Samples pixel colours directly from thumbnail."""
    try:
        pb = load_thumbnail(path)
        if pb is None:
            pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, 64, 64, True)
            
        if pb is not None:
            grid = pb.scale_simple(16, 16, GdkPixbuf.InterpType.BILINEAR)
            pixels = grid.get_pixels()
            n_channels = grid.get_n_channels()
            rowstride = grid.get_rowstride()
            
            best_color = None
            max_saturation = -1.0
            avg_r, avg_g, avg_b = 0, 0, 0
            count = 0

            for y in range(16):
                row = pixels[y * rowstride : (y + 1) * rowstride]
                for x in range(16):
                    idx = x * n_channels
                    r, g, b = row[idx], row[idx+1], row[idx+2]
                    avg_r += r
                    avg_g += g
                    avg_b += b
                    count += 1
                    
                    mx, mn = max(r, g, b), min(r, g, b)
                    sat = 0.0 if mx == 0 else (mx - mn) / mx
                    
                    if 20 < mx < 240 and sat > max_saturation:
                        max_saturation = sat
                        best_color = (r, g, b)

            if not best_color or max_saturation < 0.08:
                r, g, b = avg_r // count, avg_g // count, avg_b // count
                shift = -50 if r > 128 else 50
                r2 = max(0, min(255, r + shift))
                g2 = max(0, min(255, g + shift))
                b2 = max(0, min(255, b + shift))
            else:
                r, g, b = best_color
                r2 = (r + 40) % 255
                g2 = (g + 80) % 255
                b2 = (b + 120) % 255

            col1 = f"0xff{r:02x}{g:02x}{b:02x}"
            col2 = f"0xff{r2:02x}{g2:02x}{b2:02x}"
            return col1, col2
    except Exception:
        pass
    return "0xff767b7e", "0xff222222"

def apply_wallpaper(path, status_cb, done_cb):
    name = os.path.basename(path)
    GLib.idle_add(status_cb, f"󰐍  Switching to {name}...")
    
    col1, col2 = extract_wall_color(path)

    # awww transition logic
    subprocess.Popen(['awww', 'img', path, '--transition-type', 'fade', 
                        '--transition-pos', 'left', '--transition-fps', '120',
                        '--transition-step', '150'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Cache colours for session persistence and Lua module reading
    cache_file = os.path.expanduser("~/.cache/hypr_border_colors.conf")
    try:
        with open(cache_file, "w") as f:
            f.write(f"{col1},{col2}\n")
    except Exception:
        pass

    # Trigger compositor reload to execute adaptive-borders.lua with updated palette
    subprocess.run(['hyprctl', 'reload'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    GLib.idle_add(status_cb, f"✓  Active: {name}")
    GLib.idle_add(done_cb)

class WallWidget(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("changewall-widget")
        self.set_keep_above(True)
        self.set_decorated(False); self.set_resizable(False)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited(): self.set_visual(visual)

        prov = Gtk.CssProvider()
        prov.load_from_data(CSS.encode())
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.connect("key-press-event", self._on_key)
        self.connect("destroy", Gtk.main_quit)
        self.connect("realize", self._position)

        self._applying = False
        self._thumb_boxes = {}
        self._paths_list = []
        self._current_index = -1

        # Main Layout
        frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        frame.get_style_context().add_class('frame')
        self.add(frame)

        # Bar
        bar = Gtk.Box(); bar.get_style_context().add_class('bar')
        title = Gtk.Label(label="󰸉  WALLPAPER")
        title.get_style_context().add_class('title'); title.set_halign(Gtk.Align.START)
        self.status_lbl = Gtk.Label(label="")
        self.status_lbl.get_style_context().add_class('applying')
        hint = Gtk.Label(label="←/→ Browse  •  ENTER Select  •  ESC Close")
        hint.get_style_context().add_class('hint'); hint.set_halign(Gtk.Align.END)
        
        bar.pack_start(title, False, False, 0)
        bar.pack_start(self.status_lbl, True, True, 0)
        bar.pack_end(hint, False, False, 0)
        frame.pack_start(bar, False, False, 0)

        # Gallery
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        scroll.get_style_context().add_class('gallery')
        self.gallery = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        scroll.add(self.gallery)
        frame.pack_start(scroll, True, True, 0)
        scroll.connect("scroll-event", self._on_scroll)
        self._scroll = scroll

        self._start_loading()

    def _position(self, *_):
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor() or display.get_monitor(0)
        geo = monitor.get_geometry()
        w = geo.width - WIDGET_MARGIN * 2
        x = geo.x + WIDGET_MARGIN
        y = geo.y + geo.height - WIDGET_HEIGHT - 20 # Bottom spacing
        self.set_default_size(w, WIDGET_HEIGHT)
        self.move(x, y)

    def _start_loading(self):
        walls = find_wallpapers()
        if not walls: return
        cached, uncached = [], []
        for p in walls: (cached if os.path.exists(cache_path(p)) else uncached).append(p)
        for path in cached: self._add_thumb(path, load_thumbnail(path))
        if uncached:
            def worker():
                with ThreadPoolExecutor() as ex:
                    for path, pb in zip(uncached, ex.map(load_thumbnail, uncached)):
                        GLib.idle_add(self._add_thumb, path, pb)
            threading.Thread(target=worker, daemon=True).start()

    def _add_thumb(self, path, pb):
        name = os.path.splitext(os.path.basename(path))[0]
        evbox = Gtk.EventBox()
        evbox.get_style_context().add_class('thumb-box')
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        for m in (inner.set_margin_top, inner.set_margin_bottom, inner.set_margin_start, inner.set_margin_end): m(5)
        img = Gtk.Image.new_from_pixbuf(pb) if pb else Gtk.Image.new_from_icon_name("image-missing", Gtk.IconSize.DIALOG)
        img.set_size_request(THUMB_SIZE, THUMB_SIZE)
        inner.pack_start(img, False, False, 0)
        name_lbl = Gtk.Label(label=name[:18] if len(name) <= 18 else name[:16] + "…")
        name_lbl.get_style_context().add_class('thumb-name')
        inner.pack_start(name_lbl, False, False, 0)
        evbox.add(inner)
        evbox.connect("button-press-event", self._on_click, path)
        self.gallery.pack_start(evbox, False, False, 0)
        self._thumb_boxes[path] = (evbox, name_lbl)
        self._paths_list.append(path)
        
        if self._current_index == -1:
            self._current_index = 0
            self._update_highlight()

        self.gallery.show_all()

    def _update_highlight(self):
        if not self._paths_list or self._current_index < 0: return
        target_path = self._paths_list[self._current_index]
        
        for p, (eb, nl) in self._thumb_boxes.items():
            if p == target_path:
                eb.get_style_context().remove_class('thumb-box')
                eb.get_style_context().add_class('thumb-active')
                nl.get_style_context().add_class('thumb-name-active')
                
                # Adjust viewport scroll boundary dynamically
                adj = self._scroll.get_hadjustment()
                alloc = eb.get_allocation()
                # Use default width if the widget asset hasn't completed initial realization
                item_w = alloc.width if alloc.width > 1 else (THUMB_SIZE + 18)
                
                # Compute parent layout offsets
                item_x = eb.translate_coordinates(self.gallery, 0, 0)
                if item_x is not None:
                    item_left = item_x[0]
                    item_right = item_left + item_w
                    
                    view_left = adj.get_value()
                    view_w = self._scroll.get_allocated_width()
                    view_right = view_left + (view_w if view_w > 1 else (Gdk.Screen.get_default().get_primary_monitor().get_geometry().width - WIDGET_MARGIN * 2))
                    
                    if item_left < view_left:
                        adj.set_value(max(0, item_left - 10))
                    elif item_right > view_right:
                        adj.set_value(min(adj.get_upper() - adj.get_page_size(), item_right - view_w + 10))
            else:
                eb.get_style_context().remove_class('thumb-active')
                eb.get_style_context().add_class('thumb-box')
                nl.get_style_context().remove_class('thumb-name-active')

    def _on_click(self, w, event, path):
        if self._applying or event.button != 1: return
        if path in self._paths_list:
            self._current_index = self._paths_list.index(path)
            self._update_highlight()
        self._trigger_switch(path)

    def _trigger_switch(self, path):
        if self._applying: return
        self._applying = True
        threading.Thread(target=apply_wallpaper, args=(path, self._set_status, self._done_applying), daemon=True).start()

    def _set_status(self, msg): self.status_lbl.set_text(msg)
    def _done_applying(self):
        self._applying = False
        GLib.timeout_add(3000, lambda: self.status_lbl.set_text("") or False)

    def _on_scroll(self, widget, event):
        adj = self._scroll.get_hadjustment()
        step = 120
        if event.direction == Gdk.ScrollDirection.DOWN or (event.direction == Gdk.ScrollDirection.SMOOTH and event.delta_y > 0):
            adj.set_value(adj.get_value() + step)
        elif event.direction == Gdk.ScrollDirection.UP or (event.direction == Gdk.ScrollDirection.SMOOTH and event.delta_y < 0):
            adj.set_value(adj.get_value() - step)
        return True

    def _on_key(self, widget, event):
        if event.keyval == Gdk.KEY_Escape: 
            Gtk.main_quit()
            return True
            
        if not self._paths_list:
            return False

        if event.keyval == Gdk.KEY_Left:
            if self._current_index > 0:
                self._current_index -= 1
                self._update_highlight()
            return True
        elif event.keyval == Gdk.KEY_Right:
            if self._current_index < len(self._paths_list) - 1:
                self._current_index += 1
                self._update_highlight()
            return True
        elif event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            if 0 <= self._current_index < len(self._paths_list):
                self._trigger_switch(self._paths_list[self._current_index])
            return True
            
        return False

if __name__ == "__main__":
    win = WallWidget()
    win.show_all()
    Gtk.main()

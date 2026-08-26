#!/usr/bin/env python3

# --------------------------------------------------------------------------------------
# TERMINAL WI-FI CONNECTION WIDGET
# Version: v0.4.1
# Created by Lukas Grumlik - (Rakosn1cek)
# August 2026
# --------------------------------------------------------------------------------------

import curses
import subprocess
import sys
import threading
import time

APP_TITLE = "wifi-widget"
APP_VERSION = "v0.4.1"


def set_terminal_title(title):
    # Set terminal window title using OSC escape sequence
    sys.stdout.write(f"\x1b]0;{title}\x07")
    sys.stdout.flush()


def fetch_networks():
    cmd = [
        "nmcli",
        "--terse",
        "--fields",
        "IN-USE,SSID,SIGNAL,BARS,SECURITY,FREQ,CHAN,RATE,MODE",
        "device",
        "wifi",
        "list",
    ]
    try:
        raw = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode("utf-8")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

    networks = []
    seen = set()
    for line in raw.strip().split("\n"):
        if not line or line.startswith(":"):
            continue
        parts = line.split(":")
        if len(parts) < 9:
            continue
        in_use = parts[0] == "*"
        ssid = parts[1].strip()
        signal = int(parts[2]) if parts[2].isdigit() else 0
        bars = parts[3].strip()
        security = parts[4].strip() or "OPEN"
        freq = parts[5].strip()
        chan = parts[6].strip()
        rate = parts[7].strip()
        mode = parts[8].strip()

        if ssid and ssid not in seen:
            seen.add(ssid)
            networks.append({
                "in_use": in_use,
                "ssid": ssid,
                "signal": signal,
                "bars": bars,
                "security": security,
                "freq": freq,
                "chan": chan,
                "rate": rate,
                "mode": mode,
            })
    return networks


def get_saved_connections():
    cmd = ["nmcli", "--terse", "--fields", "NAME", "connection", "show"]
    try:
        raw = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode("utf-8")
        return {line.strip() for line in raw.split("\n") if line.strip()}
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()


def run_command(cmd):
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return res.returncode == 0, res.stderr.strip() or res.stdout.strip()
    except Exception as e:
        return False, str(e)


def prompt_password(stdscr, ssid):
    curses.echo()
    curses.curs_set(1)
    h, w = stdscr.getmaxyx()
    box_w = min(50, w - 4)
    box_y = h // 2 - 2
    box_x = max(2, (w - box_w) // 2)

    win = curses.newwin(5, box_w, box_y, box_x)
    win.box()
    win.addstr(1, 2, f"Password for {ssid[:box_w-18]}:", curses.color_pair(2) | curses.A_BOLD)
    win.refresh()

    pwd_bytes = bytearray()
    while True:
        ch = win.getch(2, 2 + len(pwd_bytes))
        if ch in (10, 13):
            break
        elif ch in (27,):
            curses.noecho()
            curses.curs_set(0)
            return None
        elif ch in (curses.KEY_BACKSPACE, 127, 8):
            if pwd_bytes:
                pwd_bytes.pop()
                win.addstr(2, 2 + len(pwd_bytes), " ")
                win.refresh()
        elif 32 <= ch <= 126:
            pwd_bytes.append(ch)
            win.addch(2, 1 + len(pwd_bytes), "*")
            win.refresh()

    curses.noecho()
    curses.curs_set(0)
    return pwd_bytes.decode("utf-8")


def draw_ui(stdscr):
    set_terminal_title(APP_TITLE)
    curses.curs_set(0)
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_MAGENTA, -1)
    curses.init_pair(2, curses.COLOR_CYAN, -1)
    curses.init_pair(3, curses.COLOR_GREEN, -1)
    curses.init_pair(4, curses.COLOR_YELLOW, -1)
    curses.init_pair(6, curses.COLOR_RED, -1)

    stdscr.timeout(100)
    selected_idx = 0
    status_msg = "Scanning access points..."
    status_color = 4

    networks = []
    saved = set()
    is_scanning = True

    def scan_worker(force_rescan=False):
        nonlocal networks, saved, is_scanning, status_msg, status_color
        if force_rescan:
            subprocess.run(["nmcli", "device", "wifi", "rescan"], stderr=subprocess.DEVNULL)
            time.sleep(0.6)
        nets = fetch_networks()
        svs = get_saved_connections()
        networks = nets
        saved = svs
        is_scanning = False
        status_msg = "Ready."
        status_color = 2

    threading.Thread(target=scan_worker, args=(False,), daemon=True).start()

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()

        # Header section
        header_title = f"󰖩  WI-FI MANAGER {APP_VERSION}"
        subtitle = "Enter: Connect | d: Disconnect | r: Rescan | q: Quit"
        stdscr.addstr(1, max(2, (w - len(header_title)) // 2), header_title, curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(2, max(2, (w - len(subtitle)) // 2), subtitle, curses.color_pair(4))
        stdscr.hline(3, 2, curses.ACS_HLINE, w - 4)

        # Columns header layout
        col_format = "{:<3} {:<22} {:<6} {:<6} {:<10} {:<6} {:<12} {:<10}"
        table_hdr = col_format.format("", "SSID", "SIG%", "BARS", "FREQ", "CHAN", "RATE", "SECURITY")
        stdscr.addstr(4, 3, table_hdr[:w-6], curses.A_DIM)

        max_rows = max(1, h - 8)

        if is_scanning and not networks:
            scan_hint = "Scanning for available wireless networks..."
            stdscr.addstr(6, max(2, (w - len(scan_hint)) // 2), scan_hint, curses.color_pair(4) | curses.A_BOLD)
        else:
            start_idx = max(0, min(selected_idx - max_rows // 2, max(0, len(networks) - max_rows)))
            visible = networks[start_idx:start_idx + max_rows]

            for i, net in enumerate(visible):
                row_idx = start_idx + i
                y = 5 + i
                active_mark = "●" if net["in_use"] else " "
                sig_str = f"{net['signal']}%"
                row_str = col_format.format(
                    active_mark,
                    net["ssid"][:21],
                    sig_str,
                    net["bars"],
                    net["freq"][:9],
                    net["chan"][:5],
                    net["rate"][:11],
                    net["security"][:9],
                )

                if row_idx == selected_idx:
                    # Theme-agnostic selection highlight using reverse video
                    stdscr.attron(curses.A_REVERSE | curses.A_BOLD)
                    stdscr.addstr(y, 2, f" {row_str[:w-5]:<{w-4}} ")
                    stdscr.attroff(curses.A_REVERSE | curses.A_BOLD)
                else:
                    row_colour = curses.color_pair(3) if net["in_use"] else curses.A_NORMAL
                    stdscr.addstr(y, 3, row_str[:w-6], row_colour)

        # Footer section
        stdscr.hline(h - 3, 2, curses.ACS_HLINE, w - 4)
        if is_scanning:
            stdscr.addstr(h - 2, 3, "Scanning in progress...", curses.color_pair(4) | curses.A_BOLD)
        elif status_msg:
            stdscr.addstr(h - 2, 3, status_msg[:w-6], curses.color_pair(status_color) | curses.A_BOLD)
        else:
            total_net = f"Networks found: {len(networks)}"
            stdscr.addstr(h - 2, 3, total_net, curses.A_DIM)

        stdscr.refresh()

        key = stdscr.getch()
        if key == -1:
            continue

        if key in (ord('q'), 27):
            break
        elif key in (curses.KEY_UP, ord('k')):
            if networks:
                selected_idx = (selected_idx - 1) % len(networks)
        elif key in (curses.KEY_DOWN, ord('j')):
            if networks:
                selected_idx = (selected_idx + 1) % len(networks)
        elif key == ord('r'):
            if not is_scanning:
                is_scanning = True
                status_msg = "Rescanning access points..."
                status_color = 4
                threading.Thread(target=scan_worker, args=(True,), daemon=True).start()
        elif key == ord('d'):
            if networks and selected_idx < len(networks):
                target = networks[selected_idx]["ssid"]
                status_msg = f"Disconnecting {target}..."
                stdscr.refresh()
                ok, out = run_command(["nmcli", "connection", "down", target])
                is_scanning = True
                threading.Thread(target=scan_worker, args=(False,), daemon=True).start()
                status_msg = "Disconnected." if ok else f"Error: {out}"
                status_color = 3 if ok else 6
        elif key in (10, 13):
            if not networks or selected_idx >= len(networks):
                continue
            net = networks[selected_idx]
            ssid = net["ssid"]

            if net["in_use"]:
                status_msg = f"Already connected to {ssid}"
                status_color = 3
                continue

            if ssid in saved:
                status_msg = f"Connecting to saved network {ssid}..."
                stdscr.refresh()
                ok, out = run_command(["nmcli", "connection", "up", ssid])
                status_msg = f"Connected to {ssid}." if ok else f"Failed: {out}"
                status_color = 3 if ok else 6
                is_scanning = True
                threading.Thread(target=scan_worker, args=(False,), daemon=True).start()
            elif net["security"] == "OPEN":
                status_msg = f"Connecting to open network {ssid}..."
                stdscr.refresh()
                ok, out = run_command(["nmcli", "device", "wifi", "connect", ssid])
                status_msg = f"Connected to {ssid}." if ok else f"Failed: {out}"
                status_color = 3 if ok else 6
                is_scanning = True
                threading.Thread(target=scan_worker, args=(False,), daemon=True).start()
            else:
                pwd = prompt_password(stdscr, ssid)
                if pwd:
                    status_msg = f"Authenticating with {ssid}..."
                    stdscr.refresh()
                    ok, out = run_command(["nmcli", "device", "wifi", "connect", ssid, "password", pwd])
                    status_msg = f"Connected to {ssid}." if ok else f"Authentication failed: {out}"
                    status_color = 3 if ok else 6
                    is_scanning = True
                    threading.Thread(target=scan_worker, args=(False,), daemon=True).start()
                else:
                    status_msg = "Connection cancelled."
                    status_color = 4


def main():
    curses.wrapper(draw_ui)


if __name__ == "__main__":
    main()

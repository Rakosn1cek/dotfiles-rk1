#!/usr/bin/env python3
import os
import json
import shutil
import subprocess
import sys
from datetime import datetime

# --- Configuration ---
VERSION = "1.8.5"
BACKUP_DIR = os.path.expanduser("~/dotfiles")
TASKS_JSON = os.path.expanduser("~/.local/share/arch_task_manager/tasks.json")
SYNC_CACHE = os.path.expanduser("~/.cache/last_synced")
# List all projects here
PROJECTS = [
    os.path.expanduser("~/arch-projects/XC-Manager"),
    os.path.expanduser("~/arch-projects/mend"),
    os.path.expanduser("~/arch-projects/RTM"),
    os.path.expanduser("~/arch-projects/Budget-Buddy"),
    os.path.expanduser("~/arch-projects/oversight"),
    os.path.expanduser("~/arch-projects/MIREC")
]

# Live folders to watch for changes
LIVE_CONFIGS = [
    os.path.expanduser("~/.config/hypr"),
    os.path.expanduser("~/.config/kitty"),
    os.path.expanduser("~/.config/fastfetch"),
    os.path.expanduser("~/custom-scripts")
]

# Colors
CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BOLD = '\033[1m'
RESET = '\033[0m'

def get_updates():
    try:
        official = subprocess.check_output(["checkupdates"], stderr=subprocess.DEVNULL).decode().count('\n')
    except:
        official = 0
    try:
        aur_output = subprocess.check_output(["yay", "-Qua", "--quiet"], stderr=subprocess.DEVNULL).decode().strip()
        aur = len([line for line in aur_output.split('\n') if line])
    except:
        aur = 0
    total = official + aur
    if total == 0:
        return f"{GREEN}Up-to-date{RESET}"
    else:
        color = YELLOW if total < 15 else RED
        if aur > 0:
            return f"{color}{total} Total ({aur} AUR){RESET}"
        else:
            return f"{color}{total} Pending{RESET}"

def get_cache_size():
    cache_path = "/var/cache/pacman/pkg/"
    if not os.path.exists(cache_path): return "N/A"
    try:
        total = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(cache_path) for f in fs)
        gb = total / (1024**3)
        color = RED if gb > 10 else (YELLOW if gb > 5 else GREEN)
        return f"{color}{gb:.1f} GB{RESET}"
    except: return "Error"

def get_pending_tasks():
    if not os.path.exists(TASKS_JSON): return f"{YELLOW}No Data{RESET}"
    try:
        with open(TASKS_JSON, 'r') as f:
            tasks = json.load(f)
            pending = sum(1 for t in tasks if not (t.get('completed') or t.get('status') == 'done'))
            return f"{YELLOW}{pending} Pending{RESET}"
    except: return f"{RED}Error{RESET}"

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
            if is_dirty: return "dirty"
            if ahead > 0: return f"ahead:{ahead}"
            return "clean"
        except:
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

    # Construct the display string
    if dirty_projects:
        proj_display = f"{RED}Dirty{RESET} ({', '.join(dirty_projects)})"
    elif ahead_projects:
        proj_display = f"{GREEN}Clean{RESET} {YELLOW}↑ ({', '.join(ahead_projects)}){RESET}"
    else:
        proj_display = f"{GREEN}Clean{RESET}"

    # Check dots status separately
    dot_raw = check_repo(BACKUP_DIR)
    dot_status = f"{RED}Dirty{RESET}" if dot_raw == "dirty" else f"{GREEN}Clean{RESET}"
    if "ahead" in dot_raw:
        dot_status = f"{GREEN}Clean{RESET} {YELLOW}↑{RESET}"

    try:
        with open(SYNC_CACHE, 'r') as f:
            sync_date = f.read().strip()
    except:
        sync_date = "Never"

    return {
        "dots": dot_status,
        "proj": proj_display,
        "date": sync_date
    }

def get_budget_status():
    try:
        path = os.path.expanduser("~/arch-projects/Budget-Buddy/budget-buddy.py")
        result = subprocess.check_output(["python", path, "--stats"], stderr=subprocess.DEVNULL).decode().strip()
        return result
    except:
        return f"{RED}Budget Data Unavailable{RESET}"

def main():
    git_data = get_git_status()
    needs_sync = check_live_changes()
    
    print(f"\n{BOLD}{CYAN}󰣇 SYSTEM REPORT{RESET} | {datetime.now().strftime('%H:%M:%S')}")
    print(f"{CYAN}......................................................{RESET}")
    
    # Handle the Dots status with a live sync reminder
    dot_status = git_data['dots']
    if needs_sync:
        dot_status = f"{RED}Sync Required{RESET}"

    # Row 1
    s_text = f" 💾 {BOLD}Storage:{RESET}  {shutil.disk_usage(os.path.expanduser('~')).free // (2**30)} GB Free"
    t_text = f" 📝 {BOLD}Tasks:{RESET}  {get_pending_tasks()}"
    
    # Row 2
    u_text = f" 📦 {BOLD}Updates:{RESET}  {get_updates()}"
    d_text = f" 󱓞  {BOLD}Dots:{RESET}   {dot_status} ({git_data['date']})"
    
    # Row 3
    c_text = f" 󰒋  {BOLD}Cache:{RESET}    {get_cache_size()}"
    p_text = f" 󱚝  {BOLD}Proj:{RESET}   {git_data['proj']}"

    print(f"{s_text:<40} {t_text}")
    print(f"{u_text:<49} {d_text}")
    print(f"{c_text:<50} {p_text}")
    print(f" 󱚝  {BOLD}Budget:{RESET}   {get_budget_status()}")
    
    print(f"{CYAN}......................................................{RESET}\n")

if __name__ == "__main__":
    main()

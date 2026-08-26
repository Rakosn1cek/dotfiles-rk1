# Minimalist Wi-Fi Controllers

A pair of lightweight, standalone `fzf` terminal widgets designed to scan, select, and connect to Wi-Fi networks without relying on a status bar, panel applet, or heavy graphical interface. 

---

## Choosing the Right Script

Depending on how the system network layer is configured, choose the script that matches the active system backend daemon:

### 1. The `nmcli` Wrapper (`wwifi`)
* **Target System:** Best if running standard **NetworkManager** to handle connections.
* **How it works:** Queries `nmcli` to fetch available access points, presents them cleanly inside `fzf`, and prompts for a security passphrase if a new network profile is detected. 
* **Active Status:** Automatically reads connection profiles and displays active connection states natively.

### 2. The `iwctl` Wrapper (`iw-wifi.sh`)
* **Target System:** Built for minimalist setups running **iwd (iNet Wireless Daemon)** directly.
* **How it works:** Communicates directly with the lightweight Intel wireless engine. It handles formatting anomalies caused by `iwctl` stream pipes, stripping raw ANSI escape color codes and parsing complex network names (including those with spaces) from right to left.
* **Active Status:** Leverages a hybrid check against local hardware tables to map out network availability smoothly.

### 3. The Python `nmcli` (`wifi-widget.py`)
* This widget is still in development but works. **Use at your own risk**
---

## Dependencies

Ensure the following utilities are installed via the system package manager before launching the widgets:
* `fzf` (The core interactive menu selector)
* `networkmanager` (For the `nmcli` script)
* `iwd` (For the `iwctl` script)
* `python` (If you want to use the Python widget)

### Creating a widget style pop/slide in

If you want to have it pop or lide in as a widget seen in my setup, you can achieve that with windowrules and keybinds.

**Example windowrule in Lua:**

```zsh
hl.window_rule({ 
    name = "wifi-widget", 
    match = { class = "floating_wifi" }, 
    float = true, move = {560, 1}, 
    size = {700, 400}, 
    border_size = 2, 
    border_color = "rgb(767b7e)", 
    animation = "slide top", 
    opacity = 0.9 
    })
```    
> *NOTE: If you find a minute, leave a feedback in the Discussions please. All feedback is welcome.* 

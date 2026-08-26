-- Autostart Configuration for Hyprland
-- File: ~/.config/hypr/configs/autostart.lua

hl.on("hyprland.start", function () 
    -- 1. Core System & Polkit
    -- Sequential chain to guarantee systemd recognizes the active session before any portal calls occur
    hl.exec_cmd("dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP && systemctl --user import-environment WAYLAND_DISPLAY XDG_CURRENT_DESKTOP && systemctl --user start graphical-session.target")
    hl.exec_cmd("/usr/lib/polkit-kde-authentication-agent-1")
    hl.exec_cmd("udiskie &")

    -- 2. Theme & Wallpaper
    hl.exec_cmd("awww-daemon & sleep 0.5 && awww img $(cat ~/.cache/wal/wal)")
    hl.exec_cmd("dunst")

    -- 3. Hardware & Utilities
    hl.exec_cmd("brightnessctl set $(cat ~/.cache/brightness_level)")

    -- 4. Clipboard management
    hl.exec_cmd("bash ~/.config/hypr/scripts/cliphist-start.sh")
    hl.exec_cmd("wl-paste --type text --watch cliphist store -max-items 200")
    hl.exec_cmd("wl-paste --type image --watch cliphist store -max-items 200")

    -- 5. Apps to workspaces
    -- Start Browser on workspace 1
    -- hl.exec_cmd("min")
    hl.exec_cmd("~/arch-projects/MiseBrowser/launch.sh")
    
    -- Start Terminal on workspace 2
    -- hl.exec_cmd("kitty")

    -- Choice of editor for workspace 3
    -- hl.exec_cmd("geany")
    -- hl.exec_cmd("kitty --class yazi -e yazi")

    -- Clock + Conky Widgets
    hl.exec_cmd("python3 ~/custom-scripts/Python-Widgets/desktop-clock.py")
    hl.exec_cmd("python3 ~/custom-scripts/Control-Panel/conky-widget.py")
    hl.exec_cmd("python3 ~/custom-scripts/Dashboard/dashboard-widget.py")

    -- HyprRings
    -- hl.exec_cmd("python3 ~/arch-projects/HyprRings/main.py")

    -- Cursor
    hl.exec_cmd("hyprctl setcursor Empty-Butterfly-Yellow-vr8 24")
end)

-- Prepared for Hyprland v0.55+ 
-- Configuration based on official migration guidelines

-- 1. Environment Variables
hl.env("GDK_BACKEND", "wayland")
hl.env("QT_QPA_PLATFORM", "wayland;xcb")
hl.env("CLUTTER_BACKEND", "wayland")
hl.env("XDG_CURRENT_DESKTOP", "Hyprland")
hl.env("XDG_SESSION_TYPE", "wayland")
hl.env("XDG_SESSION_DESKTOP", "Hyprland")
hl.env("WLR_NO_HARDWARE_CURSORS", "1")
-- hl.env("WLR_RENDERER_ALLOW_SOFTWARE", "1")
hl.env("WLR_RENDERER", "gles2")
hl.env("TERMINAL", "kitty")
hl.env("LIBVA_DRIVER_NAME", "iHD")
hl.env("HYPRCURSOR_THEME", "Empty-Butterfly-Yellow-vr8")
hl.env("HYPRCURSOR_SIZE", "24")
hl.env("GTK_USE_PORTAL", "1")
hl.env("GDK_DEBUG", "portals")

-- 2. Configuration Tables
hl.monitor({
    output   = "",
    mode     = "preferred",
    position = "auto",
    scale    = "1",
})

hl.config({
    input = {
        kb_layout = "us",
        follow_mouse = 1,
        sensitivity = 0,
        touchpad = {
            -- Lua requires brackets/quotes for keys with hyphens
            ["tap_to_click"] = true,
            ["tap_and_drag"] = true,
        }
    },
    cursor = {
        no_hardware_cursors = true
    },
    debug = {
        -- v0.55 moved vfr from misc to debug
        vfr = true 
    },
    misc = {
        disable_hyprland_logo = true
    },
    general = {
        gaps_in = 15,
        gaps_out = 15,
        layout = "master"
    },
    master = {
        new_status = "slave",
        new_on_active = "none",
        new_on_top = false,
        mfact = 0.55,
        orientation = "left",
        special_scale_factor = 1.0,
        slave_count_for_center_master = 2
    },
    scrolling = {
        column_width = 0.9,
        fullscreen_on_one_column = true,
        direction = "right"
    },
    dwindle = {
        force_split                  = 0,
        preserve_split               = false,
        smart_split                  = false,
        smart_resizing               = true,
        permanent_direction_override = false,
        special_scale_factor         = 1,
        split_width_multiplier       = 1.0,
        use_active_for_splits        = true,
        default_split_ratio          = 1.0,
        split_bias                   = 0,
        precise_mouse_move           = false
    },
    decoration = {
        rounding = 10,
        active_opacity = 1,
        inactive_opacity = 1.0,
        fullscreen_opacity = 1,
        blur = {
            enabled = true,
            size = 5,
            passes = 4,
        },
        shadow = {
            enabled = true,
            range = 15,
            render_power = 4,
        }
    },
    animations = {
        enabled = true,
    }
})

-- 3. Animation Definitions (External for cleaner syntax)
hl.curve("myBezier", { type = "bezier", points = { {0.05, 0.9}, {0.1, 1.05} } })

hl.animation({ leaf = "windows",    enabled = true, speed = 7,  bezier = "myBezier" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 7,  bezier = "default" })
hl.animation({ leaf = "layers",     enabled = true, speed = 15, bezier = "myBezier", style = "slide" })

-- 4. Workspace & Gestures
-- Use workspace_rule instead of hl.workspace
hl.workspace_rule({ 
    workspace = "1", 
    layout = "scrolling",
    default_name = "Browsers",
    layout_opts = { direction = "down" } 
})

hl.workspace_rule({ 
    workspace = "2", 
    layout = "dwindle",
    default_name = "Terminals"
})

hl.workspace_rule({ 
    workspace = "3", 
    layout = "master",
    default_name = "Files"
})

hl.gesture({
    fingers = 3,
    direction = "horizontal",
    action = "workspace"
})
hl.gesture({
    fingers = 3,
    direction = "vertical",
    action = "scroll_move"
})


-- 5. Module Imports
-- Ensure these files exist as .lua in your configs folder
require("configs.autostart")
require("configs.keybinds")
require("configs.windowrules")

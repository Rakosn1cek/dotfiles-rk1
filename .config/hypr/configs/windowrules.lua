-- Window and Layer Rules for Hyprland v0.55
-- Auto-generated via Rule Manager TUI

local rules = {
    widgets = {
        {
            name = "Power menu",
            match = { title = "powermenu.py" },
            float = true,
            center = true,
            animation = "gnomed",
            no_blur = false
        },
        {
            name = "keybinds-widget",
            match = { class = "keybinds" },
            float = true,
            size = {750, 650},
            move = {585, 1},
            border_size = 2,
            border_color = "rgb(767b7e)",
            opacity = 0.8,
            animation = "slide top"
        },
        {
            name = "aliases-widget",
            match = { class = "show-aliases" },
            float = true,
            size = {750, 650},
            move = {585, 1},
            border_size = 2,
            border_color = "rgb(767b7e)",
            opacity = 0.8,
            animation = "slide top"
        },
        {
            name = "windowrules-tui",
            match = { class = "wr-manager" },
            float = true,
            center = true,
            size = {1100, 700},
            border_size = 2,
            border_color = "rgb(767b7e)",
            opacity = 0.8,
            animation = "gnomed",
            no_blur = false
        },
        {
            name = "audio-widget",
            match = { class = "Audio Switcher" },
            float = true,
            size = {500, 250},
            move = {710, 0},
            border_size = 2,
            border_color = "rgb(767b7e)",
            opacity = 0.8,
            animation = "slide top"
        },
        {
            name = "mirec-widget",
            match = { class = "Mirec" },
            float = true,
            size = {500, 300},
            move = {5, 1},
            border_size = 2,
            border_color = "rgb(767b7e)",
            opacity = 0.8,
            animation = "slide left"
        },
        {
            name = "bt-widget",
            match = { class = "bt-menu" },
            float = true,
            size = {600, 400},
            move = {660, 0},
            border_size = 2,
            border_color = "rgb(767b7e)",
            opacity = 0.8,
            animation = "slide top"
        },
        {
            name = "wifi-widget",
            match = { class = "floating_wifi" },
            float = true,
            size = {700, 400},
            move = {560, 1},
            border_size = 2,
            border_color = "rgb(767b7e)",
            opacity = 0.8,
            animation = "slide top"
        },
        {
            name = "tt-widget",
            match = { class = "tt" },
            float = true,
            size = {550, 350},
            move = {5, 0},
            border_size = 2,
            border_color = "rgb(767b7e)",
            opacity = 0.8,
            animation = "slide left"
        },
        {
            name = "sysinfo-widget",
            match = { class = "sysinfo-widget" },
            float = true,
            size = {500, 450},
            move = {1415, 0},
            border_size = 2,
            border_color = "rgb(767b7e)",
            opacity = 0.8,
            animation = "slide right"
        },
        {
            name = "changewall-widget",
            match = { class = "changewall-widget.py" },
            float = true,
            move = {355, 830},
            border_size = 0,
            animation = "gnomed"
        },
        {
            name = "theme-widget",
            match = { class = "theme-widget.py" },
            float = true,
            center = true,
            size = {550, 340},
            border_size = 0,
            animation = "gnomed"
        },
        {
            name = "kitty-themes",
            match = { class = "kitty-themes" },
            float = true,
            size = {400, 500},
            move = {1515, 1},
            border_size = 0,
            opacity = 0.8,
            animation = "slide right",
            no_max_size = true
        },
        {
            name = "schedule-widget",
            match = { class = "schedule-widget" },
            float = true,
            center = true,
            size = {450, 120},
            border_size = 2,
            border_color = "rgb(767b7e)",
            opacity = 0.8,
            animation = "gnomed"
        },
        {
            name = "schedule-alert",
            match = { class = "schedule-alert" },
            float = true,
            center = true,
            size = {500, 200},
            border_size = 2,
            border_color = "rgb(ff0008)",
            opacity = 0.8,
            animation = "gnomed"
        },
        {
            name = "budget-buddy",
            match = { class = "budget-buddy" },
            float = true,
            size = {740, 780},
            move = {600, 3},
            border_size = 2,
            border_color = "rgb(767b7e)",
            opacity = 0.8,
            animation = "slide top"
        },
        {
            name = "rtm",
            match = { class = "rtm" },
            float = true,
            size = {800, 880},
            move = {550, 3},
            border_size = 2,
            border_color = "rgb(767b7e)",
            opacity = 0.8,
            animation = "slide top"
        }
    },
    apps = {
        {
            name = "Calendar",
            match = { class = "cal" },
            float = true,
            center = true,
            size = {1000, 450},
            border_size = 2,
            border_color = "rgb(767b7e)",
            opacity = 0.8,
            animation = "gnomed"
        },
        {
            name = "clipbox",
            match = { class = "clipbox" },
            float = true,
            size = {900, 450},
            move = {500, 2},
            border_size = 2,
            border_color = "rgb(767b7e)",
            opacity = 0.8,
            animation = "slide down"
        },
        {
            name = "Notifications",
            match = { class = "notif" },
            float = true,
            size = {800, 400},
            move = {600, 2},
            border_size = 2,
            border_color = "rgb(767b7e)",
            opacity = 0.8,
            animation = "slide top"
        },
        {
            name = "Hypr Workspaces",
            match = { class = "hypr-workspaces" },
            float = true,
            size = {600, 350},
            move = {650, 2},
            animation = "slide top"
        },
        {
            name = "S-Bar",
            match = { title = "s-bar" },
            size = {500, 500},
            move = {700, 5},
            stay_focused = true,
            border_size = 0,
            animation = "slide top"
        },
        {
            name = "Yazi-Picker",
            match = { class = "file_chooser" },
            float = true,
            center = true,
            size = {900, 600},
            animation = "gnomed",
            no_blur = false
        },
        {
            name = "pass-manager",
            match = { class = "pass" },
            float = true,
            center = true,
            size = {800, 400},
            border_size = 0,
            opacity = 0.8,
            animation = "gnomed"
        },
        {
            name = "Mirec",
            match = { class = "Mirec" },
            opacity = 0.8
        },
        {
            name = "notifications",
            match = { class = "dunst" },
            opacity = 0.9,
            no_blur = false
        },
        {
            name = "music-player",
            match = { class = "music" },
            float = true,
            center = true,
            size = {1000, 850},
            border_size = 0,
            opacity = 0.9
        },
        {
            name = "kitty",
            match = { class = "kitty" },
            workspace = 2,
            float = true,
            size = {1595, 1046},
            move = {5, 10},
            border_size = 2,
            animation = "gnomed",
            no_blur = true
        },
        {
            name = "foot",
            match = { class = "foot" },
            float = true,
            size = {1595, 1046},
            move = {5, 10},
            border_size = 0,
            opacity = 0.8,
            no_blur = true
        },
        {
            name = "yazi",
            match = { class = "yazi" },
            workspace = 3,
            float = true,
            size = {1395, 700},
            move = {5, 10},
            border_size = 2,
            opacity = 0.95,
            animation = "gnomed",
            no_blur = true
        },
        {
            name = "geany-rule",
            match = { class = "geany" },
            workspace = 5,
            border_size = 0,
            opacity = 0.9,
            animation = "fade"
        },
        {
            name = "qalculate-rule",
            match = { class = "qalculate-gtk" },
            size = {600, 400},
            border_size = 0,
            opacity = 0.9,
            animation = "slide top"
        },
        {
            name = "min-browser",
            match = { class = "min" },
            workspace = 1,
            float = true,
            border_size = 2,
            opacity = "0.8 override"
        },
        {
            name = "Mise-browser",
            match = { title = "Mise" },
            workspace = 1,
            float = true,
            size = {1595, 1046},
            move = {5, 10},
            border_size = 1,
            no_blur = true
        },
        {
            name = "save-open-rule",
            match = { title = "^.*(Save|Open).*$" },
            float = true,
            center = true,
            stay_focused = true
        },
        {
            name = "magic-workspace-fallback-rule",
            match = { workspace = "special:magic" },
            border_size = 1,
            border_color = "rgb(ffff00)"
        }
    },
    workspaces = {
        {
            workspace = "special:magic",
            on_created_empty = ""
        }
    },
    layers = {
        {
            name = "notifications",
            match = { namespace = "dunst" },
            blur = true
        },
        {
            name = "Conky",
            match = { namespace = "conky-monitor" },
            blur = false
        },
        {
        	name = "Dashboard Widget",
        	match = { namespace = "dashboard-widget" },
        	blur = false 	
        }
    }
}

if hl then
    if hl.window_rule then
        for _, rule in ipairs(rules.widgets) do hl.window_rule(rule) end
        for _, rule in ipairs(rules.apps)    do hl.window_rule(rule) end
    end
    if hl.workspace_rule then
        for _, rule in ipairs(rules.workspaces) do hl.workspace_rule(rule) end
    end
    if hl.layer_rule then
        for _, rule in ipairs(rules.layers) do hl.layer_rule(rule) end
    end
end

return rules

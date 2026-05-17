#!/bin/sh

# notes - a note manager made by using fzf and bash
# created by zyuzya1984.

# variable, where notes will be located
folder=$HOME/notes/

# menu to search and select directories
menu_dir() {
    fzf --style full \
        --no-border \
        --prompt "> " \
        --print-query \
        --layout reverse \
        --input-label ' 󰍉 Search ' \
        --bind 'result:transform-list-label:
            echo " $FZF_MATCH_COUNT directories "' \
        --no-preview \
        --color 'list-border:#669966,list-label:#99cc99' \
        --color 'input-border:#996666,input-label:#ffcccc' \
        | tail -1
}

# menu to enter a name for the new note
menu_name() {
    fzf --style full \
        --no-border \
        --prompt "> " \
        --print-query \
        --input-label ' 󰍉 Enter a name ' \
        --no-preview \
        --color 'input-border:#996666,input-label:#ffcccc' \
        | tail -1
}

# the MAIN menu for searching notes
menu_with_preview() {
    fzf --style full \
        --no-border \
        --prompt "> " \
        --print-query \
        --layout reverse \
        --input-label ' 󰍉 Search ' \
        --bind 'result:transform-list-label:
            if [[ -z $FZF_QUERY ]]; then
                echo " $FZF_MATCH_COUNT notes "
            else
                echo " $FZF_MATCH_COUNT matches for [$FZF_QUERY] "
            fi' \
        --no-preview \
        --color 'list-border:#669966,list-label:#99cc99' \
        --color 'input-border:#996666,input-label:#ffcccc' \
        | tail -1
}

# format the notes list with Nerd Font icons for better visuals
format_list() {
    while IFS= read -r line; do
        if [[ "$line" == "New" ]]; then
            echo "󰐕 New (create a new note)"
        elif [[ "$line" == *.md ]]; then
            echo "󰍔 $line"
        else
            echo "   $line"
        fi
    done
}

# ddd indentation to the directory list for a cleaner fzf layout
format_dirs() {
    while IFS= read -r line; do
        echo "  $line"
    done
}

# handle the creation of a new note
newnote() {
    dir="$(find "$folder" -maxdepth 1 -type d | format_dirs | menu_dir)" || exit 0
    dir=$(echo "$dir" | sed 's/^[^ ]* *//')
    : "${dir:=$folder}"
    name="$(echo "" | menu_name <&-)" || exit 0
    : "${name:=$(date +%F_%H-%M-%S)}"
    setsid -f "$TERMINAL" -e nvim "${dir%/}/$name.md" >/dev/null 2>&1
    kill $PPID
}

# list files by mtime and handle selection
selected() {
    choice=$(
        echo -e "New\n$(find $folder -type f -printf '%T@ %P\n' | sort -nr | cut -d' ' -f2-)" \
        | format_list \
        | menu_with_preview
    )
    choice=$(echo "$choice" | sed 's/^[^ ]* *//' | cut -d' ' -f1)
    case $choice in
        New)  newnote ;;
        *.md) setsid -f "$TERMINAL" -e nvim "$folder$choice" >/dev/null 2>&1
              kill $PPID ;;
        *)    kill $PPID ;;
    esac
}

# run this shit
selected

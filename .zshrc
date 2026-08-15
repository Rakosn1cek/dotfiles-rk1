# --- Colours ---
export LS_COLORS='di=1;34:ln=1;36:so=1;35:pi=33:ex=1;32:bd=1;33:cd=1;33:su=1;31:sg=1;31:tw=1;34:ow=1;34:'
alias ls='ls --color=auto'
alias grep='grep --color=auto'

export LESS_TERMCAP_mb=$'\e[1;31m'
export LESS_TERMCAP_md=$'\e[1;34m'
export LESS_TERMCAP_me=$'\e[0m'
export LESS_TERMCAP_so=$'\e[1;33m'
export LESS_TERMCAP_se=$'\e[0m'
export LESS_TERMCAP_us=$'\e[4;36m'
export LESS_TERMCAP_ue=$'\e[0m'
# export MANPAGER='less -R'

export MANPAGER="oversight"
export PAGER="oversight"

# --- Completion ---
autoload -Uz compinit && compinit
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"
zstyle ':completion:*' menu select

# --- Prompt (replaces p10k) ---
autoload -Uz vcs_info
precmd() {
    vcs_info
}
local _git_icon=$'\uf418'
zstyle ':vcs_info:*' enable git
zstyle ':vcs_info:git:*' check-for-changes yes
zstyle ':vcs_info:git:*' check-for-staged-changes yes
zstyle ':vcs_info:git:*' formats " %F{green}${_git_icon} %b%f%c%u"
zstyle ':vcs_info:git:*' actionformats " %F{green}${_git_icon} %b%f %F{red}(%a)%f%c%u"
zstyle ':vcs_info:git:*' stagedstr " %F{green}+%i%f"
zstyle ':vcs_info:git:*' unstagedstr " %F{red}!%u%f"

autoload -Uz vcs_info +X add-zsh-hook

# Hook to inject file counts into %i and %u
+vi-git-counts() {
    local staged unstaged untracked
    staged=$(git diff --cached --numstat 2>/dev/null | wc -l | tr -d ' ')
    unstaged=$(git diff --numstat 2>/dev/null | wc -l | tr -d ' ')
    untracked=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l | tr -d ' ')
    hook_com[staged]=''
    hook_com[unstaged]=''
    [[ $staged -gt 0 ]] && hook_com[staged]=" %F{green}+${staged}%f"
    [[ $unstaged -gt 0 ]] && hook_com[unstaged]+=" %F{red}!${unstaged}%f"
    [[ $untracked -gt 0 ]] && hook_com[unstaged]+=" %F{yellow}?${untracked}%f"
}
zstyle ':vcs_info:git+set-message:*' hooks git-counts
setopt PROMPT_SUBST

PROMPT='%F{blue}%~%f${vcs_info_msg_0_}
%(?.%F{magenta}❯%f.%F{red}❯%f) '
RPROMPT='%F{spatial}%D{%H:%M}%f %(?.%F{green}✓.%F{red}✗ %?)%f'

# figlet -f smslant Welcome Back - Rk 1
# kitten icat --align left ~/Pictures/Fastfetch/cover.png
kitten icat --align left ~/Pictures/Fastfetch/anime-kitty.png

# --- User Configuration ---
export LANG=en_GB.UTF-8
export LC_ALL=en_GB.UTF-8
export EDITOR='micro'
export VISUAL='geany'
export PATH="$HOME/custom-scripts:$PATH"
# Set the correct directory for figlet fonts
export FIGLET_FONTDIR="/usr/share/figlet/fonts"
cdpath=(. ~)

# --- Aliases ---
 
# --- Functions ---
function y() {
	local tmp="$(mktemp -t "yazi-cwd.XXXXXX")"
	yazi "$@" --cwd-file="$tmp"
	if cwd="$(cat -- "$tmp")" && [ -n "$cwd" ] && [ "$cwd" != "$PWD" ]; then
		builtin cd -- "$cwd"
	fi
	rm -f -- "$tmp"
}

dotsync() {
    # Update your package list using pacman
    pacman -Qqe > ~/dotfiles/pkglist.txt

    echo "󰒲 Copying live config to GitHub folder..."

    # Sync .config folders directly to the repo's .config directory
    # Using the / suffix on source ensures we sync the content into the named destination
    rsync -a --delete ~/.config/hypr/ ~/dotfiles/.config/hypr/
    rsync -a --delete ~/.config/nwg-look/ ~/dotfiles/.config/nwg-look/
    rsync -a --delete ~/.config/wal/ ~/dotfiles/.config/wal/
    rsync -a --delete ~/.config/kitty/ ~/dotfiles/.config/kitty/
    rsync -a --delete ~/.config/backgrounds/ ~/dotfiles/.config/backgrounds/
    rsync -a --delete ~/custom-scripts/ ~/dotfiles/custom-scripts/
    cp ~/.zshrc ~/dotfiles/.zshrc
    cp ~/.bashrc ~/dotfiles/.bashrc

    # GitHub Upload
    cd ~/dotfiles || return
    echo "󰚰 Changes detected in your dotfiles:"
    git status -sb
    
    echo -n "󰏖 Commit and push these changes? [y/N]: "
    read -k 1 "REPLY" # Using -k 1 for a cleaner single-key read in zsh
    echo ""
    
    if [[ "$REPLY" =~ ^[Yy]$ ]]; then
        git add .
        # Commit with summary and detailed file changes in the body
        git commit -m "Sync: $(date +'%H:%M')" -m "$(git status --porcelain)"
        git push
        date +"%m/%d %H:%M" > ~/.cache/last_synced
        echo "󰄬 Everything is safe on GitHub."
    else
        echo "󰅙 Sync aborted."
    fi
}

# Source external shell utility functions
[[ -f ~/.config/zsh/functions/jknot.zsh ]] && source ~/.config/zsh/functions/jknot.zsh

# --- zsh-autosuggestions (sourced directly, no plugin manager) ---
source /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh

# --- XC-Manager Settings ---
# Source the AUR-installed plugin (handles fpath, autoload, and bindkey automatically)
source ~/arch-projects/XC-Manager/xc.plugin.zsh
# Test local dev version instead
fpath=(~/arch-projects/XC-Manager/autoload $fpath)
autoload -Uz fzf-vault-widget
zle -N fzf-vault-widget
bindkey '^G' fzf-vault-widget

# UI Customization (These are read by the functions when called)
zstyle ':xc:*' separator "->" 
zstyle ':xc:*' fzf_colors "fg:7,hl:4,fg+:15,hl+:12,info:2,prompt:5,pointer:12"

# --- History ---
HISTFILE=~/.zsh_history
HISTSIZE=10000
SAVEHIST=10000

# Deduplication is key to stopping the growth
setopt HIST_IGNORE_ALL_DUPS
setopt HIST_REDUCE_BLANKS
setopt HIST_IGNORE_SPACE
setopt HIST_EXPIRE_DUPS_FIRST

setopt sharehistory
setopt autocd
setopt EXTENDED_HISTORY

# --- Startup ---
echo "󱓞 System Version: Rk1"

[[ -f ~/.zshrc.local ]] && source ~/.zshrc.local

export PATH="$HOME/.local/bin:$PATH"
[[ -f ~/.zsh_aliases ]] && source ~/.zsh_aliases

# --- Mend plugin ---
source $HOME/arch-projects/mend/mend.plugin.zsh
fpath=($HOME/arch-projects/mend/functions $fpath)
# source /usr/share/zsh/plugins/mend/mend.plugin.zsh
# fpath=(/usr/share/zsh/plugins/mend/functions $fpath)
autoload -Uz mend

# --- 2. The Function ---
unalias d 2>/dev/null
d() {
  # List stack, skip current dir, and fuzzy search unique paths
  local dir=$(dirs -p -v | tail -n +2 | fzf --height 40% --reverse --header="Jump to Previous Directory" | awk '{print $2}')
  
  # Jump if a selection was made
  if [[ -n "$dir" ]]; then
    cd "${dir/#\~/$HOME}"
  fi
}

# --- Oversight Security Tool ---
source /home/rk1/.local/share/oversight/oversight.zsh
add-zsh-hook preexec _oversight_preexec

# --- Gemini-Chat ---
gchat() {
    # Set the path to the directory containing your project
    local project_dir="/home/rk1/arch-projects/GeminiChat"
    # Use the passed argument as the target directory, or default to current dir
    local target_dir="${1:-.}"
    # Move to the target directory
    pushd "$target_dir" > /dev/null
    # Activate virtual environment and run the chat script
    source "$project_dir/venv/bin/activate"
    python "$project_dir/gemini-chat.py"
    # Return to the original directory
    popd > /dev/null
}

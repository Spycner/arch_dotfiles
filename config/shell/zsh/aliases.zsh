# Vivaldi Browser Aliases with Wayland Support
WAYLAND_FLAGS="--ozone-platform=wayland --enable-features=UseOzonePlatform,WaylandWindowDecorations"
alias vivaldi="vivaldi-stable $WAYLAND_FLAGS"
alias vivaldi-private="vivaldi-stable $WAYLAND_FLAGS --incognito"

# eza as ls replacement
alias ld="eza -lD" # list only directories
alias lf="eza -lf --color=always | grep -v /" # list only files
alias lh="eza -dl .* --group-directories-first" # list only hidden files
alias ll="eza -al --group-directories-first" # list everything with directories first
alias ls="eza -alf --color=always --sort=size | grep -v /" # list files sorted by size
alias lt="eza -al --modified" # list everything sorted by time

# File mods
alias cp="cp -iv"
alias mv="mv -iv"
alias rm="rm -iv"

alias cat="bat"
alias bathelp="bat --plain --language=help"
alias batl="bat --paging=never -l log"

# Search aliases - ripgrep and traditional grep
alias grep="grep -P -i --color=auto"    # Traditional grep with good defaults
alias search="rg -i --color=always"     # Fast case-insensitive search with ripgrep
alias find-in="rg --color=always"       # Fast search preserving case
alias search-code="rg --type-not=min --type-not=lock"  # Search excluding minified/lock files

alias vim="nvim"

# help overwrites
alias -g -- -h="-h 2>&1 | bat --language=help --style=plain"
alias -g -- --help"--help 2>&1 | bat --language=help --style=plain"

# Vim mode configuration for zsh
# Managed by arch_dotfiles repository via setup-vim-mode.py

# Vim mode plugin configuration (set before loading)
ZVM_VI_INSERT_ESCAPE_BINDKEY=jj
ZVM_KEYTIMEOUT=0.1

# Cursor styling for different modes
ZVM_CURSOR_STYLE_ENABLED=true
ZVM_VI_INSERT_CURSOR=beam
ZVM_VI_NORMAL_CURSOR=block
ZVM_VI_VISUAL_CURSOR=underline

# Visual mode highlighting
ZVM_VI_HIGHLIGHT_BACKGROUND=blue
ZVM_VI_HIGHLIGHT_FOREGROUND=white

# Enable surround operations (like vim-surround)
ZVM_VI_SURROUND_BINDKEY=s-prefix

# Text objects and advanced features
ZVM_VI_EDITOR=nvim

# Load the vim mode plugin
zinit load jeffreytse/zsh-vi-mode

# Vim mode enhancements and fixes (applied after plugin initialization)
function zvm_after_init() {
    # Restore essential keybindings that might be overridden
    bindkey '^R' history-incremental-search-backward
    bindkey '^S' history-incremental-search-forward
    
    # Ensure word deletion works properly
    bindkey '^W' backward-kill-word
    
    # Better backspace behavior
    bindkey '^?' backward-delete-char
    bindkey '^H' backward-delete-char
    
    # Search in vim command mode
    bindkey -M vicmd '/' history-incremental-search-forward
    bindkey -M vicmd '?' history-incremental-search-backward
    
    # Edit command in vim
    bindkey -M vicmd '^V' edit-command-line
    
    # Enhanced history navigation in command mode
    bindkey -M vicmd 'k' up-line-or-beginning-search
    bindkey -M vicmd 'j' down-line-or-beginning-search
    
    # Additional vim-like bindings for better experience
    bindkey -M vicmd 'gg' beginning-of-buffer-or-history
    bindkey -M vicmd 'G' end-of-buffer-or-history
    
    # Increment/decrement numbers (like vim's Ctrl+A/Ctrl+X)
    bindkey -M vicmd '^A' increment-number
    bindkey -M vicmd '^X' decrement-number
}
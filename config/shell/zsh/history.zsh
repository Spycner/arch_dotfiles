# History configuration for zsh
# Managed by arch_dotfiles repository
# Provides comprehensive history management with real-time sharing between sessions

# History sharing and persistence options
setopt SHARE_HISTORY          # Share history between all sessions in real-time
setopt APPEND_HISTORY         # Append history rather than overwriting
setopt INC_APPEND_HISTORY     # Append commands immediately after execution
setopt EXTENDED_HISTORY       # Record timestamps and runtime for each command

# History deduplication and filtering
setopt HIST_IGNORE_DUPS       # Don't record duplicate consecutive commands
setopt HIST_IGNORE_ALL_DUPS   # Remove older duplicates from history list
setopt HIST_IGNORE_SPACE      # Don't record commands that start with a space
setopt HIST_REDUCE_BLANKS     # Remove superfluous blanks from history entries
setopt HIST_NO_STORE          # Don't store 'history' or 'fc' commands

# History expansion and verification
setopt HIST_VERIFY            # Show expanded history command before execution

# History size configuration
HISTSIZE=50000                # Number of commands to remember in memory
SAVEHIST=50000               # Number of commands to save to history file
HISTFILE="$HOME/.zsh_history" # History file location

# Additional history behavior improvements
setopt HIST_BEEP              # Beep when accessing non-existent history
setopt HIST_SAVE_NO_DUPS      # Don't save duplicate entries to history file
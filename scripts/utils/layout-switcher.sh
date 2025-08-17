#!/usr/bin/env bash

# Layout Switcher Script for Hyprland (Multi-Layout Implementation)
# Uses Hyprland's multiple layout feature to avoid error messages
# Maintains minimal state for status bar integration
# Bound to Super+Shift+L for fast keyboard layout switching

set -euo pipefail

# Script version
VERSION="2.0.0"

# XDG Base Directory compliance
XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
STATE_DIR="$XDG_DATA_HOME/arch_dotfiles"
STATE_FILE="$STATE_DIR/layout-current"  # Simple state file for current layout

# Layout names for display
declare -A LAYOUT_NAMES
LAYOUT_NAMES[0]="us-intl"
LAYOUT_NAMES[1]="de-qwertz"

# Layout display names for status bar
declare -A LAYOUT_DISPLAY
LAYOUT_DISPLAY[0]="US"
LAYOUT_DISPLAY[1]="DE"

# Ensure state directory exists
ensure_state_dir() {
    mkdir -p "$STATE_DIR" 2>/dev/null || true
}

# Setup both layouts at once in Hyprland to avoid variant persistence issues
setup_layouts() {
    hyprctl keyword input:kb_layout "us,de" >/dev/null 2>&1
    hyprctl keyword input:kb_variant "intl,nodeadkeys" >/dev/null 2>&1
}

# Read current layout index from state file
read_state() {
    ensure_state_dir
    if [[ -f "$STATE_FILE" ]]; then
        cat "$STATE_FILE" 2>/dev/null || echo "0"
    else
        echo "0"
    fi
}

# Write current layout index to state file
write_state() {
    ensure_state_dir
    echo "$1" > "$STATE_FILE"
}

# Get the next layout index
get_next_index() {
    local current="$1"
    case "$current" in
        "0") echo "1" ;;
        "1") echo "0" ;;
        *) echo "0" ;;
    esac
}

# Main toggle function
toggle_layout() {
    # Ensure layouts are configured
    setup_layouts
    
    # Toggle to next layout using Hyprland's built-in switcher
    hyprctl switchxkblayout all next >/dev/null 2>&1
    
    # Wait a moment for the change to take effect
    sleep 0.1
    
    # Detect what layout we actually ended up with
    local current_layout current_variant next_index
    current_layout=$(hyprctl getoption input:kb_layout -j 2>/dev/null | jq -r '.str // "us"')
    current_variant=$(hyprctl getoption input:kb_variant -j 2>/dev/null | jq -r '.str // ""')
    
    # Determine index based on actual layout
    # When multiple layouts are set, Hyprland shows "us,de" but we need to detect which is active
    # We'll check the first active keyboard device instead
    local active_layout
    active_layout=$(hyprctl devices -j 2>/dev/null | jq -r '.keyboards[0].active_keymap // "us"' | tr '[:upper:]' '[:lower:]')
    
    # Determine index based on active layout
    # German layout shows as "German (no dead keys)"
    # US International shows as "English (US, intl., with dead keys)" or similar
    if [[ "$active_layout" == *"german"* ]]; then
        next_index="1"
    else
        next_index="0"
    fi
    
    # Update state to match reality
    write_state "$next_index"
    
    # Optional: Send notification if notify-send is available
    if command -v notify-send >/dev/null 2>&1; then
        local layout_name="${LAYOUT_NAMES[$next_index]}"
        local display_name="${LAYOUT_DISPLAY[$next_index]}"
        
        case "$next_index" in
            "0")
                notify-send --urgency=low --expire-time=2000 \
                    "Layout: $display_name" \
                    "US International (AltGr for umlauts)" \
                    2>/dev/null || true
                ;;
            "1")
                notify-send --urgency=low --expire-time=2000 \
                    "Layout: $display_name" \
                    "German QWERTZ (direct umlauts)" \
                    2>/dev/null || true
                ;;
        esac
    fi
    
    echo "${LAYOUT_NAMES[$next_index]}"
}

# Show current status
show_status() {
    local current_index
    current_index=$(read_state)
    local layout_name="${LAYOUT_NAMES[$current_index]}"
    echo "$layout_name"
}

# Show status bar friendly output
show_status_bar() {
    local current_index
    current_index=$(read_state)
    echo "${LAYOUT_DISPLAY[$current_index]}"
}

# Show detailed status
show_status_detailed() {
    local current_index
    current_index=$(read_state)
    local layout_name="${LAYOUT_NAMES[$current_index]}"
    local display_name="${LAYOUT_DISPLAY[$current_index]}"
    
    echo "Current layout: $layout_name"
    echo "Display name: $display_name"
    echo "Layout index: $current_index"
    
    # Show actual Hyprland configuration
    if command -v hyprctl >/dev/null 2>&1; then
        echo ""
        echo "Hyprland configuration:"
        echo -n "  Layouts: "
        hyprctl getoption input:kb_layout -j 2>/dev/null | jq -r '.str // "unknown"'
        echo -n "  Variants: "
        hyprctl getoption input:kb_variant -j 2>/dev/null | jq -r '.str // "unknown"'
    fi
}

# Reset to US International
reset_layout() {
    setup_layouts
    
    # Ensure we're on US International (index 0)
    local current_index
    current_index=$(read_state)
    
    if [[ "$current_index" != "0" ]]; then
        # Switch to US
        hyprctl switchxkblayout all next >/dev/null 2>&1
        write_state "0"
    fi
    
    echo "Reset to US International"
}

# Show help
show_help() {
    cat << EOF
Layout Switcher Script v$VERSION

Usage: $(basename "$0") [OPTION]

Toggles between keyboard layouts using Hyprland's multi-layout configuration:
  • US International (English + German chars via AltGr)  
  • German QWERTZ with nodeadkeys (direct umlauts, no dead keys)

OPTIONS:
    --help, -h         Show this help message
    --status, -s       Show current layout (full name)
    --status-bar      Show status bar friendly output (US/DE)
    --status-detail   Show detailed status information
    --setup           Setup dual layout configuration
    --reset           Reset to US International
    --toggle          Toggle between layouts (default action)
    --version         Show version information

STATUS BAR INTEGRATION:
    For waybar, polybar, or other status bars, use:
    $(basename "$0") --status-bar
    
    This returns simply "US" or "DE" for clean display.

EXAMPLES:
    $(basename "$0")                    # Toggle layout
    $(basename "$0") --status           # Show current layout
    $(basename "$0") --status-bar       # Get US/DE for status bar
    
KEYBIND SETUP:
    Add to Hyprland config:
    bind = SUPER SHIFT, L, exec, $(realpath "$0")

EOF
}

# Main execution
main() {
    case "${1:-toggle}" in
        --help|-h)
            show_help
            ;;
        --status|-s)
            show_status
            ;;
        --status-bar)
            show_status_bar
            ;;
        --status-detail)
            show_status_detailed
            ;;
        --setup)
            setup_layouts
            write_state "0"
            echo "Dual layout configuration applied"
            ;;
        --reset)
            reset_layout
            ;;
        --version)
            echo "Layout Switcher v$VERSION"
            ;;
        --toggle|toggle)
            toggle_layout
            ;;
        *)
            toggle_layout
            ;;
    esac
}

# Sync state with actual current layout
sync_state() {
    local active_layout
    active_layout=$(hyprctl devices -j 2>/dev/null | jq -r '.keyboards[0].active_keymap // "us"' | tr '[:upper:]' '[:lower:]')
    
    local current_index
    # German layout shows as "German (no dead keys)"
    # US International shows as "English (US, intl., with dead keys)" or similar
    if [[ "$active_layout" == *"german"* ]]; then
        current_index="1"
    else
        current_index="0"
    fi
    
    write_state "$current_index"
    echo "State synced: ${LAYOUT_NAMES[$current_index]}"
}

# Initialize state if needed or sync with reality
if [[ ! -f "$STATE_FILE" ]] || [[ "${1:-}" == "--sync" ]]; then
    ensure_state_dir
    sync_state >/dev/null 2>&1
fi

# Handle --sync as a special case
if [[ "${1:-}" == "--sync" ]]; then
    sync_state
    exit 0
fi

main "$@"
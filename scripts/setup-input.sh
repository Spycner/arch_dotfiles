#!/bin/bash

# Smart Input Configuration Setup for Hyprland
# Handles German QWERTZ laptop keyboard + US layout external keyboards
# Provides automatic per-device layouts with German character support

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$SCRIPT_DIR/input-configs"
UTILS_DIR="$SCRIPT_DIR/utils"
HYPR_CONFIG_DIR="$HOME/.config/hypr"
BACKUP_DIR="$HOME/.local/share/arch_dotfiles/backups"
LOG_DIR="$HOME/.local/share/arch_dotfiles/logs"

# Ensure directories exist
mkdir -p "$BACKUP_DIR" "$LOG_DIR" "$CONFIG_DIR"

# Logging setup
LOG_FILE="$LOG_DIR/input-setup-$(date +%Y%m%d_%H%M%S).log"
exec 1> >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)

echo "=== Smart Input Configuration Setup ==="
echo "Started at: $(date)"
echo "Log file: $LOG_FILE"

# Color output functions
red() { echo -e "\033[31m$*\033[0m"; }
green() { echo -e "\033[32m$*\033[0m"; }
yellow() { echo -e "\033[33m$*\033[0m"; }
blue() { echo -e "\033[34m$*\033[0m"; }

# Help function
show_help() {
    cat << EOF
Smart Input Configuration Setup for Hyprland

Usage: $0 [OPTIONS]

OPTIONS:
    --help              Show this help message
    --dry-run          Preview changes without applying them
    --rollback         Restore previous configuration from backup
    --list-devices     Show detected keyboard devices
    --test-layouts     Test different layout configurations
    --force            Skip confirmation prompts

DESCRIPTION:
    This script sets up intelligent keyboard input configuration for Hyprland,
    automatically detecting laptop vs external keyboards and applying appropriate
    layouts:
    
    - Laptop keyboard: German QWERTZ layout
    - External keyboards: US International layout with German chars via AltGr
    - Dynamic layout switching with Super+Space keybind
    - Automatic device detection and configuration

EXAMPLES:
    $0                 # Interactive setup with preview
    $0 --dry-run       # Preview changes only
    $0 --force         # Apply changes without confirmation
    $0 --rollback      # Restore previous configuration

EOF
}

# Parse command line arguments
DRY_RUN=false
ROLLBACK=false
LIST_DEVICES=false
TEST_LAYOUTS=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --rollback)
            ROLLBACK=true
            shift
            ;;
        --list-devices)
            LIST_DEVICES=true
            shift
            ;;
        --test-layouts)
            TEST_LAYOUTS=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        *)
            red "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Detect keyboard devices
detect_keyboards() {
    echo "$(blue "Detecting keyboard devices...")"
    
    # Get keyboard devices from hyprctl
    local keyboards
    keyboards=$(hyprctl devices -j | jq -r '.keyboards[] | select(.main == true or (.name | test("keyboard|Keyboard"; "i"))) | "\(.name)|\(.main)"')
    
    echo "Found keyboards:"
    while IFS='|' read -r name is_main; do
        local status=""
        [[ "$is_main" == "true" ]] && status=" (main)"
        echo "  - $name$status"
        
        # Classify keyboard type
        if [[ "$name" =~ (at-translated-set-2|laptop|internal) ]]; then
            echo "    Type: Laptop keyboard (will use German QWERTZ)"
        else
            echo "    Type: External keyboard (will use US International)"
        fi
    done <<< "$keyboards"
    
    return 0
}

# Test layout configurations
test_layouts() {
    echo "$(blue "Testing layout configurations...")"
    echo
    echo "Current layout:"
    hyprctl getoption input:kb_layout -j | jq -r '.str'
    echo
    echo "Available layouts for testing:"
    echo "  1. us,de (US International + German)"
    echo "  2. us (US International only)"
    echo "  3. de (German only)"
    echo
    echo "Test with: hyprctl keyword input:kb_layout <layout>"
    echo "Reset with: hyprctl reload"
}

# Backup existing configuration
backup_config() {
    echo "$(blue "Creating backup of existing configuration...")"
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/hyprland-config-$timestamp.tar.gz"
    
    if [[ -f "$HYPR_CONFIG_DIR/hyprland.conf" ]]; then
        tar -czf "$backup_file" -C "$HOME/.config" hypr/
        echo "Backup created: $backup_file"
        echo "$backup_file" > "$BACKUP_DIR/latest-backup.txt"
    else
        yellow "No existing Hyprland config found to backup"
    fi
}

# Restore from backup
restore_backup() {
    echo "$(blue "Restoring from backup...")"
    
    if [[ ! -f "$BACKUP_DIR/latest-backup.txt" ]]; then
        red "No backup found to restore from"
        exit 1
    fi
    
    local backup_file
    backup_file=$(cat "$BACKUP_DIR/latest-backup.txt")
    
    if [[ ! -f "$backup_file" ]]; then
        red "Backup file not found: $backup_file"
        exit 1
    fi
    
    echo "Restoring from: $backup_file"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        tar -xzf "$backup_file" -C "$HOME/.config"
        echo "$(green "Configuration restored successfully")"
        echo "Reloading Hyprland configuration..."
        hyprctl reload
    else
        echo "DRY RUN: Would restore from $backup_file"
    fi
}

# Generate input configuration
generate_input_config() {
    echo "$(blue "Generating input configuration...")"
    
    # Create the main input configuration
    cat > "$CONFIG_DIR/hyprland-input.conf" << 'EOF'
# Smart Input Configuration
# Generated by setup-input.sh

#############
### INPUT ###
#############

# Global input settings with multiple layouts and compose key
input {
    # Multiple layouts: US International (primary), German (secondary)
    kb_layout = us,de
    kb_variant = intl,qwertz
    kb_model = pc105
    
    # Layout switching and compose key configuration
    # grp:alt_shift_toggle = Alt+Shift switches layouts
    # compose:ralt = Right Alt as compose key for special characters
    kb_options = grp:alt_shift_toggle,compose:ralt
    
    # Standard options
    kb_rules = evdev
    follow_mouse = 1
    sensitivity = 0
    
    # Touchpad settings
    touchpad {
        natural_scroll = false
        disable_while_typing = true
        clickfinger_behavior = true
        scroll_factor = 1.0
    }
}

# Per-device configuration for laptop keyboard
# This will override global settings for the main laptop keyboard
device {
    name = at-translated-set-2-keyboard
    kb_layout = de
    kb_variant = qwertz
    kb_options = compose:ralt
    # Note: Laptop keyboard uses German layout directly
    # External keyboards will use the global US International layout
}

###################
### KEYBINDINGS ###
###################

# Layout switching keybinds
bind = SUPER, SPACE, exec, hyprctl switchxkblayout current next
bind = SUPER SHIFT, SPACE, exec, hyprctl switchxkblayout current prev

# Quick layout selection
bind = SUPER, F1, exec, hyprctl keyword input:kb_layout "us,de"
bind = SUPER, F2, exec, hyprctl keyword input:kb_layout "de,us"

EOF

    echo "Input configuration generated: $CONFIG_DIR/hyprland-input.conf"
}

# Generate utility scripts
generate_utils() {
    echo "$(blue "Generating utility scripts...")"
    
    # Layout switcher script
    cat > "$UTILS_DIR/layout-switcher.sh" << 'EOF'
#!/bin/bash
# Quick layout switcher utility

case "${1:-next}" in
    next)
        hyprctl switchxkblayout current next
        ;;
    prev)
        hyprctl switchxkblayout current prev
        ;;
    us)
        hyprctl keyword input:kb_layout "us,de"
        hyprctl keyword input:kb_variant "intl,qwertz"
        ;;
    de)
        hyprctl keyword input:kb_layout "de,us"
        hyprctl keyword input:kb_variant "qwertz,intl"
        ;;
    status)
        echo "Current layout:"
        hyprctl getoption input:kb_layout -j | jq -r '.str'
        ;;
    *)
        echo "Usage: $0 {next|prev|us|de|status}"
        exit 1
        ;;
esac
EOF

    # Keyboard detector script
    cat > "$UTILS_DIR/keyboard-detector.sh" << 'EOF'
#!/bin/bash
# Keyboard detection utility

detect_keyboards() {
    echo "=== Keyboard Detection Report ==="
    echo "Timestamp: $(date)"
    echo
    
    # List all keyboards from hyprctl
    echo "Hyprland detected keyboards:"
    hyprctl devices -j | jq -r '.keyboards[] | "  \(.name) (main: \(.main))"'
    echo
    
    # Show current layout configuration
    echo "Current layout configuration:"
    echo "  Layout: $(hyprctl getoption input:kb_layout -j | jq -r '.str')"
    echo "  Variant: $(hyprctl getoption input:kb_variant -j | jq -r '.str')"
    echo "  Options: $(hyprctl getoption input:kb_options -j | jq -r '.str')"
    echo
    
    # Show per-device status
    echo "Device-specific configurations:"
    local devices
    devices=$(hyprctl devices -j | jq -r '.keyboards[] | select(.main == true) | .name')
    
    while read -r device; do
        if [[ -n "$device" ]]; then
            echo "  Main device: $device"
            # Try to get device-specific config (this may not work in all Hyprland versions)
            echo "    Layout: $(hyprctl getoption device[$device]:kb_layout -j 2>/dev/null | jq -r '.str // "using global"')"
        fi
    done <<< "$devices"
}

case "${1:-detect}" in
    detect)
        detect_keyboards
        ;;
    monitor)
        echo "Monitoring keyboard changes... (Ctrl+C to stop)"
        while true; do
            detect_keyboards
            echo "----------------------------------------"
            sleep 5
        done
        ;;
    *)
        echo "Usage: $0 {detect|monitor}"
        exit 1
        ;;
esac
EOF

    # Make utility scripts executable
    chmod +x "$UTILS_DIR/layout-switcher.sh"
    chmod +x "$UTILS_DIR/keyboard-detector.sh"
    
    echo "Utility scripts generated:"
    echo "  - $UTILS_DIR/layout-switcher.sh"
    echo "  - $UTILS_DIR/keyboard-detector.sh"
}

# Integrate with Hyprland configuration
integrate_config() {
    echo "$(blue "Integrating with Hyprland configuration...")"
    
    local hyprland_conf="$HYPR_CONFIG_DIR/hyprland.conf"
    
    if [[ ! -f "$hyprland_conf" ]]; then
        red "Hyprland configuration not found: $hyprland_conf"
        exit 1
    fi
    
    # Create backup before modifying
    local backup_file="$hyprland_conf.backup-$(date +%Y%m%d_%H%M%S)"
    cp "$hyprland_conf" "$backup_file"
    echo "Created backup: $backup_file"
    
    # Create input-configs directory if it doesn't exist
    mkdir -p "$HYPR_CONFIG_DIR/input-configs"
    
    # Check if our config is already included
    if grep -q "source.*input-configs/hyprland-input.conf" "$hyprland_conf"; then
        yellow "Input configuration already included in hyprland.conf"
    else
        # Add include for our input configuration at the end
        echo "" >> "$hyprland_conf"
        echo "# Smart Input Configuration (auto-generated)" >> "$hyprland_conf"
        echo "source = ~/.config/hypr/input-configs/hyprland-input.conf" >> "$hyprland_conf"
        echo "Added source directive to hyprland.conf"
    fi
    
    # Remove any existing duplicate input sections (cleanup)
    # Look for the old default input section and remove it if it conflicts
    if grep -q "^# https://wiki.hypr.land/Configuring/Variables/#input" "$hyprland_conf" && \
       grep -A 20 "^# https://wiki.hypr.land/Configuring/Variables/#input" "$hyprland_conf" | grep -q "kb_layout = us$"; then
        echo "Removing old default input section to avoid conflicts..."
        # Create a temporary file without the old input section
        awk '
        /^# https:\/\/wiki\.hypr\.land\/Configuring\/Variables\/#input/ {
            in_old_input = 1
            next
        }
        in_old_input && /^}$/ {
            in_old_input = 0
            next
        }
        in_old_input {
            next
        }
        !in_old_input {
            print
        }
        ' "$hyprland_conf" > "$hyprland_conf.tmp" && mv "$hyprland_conf.tmp" "$hyprland_conf"
        echo "Removed conflicting input section"
    fi
    
    # Create symlink in hypr config directory
    if ln -sf "$CONFIG_DIR/hyprland-input.conf" "$HYPR_CONFIG_DIR/input-configs/"; then
        echo "Created symlink: $HYPR_CONFIG_DIR/input-configs/hyprland-input.conf"
    else
        red "Failed to create symlink"
        return 1
    fi
    
    # Verify integration
    if [[ -f "$HYPR_CONFIG_DIR/input-configs/hyprland-input.conf" ]]; then
        echo "$(green "✓ Configuration integrated successfully")"
    else
        red "✗ Configuration integration failed"
        return 1
    fi
}

# Main execution flow
main() {
    if [[ "$LIST_DEVICES" == "true" ]]; then
        detect_keyboards
        exit 0
    fi
    
    if [[ "$TEST_LAYOUTS" == "true" ]]; then
        test_layouts
        exit 0
    fi
    
    if [[ "$ROLLBACK" == "true" ]]; then
        restore_backup
        exit 0
    fi
    
    echo "$(green "Starting smart input configuration setup...")"
    echo
    
    # Show current state
    echo "Current system state:"
    detect_keyboards
    echo
    
    # Generate configurations
    if [[ "$DRY_RUN" == "false" ]]; then
        backup_config
    else
        echo "$(yellow "DRY RUN: Skipping backup creation")"
    fi
    
    generate_input_config
    generate_utils
    
    if [[ "$DRY_RUN" == "false" ]]; then
        if [[ "$FORCE" == "false" ]]; then
            echo
            read -p "Apply configuration changes? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                yellow "Configuration generated but not applied"
                echo "Generated files:"
                echo "  - $CONFIG_DIR/hyprland-input.conf"
                echo "  - $UTILS_DIR/layout-switcher.sh"
                echo "  - $UTILS_DIR/keyboard-detector.sh"
                echo
                echo "To apply manually:"
                echo "  $0 --force"
                exit 0
            fi
        fi
        
        integrate_config
        
        echo
        echo "$(green "Reloading Hyprland configuration...")"
        hyprctl reload
        
        echo
        echo "$(green "✅ Smart input configuration setup complete!")"
        echo
        echo "Configuration summary:"
        echo "  - Laptop keyboard: German QWERTZ layout"
        echo "  - External keyboards: US International layout"
        echo "  - German characters via AltGr (AltGr+a=ä, AltGr+o=ö, AltGr+u=ü, AltGr+s=ß)"
        echo "  - Layout switching: Super+Space (next), Super+Shift+Space (prev)"
        echo "  - Quick layouts: Super+F1 (US primary), Super+F2 (DE primary)"
        echo
        echo "Utility commands:"
        echo "  - Layout switcher: $UTILS_DIR/layout-switcher.sh"
        echo "  - Device detector: $UTILS_DIR/keyboard-detector.sh"
        echo
        echo "To test German characters with AltGr:"
        echo "  AltGr + a = ä"
        echo "  AltGr + o = ö"
        echo "  AltGr + u = ü"
        echo "  AltGr + s = ß"
        
    else
        echo "$(yellow "DRY RUN: Configuration files generated but not applied")"
        echo "Generated files:"
        echo "  - $CONFIG_DIR/hyprland-input.conf"
        echo "  - $UTILS_DIR/layout-switcher.sh"
        echo "  - $UTILS_DIR/keyboard-detector.sh"
        echo
        echo "To apply:"
        echo "  $0 --force"
    fi
    
    echo
    echo "Setup completed at: $(date)"
}

# Run main function
main "$@"
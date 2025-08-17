# Utility Scripts

This directory contains utility scripts for the Arch Linux dotfiles system.

## layout-switcher.sh

A fast keyboard layout switcher for Hyprland that toggles between US International and German QWERTZ layouts.

### Features

- **Two-state toggle**: US International ↔ German QWERTZ (with nodeadkeys)
- **Error-free operation**: Uses Hyprland's multi-layout configuration to avoid variant persistence issues
- **State tracking**: Accurately detects and tracks the active layout
- **Status bar integration**: Provides clean output for waybar/polybar integration
- **Fast performance**: ~61ms execution time

### Usage

```bash
# Toggle between layouts (default action)
./layout-switcher.sh

# Get current layout status
./layout-switcher.sh --status          # Returns: us-intl or de-qwertz
./layout-switcher.sh --status-bar      # Returns: US or DE (for status bars)
./layout-switcher.sh --status-detail   # Shows detailed information

# Setup and maintenance
./layout-switcher.sh --setup           # Configure dual layout in Hyprland
./layout-switcher.sh --sync            # Sync state with actual layout
./layout-switcher.sh --reset           # Reset to US International
```

### Hyprland Integration

Add this keybind to your Hyprland configuration:

```conf
# In ~/.config/hypr/hyprland.conf or ~/.config/hypr/conf.d/keybinds.conf
bind = SUPER SHIFT, L, exec, ~/.config/hypr/scripts/utils/layout-switcher.sh
```

### Status Bar Integration

#### Waybar Example

Add to your waybar config:

```json
"custom/keyboard-layout": {
    "exec": "~/.config/hypr/scripts/utils/layout-switcher.sh --status-bar",
    "interval": 1,
    "format": "⌨ {}",
    "on-click": "~/.config/hypr/scripts/utils/layout-switcher.sh",
    "tooltip-format": "Click to toggle layout"
}
```

### Technical Details

- **State file**: `~/.local/share/arch_dotfiles/layout-current`
- **Layouts configured**: `us,de` with variants `intl,nodeadkeys`
- **Detection method**: Reads Hyprland's active_keymap from device info
- **German characters**: Direct access to ä, ö, ü, ß (no dead keys)
- **US International**: AltGr+a=ä, AltGr+o=ö, AltGr+u=ü, AltGr+s=ß

### Implementation Notes

The script uses Hyprland's native multi-layout support with `hyprctl switchxkblayout` to avoid the error messages that occur when setting layout and variant separately. State is tracked by detecting the actual active keymap name from Hyprland's device information.

## Future Scripts

Additional utility scripts will be added here as the dotfiles system expands.
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is an Arch Linux dotfiles repository designed to automate system configuration and setup. The repository includes comprehensive documentation for Arch Linux installation and will house configuration files for various system components.

## Project Structure

```
arch_dotfiles/
├── README.md                      # Main project documentation
├── docs/
│   └── arch-installation-guide.md # Comprehensive Arch Linux installation guide
└── CLAUDE.md                      # This file
```

## Expected Configuration Files

As this repository develops, it will likely include:

- **Shell configurations**: `.zshrc`, `.bashrc`, shell aliases and functions
- **Window manager configs**: Hyprland configuration files (mentioned in installation guide)
- **Terminal emulator configs**: kitty, ghostty configurations
- **Package lists**: Lists of packages to install via pacman/paru
- **Installation scripts**: Shell scripts to automate dotfile deployment
- **System configurations**: Various `/etc/` configurations that need to be symlinked or copied

## Common Development Tasks

### Adding New Configuration Files

When adding new dotfiles or configuration files:
1. Place them in a logical directory structure (e.g., `config/hyprland/`, `shell/zsh/`)
2. Consider creating a corresponding installation script or adding to an existing one
3. Document any dependencies or special installation requirements

### Creating Installation Scripts

**Script Language Policy:**
- **Python scripts for user-facing tools**: All scripts intended to be run by users should be written in Python and executed via `uv run`
- **Bash scripts for system integration**: Only use bash for lightweight scripts called by keyboard shortcuts or system hooks

When creating Python automation scripts:
1. Use PEP 723 inline script metadata for dependencies (uv script format)
2. Follow this structure:
   ```python
   """
   Script description
   
   Usage:
       uv run script_name.py [options]
   """
   # /// script
   # requires-python = ">=3.8"
   # dependencies = [
   #     "requests>=2.25.0",
   # ]
   # ///
   ```
3. Include comprehensive error handling and user feedback
4. Add informative colored output to show progress
5. Check for existing files before overwriting
6. Use argparse for command-line options (--dry-run, --rollback, --help)

When creating bash scripts (system integration only):
1. Keep minimal and fast for responsive hotkeys
2. Include error handling with `set -euo pipefail`
3. Use for simple system calls only

#### Critical Script Requirements

**All scripts MUST be:**
1. **Idempotent**: Running the script multiple times should produce the same result without causing errors or duplicating actions
   - Check if configurations already exist before creating them
   - Verify if packages are installed before attempting installation
   - Use conditional logic to skip already-completed steps

2. **Rollback-capable**: Every script should support an undo mechanism
   - Create backups before modifying existing files (timestamp them)
   - Implement a `--rollback` or `--undo` flag
   - Store rollback information in a state file or backup directory
   - Log all changes made for potential manual rollback

Example patterns:
```bash
# Idempotent symlink creation
if [ ! -L "$HOME/.config/nvim" ]; then
    ln -s "$DOTFILES/nvim" "$HOME/.config/nvim"
fi

# Backup before overwriting
if [ -f "$HOME/.zshrc" ]; then
    cp "$HOME/.zshrc" "$HOME/.zshrc.backup.$(date +%Y%m%d_%H%M%S)"
fi
```

### Working with Package Lists

When managing package lists:
1. Separate official repository packages from AUR packages
2. Group packages by purpose (e.g., development, multimedia, system utilities)
3. Include comments explaining why specific packages are needed

## Key Technologies and Tools

Based on the installation guide, this repository targets:

- **Package Managers**: pacman (official), paru (AUR helper)
- **Window Manager**: Hyprland (Wayland compositor)
- **Terminal Emulators**: kitty, ghostty
- **Shell**: zsh (with potential oh-my-zsh integration)
- **Session Manager**: uwsm (Wayland session manager)
- **Development Tools**: git, github-cli, neovim

## Architecture Considerations

### Dotfile Management Strategy

When implementing dotfile management:
1. Consider using GNU Stow for symlink management if the repository grows complex
2. Keep user-specific settings separate from system-wide configurations
3. Provide backup mechanisms before overwriting existing configurations

### Script Organization

Organize scripts by function:
- `install/` - Installation and setup scripts
- `backup/` - Backup existing configurations  
- `utils/` - Utility scripts for maintenance

All scripts should follow a consistent pattern:
1. Support `--help` flag for usage information
2. Support `--dry-run` flag to preview changes without applying them
3. Support `--rollback` flag to undo previous changes
4. Maintain logs in `~/.local/share/arch_dotfiles/logs/`
5. Store backups in `~/.local/share/arch_dotfiles/backups/`

### Configuration File Structure

Follow XDG Base Directory Specification:
- User configurations: `~/.config/`
- User data: `~/.local/share/`
- Cache: `~/.cache/`

## Important Notes

### System Compatibility

- This repository is specifically for Arch Linux systems
- UEFI boot mode is assumed (as per the installation guide)
- NetworkManager is the primary network management tool
- Wayland is the display protocol (via Hyprland)

### Locale and Regional Settings

The installation guide shows mixed locale settings:
- Primary: `en_US.UTF-8`
- Secondary: `de_DE.UTF-8` (for numeric, time, monetary, and measurements)
- Timezone: Europe/Berlin

When adding configuration files, be aware of these regional preferences.

### Security Considerations

- Never commit sensitive information (passwords, API keys, tokens)
- Use environment variables or separate untracked files for secrets
- Consider using tools like `pass` or `bitwarden-cli` for credential management

## Testing and Validation

When developing installation scripts or configuration changes:
1. Test in a clean Arch Linux environment (consider using VMs)
2. Verify that all symlinks are created correctly
3. Check that configurations work with the specified package versions
4. Ensure scripts are idempotent (can be run multiple times safely)

## Task Master AI Instructions
**Import Task Master's development workflow commands and guidelines, treat as if import is in the main CLAUDE.md file.**
@./.taskmaster/CLAUDE.md

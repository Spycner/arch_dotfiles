# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is an Arch Linux dotfiles repository designed to automate system configuration and setup. The repository includes comprehensive documentation for Arch Linux installation and configuration files for Hyprland window manager and various system components.

## Project Structure

```
arch_dotfiles/
├── README.md                          # Main project documentation
├── CLAUDE.md                          # This file
├── .claude/                           # Claude Code configuration
│   ├── agents/                        # Project-specific AI agents
│   └── commands/                      # Project-specific slash commands
├── docs/
│   └── arch-installation-guide.md     # Comprehensive Arch Linux installation guide
├── config/
│   └── hypr/                          # Hyprland window manager configuration
│       ├── hyprland.conf              # Main Hyprland config
│       ├── conf.d/                    # Modular configuration files
│       │   ├── input.conf             # Input device settings
│       │   ├── keybinds.conf         # Keyboard shortcuts
│       │   ├── appearance.conf       # Visual settings
│       │   └── windowrules.conf      # Window management rules
│       └── scripts/                   # Hyprland utility scripts
│           └── reload-config.sh       # Config reload helper
├── scripts/
│   ├── setup_hyprland.py             # Hyprland setup with backup/rollback
│   ├── setup-claude.py               # Claude Code configuration setup
│   ├── setup-theming.py              # Theming packages installer
│   ├── setup-fuzzel.py               # Fuzzel launcher setup with Catppuccin Latte theme
│   ├── setup-utils.py                # Utilities setup script
│   ├── setup-input.sh                # Input configuration script
│   ├── install-cli-tools.py          # CLI tools installer
│   ├── utils/                        # Utility scripts
│   │   ├── layout-switcher.sh        # Keyboard layout toggle (US/DE)
│   │   └── README.md                 # Utils documentation
│   └── optional-installs/            # Optional component installers
│       └── task-master/               # Task Master AI setup
└── .taskmaster/                       # Task Master AI configuration
    ├── config.json                    # AI model configuration
    ├── tasks/                         # Task files directory
    └── CLAUDE.md                      # Task Master specific guidance
```

## Common Commands

### Hyprland Setup and Management

```bash
# Setup Hyprland configuration (idempotent, creates backups)
uv run scripts/setup_hyprland.py

# Preview changes without applying
uv run scripts/setup_hyprland.py --dry-run

# Rollback to previous configuration
uv run scripts/setup_hyprland.py --rollback

# Reload Hyprland configuration
hyprctl reload

# Toggle keyboard layout (US International ↔ German QWERTZ)
./scripts/utils/layout-switcher.sh

# Check current keyboard layout
./scripts/utils/layout-switcher.sh --status
```

### Theming Setup

```bash
# Install all theming packages and tools
uv run scripts/setup-theming.py

# Install only essential theming tools (no themes)
uv run scripts/setup-theming.py --minimal

# Skip AUR packages, only official repos
uv run scripts/setup-theming.py --skip-aur

# Preview what would be installed
uv run scripts/setup-theming.py --dry-run

# After installation, configure themes:
nwg-look          # GTK settings for Wayland
qt5ct             # Qt5 theme configuration
kvantummanager    # Advanced Qt theming

# Fuzzel launcher setup (Wayland-native app launcher)
uv run scripts/setup-fuzzel.py               # Install and configure with Catppuccin Latte theme
uv run scripts/setup-fuzzel.py --dry-run     # Preview changes without applying
uv run scripts/setup-fuzzel.py --rollback    # Revert to previous launcher setup
```

### Task Master Workflow

```bash
# Parse PRD to generate tasks
task-master parse-prd .taskmaster/docs/prd.txt

# View all tasks
task-master list

# Get next task to work on
task-master next

# Mark task complete
task-master set-status --id=<id> --status=done

# Expand task into subtasks
task-master expand --id=<id> --research
```

### Claude Code Configuration

```bash
# Setup Claude Code agents and commands (idempotent, creates backups)
uv run scripts/setup-claude.py

# Preview changes without applying
uv run scripts/setup-claude.py --dry-run

# Check current status of Claude configuration
uv run scripts/setup-claude.py --status

# Rollback Claude configuration setup
uv run scripts/setup-claude.py --rollback

# Add a new project agent
echo "---
name: \"arch-expert\"
description: \"Specializes in Arch Linux configuration\"
tools: [\"Read\", \"Edit\", \"Bash\"]
---

You are an Arch Linux expert. Help with system configuration, package management, and troubleshooting." > .claude/agents/arch-expert.md

# Add a new project command
echo "Review the Hyprland configuration in @config/hypr/hyprland.conf and suggest optimizations" > .claude/commands/review-hypr.md

# List available agents and commands
claude --help
```

## Implemented Features

### Hyprland Window Manager
- **Complete configuration**: Modular config in `config/hypr/` with separate files for input, keybinds, appearance, and window rules
- **Automated setup**: Python script with full backup and rollback support at scripts/setup_hyprland.py:39-317
- **Symlink management**: Automatic creation of symlinks from repo to `~/.config/hypr/`
- **State tracking**: JSON state file for rollback operations

### Keyboard Layout Management
- **Dual layout support**: US International and German QWERTZ switching via scripts/utils/layout-switcher.sh:1-281
- **Hyprland integration**: Uses native Hyprland multi-layout feature to avoid errors
- **State persistence**: Maintains layout state in `~/.local/share/arch_dotfiles/`
- **Status bar support**: Provides simple US/DE output for waybar/polybar integration
- **Hotkey binding**: Designed for Super+Shift+L keyboard shortcut

### Task Master AI Integration
- **Project management**: Full Task Master setup for tracking development tasks
- **MCP server ready**: Configuration for Claude Code MCP integration
- **Research capabilities**: Support for Perplexity AI-powered research
- **Task workflows**: Commands for parsing PRDs, expanding tasks, and tracking progress

### Theming Infrastructure
- **Package installer**: Python script to install theming tools and popular themes at scripts/setup-theming.py
- **Multi-toolkit support**: Installs tools for GTK (nwg-look, lxappearance), Qt (qt5ct, qt6ct), and Kvantum theming
- **Theme collections**: Optional installation of popular themes (Nordic, Dracula, Catppuccin, Gruvbox, etc.)
- **Icon and cursor themes**: Papirus, Numix, Bibata, and other popular icon/cursor sets
- **Font packages**: Comprehensive font collection including Nerd Fonts, Roboto, Fira Code
- **Environment template**: Auto-generates env.conf template for Hyprland theme variables

### Fuzzel App Launcher
- **Wayland-native launcher**: Modern application launcher optimized for Hyprland and wlroots compositors
- **Catppuccin Latte theming**: Light, elegant color scheme with background `#eff1f5`, text `#4c4f69`, and blue accents
- **Complete automation**: Python setup script handles installation, configuration, and Hyprland integration at scripts/setup-fuzzel.py
- **Dual keybinds**: Super+Space (primary) and Super+R (alternative) for quick launcher access
- **Backup and rollback**: Full state tracking with timestamped backups for safe configuration changes
- **dmenu compatibility**: Supports script integration with dmenu-compatible interface

### Claude Code Configuration
- **Project-specific agents**: Version-controlled AI agents in `.claude/agents/` for team sharing at .claude/agents/README.md
- **Custom slash commands**: Project-specific commands in `.claude/commands/` for frequently-used prompts at .claude/commands/README.md
- **Symlink management**: Automated setup script creates symlinks from `~/.claude/` to project directories at scripts/setup-claude.py:1-582
- **Backup and rollback**: Full backup support with timestamped state tracking
- **Team collaboration**: Share Claude configurations with version control while maintaining user-level compatibility

## Expected Future Additions

- **Shell configurations**: `.zshrc`, `.bashrc`, shell aliases and functions
- **Terminal emulator config**: kitty configuration with GPU acceleration and image viewing  
- **Package lists**: Lists of packages to install via pacman/paru
- **System configurations**: Various `/etc/` configurations that need to be symlinked or copied

## Testing and Validation Commands

### Script Validation
```bash
# Test Hyprland setup without making changes
uv run scripts/setup_hyprland.py --dry-run

# Validate Hyprland configuration syntax
hyprctl reload 2>&1 | grep -q "error" && echo "Config has errors" || echo "Config valid"

# Test keyboard layout switcher
./scripts/utils/layout-switcher.sh --status-detail

# Check Task Master configuration
task-master models  # Shows configured AI models and API key status

# Test Claude Code setup without making changes
uv run scripts/setup-claude.py --dry-run

# Check Claude configuration status
uv run scripts/setup-claude.py --status
```

### Python Script Linting
Since all user-facing scripts use `uv run`, ensure PEP 723 compliance:
```bash
# Check Python script has correct inline metadata
grep -A5 "# /// script" scripts/setup_hyprland.py

# Run script help to verify it works
uv run scripts/setup_hyprland.py --help
```

## Common Development Tasks

### Adding New Configuration Files

When adding new dotfiles or configuration files:
1. Place them in a logical directory structure (e.g., `config/hyprland/`, `shell/zsh/`)
2. Create a corresponding Python setup script using the `setup_hyprland.py` pattern
3. Document any dependencies or special installation requirements
4. Test with `--dry-run` flag before actual deployment

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
- **Terminal Emulator**: kitty (GPU-accelerated with image viewing support)
- **Shell**: zsh (with potential oh-my-zsh integration)
- **Session Manager**: uwsm (Wayland session manager)
- **Development Tools**: git, github-cli, neovim

## Architecture Patterns

### Script Implementation Pattern (Python)
All Python scripts follow the pattern established in scripts/setup_hyprland.py:25-321:
```python
class SetupClass:
    def __init__(self, repo_root: Path, dry_run: bool = False):
        self.repo_root = repo_root
        self.dry_run = dry_run
        self.backup_dir = Path.home() / '.local' / 'share' / 'arch_dotfiles' / 'backups'
        self.state_file = Path.home() / '.local' / 'share' / 'arch_dotfiles' / 'setup_state.json'
        
    def backup_existing_config(self) -> Dict[str, str]:
        # Create timestamped backups
        
    def setup(self) -> bool:
        # Main setup logic with validation
        
    def rollback(self) -> bool:
        # Restore from backup using state file
```

### Symlink Management Strategy
- **Source of truth**: Repository files in `config/` directory
- **Target location**: User's `~/.config/` directory
- **Linking method**: Python's `Path.symlink_to()` for atomic operations
- **Backup strategy**: Timestamped copies before any modifications
- **State tracking**: JSON file with setup metadata for reliable rollback

### Script Organization

Current organization (implemented):
- `scripts/` - Main setup scripts (Python for user-facing, bash for system hooks)
- `scripts/utils/` - Utility scripts (keyboard layout switcher, etc.)
- `scripts/optional-installs/` - Optional component installers
- `config/` - Configuration files organized by application

All scripts follow a consistent pattern:
1. **Required flags**: `--help`, `--dry-run`, `--rollback`
2. **State persistence**: JSON files in `~/.local/share/arch_dotfiles/`
3. **Backup location**: `~/.local/share/arch_dotfiles/backups/` with timestamps
4. **Idempotency**: Check existing state before making changes
5. **Color output**: Consistent color scheme using ANSI codes

### Configuration File Structure

Follow XDG Base Directory Specification:
- User configurations: `~/.config/`
- User data: `~/.local/share/`
- Cache: `~/.cache/`
- State files: `~/.local/share/arch_dotfiles/`

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

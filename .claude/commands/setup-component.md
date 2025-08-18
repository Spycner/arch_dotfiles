---
description: "Create a new component with boilerplate following repository patterns"
tools: ["Write", "Edit", "Read"]
---

Create a new $ARGUMENTS component following the arch_dotfiles repository patterns.

Requirements:
1. **Python Script**: Use PEP 723 inline metadata for uv script execution
2. **Class Structure**: Follow the pattern from setup_hyprland.py with backup/rollback
3. **Standard Features**: Include --dry-run, --rollback, --help, --status flags
4. **State Management**: JSON state file in ~/.local/share/arch_dotfiles/
5. **Logging**: Timestamped logs in ~/.local/share/arch_dotfiles/logs/
6. **Color Output**: Use ANSI colors for user feedback
7. **Error Handling**: Comprehensive exception handling
8. **Documentation**: Include usage examples and description

Generate the complete Python script with proper structure and all necessary functionality.
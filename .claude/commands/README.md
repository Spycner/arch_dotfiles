# Project Commands

This directory contains project-specific Claude Code slash commands that are shared with the team.

## About Commands

Slash commands allow you to define frequently-used prompts as Markdown files. They support dynamic arguments and can execute bash commands.

## Usage

Commands in this directory are available when working in this project and are shown with "(project)" in the command list.

To use a command:
```bash
/command-name [arguments]
```

To list available commands:
```bash
/help
```

## Creating Commands

Create a new command by adding a Markdown file:

### Simple Command
```markdown
Analyze this code for potential security vulnerabilities
```

### Command with Arguments
```markdown
---
description: "Setup a new component with boilerplate"
tools: ["Write", "Edit"]
---

Create a new $ARGUMENTS component following the repository patterns.
Include proper error handling and documentation.
```

### Command with File Reference
```markdown
Review the configuration in @hyprland.conf and suggest optimizations
```

## Examples

- `setup-component.md` - Creates boilerplate for new components
- `review-config.md` - Reviews configuration files for best practices
- `check-deps.md` - Analyzes project dependencies
- `optimize.md` - Suggests performance improvements

## Documentation

For more information about creating and using slash commands, see:
- [Claude Code Slash Commands Documentation](https://docs.anthropic.com/en/docs/claude-code/slash-commands)
# Project Agents

This directory contains project-specific Claude Code agents that are shared with the team.

## About Agents

Agents are specialized AI assistants defined in Markdown files with YAML frontmatter. They provide custom prompts and tool permissions for specific tasks.

## Usage

Agents in this directory are available when working in this project and are shown with "(project)" in the agent list.

To use an agent:
```bash
claude --agent <agent-name>
```

## Creating Agents

Create a new agent by adding a Markdown file:
```markdown
---
name: "code-reviewer"
description: "Reviews code for best practices and potential issues"
tools: ["Read", "Grep", "Bash"]
---

You are a code reviewer specializing in Python and shell scripts.
Focus on security, performance, and maintainability.
```

## Examples

- `arch-expert.md` - Agent specialized in Arch Linux system configuration
- `hyprland-helper.md` - Agent for Hyprland window manager assistance
- `dotfiles-manager.md` - Agent for managing dotfile configurations

## Documentation

For more information about creating and using agents, see:
- [Claude Code Agents Documentation](https://docs.anthropic.com/en/docs/claude-code/settings)
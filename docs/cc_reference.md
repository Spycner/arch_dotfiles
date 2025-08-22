# Claude Code Reference

## Overview
Claude Code is Anthropic's official CLI tool that provides an interactive development environment powered by Claude AI. It combines the capabilities of a powerful AI assistant with comprehensive development tools, custom commands, specialized subagents, and extensible integrations.

### Development Status
- **Current Version**: Production-ready
- **Development Stage**: Stable
- **Stability**: Production-ready for professional development

### Key Features
- Interactive AI-powered development assistance
- Custom slash commands for reusable workflows
- Specialized subagents with isolated context windows
- Model Context Protocol (MCP) integrations
- Comprehensive tool ecosystem (file operations, web search, code execution)
- Project-specific and user-level configurations
- Memory management and context preservation

## Installation & Usage

### Installation
Claude Code is available through multiple installation methods:

```bash
# Install via package managers
npm install -g @anthropic-ai/claude-code
# or
brew install claude-code
# or
pip install claude-code
```

### Basic Usage
Start Claude Code in interactive mode:

```bash
# Start in current directory
claude

# Start with specific context
claude --resume
claude --memory

# Start with project-specific settings
cd /path/to/project && claude
```

## Configuration

### Configuration File Discovery
Claude Code searches for configuration in multiple locations:
1. Project-level: `.claude/` directory in current or parent directories
2. User-level: `~/.claude/` directory (macOS/Linux) or `%APPDATA%\claude\` (Windows)
3. System-level: Global configuration files

### Configuration Precedence
- Command-line options override all persistent configuration
- Project-level configuration overrides user-level configuration
- Local project settings take precedence over global settings

### Project Configuration Structure
```
.claude/
├── commands/           # Custom slash commands
│   ├── command1.md
│   └── command2.md
├── agents/            # Custom subagents
│   ├── agent1.md
│   └── agent2.md
├── settings.json      # Project-specific settings
└── memory/           # Project memory and context
```

### Available Configuration Options

#### Core Settings (settings.json)
```json
{
  "model": "claude-3-5-sonnet-20241022",
  "temperature": 0.7,
  "max_tokens": 4096,
  "tools": ["*"],
  "memory": {
    "enabled": true,
    "max_entries": 1000
  },
  "mcp": {
    "servers": []
  }
}
```

#### Environment Variables
- **`ANTHROPIC_API_KEY`**: Authentication for Claude API
- **`CLAUDE_CODE_CONFIG_PATH`**: Custom configuration directory
- **`CLAUDE_CODE_LOG_LEVEL`**: Logging verbosity (debug, info, warn, error)

## Slash Commands System

### Built-in Commands
Claude Code provides several built-in slash commands:

```bash
/help              # Show available commands
/clear             # Clear conversation history
/memory            # Manage conversation memory
/settings          # View/modify settings
/agents            # List available subagents
/tools             # List available tools
/exit              # Exit Claude Code
```

### Custom Commands

#### Creating Custom Commands
Custom commands are Markdown files with YAML frontmatter:

```markdown
---
allowed-tools: Read, Write, Edit, Bash
description: Description of what this command does
model: sonnet  # Optional: specific model for this command
---

# Command Content
Your prompt template with $ARGUMENTS placeholder.
```

#### Command Locations
- **Project-level**: `.claude/commands/command-name.md`
- **User-level**: `~/.claude/commands/command-name.md`

#### Command Features
- **Dynamic Arguments**: Use `$ARGUMENTS` placeholder for user input
- **Tool Restrictions**: Specify allowed tools in frontmatter
- **Model Selection**: Override default model per command
- **File References**: Include file content with `@filename`
- **Bash Integration**: Execute shell commands with `!command`

#### Advanced Command Examples

**Code Review Command:**
```markdown
---
allowed-tools: Read, Grep, Edit
description: Perform comprehensive code review
---

# Code Review

Review the following code for:
- Security vulnerabilities
- Performance issues
- Code quality and best practices
- Potential bugs

Files to review: $ARGUMENTS

Provide detailed feedback and suggestions for improvement.
```

**Project Setup Command:**
```markdown
---
allowed-tools: Write, Bash, Edit
description: Initialize new project with standard structure
---

# Project Setup

Create a new project structure for: $ARGUMENTS

Include:
- Standard directory structure
- Configuration files (pyproject.toml, .gitignore)
- Basic documentation (README.md)
- Development workflow setup
```

## Subagents System

### Overview
Subagents are specialized AI assistants with dedicated context windows, custom system prompts, and specific tool access. They operate independently and can be invoked automatically or explicitly.

### Subagent Architecture
- **Isolated Context**: Each subagent has its own conversation context
- **Specialized Prompts**: Custom system prompts for specific domains
- **Tool Restrictions**: Limited tool access for security and focus
- **Parallel Execution**: Multiple subagents can run concurrently (up to 10)

### Creating Custom Subagents

#### Subagent File Structure
```markdown
---
name: subagent-name
description: When this subagent should be invoked
tools: Read, Write, Edit, Grep  # Optional - inherits all if omitted
model: sonnet  # Optional - sonnet, opus, or haiku
---

# Subagent System Prompt

You are a specialized agent focused on [specific domain].

Your responsibilities include:
- [Responsibility 1]
- [Responsibility 2]
- [Responsibility 3]

## Methodology
[Detailed instructions for the subagent]

## Output Requirements
[Specifications for expected outputs]
```

#### Subagent Locations
- **Project-level**: `.claude/agents/agent-name.md`
- **User-level**: `~/.claude/agents/agent-name.md`

### Subagent Invocation

#### Automatic Invocation
Claude Code automatically selects appropriate subagents based on:
- Task description in user request
- Subagent description field
- Current context and available tools
- Pattern matching and semantic similarity

#### Explicit Invocation
```bash
# Direct subagent request
"Use the code-reviewer subagent to analyze this function"

# Task delegation
"Have the security-analyst subagent audit this authentication code"
```

#### Built-in Subagent Types
- **general-purpose**: Multi-step tasks and complex research
- **statusline-setup**: Configure Claude Code status line
- **output-style-setup**: Create custom output styles

### Advanced Subagent Examples

**Security Analyst:**
```markdown
---
name: security-analyst
description: Analyze code for security vulnerabilities and compliance
tools: Read, Grep, WebSearch
---

# Security Analysis Specialist

You are a cybersecurity expert focused on code security analysis.

Analyze code for:
- SQL injection vulnerabilities
- XSS attack vectors
- Authentication/authorization flaws
- Data exposure risks
- Dependency vulnerabilities

Provide detailed reports with remediation steps.
```

**Performance Optimizer:**
```markdown
---
name: performance-optimizer
description: Optimize code performance and identify bottlenecks
tools: Read, Edit, Bash
---

# Performance Optimization Specialist

You specialize in code performance analysis and optimization.

Focus areas:
- Algorithm complexity analysis
- Memory usage optimization
- Database query optimization
- Caching strategies
- Profiling and benchmarking
```

## Model Context Protocol (MCP) Integration

### Overview
MCP enables Claude Code to connect with external tools, databases, and APIs through standardized interfaces.

### Connection Types
- **Local stdio**: Direct process communication
- **Remote SSE**: Server-Sent Events for real-time updates
- **Remote HTTP**: Standard HTTP API integration

### MCP Configuration
```bash
# Add MCP server
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp

# List configured servers
claude mcp list

# Remove server
claude mcp remove sentry
```

### MCP Capabilities
- Issue tracker integration (GitHub, Jira, Linear)
- Database connectivity (PostgreSQL, MySQL, MongoDB)
- Monitoring and observability (Sentry, DataDog)
- Cloud service integration (AWS, GCP, Azure)
- Custom tool development

## Tool Ecosystem

### Core Tools
- **File Operations**: Read, Write, Edit, MultiEdit, Glob
- **Search**: Grep, WebSearch, WebFetch
- **Execution**: Bash, NotebookEdit, executeCode
- **Development**: Task (subagent delegation), TodoWrite
- **IDE Integration**: getDiagnostics, language server features

### Tool Access Control
Tools can be restricted at multiple levels:
- Command-level (in slash command frontmatter)
- Subagent-level (in subagent configuration)
- Project-level (in settings.json)
- User-level (in global configuration)

### Custom Tool Development
Create custom tools through MCP servers:
```python
# Example MCP tool implementation
from mcp import Server, Tool

class CustomTool(Tool):
    name = "custom-operation"
    description = "Performs custom operation"
    
    async def execute(self, **kwargs):
        # Tool implementation
        return result
```

## Integration with Development Workflow

### IDE Integration
- **VS Code**: Native extension with language server
- **PyCharm**: Plugin support for AI assistance
- **Vim/Neovim**: Command-line integration
- **Cursor**: Built-in Claude Code support

### CI/CD Integration
```yaml
# GitHub Actions example
- name: AI Code Review
  uses: anthropic/claude-code-action@v1
  with:
    command: "/code-review ${{ github.event.pull_request.head.sha }}"
    api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

### Version Control Integration
```bash
# Git hooks integration
git config core.hooksPath .claude/hooks

# Pre-commit AI review
echo "claude /code-review --staged" > .claude/hooks/pre-commit
```

## Best Practices

### 1. **Command Organization**
- Create focused, single-purpose commands
- Use descriptive names and documentation
- Version control project-level commands
- Share useful commands with team

### 2. **Subagent Design**
- Design for specific domains and expertise
- Limit tool access for security
- Write comprehensive system prompts
- Test subagent behavior thoroughly

### 3. **Project Structure**
- Maintain clean `.claude/` directory structure
- Document custom commands and subagents
- Use consistent naming conventions
- Regular cleanup of unused configurations

### 4. **Security Considerations**
- Restrict sensitive tool access
- Use environment variables for secrets
- Regular audit of MCP connections
- Monitor subagent permissions

## Troubleshooting

### Command Issues
**Command not found:**
```bash
# Check command file exists
ls .claude/commands/
ls ~/.claude/commands/

# Verify file format and frontmatter
```

**Permission errors:**
```bash
# Check tool permissions in frontmatter
allowed-tools: Read, Write, Edit

# Verify file system permissions
chmod 644 .claude/commands/*.md
```

### Subagent Issues
**Subagent not invoked automatically:**
- Check description field specificity
- Verify subagent name uniqueness
- Test explicit invocation first

**Context window errors:**
- Each subagent has independent context
- Consider task complexity and size
- Use Task tool for delegation

### MCP Connection Issues
**Server connection failed:**
```bash
# Check server status
claude mcp status server-name

# Verify authentication
echo $ANTHROPIC_API_KEY

# Test connection manually
curl -H "Authorization: Bearer $ANTHROPIC_API_KEY" <server-url>
```

### General Troubleshooting
**Memory issues:**
```bash
# Clear conversation memory
/clear

# Reset project memory
rm -rf .claude/memory/
```

**Configuration conflicts:**
```bash
# Check effective configuration
claude --show-config

# Reset to defaults
claude --reset-config
```

## Advanced Features

### Memory Management
- **Conversation Memory**: Automatic context preservation
- **Project Memory**: Long-term project knowledge
- **Semantic Search**: Intelligent memory retrieval
- **Memory Cleanup**: Automatic and manual memory management

### Parallel Processing
- **Concurrent Subagents**: Up to 10 parallel executions
- **Task Queuing**: Automatic task scheduling
- **Resource Management**: Intelligent resource allocation

### Context Window Optimization
- **Dynamic Context**: Intelligent context selection
- **Memory Summarization**: Automatic long conversation handling
- **Context Sharing**: Selective context sharing between subagents

## Migration and Upgrade

### Upgrading Claude Code
```bash
# Check current version
claude --version

# Upgrade to latest
npm update -g @anthropic-ai/claude-code

# Migrate configuration if needed
claude --migrate-config
```

### Migrating from Other AI Tools
1. **Export existing configurations**
2. **Convert command formats to Claude Code syntax**
3. **Update tool references and permissions**
4. **Test all custom workflows**

## Resources
- [Official Documentation](https://docs.anthropic.com/en/docs/claude-code)
- [GitHub Repository](https://github.com/anthropics/claude-code)
- [Community Discord](https://discord.gg/anthropic)
- [MCP Documentation](https://docs.anthropic.com/en/docs/claude-code/mcp)
- [API Reference](https://docs.anthropic.com/en/api)

## Community Resources
- [Awesome Claude Code Agents](https://github.com/hesreallyhim/awesome-claude-code-agents)
- [Production Subagents Collection](https://github.com/VoltAgent/awesome-claude-code-subagents)
- [Claude Code Examples](https://github.com/wshobson/agents)

## Notes
- **Production Ready**: Claude Code is stable and suitable for professional development
- **Active Development**: Regular updates and new features
- **Community Driven**: Strong community contribution to subagents and tools
- **Extensible**: Highly customizable through commands, subagents, and MCP
- **Privacy Focused**: Local configuration and optional cloud features
- **Cross-Platform**: Support for macOS, Linux, and Windows

---

This reference provides comprehensive coverage of Claude Code's capabilities, from basic usage to advanced customization and integration patterns.
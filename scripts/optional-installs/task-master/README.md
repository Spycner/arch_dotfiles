# Task Master AI Setup Documentation

## Overview

Task Master AI is a task management and development workflow automation tool that integrates with Claude Code. This documentation covers the automated setup process that has been configured for this repository.

## Configuration Details

Based on the interactive initialization requirements, the automated setup configures Task Master with:

### Interactive Responses Mapping
The original interactive `task-master init` prompts and our automated responses:

1. **First prompt (y)**: Enable AI-powered features
2. **Second prompt (n)**: Decline telemetry/analytics
3. **Third prompt (y)**: Enable Claude Code integration
4. **Fourth prompt (y)**: Enable advanced features

### Model Configuration
- **Provider Selection**: "Claude Code" (exclusively)
- **Language**: English (default)
- **Models**: All three models (main, research, fallback) use:
  - Provider: `claude-code`
  - Model ID: `sonnet`
  - Max Tokens: `64000`
  - Temperature: `0.2` (main/fallback), `0.1` (research)

## Installation Scripts

The repository includes three Python scripts for Task Master setup:

### 1. `install-task-master.py`
Handles the npm package installation:
- Installs `task-master-ai` globally
- Supports idempotent installation
- Provides rollback capability
- Logs all operations

### 2. `init-task-master.py`
Handles Task Master initialization:
- Creates `.taskmaster` directory structure
- Generates `config.json` with predefined settings
- Creates `CLAUDE.md` for AI instructions
- Supports backup and rollback

### 3. `setup-task-master.sh`
Combined setup script that orchestrates both installation and initialization:
- Runs both Python scripts in sequence
- Provides unified interface
- Handles prerequisites checking

## Quick Start

### Prerequisites

1. **Node.js and npm**:
   ```bash
   # Install via nvm (recommended)
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
   nvm install node
   ```

2. **Python 3.11+ and uv**:
   ```bash
   # Install uv
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

### Complete Setup (Recommended)

Run the combined setup script:

```bash
# Complete installation and initialization
./scripts/optional-installs/task-master/setup-task-master.sh

# Or with individual steps visible
./scripts/optional-installs/task-master/setup-task-master.sh --dry-run  # Preview
./scripts/optional-installs/task-master/setup-task-master.sh             # Execute
```

### Individual Operations

If you need more control, use the individual scripts:

```bash
# Install only
uv run scripts/optional-installs/task-master/install-task-master.py install

# Initialize only (requires installation)
uv run scripts/optional-installs/task-master/init-task-master.py init

# Check status
uv run scripts/optional-installs/task-master/install-task-master.py status
uv run scripts/optional-installs/task-master/init-task-master.py status

# Rollback
uv run scripts/optional-installs/task-master/install-task-master.py rollback
uv run scripts/optional-installs/task-master/init-task-master.py rollback
```

## Script Features

### Idempotency
All scripts are idempotent - running them multiple times produces the same result:
- Installation checks if package is already installed
- Initialization checks for existing configuration
- Use `--force` flag to override

### Rollback Capability
Every operation can be rolled back:
- Installation: Uninstalls the npm package
- Initialization: Restores from automatic backups
- Backups stored in `~/.local/share/arch_dotfiles/backups/`

### Logging
All operations are logged:
- Log location: `~/.local/share/arch_dotfiles/logs/`
- Separate log file for each run
- State tracking for rollback operations

### Dry Run Mode
Preview changes before applying:
```bash
./scripts/optional-installs/task-master/setup-task-master.sh --dry-run
```

## Directory Structure

After setup, Task Master creates the following structure:

```
.taskmaster/
├── config.json      # Main configuration file
├── state.json       # State tracking
├── CLAUDE.md        # AI-specific instructions
├── tasks/           # Task definitions
├── reports/         # Generated reports
├── docs/            # Documentation
└── templates/       # Task templates
```

## Configuration File

The generated `config.json` includes:

```json
{
  "models": {
    "main": {
      "provider": "claude-code",
      "modelId": "sonnet",
      "maxTokens": 64000,
      "temperature": 0.2
    },
    "research": {
      "provider": "claude-code",
      "modelId": "sonnet",
      "maxTokens": 64000,
      "temperature": 0.1
    },
    "fallback": {
      "provider": "claude-code",
      "modelId": "sonnet",
      "maxTokens": 64000,
      "temperature": 0.2
    }
  },
  "global": {
    "logLevel": "info",
    "debug": false,
    "responseLanguage": "English",
    "projectName": "Taskmaster"
  }
}
```

## Troubleshooting

### Common Issues

1. **"task-master: command not found"**
   - Ensure npm global bin is in PATH
   - Run: `npm config get prefix` and add `/bin` to PATH

2. **"uv: command not found"**
   - Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Restart terminal or source shell config

3. **Permission errors**
   - Ensure you have write permissions to current directory
   - npm global installations may require proper npm setup

### Verification

After setup, verify installation:

```bash
# Check installation
task-master --version

# Check configuration
cat .taskmaster/config.json

# Run Task Master help
task-master --help
```

## Integration with Claude Code

Task Master is configured to work exclusively with Claude Code:
- All AI operations use Claude Code as the provider
- Sonnet model for optimal performance
- Configuration aligned with Claude Code capabilities

The `.taskmaster/CLAUDE.md` file provides specific instructions for Claude when working with Task Master tasks in this project.

## Best Practices

1. **Always use the setup script for initial installation**
   - Ensures consistent configuration
   - Proper logging and state tracking

2. **Check status before operations**
   ```bash
   ./scripts/optional-installs/task-master/setup-task-master.sh --status
   ```

3. **Use dry-run for testing**
   ```bash
   ./scripts/optional-installs/task-master/setup-task-master.sh --dry-run
   ```

4. **Keep backups**
   - Automatic backups are created
   - Located in `~/.local/share/arch_dotfiles/backups/`

5. **Review logs for troubleshooting**
   - Logs in `~/.local/share/arch_dotfiles/logs/`
   - Each run creates a timestamped log file

## Advanced Usage

### Force Reinstallation
```bash
./scripts/optional-installs/task-master/setup-task-master.sh --force
```

### Partial Setup
```bash
# Install only
./scripts/optional-installs/task-master/setup-task-master.sh --install-only

# Initialize only
./scripts/optional-installs/task-master/setup-task-master.sh --init-only
```

### Complete Removal
```bash
./scripts/optional-installs/task-master/setup-task-master.sh --rollback
```

## Support

For issues or questions:
1. Check the logs in `~/.local/share/arch_dotfiles/logs/`
2. Run status command: `./scripts/optional-installs/task-master/setup-task-master.sh --status`
3. Review this documentation
4. Check Task Master documentation: `task-master --help`
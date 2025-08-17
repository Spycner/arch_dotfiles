# Optional Installations

This directory contains installation scripts for optional tools and software that complement the base Arch Linux setup.

## Available Optional Installs

### Task Master AI (`task-master/`)

AI-powered task management and development workflow automation tool that integrates with Claude Code.

**Quick Setup:**
```bash
./scripts/optional-installs/task-master/setup-task-master.sh
```

**Features:**
- Automated installation and initialization
- Claude Code integration
- Idempotent operations with rollback support
- Comprehensive logging and state tracking

See [`task-master/README.md`](task-master/README.md) for detailed documentation.

## Structure

```
optional-installs/
├── README.md                           # This file
└── task-master/                        # Task Master AI installation
    ├── README.md                       # Detailed Task Master documentation
    ├── setup-task-master.sh           # Main setup script (recommended)
    ├── install-task-master.py         # Installation script
    └── init-task-master.py            # Initialization script
```

## Usage Pattern

Each optional installation follows a consistent pattern:

1. **Combined setup script** (`.sh`) - Recommended for most users
2. **Individual component scripts** (`.py`) - For advanced users
3. **Comprehensive documentation** (`README.md`)
4. **Idempotent operations** - Safe to run multiple times
5. **Rollback capability** - Can undo installations

## Adding New Optional Installs

When adding new optional installation scripts:

1. Create a new subdirectory: `scripts/optional-installs/[tool-name]/`
2. Include setup script, individual components, and documentation
3. Follow the established patterns for idempotency and rollback
4. Update this README to list the new option

Each tool should be self-contained within its directory and not depend on other optional installations.
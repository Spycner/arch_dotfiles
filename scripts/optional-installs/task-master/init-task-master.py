# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "rich",
#     "typer",
# ]
# ///

"""
Initialize task-master-ai with predefined configuration.

This script provides automated initialization of Task Master AI with specific
configuration settings, avoiding the need for interactive setup. It creates
the necessary configuration files and directory structure with idempotent
and rollback capabilities.

Configuration Details:
    - Models: Claude Code / Sonnet (3 model configurations)
    - Provider: Claude Code only
    - Language: English
    - Interactive prompts: y, n, y, y (as per documented setup)

Usage Examples:
    # Initialize Task Master with default configuration
    uv run scripts/install/init-task-master.py init
    
    # Check current Task Master status
    uv run scripts/install/init-task-master.py status
    
    # Preview initialization (dry run)
    uv run scripts/install/init-task-master.py init --dry-run
    
    # Force reinitialization (overwrites existing config)
    uv run scripts/install/init-task-master.py init --force
    
    # Rollback initialization (restore backup)
    uv run scripts/install/init-task-master.py rollback
    
    # Preview rollback
    uv run scripts/install/init-task-master.py rollback --dry-run

Prerequisites:
    - task-master-ai must be installed (use install-task-master.py)
    - Node.js and npm must be available

Logs:
    All operations are logged to ~/.local/share/arch_dotfiles/logs/
    Backups are stored in ~/.local/share/arch_dotfiles/backups/
"""

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

app = typer.Typer(
    help="Task Master AI Initialization Script - Automate task-master initialization",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()

# Configuration
SCRIPT_NAME = "init-task-master"
SCRIPT_VERSION = "1.0.0"

# Paths
HOME = Path.home()
CWD = Path.cwd()
TASKMASTER_DIR = CWD / ".taskmaster"
DATA_DIR = HOME / ".local" / "share" / "arch_dotfiles"
LOG_DIR = DATA_DIR / "logs"
BACKUP_DIR = DATA_DIR / "backups" / "task-master"
STATE_FILE = LOG_DIR / f"{SCRIPT_NAME}.state"

# Ensure directories exist
LOG_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# Create log file for this run
LOG_FILE = LOG_DIR / f"{SCRIPT_NAME}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Default Task Master configuration based on user's interactive responses
DEFAULT_CONFIG = {
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
        "debug": False,
        "defaultNumTasks": 10,
        "defaultSubtasks": 5,
        "defaultPriority": "medium",
        "projectName": "Taskmaster",
        "ollamaBaseURL": "http://localhost:11434/api",
        "bedrockBaseURL": "https://bedrock.us-east-1.amazonaws.com",
        "responseLanguage": "English",
        "defaultTag": "master",
        "azureOpenaiBaseURL": "https://your-endpoint.openai.azure.com/"
    },
    "claudeCode": {}
}

# Default state.json for Task Master
DEFAULT_STATE = {
    "version": "2.0.0",
    "initialized": True,
    "migrations": []
}

# Default CLAUDE.md content for Task Master
CLAUDE_MD_CONTENT = """# Task Master AI Instructions

This file contains specific instructions for Claude when working with Task Master AI in this project.

## Overview
Task Master AI is configured to work with Claude Code as the AI provider for all models (main, research, and fallback).

## Configuration
- **Models**: All models use Claude Code / Sonnet
- **Language**: English
- **Provider**: Claude Code exclusively

## Task Management
When using Task Master:
1. Tasks are managed in the `tasks/` directory
2. Reports are generated in the `reports/` directory
3. Configuration is stored in `config.json`
4. State tracking is maintained in `state.json`

## Development Workflow
Follow the Task Master development workflow for:
- Task creation and management
- Research documentation
- Code generation
- Report generation

## Integration with Claude Code
This configuration is optimized for use with Claude Code CLI, ensuring consistent AI-powered development assistance.
"""


class Logger:
    """Simple logger that writes to both file and console."""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
    
    def _write(self, level: str, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        with open(self.log_file, "a") as f:
            f.write(log_entry)
    
    def info(self, message: str, show=True):
        self._write("INFO", message)
        if show:
            console.print(f"[blue][INFO][/blue] {message}")
    
    def success(self, message: str):
        self._write("SUCCESS", message)
        console.print(f"[green][SUCCESS][/green] {message}")
    
    def warning(self, message: str):
        self._write("WARNING", message)
        console.print(f"[yellow][WARNING][/yellow] {message}")
    
    def error(self, message: str):
        self._write("ERROR", message)
        console.print(f"[red][ERROR][/red] {message}", err=True)


logger = Logger(LOG_FILE)


def run_command(cmd: list[str], capture_output=True, check=True) -> Optional[subprocess.CompletedProcess]:
    """Run a command and return the result."""
    logger.info(f"Running command: {' '.join(cmd)}", show=False)
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        if e.stderr:
            logger.error(f"Error output: {e.stderr}")
        if check:
            raise
        return None


def check_prerequisites() -> bool:
    """Check if task-master is installed."""
    logger.info("Checking prerequisites...")
    
    # Check if task-master is installed
    result = run_command(["which", "task-master"], check=False)
    if not result or result.returncode != 0:
        logger.error("task-master is not installed. Please run install-task-master.py first.")
        return False
    
    logger.success("Prerequisites check passed")
    logger.info(f"task-master location: {result.stdout.strip()}")
    return True


def is_initialized() -> bool:
    """Check if Task Master is already initialized."""
    return TASKMASTER_DIR.exists() and (TASKMASTER_DIR / "config.json").exists()


def backup_existing_config() -> Optional[Path]:
    """Backup existing Task Master configuration."""
    if not TASKMASTER_DIR.exists():
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"taskmaster_backup_{timestamp}"
    
    logger.info(f"Creating backup at {backup_path}")
    shutil.copytree(TASKMASTER_DIR, backup_path)
    logger.success(f"Backup created: {backup_path}")
    
    return backup_path


def record_state(action: str, backup_path: Optional[Path] = None):
    """Record action in state file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_str = str(backup_path) if backup_path else "none"
    entry = f"{timestamp}|{action}|{CWD}|{backup_str}\n"
    
    with open(STATE_FILE, "a") as f:
        f.write(entry)


def create_taskmaster_structure():
    """Create the Task Master directory structure."""
    directories = [
        TASKMASTER_DIR / "tasks",
        TASKMASTER_DIR / "reports",
        TASKMASTER_DIR / "docs",
        TASKMASTER_DIR / "templates"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory}")


def initialize_taskmaster(force: bool = False, dry_run: bool = False) -> bool:
    """Initialize Task Master with predefined configuration."""
    logger.info("Initializing Task Master...")
    
    # Check if already initialized
    if is_initialized() and not force:
        logger.warning("Task Master is already initialized in this directory")
        logger.info("Use --force to reinitialize")
        return True
    
    if dry_run:
        logger.info("[DRY-RUN] Would initialize Task Master with the following configuration:")
        console.print(json.dumps(DEFAULT_CONFIG, indent=2))
        logger.info(f"[DRY-RUN] Would create directory structure at: {TASKMASTER_DIR}")
        return True
    
    # Backup existing configuration if present
    backup_path = None
    if is_initialized():
        backup_path = backup_existing_config()
    
    # Create directory structure
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating Task Master structure...", total=None)
        
        try:
            # Create directories
            create_taskmaster_structure()
            
            # Write config.json
            config_file = TASKMASTER_DIR / "config.json"
            with open(config_file, "w") as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)
            logger.success(f"Created config.json: {config_file}")
            
            # Write state.json
            state_file = TASKMASTER_DIR / "state.json"
            with open(state_file, "w") as f:
                json.dump(DEFAULT_STATE, f, indent=2)
            logger.success(f"Created state.json: {state_file}")
            
            # Write CLAUDE.md
            claude_file = TASKMASTER_DIR / "CLAUDE.md"
            with open(claude_file, "w") as f:
                f.write(CLAUDE_MD_CONTENT)
            logger.success(f"Created CLAUDE.md: {claude_file}")
            
            progress.update(task, completed=True)
            
            # Record the state
            record_state("initialized", backup_path)
            
            logger.success("Task Master initialized successfully!")
            logger.info("Configuration:")
            logger.info("  - Provider: Claude Code")
            logger.info("  - Models: Sonnet (main, research, fallback)")
            logger.info("  - Language: English")
            logger.info(f"  - Location: {TASKMASTER_DIR}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Task Master: {e}")
            # Attempt to restore backup if initialization failed
            if backup_path and backup_path.exists():
                logger.info("Attempting to restore from backup...")
                if TASKMASTER_DIR.exists():
                    shutil.rmtree(TASKMASTER_DIR)
                shutil.copytree(backup_path, TASKMASTER_DIR)
                logger.success("Restored from backup")
            return False


def rollback_initialization(dry_run: bool = False) -> bool:
    """Rollback Task Master initialization."""
    logger.info("Rolling back Task Master initialization...")
    
    if not is_initialized():
        logger.warning("Task Master is not initialized in this directory")
        return True
    
    # Find the most recent backup
    if BACKUP_DIR.exists():
        backups = sorted(BACKUP_DIR.glob("taskmaster_backup_*"))
        if backups:
            latest_backup = backups[-1]
            logger.info(f"Found backup: {latest_backup}")
            
            if dry_run:
                logger.info(f"[DRY-RUN] Would restore from: {latest_backup}")
                logger.info(f"[DRY-RUN] Would remove: {TASKMASTER_DIR}")
                return True
            
            # Remove current configuration
            if TASKMASTER_DIR.exists():
                shutil.rmtree(TASKMASTER_DIR)
                logger.success(f"Removed current configuration: {TASKMASTER_DIR}")
            
            # Restore from backup
            shutil.copytree(latest_backup, TASKMASTER_DIR)
            logger.success(f"Restored from backup: {latest_backup}")
            
            record_state("rolled_back", latest_backup)
            return True
    
    # No backup found, just remove the directory
    if dry_run:
        logger.info(f"[DRY-RUN] Would remove: {TASKMASTER_DIR}")
        return True
    
    if TASKMASTER_DIR.exists():
        # Create a backup before removing
        backup_path = backup_existing_config()
        shutil.rmtree(TASKMASTER_DIR)
        logger.success(f"Removed Task Master configuration: {TASKMASTER_DIR}")
        record_state("removed", backup_path)
    
    return True


@app.command()
def init(
    force: bool = typer.Option(False, "--force", "-f", help="Force reinitialization even if already initialized"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without applying them"),
):
    """Initialize task-master with predefined configuration."""
    console.print(Panel.fit(
        f"[bold green]Task Master AI Initialization[/bold green]\n"
        f"Version: {SCRIPT_VERSION}",
        border_style="green"
    ))
    
    logger.info(f"Starting {SCRIPT_NAME} script (v{SCRIPT_VERSION})")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info(f"Working directory: {CWD}")
    
    if not check_prerequisites():
        raise typer.Exit(1)
    
    if initialize_taskmaster(force=force, dry_run=dry_run):
        logger.info("Script completed successfully")
    else:
        raise typer.Exit(1)


@app.command()
def rollback(
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without applying them"),
):
    """Rollback Task Master initialization."""
    console.print(Panel.fit(
        f"[bold yellow]Task Master AI Rollback[/bold yellow]\n"
        f"Version: {SCRIPT_VERSION}",
        border_style="yellow"
    ))
    
    logger.info(f"Starting {SCRIPT_NAME} rollback (v{SCRIPT_VERSION})")
    logger.info(f"Log file: {LOG_FILE}")
    
    if rollback_initialization(dry_run=dry_run):
        logger.info("Rollback completed successfully")
    else:
        raise typer.Exit(1)


@app.command()
def status():
    """Check Task Master initialization status."""
    console.print(Panel.fit(
        f"[bold blue]Task Master AI Status[/bold blue]",
        border_style="blue"
    ))
    
    # Check if task-master is installed
    tm_result = run_command(["which", "task-master"], check=False)
    if tm_result and tm_result.returncode == 0:
        console.print(f"✅ task-master is installed: {tm_result.stdout.strip()}")
    else:
        console.print("❌ task-master is not installed")
    
    # Check initialization status
    if is_initialized():
        console.print(f"✅ Task Master is initialized in: {TASKMASTER_DIR}")
        
        # Show configuration details
        config_file = TASKMASTER_DIR / "config.json"
        if config_file.exists():
            with open(config_file) as f:
                config = json.load(f)
            
            # Create a table for configuration
            table = Table(title="Current Configuration", border_style="blue")
            table.add_column("Model", style="cyan")
            table.add_column("Provider", style="green")
            table.add_column("Model ID", style="yellow")
            table.add_column("Max Tokens", style="magenta")
            
            for model_name, model_config in config.get("models", {}).items():
                table.add_row(
                    model_name,
                    model_config.get("provider", "N/A"),
                    model_config.get("modelId", "N/A"),
                    str(model_config.get("maxTokens", "N/A"))
                )
            
            console.print(table)
            
            # Show global settings
            global_config = config.get("global", {})
            console.print("\n[bold]Global Settings:[/bold]")
            console.print(f"  Language: {global_config.get('responseLanguage', 'N/A')}")
            console.print(f"  Project: {global_config.get('projectName', 'N/A')}")
            console.print(f"  Log Level: {global_config.get('logLevel', 'N/A')}")
    else:
        console.print(f"❌ Task Master is not initialized in: {CWD}")
    
    # Show recent history from state file
    if STATE_FILE.exists():
        console.print("\n[bold]Recent History:[/bold]")
        with open(STATE_FILE) as f:
            lines = f.readlines()
            for line in lines[-5:]:  # Show last 5 entries
                parts = line.strip().split("|")
                if len(parts) == 4:
                    timestamp, action, location, backup = parts
                    dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                    
                    if action == "initialized":
                        console.print(f"  [green]✓[/green] {formatted_time}: Initialized at {location}")
                    elif action == "rolled_back":
                        console.print(f"  [yellow]↺[/yellow] {formatted_time}: Rolled back at {location}")
                    elif action == "removed":
                        console.print(f"  [red]✗[/red] {formatted_time}: Removed from {location}")


if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
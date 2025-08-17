# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "rich",
#     "typer",
# ]
# ///

"""
Install task-master-ai globally via npm.

This script provides idempotent installation and rollback capabilities for the
task-master-ai npm package. It ensures safe installation with proper logging,
state tracking, and the ability to undo changes.

Requirements:
    - Node.js and npm must be installed (use nvm to install: nvm install node)
    - User must have permissions for global npm installations

Usage Examples:
    # Install task-master-ai
    uv run scripts/install/install-task-master.py install
    
    # Check installation status
    uv run scripts/install/install-task-master.py status
    
    # Preview what would be installed (dry run)
    uv run scripts/install/install-task-master.py install --dry-run
    
    # Force reinstallation
    uv run scripts/install/install-task-master.py install --force
    
    # Uninstall (rollback)
    uv run scripts/install/install-task-master.py rollback
    
    # Preview uninstallation
    uv run scripts/install/install-task-master.py rollback --dry-run

Logs:
    All operations are logged to ~/.local/share/arch_dotfiles/logs/
    State tracking is maintained for rollback capabilities.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(
    help="Task Master AI Installation Script - Install task-master-ai globally using npm",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()

# Configuration
PACKAGE_NAME = "task-master-ai"
SCRIPT_NAME = "install-task-master"
SCRIPT_VERSION = "2.0.0"

# Paths
HOME = Path.home()
DATA_DIR = HOME / ".local" / "share" / "arch_dotfiles"
LOG_DIR = DATA_DIR / "logs"
BACKUP_DIR = DATA_DIR / "backups"
STATE_FILE = LOG_DIR / f"{SCRIPT_NAME}.state"

# Ensure directories exist
LOG_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# Create log file for this run
LOG_FILE = LOG_DIR / f"{SCRIPT_NAME}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"


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
    """Check if Node.js and npm are installed."""
    logger.info("Checking prerequisites...")
    
    # Check Node.js
    node_result = run_command(["node", "--version"], check=False)
    if not node_result or node_result.returncode != 0:
        logger.error("Node.js is not installed. Please install Node.js first.")
        logger.info("You can install Node.js using: nvm install node")
        return False
    
    # Check npm
    npm_result = run_command(["npm", "--version"], check=False)
    if not npm_result or npm_result.returncode != 0:
        logger.error("npm is not installed. Please install npm first.")
        return False
    
    logger.success("Prerequisites check passed")
    logger.info(f"Node.js version: {node_result.stdout.strip()}")
    logger.info(f"npm version: {npm_result.stdout.strip()}")
    return True


def is_package_installed() -> bool:
    """Check if the package is already installed globally."""
    result = run_command(
        ["npm", "list", "-g", PACKAGE_NAME, "--depth=0", "--json"],
        check=False
    )
    
    if not result or result.returncode != 0:
        return False
    
    try:
        data = json.loads(result.stdout)
        return PACKAGE_NAME in data.get("dependencies", {})
    except json.JSONDecodeError:
        return False


def get_installed_version() -> Optional[str]:
    """Get the installed version of the package."""
    result = run_command(
        ["npm", "list", "-g", PACKAGE_NAME, "--depth=0", "--json"],
        check=False
    )
    
    if not result or result.returncode != 0:
        return None
    
    try:
        data = json.loads(result.stdout)
        package_info = data.get("dependencies", {}).get(PACKAGE_NAME, {})
        return package_info.get("version")
    except (json.JSONDecodeError, KeyError):
        return None


def record_state(action: str, version: Optional[str] = None):
    """Record action in state file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    version_str = version or "unknown"
    entry = f"{timestamp}|{action}|{PACKAGE_NAME}|{version_str}\n"
    
    with open(STATE_FILE, "a") as f:
        f.write(entry)


def install_package(force: bool = False, dry_run: bool = False) -> bool:
    """Install the package globally."""
    logger.info(f"Installing {PACKAGE_NAME} globally...")
    
    if is_package_installed() and not force:
        version = get_installed_version()
        logger.warning(f"{PACKAGE_NAME} is already installed (version: {version})")
        logger.info("Use --force to reinstall")
        return True
    
    if dry_run:
        logger.info(f"[DRY-RUN] Would install {PACKAGE_NAME} globally")
        logger.info(f"[DRY-RUN] Command: npm install -g {PACKAGE_NAME}")
        return True
    
    # Perform installation
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Installing {PACKAGE_NAME}...", total=None)
        
        result = run_command(["npm", "install", "-g", PACKAGE_NAME])
        
        if result and result.returncode == 0:
            progress.update(task, completed=True)
            logger.success(f"{PACKAGE_NAME} installed successfully")
            
            version = get_installed_version()
            record_state("installed", version)
            
            # Verify installation
            which_result = run_command(["which", "task-master"], check=False)
            if which_result and which_result.returncode == 0:
                logger.success("task-master command is available")
                logger.info(f"Installation location: {which_result.stdout.strip()}")
            else:
                logger.warning("Installation completed but task-master command not found in PATH")
            
            return True
        else:
            logger.error(f"Failed to install {PACKAGE_NAME}")
            return False


def rollback_package(dry_run: bool = False) -> bool:
    """Uninstall the package."""
    logger.info(f"Rolling back: Uninstalling {PACKAGE_NAME}...")
    
    if not is_package_installed():
        logger.warning(f"{PACKAGE_NAME} is not installed")
        return True
    
    version = get_installed_version()
    
    if dry_run:
        logger.info(f"[DRY-RUN] Would uninstall {PACKAGE_NAME} (version: {version})")
        logger.info(f"[DRY-RUN] Command: npm uninstall -g {PACKAGE_NAME}")
        return True
    
    # Perform uninstallation
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Uninstalling {PACKAGE_NAME}...", total=None)
        
        result = run_command(["npm", "uninstall", "-g", PACKAGE_NAME])
        
        if result and result.returncode == 0:
            progress.update(task, completed=True)
            logger.success(f"{PACKAGE_NAME} uninstalled successfully")
            record_state("uninstalled", version)
            return True
        else:
            logger.error(f"Failed to uninstall {PACKAGE_NAME}")
            return False


@app.command()
def install(
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstallation even if already installed"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without applying them"),
):
    """Install task-master-ai globally."""
    console.print(Panel.fit(
        f"[bold green]Task Master AI Installation Script[/bold green]\n"
        f"Version: {SCRIPT_VERSION}",
        border_style="green"
    ))
    
    logger.info(f"Starting {SCRIPT_NAME} script (v{SCRIPT_VERSION})")
    logger.info(f"Log file: {LOG_FILE}")
    
    if not check_prerequisites():
        raise typer.Exit(1)
    
    if install_package(force=force, dry_run=dry_run):
        logger.info("Script completed successfully")
    else:
        raise typer.Exit(1)


@app.command()
def rollback(
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without applying them"),
):
    """Uninstall task-master-ai."""
    console.print(Panel.fit(
        f"[bold yellow]Task Master AI Rollback[/bold yellow]\n"
        f"Version: {SCRIPT_VERSION}",
        border_style="yellow"
    ))
    
    logger.info(f"Starting {SCRIPT_NAME} rollback (v{SCRIPT_VERSION})")
    logger.info(f"Log file: {LOG_FILE}")
    
    if not check_prerequisites():
        raise typer.Exit(1)
    
    if rollback_package(dry_run=dry_run):
        logger.info("Rollback completed successfully")
    else:
        raise typer.Exit(1)


@app.command()
def status():
    """Check installation status of task-master-ai."""
    console.print(Panel.fit(
        f"[bold blue]Task Master AI Status[/bold blue]",
        border_style="blue"
    ))
    
    if is_package_installed():
        version = get_installed_version()
        console.print(f"✅ {PACKAGE_NAME} is installed (version: {version})")
        
        which_result = run_command(["which", "task-master"], check=False)
        if which_result and which_result.returncode == 0:
            console.print(f"📍 Location: {which_result.stdout.strip()}")
    else:
        console.print(f"❌ {PACKAGE_NAME} is not installed")
    
    # Show recent history from state file
    if STATE_FILE.exists():
        console.print("\n[bold]Recent History:[/bold]")
        with open(STATE_FILE) as f:
            lines = f.readlines()
            for line in lines[-5:]:  # Show last 5 entries
                parts = line.strip().split("|")
                if len(parts) == 4:
                    timestamp, action, package, version = parts
                    dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                    
                    if action == "installed":
                        console.print(f"  [green]↑[/green] {formatted_time}: Installed v{version}")
                    else:
                        console.print(f"  [red]↓[/red] {formatted_time}: Uninstalled v{version}")


if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Installation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
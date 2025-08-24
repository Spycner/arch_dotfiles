#!/usr/bin/env python3
"""
Sets up btop configuration and themes using symlinks.

This script creates symlinks from the repository's btop configuration 
to ~/.config/btop/, enabling a centralized management approach for 
system monitoring tool configuration.

Features:
- Creates symlinks for btop.conf and themes directory
- Backup existing configuration with timestamps
- Rollback support to restore previous configurations
- Dry-run mode to preview changes without applying them
- Idempotent execution - safe to run multiple times

Usage:
    uv run scripts/setup-btop.py [options]
    
Examples:
    uv run scripts/setup-btop.py                    # Setup btop config
    uv run scripts/setup-btop.py --dry-run          # Preview changes
    uv run scripts/setup-btop.py --rollback         # Restore previous config
    uv run scripts/setup-btop.py --status           # Check current status
"""
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "rich>=10.0.0",
# ]
# ///

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
except ImportError:
    print("Error: rich library not available. Please install with: uv add rich")
    sys.exit(1)

console = Console()

class BtopSetup:
    """Manages btop configuration setup with symlinks, backup, and rollback support."""
    
    def __init__(self, repo_root: Path, dry_run: bool = False):
        self.repo_root = repo_root
        self.dry_run = dry_run
        
        # Configuration paths
        self.config_source = repo_root / "config" / "btop"
        self.config_target = Path.home() / ".config" / "btop"
        
        # State management
        self.backup_dir = Path.home() / ".local" / "share" / "arch_dotfiles" / "backups" / "btop"
        self.state_file = Path.home() / ".local" / "share" / "arch_dotfiles" / "btop_setup_state.json"
        
        # Ensure directories exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Color scheme for output
        self.colors = {
            'success': 'green',
            'error': 'red',
            'warning': 'yellow',
            'info': 'blue',
            'dim': 'dim'
        }

    def log(self, message: str, color: str = 'info', prefix: str = '•') -> None:
        """Log a formatted message to console."""
        text = Text(f"{prefix} {message}")
        text.stylize(self.colors.get(color, 'white'))
        console.print(text)

    def validate_source_config(self) -> bool:
        """Validate that source btop configuration exists and is valid."""
        if not self.config_source.exists():
            self.log(f"Source btop config not found: {self.config_source}", 'error', '✗')
            return False
            
        required_files = [
            self.config_source / "btop.conf",
            self.config_source / "themes"
        ]
        
        missing_files = [f for f in required_files if not f.exists()]
        if missing_files:
            self.log("Missing required btop configuration files:", 'error', '✗')
            for f in missing_files:
                self.log(f"  - {f.relative_to(self.config_source)}", 'error', '    ')
            return False
            
        # Check that themes directory contains theme files
        themes_dir = self.config_source / "themes"
        if themes_dir.is_dir() and not list(themes_dir.glob("*.theme")):
            self.log("Themes directory exists but contains no .theme files", 'warning', '⚠')
            
        return True

    def get_current_state(self) -> Dict:
        """Get current setup state from state file."""
        if not self.state_file.exists():
            return {}
            
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            self.log(f"Warning: Could not read state file {self.state_file}", 'warning', '⚠')
            return {}

    def save_state(self, state: Dict) -> None:
        """Save current setup state to state file."""
        if self.dry_run:
            self.log(f"Would save state to {self.state_file}", 'dim', '→')
            return
            
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except OSError as e:
            self.log(f"Error saving state file: {e}", 'error', '✗')

    def backup_existing_config(self) -> Tuple[bool, Dict[str, str]]:
        """Create timestamped backup of existing btop configuration."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_info = {'timestamp': timestamp, 'backups': {}}
        
        if not self.config_target.exists():
            self.log("No existing btop configuration to backup", 'info')
            return True, backup_info
            
        backup_path = self.backup_dir / f"backup_{timestamp}"
        
        try:
            if self.dry_run:
                self.log(f"Would backup {self.config_target} → {backup_path}", 'dim', '→')
            else:
                shutil.copytree(self.config_target, backup_path, dirs_exist_ok=True)
                backup_info['backups']['config'] = str(backup_path)
                self.log(f"Backed up existing config → {backup_path}", 'success', '✓')
                
            return True, backup_info
            
        except OSError as e:
            self.log(f"Failed to create backup: {e}", 'error', '✗')
            return False, {}

    def create_symlinks(self) -> bool:
        """Create symlinks for btop configuration."""
        symlinks_created = []
        
        # Remove existing target if it exists
        if self.config_target.exists():
            if self.dry_run:
                self.log(f"Would remove existing {self.config_target}", 'dim', '→')
            else:
                if self.config_target.is_symlink():
                    self.config_target.unlink()
                else:
                    shutil.rmtree(self.config_target)
                    
        try:
            if self.dry_run:
                self.log(f"Would create symlink {self.config_target} → {self.config_source}", 'dim', '→')
            else:
                # Create parent directory if needed
                self.config_target.parent.mkdir(parents=True, exist_ok=True)
                
                # Create the symlink
                self.config_target.symlink_to(self.config_source)
                symlinks_created.append(str(self.config_target))
                self.log(f"Created symlink {self.config_target} → {self.config_source}", 'success', '✓')
                
            return True
            
        except OSError as e:
            self.log(f"Failed to create symlink: {e}", 'error', '✗')
            # Clean up any partial symlinks
            for symlink in symlinks_created:
                try:
                    Path(symlink).unlink(missing_ok=True)
                except OSError:
                    pass
            return False

    def verify_installation(self) -> bool:
        """Verify that btop configuration is properly linked."""
        if not self.config_target.exists():
            self.log("btop config directory does not exist", 'error', '✗')
            return False
            
        if not self.config_target.is_symlink():
            self.log("btop config is not a symlink (may be a regular directory)", 'warning', '⚠')
            return False
            
        if self.config_target.readlink() != self.config_source:
            self.log(f"btop config symlink points to wrong location: {self.config_target.readlink()}", 'error', '✗')
            return False
            
        # Check that key files are accessible through the symlink
        key_files = ["btop.conf", "themes"]
        for file_name in key_files:
            file_path = self.config_target / file_name
            if not file_path.exists():
                self.log(f"Key file not accessible: {file_name}", 'error', '✗')
                return False
                
        self.log("btop configuration properly linked and verified", 'success', '✓')
        return True

    def setup(self) -> bool:
        """Main setup process for btop configuration."""
        console.print(Panel.fit(
            "[bold blue]btop Configuration Setup[/bold blue]\n"
            "Setting up btop system monitor configuration with symlinks",
            border_style="blue"
        ))
        
        # Validate source configuration
        if not self.validate_source_config():
            return False
            
        # Check if already set up correctly
        if self.verify_installation():
            self.log("btop configuration already properly set up", 'success', '✓')
            if not self.dry_run:
                return True
                
        # Create backup
        backup_success, backup_info = self.backup_existing_config()
        if not backup_success:
            return False
            
        # Create symlinks
        if not self.create_symlinks():
            return False
            
        # Save state for potential rollback
        state = {
            'setup_time': datetime.now().isoformat(),
            'repo_root': str(self.repo_root),
            'backup_info': backup_info,
            'version': '1.0'
        }
        self.save_state(state)
        
        # Verify installation
        if not self.dry_run and not self.verify_installation():
            self.log("Setup completed but verification failed", 'warning', '⚠')
            return False
            
        self.log("btop configuration setup completed successfully!", 'success', '🎉')
        return True

    def rollback(self) -> bool:
        """Rollback btop configuration to previous state."""
        console.print(Panel.fit(
            "[bold yellow]btop Configuration Rollback[/bold yellow]\n"
            "Restoring previous btop configuration from backup",
            border_style="yellow"
        ))
        
        state = self.get_current_state()
        if not state:
            self.log("No setup state found - nothing to rollback", 'error', '✗')
            return False
            
        backup_info = state.get('backup_info', {})
        if not backup_info.get('backups'):
            self.log("No backup information found in state", 'error', '✗')
            return False
            
        # Remove current symlink
        if self.config_target.exists():
            if self.dry_run:
                self.log(f"Would remove current config: {self.config_target}", 'dim', '→')
            else:
                if self.config_target.is_symlink():
                    self.config_target.unlink()
                else:
                    shutil.rmtree(self.config_target)
                self.log(f"Removed current config: {self.config_target}", 'info', '→')
        
        # Restore from backup
        backup_path = Path(backup_info['backups']['config'])
        if not backup_path.exists():
            self.log(f"Backup not found: {backup_path}", 'error', '✗')
            return False
            
        try:
            if self.dry_run:
                self.log(f"Would restore backup: {backup_path} → {self.config_target}", 'dim', '→')
            else:
                shutil.copytree(backup_path, self.config_target, dirs_exist_ok=True)
                self.log(f"Restored backup: {backup_path} → {self.config_target}", 'success', '✓')
                
                # Remove state file
                self.state_file.unlink(missing_ok=True)
                self.log("Removed setup state file", 'info', '→')
                
        except OSError as e:
            self.log(f"Failed to restore backup: {e}", 'error', '✗')
            return False
            
        self.log("btop configuration rollback completed successfully!", 'success', '🎉')
        return True

    def status(self) -> None:
        """Display current btop configuration status."""
        console.print(Panel.fit(
            "[bold blue]btop Configuration Status[/bold blue]",
            border_style="blue"
        ))
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan", no_wrap=True)
        table.add_column("Status", style="white")
        table.add_column("Details", style="dim")
        
        # Check source configuration
        source_status = "✓ Found" if self.config_source.exists() else "✗ Missing"
        source_details = str(self.config_source)
        table.add_row("Source Config", source_status, source_details)
        
        # Check target configuration
        if self.config_target.exists():
            if self.config_target.is_symlink():
                target_status = "✓ Symlinked"
                target_details = f"→ {self.config_target.readlink()}"
            else:
                target_status = "⚠ Directory"
                target_details = "Regular directory (not symlinked)"
        else:
            target_status = "✗ Missing"
            target_details = "Not configured"
        table.add_row("Target Config", target_status, target_details)
        
        # Check setup state
        state = self.get_current_state()
        if state:
            state_status = "✓ Tracked"
            setup_time = state.get('setup_time', 'Unknown')
            state_details = f"Setup: {setup_time[:19]}"  # Trim microseconds
        else:
            state_status = "✗ Not tracked"
            state_details = "No setup state file"
        table.add_row("Setup State", state_status, state_details)
        
        # Check theme files
        if self.config_target.exists():
            themes_dir = self.config_target / "themes"
            if themes_dir.exists() and themes_dir.is_dir():
                theme_files = list(themes_dir.glob("*.theme"))
                theme_status = f"✓ {len(theme_files)} themes"
                theme_details = ", ".join([t.stem for t in theme_files[:3]])
                if len(theme_files) > 3:
                    theme_details += f" (+{len(theme_files)-3} more)"
            else:
                theme_status = "✗ No themes"
                theme_details = "Themes directory not accessible"
        else:
            theme_status = "✗ No themes"
            theme_details = "Config not available"
        table.add_row("Themes", theme_status, theme_details)
        
        console.print(table)

def main():
    parser = argparse.ArgumentParser(
        description="Setup btop configuration with symlinks and backup support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run scripts/setup-btop.py                    # Setup btop config
  uv run scripts/setup-btop.py --dry-run          # Preview changes  
  uv run scripts/setup-btop.py --rollback         # Restore previous config
  uv run scripts/setup-btop.py --status           # Check current status
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without making them'
    )
    
    parser.add_argument(
        '--rollback',
        action='store_true', 
        help='Rollback to previous configuration'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current configuration status'
    )
    
    args = parser.parse_args()
    
    # Find repository root
    repo_root = Path(__file__).parent.parent
    if not (repo_root / "config" / "btop").exists():
        console.print("[red]Error: Could not find btop config directory in repository[/red]")
        sys.exit(1)
        
    setup = BtopSetup(repo_root, dry_run=args.dry_run)
    
    try:
        if args.status:
            setup.status()
        elif args.rollback:
            success = setup.rollback()
            sys.exit(0 if success else 1)
        else:
            success = setup.setup()
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
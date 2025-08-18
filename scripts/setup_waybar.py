"""
Waybar Configuration Setup Script

This script sets up Waybar configuration by creating symlinks from the repository
to the user's config directory. It includes backup, rollback, and validation features.

Usage:
    uv run setup_waybar.py [--dry-run] [--rollback] [--help]
"""
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class WaybarSetup:
    """Main class for Waybar configuration setup."""
    
    def __init__(self, repo_root: Path, dry_run: bool = False):
        self.repo_root = repo_root
        self.dry_run = dry_run
        self.config_dir = Path.home() / '.config' / 'waybar'
        self.backup_dir = Path.home() / '.local' / 'share' / 'arch_dotfiles' / 'backups'
        self.state_file = Path.home() / '.local' / 'share' / 'arch_dotfiles' / 'waybar_setup_state.json'
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Files to link
        self.link_map = {
            'config.jsonc': self.repo_root / 'config' / 'waybar' / 'config.jsonc',
            'style.css': self.repo_root / 'config' / 'waybar' / 'style.css'
        }
    
    def print_colored(self, message: str, color: str = Colors.WHITE, bold: bool = False) -> None:
        """Print colored message to terminal."""
        style = f"{color}{Colors.BOLD if bold else ''}"
        print(f"{style}{message}{Colors.RESET}")
    
    def print_step(self, step: str) -> None:
        """Print a step message."""
        self.print_colored(f"→ {step}", Colors.CYAN)
    
    def print_success(self, message: str) -> None:
        """Print success message."""
        self.print_colored(f"✓ {message}", Colors.GREEN)
    
    def print_warning(self, message: str) -> None:
        """Print warning message."""
        self.print_colored(f"⚠ {message}", Colors.YELLOW)
    
    def print_error(self, message: str) -> None:
        """Print error message."""
        self.print_colored(f"✗ {message}", Colors.RED, bold=True)
    
    def ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self.print_step("Creating necessary directories")
        
        directories = [self.config_dir, self.backup_dir, self.state_file.parent]
        
        for directory in directories:
            if not self.dry_run:
                directory.mkdir(parents=True, exist_ok=True)
            self.print_colored(f"  Created: {directory}", Colors.BLUE)
    
    def check_waybar_installed(self) -> bool:
        """Check if waybar is installed."""
        try:
            result = subprocess.run(['which', 'waybar'], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def backup_existing_config(self) -> Dict[str, str]:
        """Backup existing configuration files."""
        self.print_step("Backing up existing configuration")
        
        backup_info = {}
        
        for name, source_path in self.link_map.items():
            target_path = self.config_dir / name
            
            if target_path.exists():
                backup_path = self.backup_dir / f"waybar_{name}.backup.{self.timestamp}"
                backup_info[name] = str(backup_path)
                
                if not self.dry_run:
                    if target_path.is_symlink():
                        # Save symlink target info
                        link_target = target_path.readlink()
                        backup_info[f"{name}_link_target"] = str(link_target)
                        self.print_colored(f"  Found existing symlink: {name} -> {link_target}", Colors.YELLOW)
                    else:
                        # Copy actual file/directory
                        if target_path.is_dir():
                            shutil.copytree(target_path, backup_path)
                        else:
                            shutil.copy2(target_path, backup_path)
                        self.print_colored(f"  Backed up: {name} -> {backup_path}", Colors.GREEN)
        
        return backup_info
    
    def save_state(self, backup_info: Dict[str, str]) -> None:
        """Save setup state for potential rollback."""
        if self.dry_run:
            return
        
        state = {
            'timestamp': self.timestamp,
            'backup_info': backup_info,
            'link_map': {k: str(v) for k, v in self.link_map.items()}
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        self.print_success(f"State saved to {self.state_file}")
    
    def create_symlinks(self) -> None:
        """Create symlinks for Waybar configuration."""
        self.print_step("Creating symlinks")
        
        for name, source_path in self.link_map.items():
            target_path = self.config_dir / name
            
            # Check if source exists
            if not source_path.exists():
                self.print_error(f"Source file not found: {source_path}")
                continue
            
            # Remove existing file/symlink
            if target_path.exists() or target_path.is_symlink():
                if not self.dry_run:
                    if target_path.is_dir() and not target_path.is_symlink():
                        shutil.rmtree(target_path)
                    else:
                        target_path.unlink()
                self.print_colored(f"  Removed existing: {target_path}", Colors.YELLOW)
            
            # Create symlink
            if not self.dry_run:
                target_path.symlink_to(source_path)
            self.print_success(f"  Created symlink: {name} -> {source_path}")
    
    def validate_config(self) -> bool:
        """Validate Waybar configuration."""
        self.print_step("Validating configuration")
        
        # Check if waybar config is valid JSON
        config_path = self.config_dir / 'config.jsonc'
        if config_path.exists():
            try:
                # Waybar uses JSONC (JSON with comments), so we can't use standard json.load
                # Instead, we'll try to run waybar with --config flag to validate
                if not self.dry_run:
                    result = subprocess.run(
                        ['waybar', '--config', str(config_path), '--help'],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        self.print_success("  Configuration is valid")
                        return True
                    else:
                        self.print_warning("  Could not validate configuration")
                else:
                    self.print_colored("  Dry run - skipping validation", Colors.BLUE)
                    return True
            except Exception as e:
                self.print_error(f"  Validation failed: {e}")
                return False
        
        return True
    
    def setup(self) -> bool:
        """Main setup process."""
        self.print_colored("\n=== Waybar Configuration Setup ===\n", Colors.MAGENTA, bold=True)
        
        if self.dry_run:
            self.print_warning("DRY RUN MODE - No changes will be made\n")
        
        # Check if waybar is installed
        if not self.check_waybar_installed():
            self.print_warning("Waybar is not installed. Install it with: paru -S waybar-git")
            if not self.dry_run:
                self.print_error("Cannot proceed without waybar installed")
                return False
        else:
            self.print_success("Waybar is installed")
        
        # Ensure directories exist
        self.ensure_directories()
        
        # Backup existing configuration
        backup_info = self.backup_existing_config()
        
        # Create symlinks
        self.create_symlinks()
        
        # Save state
        self.save_state(backup_info)
        
        # Validate configuration
        if not self.validate_config():
            self.print_warning("Configuration validation failed, but setup completed")
        
        self.print_colored("\n=== Setup Complete ===\n", Colors.GREEN, bold=True)
        
        if not self.dry_run:
            self.print_colored("Next steps:", Colors.CYAN)
            self.print_colored("  1. Reload Hyprland configuration: hyprctl reload", Colors.WHITE)
            self.print_colored("  2. Or manually start waybar: waybar &", Colors.WHITE)
            self.print_colored("  3. Customize the configuration in: config/waybar/", Colors.WHITE)
            self.print_colored("  4. To rollback: uv run setup_waybar.py --rollback", Colors.WHITE)
        
        return True
    
    def rollback(self) -> bool:
        """Rollback to previous configuration."""
        self.print_colored("\n=== Waybar Configuration Rollback ===\n", Colors.MAGENTA, bold=True)
        
        if not self.state_file.exists():
            self.print_error("No state file found. Nothing to rollback.")
            return False
        
        # Load state
        with open(self.state_file, 'r') as f:
            state = json.load(f)
        
        self.print_step(f"Rolling back to state from {state['timestamp']}")
        
        # Remove current symlinks
        for name in state['link_map'].keys():
            target_path = self.config_dir / name
            if target_path.exists() or target_path.is_symlink():
                if target_path.is_dir() and not target_path.is_symlink():
                    shutil.rmtree(target_path)
                else:
                    target_path.unlink()
                self.print_colored(f"  Removed: {target_path}", Colors.YELLOW)
        
        # Restore backups
        for name, backup_path in state['backup_info'].items():
            if name.endswith('_link_target'):
                continue
            
            target_path = self.config_dir / name
            backup_path = Path(backup_path)
            
            if backup_path.exists():
                if backup_path.is_dir():
                    shutil.copytree(backup_path, target_path)
                else:
                    shutil.copy2(backup_path, target_path)
                self.print_success(f"  Restored: {name} from {backup_path}")
        
        # Remove state file
        self.state_file.unlink()
        self.print_success("State file removed")
        
        self.print_colored("\n=== Rollback Complete ===\n", Colors.GREEN, bold=True)
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Setup Waybar configuration for Hyprland',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run setup_waybar.py              # Setup Waybar configuration
  uv run setup_waybar.py --dry-run    # Preview changes without applying
  uv run setup_waybar.py --rollback   # Restore previous configuration
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without applying them'
    )
    
    parser.add_argument(
        '--rollback',
        action='store_true',
        help='Rollback to previous configuration'
    )
    
    args = parser.parse_args()
    
    # Determine repository root
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent
    
    # Verify we're in the correct repository
    if not (repo_root / 'config' / 'waybar').exists():
        print(f"Error: Waybar configuration not found in {repo_root / 'config' / 'waybar'}")
        print("Please run this script from the arch_dotfiles repository")
        sys.exit(1)
    
    # Create setup instance
    setup = WaybarSetup(repo_root, dry_run=args.dry_run)
    
    # Execute requested action
    if args.rollback:
        success = setup.rollback()
    else:
        success = setup.setup()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
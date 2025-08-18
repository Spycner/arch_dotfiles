#!/usr/bin/env python3
"""
Set up Kitty terminal emulator configuration

This script sets up Kitty as the default terminal emulator with optimized
configuration for Arch Linux and Hyprland.

Usage:
    uv run scripts/setup-kitty.py
    uv run scripts/setup-kitty.py --dry-run
    uv run scripts/setup-kitty.py --rollback
"""
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class KittySetup:
    """Manage Kitty terminal configuration setup"""
    
    def __init__(self, repo_root: Path, dry_run: bool = False):
        self.repo_root = repo_root
        self.dry_run = dry_run
        self.config_source = repo_root / "config" / "kitty"
        self.config_target = Path.home() / ".config" / "kitty"
        
        # Setup backup and state directories
        self.backup_dir = Path.home() / ".local" / "share" / "arch_dotfiles" / "backups" / "kitty"
        self.state_file = Path.home() / ".local" / "share" / "arch_dotfiles" / "kitty_state.json"
        
        # ANSI color codes for output
        self.GREEN = "\033[92m"
        self.YELLOW = "\033[93m"
        self.RED = "\033[91m"
        self.BLUE = "\033[94m"
        self.RESET = "\033[0m"
        
    def print_status(self, status: str, message: str):
        """Print colored status messages"""
        color = {
            "success": self.GREEN,
            "warning": self.YELLOW,
            "error": self.RED,
            "info": self.BLUE
        }.get(status, self.RESET)
        
        symbol = {
            "success": "✓",
            "warning": "⚠",
            "error": "✗",
            "info": "→"
        }.get(status, "•")
        
        print(f"{color}{symbol} {message}{self.RESET}")
    
    def ensure_directories(self):
        """Create necessary directories"""
        if not self.dry_run:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
    
    def load_state(self) -> Dict:
        """Load the previous setup state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                self.print_status("warning", "Could not parse state file, starting fresh")
        return {}
    
    def save_state(self, state: Dict):
        """Save the current setup state"""
        if not self.dry_run:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
    
    def backup_existing_config(self) -> Optional[str]:
        """Backup existing Kitty configuration if it exists"""
        if self.config_target.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"kitty_backup_{timestamp}"
            
            if self.dry_run:
                self.print_status("info", f"Would backup {self.config_target} to {backup_path}")
                return str(backup_path)
            else:
                if self.config_target.is_symlink():
                    # Just remove the symlink, don't backup
                    self.config_target.unlink()
                    self.print_status("info", "Removed existing symlink")
                else:
                    # Backup real directory/file
                    shutil.copytree(self.config_target, backup_path)
                    shutil.rmtree(self.config_target)
                    self.print_status("success", f"Backed up existing config to {backup_path}")
                    return str(backup_path)
        return None
    
    def create_config_structure(self):
        """Create the Kitty configuration directory structure"""
        # Ensure source directory exists
        if not self.config_source.exists():
            self.config_source.mkdir(parents=True, exist_ok=True)
            self.print_status("info", f"Created source directory: {self.config_source}")
    
    def setup(self) -> bool:
        """Set up Kitty configuration"""
        try:
            self.print_status("info", "Setting up Kitty terminal configuration...")
            
            # Ensure necessary directories exist
            self.ensure_directories()
            self.create_config_structure()
            
            # Load previous state
            state = self.load_state()
            
            # Backup existing configuration
            backup_path = self.backup_existing_config()
            if backup_path:
                state['last_backup'] = backup_path
            
            # Create symlink to repository config
            if self.dry_run:
                self.print_status("info", f"Would create symlink: {self.config_target} -> {self.config_source}")
            else:
                self.config_target.parent.mkdir(parents=True, exist_ok=True)
                self.config_target.symlink_to(self.config_source)
                self.print_status("success", f"Created symlink: {self.config_target} -> {self.config_source}")
            
            # Update state
            state['setup_date'] = datetime.now().isoformat()
            state['config_source'] = str(self.config_source)
            state['config_target'] = str(self.config_target)
            self.save_state(state)
            
            if not self.dry_run:
                self.print_status("success", "Kitty configuration setup complete!")
                self.print_status("info", "Restart Kitty or press Ctrl+Shift+F5 to reload config")
            else:
                self.print_status("info", "Dry run complete - no changes made")
            
            return True
            
        except Exception as e:
            self.print_status("error", f"Setup failed: {str(e)}")
            return False
    
    def rollback(self) -> bool:
        """Rollback to the previous configuration"""
        try:
            state = self.load_state()
            
            if 'last_backup' not in state:
                self.print_status("warning", "No backup found to rollback to")
                return False
            
            backup_path = Path(state['last_backup'])
            
            if not backup_path.exists():
                self.print_status("error", f"Backup not found: {backup_path}")
                return False
            
            self.print_status("info", f"Rolling back to: {backup_path}")
            
            if self.dry_run:
                self.print_status("info", f"Would remove: {self.config_target}")
                self.print_status("info", f"Would restore: {backup_path} -> {self.config_target}")
            else:
                # Remove current config
                if self.config_target.exists():
                    if self.config_target.is_symlink():
                        self.config_target.unlink()
                    else:
                        shutil.rmtree(self.config_target)
                
                # Restore backup
                shutil.copytree(backup_path, self.config_target)
                self.print_status("success", "Rollback complete!")
                
                # Clear the state
                self.save_state({})
            
            return True
            
        except Exception as e:
            self.print_status("error", f"Rollback failed: {str(e)}")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Set up Kitty terminal emulator configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    uv run scripts/setup-kitty.py           # Set up Kitty configuration
    uv run scripts/setup-kitty.py --dry-run # Preview changes without applying
    uv run scripts/setup-kitty.py --rollback # Restore previous configuration
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
    
    # Find repository root
    repo_root = Path(__file__).parent.parent
    
    # Initialize setup
    setup = KittySetup(repo_root, dry_run=args.dry_run)
    
    # Execute requested action
    if args.rollback:
        success = setup.rollback()
    else:
        success = setup.setup()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
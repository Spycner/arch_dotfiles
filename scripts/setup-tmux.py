"""
Tmux Configuration Setup Script

This script sets up tmux configuration by creating symlinks from the repository
to the user's config directory. It includes backup, rollback, and validation features.

Usage:
    uv run setup-tmux.py [--dry-run] [--rollback] [--help]
"""
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import argparse
import json
import os
import shutil
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


class TmuxSetup:
    """Main class for tmux configuration setup."""
    
    def __init__(self, repo_root: Path, dry_run: bool = False):
        self.repo_root = repo_root
        self.dry_run = dry_run
        self.config_dir = Path.home() / '.config' / 'tmux'
        self.tmux_dir = Path.home() / '.tmux'
        self.backup_dir = Path.home() / '.local' / 'share' / 'arch_dotfiles' / 'backups'
        self.state_file = Path.home() / '.local' / 'share' / 'arch_dotfiles' / 'tmux_setup_state.json'
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Files and directories to link
        self.link_map = {
            'tmux.conf': {
                'source': self.repo_root / 'config' / 'tmux' / 'tmux.conf',
                'target': self.config_dir / 'tmux.conf'
            },
            'plugins': {
                'source': self.repo_root / 'config' / 'tmux' / 'plugins',
                'target': self.tmux_dir / 'plugins'
            }
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
        
        directories = [self.config_dir, self.tmux_dir, self.backup_dir, self.state_file.parent]
        
        for directory in directories:
            if not self.dry_run:
                directory.mkdir(parents=True, exist_ok=True)
            self.print_colored(f"  Created: {directory}", Colors.BLUE)
    
    def backup_existing_config(self) -> Dict[str, str]:
        """Backup existing configuration files."""
        self.print_step("Backing up existing configuration")
        
        backup_info = {}
        
        for name, paths in self.link_map.items():
            target_path = paths['target']
            
            if target_path.exists():
                backup_path = self.backup_dir / f"{name}.backup.{self.timestamp}"
                backup_info[name] = str(backup_path)
                
                if not self.dry_run:
                    if target_path.is_dir():
                        shutil.copytree(target_path, backup_path)
                    else:
                        shutil.copy2(target_path, backup_path)
                
                self.print_colored(f"  Backed up: {target_path} → {backup_path}", Colors.YELLOW)
            else:
                self.print_colored(f"  No existing config: {target_path}", Colors.BLUE)
        
        return backup_info
    
    def remove_existing_config(self) -> None:
        """Remove existing configuration files and directories."""
        self.print_step("Removing existing configuration")
        
        for name, paths in self.link_map.items():
            target_path = paths['target']
            
            if target_path.exists():
                try:
                    if not self.dry_run:
                        if target_path.is_symlink():
                            target_path.unlink()
                        elif target_path.is_dir():
                            shutil.rmtree(target_path)
                        else:
                            target_path.unlink()
                    
                    self.print_colored(f"  Removed: {target_path}", Colors.MAGENTA)
                except Exception as e:
                    self.print_warning(f"  Could not remove {target_path}: {e}")
                    # Continue with setup anyway
    
    def create_symlinks(self) -> None:
        """Create symlinks to repository configuration."""
        self.print_step("Creating symlinks to repository configuration")
        
        for name, paths in self.link_map.items():
            source_path = paths['source']
            target_path = paths['target']
            
            if not source_path.exists():
                self.print_warning(f"Source not found: {source_path}")
                continue
            
            try:
                if not self.dry_run:
                    # Ensure parent directory exists
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    # Create the symlink
                    target_path.symlink_to(source_path)
                
                self.print_colored(f"  Linked: {target_path} → {source_path}", Colors.GREEN)
            except Exception as e:
                self.print_error(f"  Failed to create link {target_path}: {e}")
                raise
    
    def save_state(self, backup_info: Dict[str, str]) -> None:
        """Save setup state for rollback."""
        self.print_step("Saving setup state")
        
        state = {
            'timestamp': self.timestamp,
            'backup_info': backup_info,
            'links_created': {name: str(paths['target']) for name, paths in self.link_map.items()},
            'repo_root': str(self.repo_root)
        }
        
        if not self.dry_run:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        
        self.print_colored(f"  State saved: {self.state_file}", Colors.BLUE)
    
    def validate_setup(self) -> bool:
        """Validate that setup was successful."""
        self.print_step("Validating setup")
        
        all_valid = True
        
        for name, paths in self.link_map.items():
            source_path = paths['source']
            target_path = paths['target']
            
            if not source_path.exists():
                self.print_warning(f"Source not found: {source_path}")
                continue
            
            if not target_path.exists():
                self.print_error(f"Link not created: {target_path}")
                all_valid = False
            elif not target_path.is_symlink():
                self.print_error(f"Not a symlink: {target_path}")
                all_valid = False
            else:
                # Check if symlink points to correct location
                try:
                    actual_target = target_path.resolve()
                    expected_target = source_path.resolve()
                    if actual_target != expected_target:
                        self.print_error(f"Wrong target: {target_path} → {actual_target} (expected {expected_target})")
                        all_valid = False
                    else:
                        self.print_success(f"Valid link: {target_path} → {source_path}")
                except Exception as e:
                    self.print_warning(f"Could not validate {target_path}: {e}")
        
        return all_valid
    
    def setup(self) -> bool:
        """Main setup process."""
        self.print_colored("Tmux Configuration Setup", Colors.CYAN, bold=True)
        
        if self.dry_run:
            self.print_warning("DRY RUN MODE - No changes will be made")
        
        try:
            # Ensure directories exist
            self.ensure_directories()
            
            # Backup existing configuration
            backup_info = self.backup_existing_config()
            
            # Remove existing configuration
            self.remove_existing_config()
            
            # Create symlinks
            self.create_symlinks()
            
            # Save state for rollback
            self.save_state(backup_info)
            
            # Validate setup
            if not self.dry_run:
                if self.validate_setup():
                    self.print_success("Tmux configuration setup completed successfully!")
                    self.print_colored("\nNext steps:", Colors.CYAN, bold=True)
                    self.print_colored("  1. Install TPM (Tmux Plugin Manager): git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm", Colors.WHITE)
                    self.print_colored("  2. Start tmux and press prefix + I to install plugins", Colors.WHITE)
                    self.print_colored("  3. Restart tmux or source the config: tmux source ~/.config/tmux/tmux.conf", Colors.WHITE)
                    return True
                else:
                    self.print_error("Setup validation failed!")
                    return False
            else:
                self.print_success("Dry run completed - setup would succeed")
                return True
        
        except Exception as e:
            self.print_error(f"Setup failed: {e}")
            return False
    
    def rollback(self) -> bool:
        """Rollback to previous configuration."""
        self.print_colored("Rolling back tmux configuration", Colors.YELLOW, bold=True)
        
        if not self.state_file.exists():
            self.print_error("No state file found - cannot rollback")
            return False
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            backup_info = state.get('backup_info', {})
            links_created = state.get('links_created', {})
            
            # Remove created symlinks
            self.print_step("Removing created symlinks")
            for name, target_path_str in links_created.items():
                target_path = Path(target_path_str)
                if target_path.exists() and target_path.is_symlink():
                    target_path.unlink()
                    self.print_colored(f"  Removed symlink: {target_path}", Colors.MAGENTA)
            
            # Restore backups
            self.print_step("Restoring backups")
            for name, backup_path_str in backup_info.items():
                backup_path = Path(backup_path_str)
                if backup_path.exists():
                    target_path = self.link_map[name]['target']
                    
                    if backup_path.is_dir():
                        shutil.copytree(backup_path, target_path)
                    else:
                        shutil.copy2(backup_path, target_path)
                    
                    self.print_colored(f"  Restored: {backup_path} → {target_path}", Colors.GREEN)
                else:
                    self.print_warning(f"Backup not found: {backup_path}")
            
            # Remove state file
            self.state_file.unlink()
            self.print_success("Rollback completed successfully!")
            return True
            
        except Exception as e:
            self.print_error(f"Rollback failed: {e}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Set up tmux configuration with symlinks, backup, and rollback support"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '--rollback',
        action='store_true',
        help='Rollback to previous configuration'
    )
    
    args = parser.parse_args()
    
    # Find repository root
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent
    
    # Verify we're in the correct repository
    if not (repo_root / 'config' / 'tmux' / 'tmux.conf').exists():
        print(f"Error: tmux configuration not found in {repo_root / 'config' / 'tmux'}")
        print("Make sure you're running this script from the arch_dotfiles repository")
        sys.exit(1)
    
    setup = TmuxSetup(repo_root, dry_run=args.dry_run)
    
    if args.rollback:
        success = setup.rollback()
    else:
        success = setup.setup()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
"""
Hyprland Configuration Setup Script

This script sets up Hyprland configuration by creating symlinks from the repository
to the user's config directory. It includes backup, rollback, and validation features.

Usage:
    uv run setup_hyprland.py [--dry-run] [--rollback] [--help]
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


class HyprlandSetup:
    """Main class for Hyprland configuration setup."""
    
    def __init__(self, repo_root: Path, dry_run: bool = False):
        self.repo_root = repo_root
        self.dry_run = dry_run
        self.config_dir = Path.home() / '.config' / 'hypr'
        self.backup_dir = Path.home() / '.local' / 'share' / 'arch_dotfiles' / 'backups'
        self.state_file = Path.home() / '.local' / 'share' / 'arch_dotfiles' / 'hyprland_setup_state.json'
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Files and directories to link
        self.link_map = {
            'hyprland.conf': self.repo_root / 'config' / 'hypr' / 'hyprland.conf',
            'conf.d': self.repo_root / 'config' / 'hypr' / 'conf.d',
            'scripts': self.repo_root / 'config' / 'hypr' / 'scripts'
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
    
    def backup_existing_config(self) -> Dict[str, str]:
        """Backup existing configuration files."""
        self.print_step("Backing up existing configuration")
        
        backup_info = {}
        
        for name, source_path in self.link_map.items():
            target_path = self.config_dir / name
            
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
                self.print_colored(f"  No existing file: {target_path}", Colors.BLUE)
        
        return backup_info
    
    def create_symlinks(self) -> None:
        """Create symlinks from repository to config directory."""
        self.print_step("Creating symlinks")
        
        for name, source_path in self.link_map.items():
            target_path = self.config_dir / name
            
            # Remove existing file/directory if it exists
            if target_path.exists():
                if not self.dry_run:
                    if target_path.is_dir():
                        shutil.rmtree(target_path)
                    else:
                        target_path.unlink()
                self.print_colored(f"  Removed existing: {target_path}", Colors.MAGENTA)
            
            # Create symlink
            if not self.dry_run:
                target_path.symlink_to(source_path)
            
            self.print_colored(f"  Linked: {target_path} → {source_path}", Colors.GREEN)
    
    def save_state(self, backup_info: Dict[str, str]) -> None:
        """Save setup state for potential rollback."""
        state = {
            'timestamp': self.timestamp,
            'repo_root': str(self.repo_root),
            'backup_info': backup_info,
            'links_created': {name: str(path) for name, path in self.link_map.items()}
        }
        
        if not self.dry_run:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        
        self.print_colored(f"  Saved state: {self.state_file}", Colors.BLUE)
    
    def validate_setup(self) -> bool:
        """Validate that symlinks are created correctly."""
        self.print_step("Validating setup")
        
        all_valid = True
        
        for name, source_path in self.link_map.items():
            target_path = self.config_dir / name
            
            if not target_path.exists():
                self.print_error(f"  Missing: {target_path}")
                all_valid = False
                continue
            
            if not target_path.is_symlink():
                self.print_error(f"  Not a symlink: {target_path}")
                all_valid = False
                continue
            
            if target_path.readlink() != source_path:
                self.print_error(f"  Wrong target: {target_path} → {target_path.readlink()}")
                all_valid = False
                continue
            
            self.print_success(f"  Valid: {name}")
        
        return all_valid
    
    def setup(self) -> bool:
        """Main setup function."""
        self.print_colored("Hyprland Configuration Setup", Colors.CYAN, bold=True)
        self.print_colored("=" * 40, Colors.CYAN)
        
        if self.dry_run:
            self.print_warning("DRY RUN MODE - No changes will be made")
            print()
        
        try:
            # Validate source files exist
            self.print_step("Validating source files")
            for name, source_path in self.link_map.items():
                if not source_path.exists():
                    self.print_error(f"  Missing source: {source_path}")
                    return False
                self.print_success(f"  Found: {name}")
            
            print()
            
            # Setup process
            self.ensure_directories()
            backup_info = self.backup_existing_config()
            self.create_symlinks()
            
            if not self.dry_run:
                self.save_state(backup_info)
                
                print()
                if self.validate_setup():
                    self.print_success("Setup completed successfully!")
                    self.print_colored("\\nTo reload Hyprland configuration:", Colors.YELLOW)
                    self.print_colored("  hyprctl reload", Colors.WHITE)
                    return True
                else:
                    self.print_error("Setup validation failed!")
                    return False
            else:
                print()
                self.print_success("Dry run completed - no changes made")
                return True
                
        except Exception as e:
            self.print_error(f"Setup failed: {e}")
            return False
    
    def rollback(self) -> bool:
        """Rollback to previous configuration."""
        self.print_colored("Hyprland Configuration Rollback", Colors.YELLOW, bold=True)
        self.print_colored("=" * 40, Colors.YELLOW)
        
        if not self.state_file.exists():
            self.print_error("No state file found - cannot rollback")
            return False
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            self.print_step(f"Rolling back setup from {state['timestamp']}")
            
            # Remove symlinks
            for name in state['links_created']:
                target_path = self.config_dir / name
                if target_path.exists() and target_path.is_symlink():
                    if not self.dry_run:
                        target_path.unlink()
                    self.print_colored(f"  Removed symlink: {target_path}", Colors.MAGENTA)
            
            # Restore backups
            for name, backup_path in state['backup_info'].items():
                backup_path = Path(backup_path)
                target_path = self.config_dir / name
                
                if backup_path.exists():
                    if not self.dry_run:
                        if backup_path.is_dir():
                            shutil.copytree(backup_path, target_path)
                        else:
                            shutil.copy2(backup_path, target_path)
                    self.print_colored(f"  Restored: {backup_path} → {target_path}", Colors.GREEN)
                else:
                    self.print_warning(f"  Backup not found: {backup_path}")
            
            if not self.dry_run:
                self.state_file.unlink()
                self.print_colored(f"  Removed state file: {self.state_file}", Colors.BLUE)
            
            self.print_success("Rollback completed successfully!")
            return True
            
        except Exception as e:
            self.print_error(f"Rollback failed: {e}")
            return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Setup Hyprland configuration with symlinks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 setup_hyprland.py              # Setup configuration
  python3 setup_hyprland.py --dry-run    # Preview changes without applying
  python3 setup_hyprland.py --rollback   # Undo previous setup
        """
    )
    
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without applying them')
    parser.add_argument('--rollback', action='store_true',
                       help='Rollback to previous configuration')
    
    args = parser.parse_args()
    
    # Find repository root
    script_path = Path(__file__).resolve()
    repo_root = None
    
    # Walk up the directory tree to find the repo root
    current = script_path.parent
    while current != current.parent:
        if (current / '.git').exists() or (current / 'CLAUDE.md').exists():
            repo_root = current
            break
        current = current.parent
    
    if not repo_root:
        print(f"{Colors.RED}✗ Could not find repository root{Colors.RESET}")
        sys.exit(1)
    
    setup = HyprlandSetup(repo_root, dry_run=args.dry_run)
    
    if args.rollback:
        success = setup.rollback()
    else:
        success = setup.setup()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
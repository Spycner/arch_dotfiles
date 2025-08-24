"""
Bat Configuration Setup Script

This script sets up bat configuration by creating symlinks from the repository
to the user's config directory. It includes backup, rollback, and validation features.

Usage:
    uv run setup-bat.py [--dry-run] [--rollback] [--help]
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


class BatSetup:
    """Main class for bat configuration setup."""
    
    def __init__(self, repo_root: Path, dry_run: bool = False):
        self.repo_root = repo_root
        self.dry_run = dry_run
        self.config_dir = Path.home() / '.config' / 'bat'
        self.backup_dir = Path.home() / '.local' / 'share' / 'arch_dotfiles' / 'backups'
        self.state_file = Path.home() / '.local' / 'share' / 'arch_dotfiles' / 'bat_setup_state.json'
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Files and directories to link
        self.link_map = {
            'config/bat': '.config/bat'
        }
        
        self.source_path = self.repo_root / 'config' / 'bat'
        
    def print_status(self, message: str, color: str = Colors.WHITE) -> None:
        """Print colored status message."""
        print(f"{color}{message}{Colors.RESET}")
        
    def print_success(self, message: str) -> None:
        """Print success message in green."""
        self.print_status(f"✓ {message}", Colors.GREEN)
        
    def print_info(self, message: str) -> None:
        """Print info message in blue."""
        self.print_status(f"→ {message}", Colors.BLUE)
        
    def print_warning(self, message: str) -> None:
        """Print warning message in yellow."""
        self.print_status(f"⚠ {message}", Colors.YELLOW)
        
    def print_error(self, message: str) -> None:
        """Print error message in red."""
        self.print_status(f"✗ {message}", Colors.RED)
        
    def ensure_directories(self) -> None:
        """Create necessary directories."""
        directories = [self.backup_dir, self.state_file.parent]
        
        for directory in directories:
            if not directory.exists():
                self.print_info(f"Creating directory: {directory}")
                if not self.dry_run:
                    directory.mkdir(parents=True, exist_ok=True)
                    
    def validate_source_files(self) -> bool:
        """Validate that source configuration exists."""
        if not self.source_path.exists():
            self.print_error(f"Source bat configuration not found: {self.source_path}")
            return False
            
        if not (self.source_path / 'config').exists():
            self.print_error(f"Bat config file not found: {self.source_path / 'config'}")
            return False
            
        self.print_success(f"Source bat configuration validated: {self.source_path}")
        return True
        
    def backup_existing_config(self) -> Dict[str, str]:
        """Create backup of existing bat configuration."""
        backup_info = {}
        
        if self.config_dir.exists():
            backup_path = self.backup_dir / f"bat_config_{self.timestamp}"
            self.print_info(f"Backing up existing bat config to: {backup_path}")
            
            if not self.dry_run:
                backup_path.mkdir(parents=True, exist_ok=True)
                shutil.copytree(self.config_dir, backup_path / 'bat', dirs_exist_ok=True)
                backup_info['config_backup'] = str(backup_path / 'bat')
        else:
            self.print_info("No existing bat configuration found - no backup needed")
            
        return backup_info
        
    def create_symlinks(self) -> bool:
        """Create symlinks for bat configuration."""
        try:
            # Remove existing config directory if it exists
            if self.config_dir.exists():
                self.print_info(f"Removing existing bat config: {self.config_dir}")
                if not self.dry_run:
                    if self.config_dir.is_symlink():
                        self.config_dir.unlink()
                    else:
                        shutil.rmtree(self.config_dir)
            
            # Create parent directory
            if not self.config_dir.parent.exists():
                self.print_info(f"Creating config parent directory: {self.config_dir.parent}")
                if not self.dry_run:
                    self.config_dir.parent.mkdir(parents=True, exist_ok=True)
            
            # Create symlink
            self.print_info(f"Creating symlink: {self.config_dir} -> {self.source_path}")
            if not self.dry_run:
                self.config_dir.symlink_to(self.source_path, target_is_directory=True)
                
            return True
            
        except Exception as e:
            self.print_error(f"Failed to create symlinks: {e}")
            return False
            
    def save_state(self, backup_info: Dict[str, str]) -> None:
        """Save setup state for rollback."""
        state = {
            'timestamp': self.timestamp,
            'repo_root': str(self.repo_root),
            'backup_info': backup_info,
            'config_dir': str(self.config_dir),
            'source_path': str(self.source_path)
        }
        
        self.print_info(f"Saving setup state to: {self.state_file}")
        if not self.dry_run:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
    def setup(self) -> bool:
        """Main setup function."""
        self.print_info(f"{'[DRY RUN] ' if self.dry_run else ''}Setting up bat configuration...")
        
        # Validate source files
        if not self.validate_source_files():
            return False
            
        # Create necessary directories
        self.ensure_directories()
        
        # Backup existing configuration
        backup_info = self.backup_existing_config()
        
        # Create symlinks
        if not self.create_symlinks():
            return False
            
        # Save state for rollback
        self.save_state(backup_info)
        
        # Rebuild bat cache to detect new themes
        if not self.dry_run:
            self.print_info("Rebuilding bat cache to detect custom themes...")
            try:
                import subprocess
                result = subprocess.run(['bat', 'cache', '--build'], 
                                     capture_output=True, text=True, check=True)
                self.print_success("✓ Bat cache rebuilt successfully")
            except subprocess.CalledProcessError as e:
                self.print_warning(f"⚠ Failed to rebuild bat cache: {e}")
                self.print_info("You may need to run 'bat cache --build' manually")
            except FileNotFoundError:
                self.print_warning("⚠ 'bat' command not found - themes may not be detected")
                self.print_info("Install bat with: paru -S bat")
        
        self.print_success(f"{'[DRY RUN] ' if self.dry_run else ''}Bat configuration setup completed!")
        self.print_info("Configuration files:")
        self.print_info(f"  • Config: {self.config_dir}/config")
        self.print_info(f"  • Themes: {self.config_dir}/themes/")
        
        if not self.dry_run:
            self.print_info("\nTo verify installation:")
            self.print_info("  • Check version: bat --version")
            self.print_info("  • List themes: bat --list-themes")
            self.print_info("  • Test themes: bat --theme='Catppuccin Mocha' <file>")
            
        return True
        
    def rollback(self) -> bool:
        """Rollback bat configuration setup."""
        if not self.state_file.exists():
            self.print_error("No setup state found - cannot rollback")
            return False
            
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                
            self.print_info(f"Rolling back bat setup from {state['timestamp']}...")
            
            # Remove current symlink
            config_dir = Path(state['config_dir'])
            if config_dir.exists():
                self.print_info(f"Removing current bat config: {config_dir}")
                if config_dir.is_symlink():
                    config_dir.unlink()
                else:
                    shutil.rmtree(config_dir)
                    
            # Restore backup if it exists
            backup_info = state.get('backup_info', {})
            if 'config_backup' in backup_info:
                backup_path = Path(backup_info['config_backup'])
                if backup_path.exists():
                    self.print_info(f"Restoring backup from: {backup_path}")
                    shutil.copytree(backup_path, config_dir, dirs_exist_ok=True)
                    
            # Remove state file
            self.state_file.unlink()
            
            self.print_success("Bat configuration rollback completed!")
            return True
            
        except Exception as e:
            self.print_error(f"Rollback failed: {e}")
            return False
            
    def status(self) -> None:
        """Show current bat configuration status."""
        self.print_info("Bat Configuration Status:")
        self.print_info("=" * 50)
        
        # Check if bat config exists
        if self.config_dir.exists():
            if self.config_dir.is_symlink():
                target = self.config_dir.resolve()
                self.print_success(f"Config directory: {self.config_dir} -> {target}")
                
                # Check if it points to our repo
                if target == self.source_path.resolve():
                    self.print_success("✓ Correctly linked to repository")
                else:
                    self.print_warning("⚠ Linked to different location")
            else:
                self.print_warning(f"⚠ Config exists but is not a symlink: {self.config_dir}")
        else:
            self.print_warning("⚠ No bat configuration found")
            
        # Check source files
        if self.source_path.exists():
            self.print_success(f"✓ Source configuration exists: {self.source_path}")
            
            # List contents
            config_file = self.source_path / 'config'
            themes_dir = self.source_path / 'themes'
            
            if config_file.exists():
                self.print_success("✓ Config file found")
            else:
                self.print_warning("⚠ Config file missing")
                
            if themes_dir.exists() and any(themes_dir.iterdir()):
                theme_count = len(list(themes_dir.glob('*.tmTheme')))
                self.print_success(f"✓ {theme_count} theme files found")
            else:
                self.print_warning("⚠ No themes found")
        else:
            self.print_error(f"✗ Source configuration missing: {self.source_path}")
            
        # Check setup state
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                self.print_info(f"Last setup: {state['timestamp']}")
            except:
                self.print_warning("⚠ Setup state file corrupted")
        else:
            self.print_info("No setup state found")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Setup bat configuration with symlinks")
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be done without making changes')
    parser.add_argument('--rollback', action='store_true',
                       help='Rollback to previous configuration')
    parser.add_argument('--status', action='store_true',
                       help='Show current configuration status')
    
    args = parser.parse_args()
    
    # Get repository root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    
    # Validate we're in the right place
    if not (repo_root / 'config' / 'bat').exists():
        print(f"{Colors.RED}✗ Bat configuration not found in repository{Colors.RESET}")
        print(f"Expected: {repo_root / 'config' / 'bat'}")
        sys.exit(1)
        
    # Create setup instance
    setup = BatSetup(repo_root, dry_run=args.dry_run)
    
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
        print(f"\n{Colors.YELLOW}Setup interrupted by user{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}Unexpected error: {e}{Colors.RESET}")
        sys.exit(1)


if __name__ == '__main__':
    main()
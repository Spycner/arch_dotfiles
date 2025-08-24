"""
Yazi Configuration Setup Script

This script sets up yazi file manager configuration by creating symlinks from the repository
to the user's config directory. It includes backup, rollback, and validation features.

Usage:
    uv run scripts/setup-yazi.py [--dry-run] [--rollback] [--help]
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


class YaziSetup:
    """Main class for yazi configuration setup."""
    
    def __init__(self, repo_root: Path, dry_run: bool = False):
        self.repo_root = repo_root
        self.dry_run = dry_run
        self.config_dir = Path.home() / '.config' / 'yazi'
        self.backup_dir = Path.home() / '.local' / 'share' / 'arch_dotfiles' / 'backups'
        self.state_file = Path.home() / '.local' / 'share' / 'arch_dotfiles' / 'yazi_setup_state.json'
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Files and directories to link
        self.link_map = {
            'yazi.toml': self.repo_root / 'config' / 'yazi' / 'yazi.toml',
            'theme.toml': self.repo_root / 'config' / 'yazi' / 'theme.toml',
            'flavors': self.repo_root / 'config' / 'yazi' / 'flavors',
            'plugins': self.repo_root / 'config' / 'yazi' / 'plugins',
        }

    def print_status(self, message: str, status: str = "INFO"):
        """Print colored status message."""
        colors = {
            "INFO": Colors.BLUE,
            "SUCCESS": Colors.GREEN,
            "WARNING": Colors.YELLOW,
            "ERROR": Colors.RED,
            "DRY_RUN": Colors.MAGENTA
        }
        color = colors.get(status, Colors.WHITE)
        prefix = "[DRY RUN]" if self.dry_run and status != "ERROR" else ""
        print(f"{color}{Colors.BOLD}{prefix}[{status}]{Colors.RESET} {message}")

    def ensure_directories(self):
        """Create necessary directories."""
        directories = [self.backup_dir, self.config_dir.parent]
        for directory in directories:
            if not self.dry_run:
                directory.mkdir(parents=True, exist_ok=True)
            self.print_status(f"Ensuring directory exists: {directory}", "INFO")

    def backup_existing_config(self) -> Dict[str, str]:
        """Backup existing yazi configuration."""
        backup_info = {}
        
        if not self.config_dir.exists():
            self.print_status("No existing yazi config found, skipping backup", "INFO")
            return backup_info

        backup_path = self.backup_dir / f'yazi_config_backup_{self.timestamp}'
        
        self.print_status(f"Creating backup at: {backup_path}", "INFO")
        
        if not self.dry_run:
            backup_path.mkdir(parents=True, exist_ok=True)
            shutil.copytree(self.config_dir, backup_path / 'yazi', dirs_exist_ok=True)
        
        backup_info['backup_path'] = str(backup_path)
        backup_info['timestamp'] = self.timestamp
        backup_info['original_path'] = str(self.config_dir)
        
        return backup_info

    def validate_source_files(self) -> bool:
        """Validate that all source files exist."""
        missing_files = []
        
        for name, source_path in self.link_map.items():
            if not source_path.exists():
                missing_files.append(f"{name}: {source_path}")
        
        if missing_files:
            self.print_status("Missing source files:", "ERROR")
            for missing in missing_files:
                self.print_status(f"  - {missing}", "ERROR")
            return False
        
        self.print_status("All source files found", "SUCCESS")
        return True

    def create_symlinks(self) -> bool:
        """Create symlinks for yazi configuration."""
        if not self.validate_source_files():
            return False
        
        self.print_status("Creating symlinks for yazi configuration", "INFO")
        
        # Remove existing config directory if it exists
        if self.config_dir.exists():
            self.print_status(f"Removing existing config: {self.config_dir}", "WARNING")
            if not self.dry_run:
                if self.config_dir.is_symlink():
                    self.config_dir.unlink()
                else:
                    shutil.rmtree(self.config_dir)
        
        # Create config directory
        if not self.dry_run:
            self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create individual symlinks
        for name, source_path in self.link_map.items():
            target_path = self.config_dir / name
            
            self.print_status(f"Linking {name}: {source_path} -> {target_path}", "INFO")
            
            if not self.dry_run:
                try:
                    # Remove existing file/symlink if it exists
                    if target_path.exists() or target_path.is_symlink():
                        if target_path.is_symlink():
                            target_path.unlink()
                        elif target_path.is_file():
                            target_path.unlink()
                        elif target_path.is_dir():
                            shutil.rmtree(target_path)
                    
                    # Create symlink
                    target_path.symlink_to(source_path)
                    self.print_status(f"Successfully linked {name}", "SUCCESS")
                    
                except OSError as e:
                    self.print_status(f"Failed to link {name}: {e}", "ERROR")
                    return False
        
        return True

    def save_state(self, backup_info: Dict[str, str]):
        """Save setup state for potential rollback."""
        state = {
            'timestamp': self.timestamp,
            'backup_info': backup_info,
            'link_map': {k: str(v) for k, v in self.link_map.items()},
            'config_dir': str(self.config_dir),
        }
        
        if not self.dry_run:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        
        self.print_status(f"Setup state saved to: {self.state_file}", "INFO")

    def rollback(self) -> bool:
        """Rollback yazi configuration to previous state."""
        if not self.state_file.exists():
            self.print_status("No state file found, cannot rollback", "ERROR")
            return False
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            self.print_status(f"Failed to read state file: {e}", "ERROR")
            return False
        
        backup_info = state.get('backup_info', {})
        backup_path = backup_info.get('backup_path')
        
        if not backup_path or not Path(backup_path).exists():
            self.print_status("No valid backup found for rollback", "ERROR")
            return False
        
        self.print_status(f"Rolling back yazi configuration from: {backup_path}", "WARNING")
        
        # Remove current symlinks
        if self.config_dir.exists():
            if not self.dry_run:
                if self.config_dir.is_symlink():
                    self.config_dir.unlink()
                else:
                    shutil.rmtree(self.config_dir)
            self.print_status(f"Removed current config: {self.config_dir}", "INFO")
        
        # Restore from backup
        backup_config_path = Path(backup_path) / 'yazi'
        if backup_config_path.exists():
            if not self.dry_run:
                shutil.copytree(backup_config_path, self.config_dir)
            self.print_status(f"Restored config from backup", "SUCCESS")
        
        # Remove state file after successful rollback
        if not self.dry_run:
            self.state_file.unlink()
        self.print_status("Rollback completed successfully", "SUCCESS")
        
        return True

    def setup(self) -> bool:
        """Main setup process."""
        self.print_status("Starting yazi configuration setup", "INFO")
        
        # Ensure required directories exist
        self.ensure_directories()
        
        # Backup existing configuration
        backup_info = self.backup_existing_config()
        
        # Create symlinks
        if not self.create_symlinks():
            self.print_status("Setup failed during symlink creation", "ERROR")
            return False
        
        # Save state for potential rollback
        self.save_state(backup_info)
        
        self.print_status("Yazi configuration setup completed successfully!", "SUCCESS")
        self.print_status("Yazi config files are now symlinked to your repository", "INFO")
        self.print_status("Run 'uv run scripts/setup-yazi.py --rollback' to undo changes", "INFO")
        
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup yazi file manager configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter
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
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    
    if not (repo_root / 'config' / 'yazi').exists():
        print(f"{Colors.RED}Error: yazi config directory not found in repository{Colors.RESET}")
        sys.exit(1)
    
    setup = YaziSetup(repo_root, dry_run=args.dry_run)
    
    try:
        if args.rollback:
            success = setup.rollback()
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
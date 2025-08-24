"""
Fuzzel App Launcher Setup Script

This script installs and configures Fuzzel as the primary application launcher for Hyprland.
Includes Catppuccin Latte theming, Hyprland integration, and complete backup/rollback support.

Usage:
    uv run scripts/setup-fuzzel.py [--dry-run] [--rollback] [--help]
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


class FuzzelSetup:
    """Main class for Fuzzel launcher setup."""
    
    def __init__(self, repo_root: Path, dry_run: bool = False):
        self.repo_root = repo_root
        self.dry_run = dry_run
        self.config_dir = Path.home() / '.config' / 'fuzzel'
        self.hypr_config_dir = Path.home() / '.config' / 'hypr'
        self.backup_dir = Path.home() / '.local' / 'share' / 'arch_dotfiles' / 'backups'
        self.state_file = Path.home() / '.local' / 'share' / 'arch_dotfiles' / 'fuzzel_setup_state.json'
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Source files to link
        self.source_config = self.repo_root / 'config' / 'fuzzel' / 'fuzzel.ini'
        self.hypr_main_config = self.hypr_config_dir / 'hyprland.conf'
        
    def print_status(self, message: str, status: str = "info") -> None:
        """Print colored status messages."""
        colors = {
            "info": Colors.BLUE,
            "success": Colors.GREEN,
            "warning": Colors.YELLOW,
            "error": Colors.RED,
            "dry_run": Colors.MAGENTA
        }
        color = colors.get(status, Colors.WHITE)
        prefix = "[DRY RUN] " if self.dry_run and status != "dry_run" else ""
        print(f"{color}{Colors.BOLD}[FUZZEL]{Colors.RESET} {prefix}{message}")
    
    def run_command(self, command: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a shell command with proper error handling."""
        if self.dry_run:
            self.print_status(f"Would run: {' '.join(command)}", "dry_run")
            return subprocess.CompletedProcess(command, 0)
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=check)
            return result
        except subprocess.CalledProcessError as e:
            self.print_status(f"Command failed: {e}", "error")
            if e.stdout:
                print(f"stdout: {e.stdout}")
            if e.stderr:
                print(f"stderr: {e.stderr}")
            raise
    
    def ensure_directories(self) -> None:
        """Create necessary directories."""
        directories = [
            self.config_dir,
            self.backup_dir,
            self.state_file.parent
        ]
        
        for directory in directories:
            if not directory.exists():
                if not self.dry_run:
                    directory.mkdir(parents=True, exist_ok=True)
                self.print_status(f"Created directory: {directory}")
    
    def is_package_installed(self, package: str) -> bool:
        """Check if a package is installed via pacman."""
        try:
            result = subprocess.run(['pacman', '-Q', package], 
                                  capture_output=True, text=True, check=False)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def install_fuzzel(self) -> bool:
        """Install fuzzel package using paru."""
        if self.is_package_installed('fuzzel'):
            self.print_status("Fuzzel is already installed", "success")
            return True
        
        self.print_status("Installing fuzzel package...")
        self.print_status("You may be prompted for your sudo password...", "info")
        try:
            # Run interactively to allow sudo password prompt
            if self.dry_run:
                self.print_status("Would run: paru -S fuzzel --needed", "dry_run")
                return True
            else:
                result = subprocess.run(['paru', '-S', 'fuzzel', '--needed'], check=True)
                self.print_status("Successfully installed fuzzel", "success")
                return True
        except subprocess.CalledProcessError:
            self.print_status("Failed to install fuzzel", "error")
            return False
    
    def backup_existing_config(self) -> Dict[str, str]:
        """Create backups of existing configurations."""
        backups = {}
        
        # Backup existing fuzzel config if it exists
        if self.config_dir.exists():
            backup_path = self.backup_dir / f"fuzzel_config_{self.timestamp}"
            if not self.dry_run:
                shutil.copytree(self.config_dir, backup_path)
            backups['fuzzel_config'] = str(backup_path)
            self.print_status(f"Backed up fuzzel config to {backup_path}")
        
        # Backup hyprland.conf for menu variable change
        if self.hypr_main_config.exists():
            backup_path = self.backup_dir / f"hyprland_conf_{self.timestamp}"
            if not self.dry_run:
                shutil.copy2(self.hypr_main_config, backup_path)
            backups['hyprland_conf'] = str(backup_path)
            self.print_status(f"Backed up hyprland.conf to {backup_path}")
        
        return backups
    
    def create_symlinks(self) -> bool:
        """Create symlinks for fuzzel configuration."""
        try:
            # Remove existing config if it's not a symlink
            if self.config_dir.exists() and not self.config_dir.is_symlink():
                if not self.dry_run:
                    shutil.rmtree(self.config_dir)
                self.print_status(f"Removed existing config directory: {self.config_dir}")
            
            # Create symlink to fuzzel config directory
            source_dir = self.repo_root / 'config' / 'fuzzel'
            if not self.dry_run:
                if self.config_dir.is_symlink():
                    self.config_dir.unlink()
                self.config_dir.symlink_to(source_dir)
            
            self.print_status(f"Created symlink: {self.config_dir} -> {source_dir}")
            return True
            
        except Exception as e:
            self.print_status(f"Failed to create symlinks: {e}", "error")
            return False
    
    def update_hyprland_config(self) -> bool:
        """Update Hyprland configuration to use fuzzel instead of wofi."""
        if not self.hypr_main_config.exists():
            self.print_status("Hyprland config not found, skipping menu update", "warning")
            return True
        
        try:
            # Read current config
            if not self.dry_run:
                with open(self.hypr_main_config, 'r') as f:
                    content = f.read()
                
                # Replace menu definition
                old_line = '$menu = wofi --show drun'
                new_line = '$menu = fuzzel'
                
                if old_line in content:
                    content = content.replace(old_line, new_line)
                    with open(self.hypr_main_config, 'w') as f:
                        f.write(content)
                    self.print_status("Updated Hyprland config to use fuzzel")
                else:
                    self.print_status("Menu definition not found, may need manual update", "warning")
            else:
                self.print_status("Would update $menu variable in hyprland.conf", "dry_run")
            
            return True
            
        except Exception as e:
            self.print_status(f"Failed to update Hyprland config: {e}", "error")
            return False
    
    def save_state(self, backups: Dict[str, str]) -> None:
        """Save setup state for rollback."""
        state = {
            'timestamp': self.timestamp,
            'backups': backups,
            'installed_package': True,
            'repo_root': str(self.repo_root),
            'config_symlink': str(self.config_dir)
        }
        
        if not self.dry_run:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        
        self.print_status(f"Saved setup state to {self.state_file}")
    
    def setup(self) -> bool:
        """Main setup function."""
        self.print_status("Starting Fuzzel setup...")
        
        # Ensure required directories exist
        self.ensure_directories()
        
        # Install fuzzel package
        if not self.install_fuzzel():
            return False
        
        # Create backups
        backups = self.backup_existing_config()
        
        # Create configuration symlinks
        if not self.create_symlinks():
            return False
        
        # Update Hyprland configuration
        if not self.update_hyprland_config():
            return False
        
        # Save state for rollback
        self.save_state(backups)
        
        self.print_status("Fuzzel setup completed successfully!", "success")
        self.print_status("Press Super+Space to launch fuzzel", "info")
        return True
    
    def rollback(self) -> bool:
        """Rollback the fuzzel setup."""
        if not self.state_file.exists():
            self.print_status("No setup state found, nothing to rollback", "warning")
            return False
        
        self.print_status("Rolling back Fuzzel setup...")
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            backups = state.get('backups', {})
            
            # Remove symlinks
            if self.config_dir.is_symlink():
                if not self.dry_run:
                    self.config_dir.unlink()
                self.print_status(f"Removed symlink: {self.config_dir}")
            
            # Restore backups
            for config_name, backup_path in backups.items():
                backup_file = Path(backup_path)
                if backup_file.exists():
                    if config_name == 'fuzzel_config':
                        if not self.dry_run:
                            shutil.copytree(backup_file, self.config_dir)
                        self.print_status(f"Restored fuzzel config from {backup_path}")
                    elif config_name == 'hyprland_conf':
                        if not self.dry_run:
                            shutil.copy2(backup_file, self.hypr_main_config)
                        self.print_status(f"Restored hyprland.conf from {backup_path}")
            
            # Remove state file
            if not self.dry_run:
                self.state_file.unlink()
            
            self.print_status("Fuzzel setup rollback completed", "success")
            self.print_status("Note: Fuzzel package was not removed", "info")
            return True
            
        except Exception as e:
            self.print_status(f"Rollback failed: {e}", "error")
            return False


def main():
    parser = argparse.ArgumentParser(description="Setup Fuzzel app launcher for Hyprland")
    parser.add_argument('--dry-run', action='store_true',
                      help='Show what would be done without making changes')
    parser.add_argument('--rollback', action='store_true',
                      help='Rollback the fuzzel setup')
    
    args = parser.parse_args()
    
    # Find repository root
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent
    
    # Verify we're in the correct repository
    if not (repo_root / 'config' / 'fuzzel').exists():
        print(f"{Colors.RED}Error: Fuzzel config directory not found. Are you in the correct repository?{Colors.RESET}")
        sys.exit(1)
    
    setup = FuzzelSetup(repo_root, dry_run=args.dry_run)
    
    if args.rollback:
        success = setup.rollback()
    else:
        success = setup.setup()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
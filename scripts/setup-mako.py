"""
Mako Notification Daemon Setup Script

This script sets up Mako notification daemon for Hyprland by installing the package,
creating configuration symlinks, and integrating with Hyprland configuration.
It includes backup, rollback, and validation features.

Usage:
    uv run setup-mako.py [--dry-run] [--rollback] [--help]
"""
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


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


class MakoSetup:
    """Main class for Mako notification daemon setup."""
    
    def __init__(self, repo_root: Path, dry_run: bool = False):
        self.repo_root = repo_root
        self.dry_run = dry_run
        self.config_source = repo_root / "config" / "hypr" / "mako"
        self.config_target = Path.home() / ".config" / "mako"
        self.hyprland_config = Path.home() / ".config" / "hypr" / "hyprland.conf"
        
        # Setup backup and state directories
        self.backup_dir = Path.home() / ".local" / "share" / "arch_dotfiles" / "backups" / "mako"
        self.state_file = Path.home() / ".local" / "share" / "arch_dotfiles" / "mako_state.json"
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def print_status(self, status: str, message: str):
        """Print colored status messages"""
        color = {
            "success": Colors.GREEN,
            "warning": Colors.YELLOW,
            "error": Colors.RED,
            "info": Colors.BLUE,
            "step": Colors.CYAN
        }.get(status, Colors.RESET)
        
        symbol = {
            "success": "✓",
            "warning": "⚠",
            "error": "✗",
            "info": "→",
            "step": "→"
        }.get(status, "•")
        
        print(f"{color}{symbol} {message}{Colors.RESET}")
    
    def ensure_directories(self):
        """Create necessary directories"""
        self.print_status("step", "Creating necessary directories")
        
        if not self.dry_run:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            self.config_target.mkdir(parents=True, exist_ok=True)
        
        self.print_status("info", f"Backup directory: {self.backup_dir}")
        self.print_status("info", f"Config target: {self.config_target}")
    
    def check_package_installed(self, package: str) -> bool:
        """Check if a package is installed"""
        try:
            result = subprocess.run(['paru', '-Q', package], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            self.print_status("error", "paru not found - please install paru first")
            return False
    
    def install_package(self, package: str) -> bool:
        """Install package using paru"""
        self.print_status("step", f"Installing {package}")
        
        if self.check_package_installed(package):
            self.print_status("success", f"{package} already installed")
            return True
        
        if self.dry_run:
            self.print_status("info", f"Would install: {package}")
            return True
        
        try:
            result = subprocess.run(['paru', '-S', '--noconfirm', package], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.print_status("success", f"Installed {package}")
                return True
            else:
                self.print_status("error", f"Failed to install {package}: {result.stderr}")
                return False
        except Exception as e:
            self.print_status("error", f"Installation error: {e}")
            return False
    
    def backup_existing_config(self) -> Dict[str, str]:
        """Backup existing configuration files"""
        self.print_status("step", "Backing up existing configuration")
        
        backup_info = {}
        
        if self.config_target.exists():
            backup_path = self.backup_dir / f"config.backup.{self.timestamp}"
            backup_info["config"] = str(backup_path)
            
            if not self.dry_run:
                if self.config_target.is_dir():
                    shutil.copytree(self.config_target, backup_path)
                else:
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(self.config_target, backup_path)
            
            self.print_status("warning", f"Backed up existing config to: {backup_path}")
        else:
            self.print_status("info", "No existing mako config found")
        
        # Backup hyprland.conf if it exists
        if self.hyprland_config.exists():
            backup_path = self.backup_dir / f"hyprland.conf.backup.{self.timestamp}"
            backup_info["hyprland"] = str(backup_path)
            
            if not self.dry_run:
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self.hyprland_config, backup_path)
            
            self.print_status("warning", f"Backed up hyprland.conf to: {backup_path}")
        
        return backup_info
    
    def create_symlinks(self):
        """Create symlinks from repository to config directory"""
        self.print_status("step", "Creating configuration symlinks")
        
        # Remove existing config if it exists
        if self.config_target.exists():
            if not self.dry_run:
                if self.config_target.is_dir():
                    shutil.rmtree(self.config_target)
                else:
                    self.config_target.unlink()
            self.print_status("info", f"Removed existing: {self.config_target}")
        
        # Create symlink to the entire mako config directory
        if not self.dry_run:
            self.config_target.parent.mkdir(parents=True, exist_ok=True)
            self.config_target.symlink_to(self.config_source)
        
        self.print_status("success", f"Linked: {self.config_target} → {self.config_source}")
    
    def update_hyprland_config(self):
        """Add mako to Hyprland configuration"""
        self.print_status("step", "Updating Hyprland configuration")
        
        if not self.hyprland_config.exists():
            self.print_status("warning", "Hyprland config not found - skipping integration")
            return
        
        # Check if mako is already configured
        try:
            with open(self.hyprland_config, 'r') as f:
                content = f.read()
            
            if 'exec-once = mako' in content:
                self.print_status("success", "Mako already configured in Hyprland")
                return
            
            if self.dry_run:
                self.print_status("info", "Would add 'exec-once = mako' to hyprland.conf")
                return
            
            # Add mako exec-once line
            with open(self.hyprland_config, 'a') as f:
                f.write('\n# Notification daemon\nexec-once = mako\n')
            
            self.print_status("success", "Added mako to Hyprland startup")
            
        except Exception as e:
            self.print_status("error", f"Failed to update Hyprland config: {e}")
    
    def save_state(self, backup_info: Dict[str, str]):
        """Save setup state for potential rollback"""
        state = {
            'timestamp': self.timestamp,
            'repo_root': str(self.repo_root),
            'backup_info': backup_info,
            'config_source': str(self.config_source),
            'config_target': str(self.config_target)
        }
        
        if not self.dry_run:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        
        self.print_status("info", f"Saved state: {self.state_file}")
    
    def validate_setup(self) -> bool:
        """Validate that setup completed correctly"""
        self.print_status("step", "Validating setup")
        
        all_valid = True
        
        # Check if mako package is installed
        if not self.check_package_installed('mako'):
            self.print_status("error", "Mako package not installed")
            all_valid = False
        else:
            self.print_status("success", "Mako package installed")
        
        # Check if config symlink exists
        if not self.config_target.exists():
            self.print_status("error", f"Config symlink missing: {self.config_target}")
            all_valid = False
        elif not self.config_target.is_symlink():
            self.print_status("error", f"Config is not a symlink: {self.config_target}")
            all_valid = False
        elif self.config_target.readlink() != self.config_source:
            self.print_status("error", f"Config points to wrong location: {self.config_target.readlink()}")
            all_valid = False
        else:
            self.print_status("success", "Configuration symlink valid")
        
        # Check if hyprland config includes mako
        if self.hyprland_config.exists():
            try:
                with open(self.hyprland_config, 'r') as f:
                    content = f.read()
                
                if 'exec-once = mako' in content:
                    self.print_status("success", "Mako configured in Hyprland")
                else:
                    self.print_status("warning", "Mako not found in Hyprland config")
            except Exception as e:
                self.print_status("error", f"Could not verify Hyprland config: {e}")
        
        return all_valid
    
    def setup(self) -> bool:
        """Main setup function"""
        self.print_status("step", f"{Colors.CYAN}{Colors.BOLD}Mako Notification Daemon Setup{Colors.RESET}")
        print(f"{Colors.CYAN}{'=' * 40}{Colors.RESET}")
        
        if self.dry_run:
            self.print_status("warning", "DRY RUN MODE - No changes will be made")
            print()
        
        try:
            # Validate source files exist
            if not self.config_source.exists():
                self.print_status("error", f"Source config not found: {self.config_source}")
                return False
            
            # Setup process
            self.ensure_directories()
            
            # Install mako package
            if not self.install_package('mako'):
                return False
            
            # Setup configuration
            backup_info = self.backup_existing_config()
            self.create_symlinks()
            self.update_hyprland_config()
            
            if not self.dry_run:
                self.save_state(backup_info)
                
                print()
                if self.validate_setup():
                    self.print_status("success", "Mako setup completed successfully!")
                    self.print_status("info", "Reload Hyprland to start mako:")
                    self.print_status("info", "  hyprctl reload")
                    self.print_status("info", "Test with: notify-send 'Test' 'Hello from mako!'")
                    return True
                else:
                    self.print_status("error", "Setup validation failed!")
                    return False
            else:
                print()
                self.print_status("success", "Dry run completed - no changes made")
                return True
                
        except Exception as e:
            self.print_status("error", f"Setup failed: {e}")
            return False
    
    def rollback(self) -> bool:
        """Rollback to previous configuration"""
        self.print_status("step", f"{Colors.YELLOW}{Colors.BOLD}Mako Configuration Rollback{Colors.RESET}")
        print(f"{Colors.YELLOW}{'=' * 40}{Colors.RESET}")
        
        if not self.state_file.exists():
            self.print_status("error", "No state file found - cannot rollback")
            return False
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            self.print_status("step", f"Rolling back setup from {state['timestamp']}")
            
            # Remove symlinks
            config_target = Path(state['config_target'])
            if config_target.exists() and config_target.is_symlink():
                if not self.dry_run:
                    config_target.unlink()
                self.print_status("info", f"Removed symlink: {config_target}")
            
            # Restore backups
            for name, backup_path in state['backup_info'].items():
                backup_path = Path(backup_path)
                
                if name == "config":
                    target_path = Path(state['config_target'])
                elif name == "hyprland":
                    target_path = self.hyprland_config
                else:
                    continue
                
                if backup_path.exists():
                    if not self.dry_run:
                        if backup_path.is_dir():
                            shutil.copytree(backup_path, target_path)
                        else:
                            shutil.copy2(backup_path, target_path)
                    self.print_status("success", f"Restored: {backup_path} → {target_path}")
                else:
                    self.print_status("warning", f"Backup not found: {backup_path}")
            
            if not self.dry_run:
                self.state_file.unlink()
                self.print_status("info", f"Removed state file: {self.state_file}")
            
            self.print_status("success", "Rollback completed successfully!")
            self.print_status("warning", "Note: Package removal not automated - run 'paru -R mako' if desired")
            return True
            
        except Exception as e:
            self.print_status("error", f"Rollback failed: {e}")
            return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Setup Mako notification daemon for Hyprland",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run setup-mako.py              # Setup mako
  uv run setup-mako.py --dry-run    # Preview changes without applying
  uv run setup-mako.py --rollback   # Undo previous setup
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
    
    setup = MakoSetup(repo_root, dry_run=args.dry_run)
    
    if args.rollback:
        success = setup.rollback()
    else:
        success = setup.setup()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
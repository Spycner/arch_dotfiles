#!/usr/bin/env python3
"""
CLI Tools Installation Script

Installs essential command-line tools for arch_dotfiles setup.
Designed to be easily extended with additional packages.

Usage:
    uv run scripts/install-cli-tools.py [options]
"""

# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import argparse
import json
import logging
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class Package:
    """Represents a package to be installed."""
    name: str
    description: str
    check_command: Optional[str] = None  # Command to check if installed (if different from name)


class CLIToolsInstaller:
    """Manages installation of CLI tools with backup and rollback support."""
    
    # Package list - easily extensible
    PACKAGES = [
        Package("jq", "JSON processor for parsing Hyprland device information"),
        Package("waybar-git", "Highly customizable Wayland bar for Hyprland (git version for latest features)", "waybar"),
        # Add more packages here as needed:
        # Package("ripgrep", "Fast text search tool", "rg"),
        # Package("fd", "Modern find replacement"),
        # Package("bat", "Cat with syntax highlighting"),
        # Package("eza", "Modern ls replacement"),
    ]
    
    def __init__(self, dry_run: bool = False, force: bool = False):
        """Initialize the installer."""
        self.dry_run = dry_run
        self.force = force
        
        # Setup directories
        self.data_dir = Path.home() / '.local' / 'share' / 'arch_dotfiles'
        self.log_dir = self.data_dir / 'logs'
        self.state_file = self.data_dir / 'cli_tools_state.json'
        self.backup_dir = self.data_dir / 'backups' / 'cli_tools'
        
        # Create necessary directories
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # ANSI color codes
        self.colors = {
            'red': '\033[31m',
            'green': '\033[32m',
            'yellow': '\033[33m',
            'blue': '\033[34m',
            'reset': '\033[0m'
        }
    
    def _setup_logging(self):
        """Setup logging configuration."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.log_dir / f'cli-tools-install-{timestamp}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Log file: {log_file}")
    
    def _color(self, text: str, color: str) -> str:
        """Apply color to text."""
        return f"{self.colors.get(color, '')}{text}{self.colors['reset']}"
    
    def _run_command(self, cmd: List[str], capture_output: bool = True) -> Tuple[bool, str]:
        """Run a shell command and return success status and output."""
        if self.dry_run:
            self.logger.info(f"DRY RUN: Would execute: {' '.join(cmd)}")
            return True, "DRY RUN"
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                check=True
            )
            return True, result.stdout if capture_output else ""
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {e}")
            return False, e.stderr if capture_output else str(e)
        except FileNotFoundError:
            self.logger.error(f"Command not found: {cmd[0]}")
            return False, f"Command not found: {cmd[0]}"
    
    def _check_paru(self) -> bool:
        """Check if paru AUR helper is installed."""
        if shutil.which('paru'):
            return True
        
        print(self._color("Error: paru (AUR helper) not found", 'red'))
        print("Please install paru first:")
        print("  cd /tmp")
        print("  git clone https://aur.archlinux.org/paru.git")
        print("  cd paru && makepkg -si")
        return False
    
    def _is_package_installed(self, package: Package) -> bool:
        """Check if a package is installed."""
        check_cmd = package.check_command or package.name
        return shutil.which(check_cmd) is not None
    
    def _load_state(self) -> Dict:
        """Load installation state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load state file: {e}")
        return {
            'installed_packages': [],
            'installation_history': []
        }
    
    def _save_state(self, state: Dict):
        """Save installation state to file."""
        if not self.dry_run:
            try:
                with open(self.state_file, 'w') as f:
                    json.dump(state, f, indent=2)
            except Exception as e:
                self.logger.error(f"Failed to save state: {e}")
    
    def _create_backup(self, package_name: str) -> Optional[Path]:
        """Create a backup entry for package installation."""
        if self.dry_run:
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f"{package_name}_{timestamp}.json"
        
        backup_data = {
            'package': package_name,
            'timestamp': timestamp,
            'action': 'installed'
        }
        
        try:
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            return backup_file
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return None
    
    def list_packages(self) -> None:
        """List all available packages and their installation status."""
        print(self._color("Available CLI tools:", 'blue'))
        print()
        
        for package in self.PACKAGES:
            if self._is_package_installed(package):
                status = self._color("✓ installed", 'green')
            else:
                status = self._color("✗ not installed", 'yellow')
            
            print(f"  {package.name:<15} {status} - {package.description}")
        print()
    
    def install_package(self, package: Package) -> bool:
        """Install a single package."""
        print(f"{self._color(f'Installing {package.name}...', 'blue')}  {package.description}")
        
        if self.dry_run:
            print(f"  DRY RUN: Would run 'paru -S --noconfirm {package.name}'")
            return True
        
        # Run installation
        success, output = self._run_command(['paru', '-S', '--noconfirm', package.name])
        
        if success:
            print(f"  {self._color(f'✓ Successfully installed {package.name}', 'green')}")
            
            # Create backup entry
            self._create_backup(package.name)
            
            # Update state
            state = self._load_state()
            if package.name not in state['installed_packages']:
                state['installed_packages'].append(package.name)
            state['installation_history'].append({
                'package': package.name,
                'timestamp': datetime.now().isoformat(),
                'success': True
            })
            self._save_state(state)
            
            return True
        else:
            print(f"  {self._color(f'✗ Failed to install {package.name}', 'red')}")
            return False
    
    def install_all(self) -> bool:
        """Install all packages."""
        packages_to_install = []
        already_installed = []
        
        print(self._color("Checking package installation status...", 'blue'))
        print()
        
        # Check which packages need installation
        for package in self.PACKAGES:
            if self._is_package_installed(package):
                already_installed.append(package.name)
                print(f"  {self._color('✓', 'green')} {package.name} - already installed")
            else:
                packages_to_install.append(package)
                print(f"  {self._color('○', 'yellow')} {package.name} - needs installation")
        
        print()
        
        # Show summary
        if already_installed:
            print(f"{self._color('Already installed:', 'green')} {', '.join(already_installed)}")
        
        if not packages_to_install:
            print(self._color("All packages are already installed!", 'green'))
            return True
        
        print(f"{self._color('Packages to install:', 'yellow')} {len(packages_to_install)}")
        for package in packages_to_install:
            print(f"  - {package.name}: {package.description}")
        print()
        
        # Confirmation prompt
        if not self.force and not self.dry_run:
            response = input("Proceed with installation? (y/N): ")
            if response.lower() != 'y':
                print(self._color("Installation cancelled", 'yellow'))
                return False
        
        # Install packages
        print(self._color("Installing packages...", 'blue'))
        print()
        
        failed_packages = []
        for package in packages_to_install:
            if not self.install_package(package):
                failed_packages.append(package.name)
            print()
        
        # Final summary
        print(self._color("Installation Summary:", 'blue'))
        print(f"  Total packages: {len(self.PACKAGES)}")
        print(f"  Already installed: {len(already_installed)}")
        print(f"  Newly installed: {len(packages_to_install) - len(failed_packages)}")
        
        if failed_packages:
            print(f"  {self._color(f'Failed installations: {len(failed_packages)}', 'red')}")
            print(f"    Failed packages: {', '.join(failed_packages)}")
            return False
        else:
            print(f"  {self._color('✓ All installations successful!', 'green')}")
            return True
    
    def install_specific(self, package_name: str) -> bool:
        """Install a specific package by name."""
        for package in self.PACKAGES:
            if package.name == package_name:
                print(f"{self._color(f'Installing specific package: {package.name}', 'blue')}")
                print()
                
                if self._is_package_installed(package):
                    print(self._color(f"✓ {package.name} is already installed", 'green'))
                    return True
                
                return self.install_package(package)
        
        print(self._color(f"Error: Package '{package_name}' not found in package list", 'red'))
        print("Available packages:")
        for package in self.PACKAGES:
            print(f"  - {package.name}")
        return False
    
    def rollback(self) -> bool:
        """Rollback the last installation (uninstall recently installed packages)."""
        state = self._load_state()
        
        if not state.get('installation_history'):
            print(self._color("No installation history found", 'yellow'))
            return True
        
        # Get the last installation session
        last_session_packages = []
        last_timestamp = None
        
        for entry in reversed(state['installation_history']):
            if entry.get('success'):
                if last_timestamp is None:
                    last_timestamp = entry['timestamp']
                
                # Group packages installed in the same session (within 1 hour)
                entry_time = datetime.fromisoformat(entry['timestamp'])
                last_time = datetime.fromisoformat(last_timestamp)
                
                if abs((entry_time - last_time).total_seconds()) < 3600:
                    last_session_packages.append(entry['package'])
                else:
                    break
        
        if not last_session_packages:
            print(self._color("No packages to rollback", 'yellow'))
            return True
        
        print(self._color(f"Rolling back installation of: {', '.join(last_session_packages)}", 'blue'))
        
        if not self.force and not self.dry_run:
            response = input("Proceed with rollback? (y/N): ")
            if response.lower() != 'y':
                print(self._color("Rollback cancelled", 'yellow'))
                return False
        
        # Uninstall packages
        failed_removals = []
        for package_name in last_session_packages:
            print(f"Removing {package_name}...")
            if self.dry_run:
                print(f"  DRY RUN: Would run 'paru -R --noconfirm {package_name}'")
            else:
                success, _ = self._run_command(['paru', '-R', '--noconfirm', package_name])
                if success:
                    print(f"  {self._color(f'✓ Removed {package_name}', 'green')}")
                    
                    # Update state
                    if package_name in state['installed_packages']:
                        state['installed_packages'].remove(package_name)
                else:
                    print(f"  {self._color(f'✗ Failed to remove {package_name}', 'red')}")
                    failed_removals.append(package_name)
        
        if not self.dry_run:
            # Add rollback entry to history
            state['installation_history'].append({
                'action': 'rollback',
                'packages': last_session_packages,
                'timestamp': datetime.now().isoformat(),
                'failed': failed_removals
            })
            self._save_state(state)
        
        if failed_removals:
            print(self._color(f"Rollback completed with errors: {', '.join(failed_removals)}", 'yellow'))
            return False
        else:
            print(self._color("✓ Rollback completed successfully", 'green'))
            return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='CLI Tools Installation Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
    uv run scripts/install-cli-tools.py              # Install all packages interactively
    uv run scripts/install-cli-tools.py --dry-run    # Preview what would be installed
    uv run scripts/install-cli-tools.py --install jq # Install only jq
    uv run scripts/install-cli-tools.py --rollback   # Undo last installation session
    uv run scripts/install-cli-tools.py --force      # Install all without confirmation

EXTENDING:
    To add new packages, edit the PACKAGES list in this script:
    PACKAGES = [
        Package("new-package", "Description of the package"),
        ...
    ]
        """
    )
    
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be installed without installing')
    parser.add_argument('--list', action='store_true',
                        help='List all available packages')
    parser.add_argument('--install', metavar='PACKAGE',
                        help='Install specific package only')
    parser.add_argument('--force', action='store_true',
                        help='Skip confirmation prompts')
    parser.add_argument('--rollback', action='store_true',
                        help='Rollback the last installation session')
    
    args = parser.parse_args()
    
    # Create installer instance
    installer = CLIToolsInstaller(dry_run=args.dry_run, force=args.force)
    
    # Header
    print("=== CLI Tools Installation ===")
    print(f"Started at: {datetime.now()}")
    print()
    
    # Check prerequisites
    if not installer._check_paru():
        return 1
    
    # Handle different modes
    if args.list:
        installer.list_packages()
        return 0
    elif args.rollback:
        success = installer.rollback()
        return 0 if success else 1
    elif args.install:
        success = installer.install_specific(args.install)
        return 0 if success else 1
    else:
        success = installer.install_all()
        return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
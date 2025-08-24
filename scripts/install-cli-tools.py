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
    
    # Core packages - essential CLI tools for development
    PACKAGES = [
        Package("jq", "JSON processor for parsing Hyprland device information"),
        Package("bat", "Cat with syntax highlighting and git integration (cat will be aliased to bat)"),
        Package("yazi", "Fast terminal file manager with vim-like keybindings and preview support"),
        Package("usbutils", "USB device utilities including lsusb command for device enumeration", "lsusb"),
        Package("lazygit", "Simple terminal UI for git commands with interactive features", "lazygit"),
        Package("man-db", "Manual page reader - essential for accessing documentation", "man"),
        Package("brightnessctl", "Utility to control screen brightness for laptops"),
        Package("vivid", "LS_COLORS manager with multiple themes"),
        Package("eza", "A modern replacement for ls"),
        Package("btop", "A better top replacement"),
        Package("ripgrep", "Fast text search tool", "rg"),
        Package("fd", "Modern find replacement"),
        Package("fzf", "Fuzzy finder for command line"),
        Package("tmux", "Terminal multiplexer"),
    ]
    
    # Optional packages - additional tools that users may want
    OPTIONAL_PACKAGES = [
        Package("onedrive-abraunegg", "Microsoft OneDrive client for Linux with full sync support", "onedrive"),
        # Add more optional packages here as needed:
        # Package("dropbox", "Dropbox client for Linux"),
        # Package("rclone", "Cloud storage sync tool"),
        # Package("syncthing", "Decentralized file synchronization"),
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
    
    def list_packages(self, optionals_only: bool = False) -> None:
        """List all available packages and their installation status."""
        if optionals_only:
            print(self._color("Optional CLI tools:", 'blue'))
            print()
            
            for package in self.OPTIONAL_PACKAGES:
                if self._is_package_installed(package):
                    status = self._color("✓ installed", 'green')
                else:
                    status = self._color("✗ not installed", 'yellow')
                
                print(f"  {package.name:<20} {status} - {package.description}")
            print()
        else:
            print(self._color("Core CLI tools:", 'blue'))
            print()
            
            for package in self.PACKAGES:
                if self._is_package_installed(package):
                    status = self._color("✓ installed", 'green')
                else:
                    status = self._color("✗ not installed", 'yellow')
                
                print(f"  {package.name:<20} {status} - {package.description}")
            
            print()
            print(self._color("Optional CLI tools:", 'blue'))
            print()
            
            for package in self.OPTIONAL_PACKAGES:
                if self._is_package_installed(package):
                    status = self._color("✓ installed", 'green')
                else:
                    status = self._color("✗ not installed", 'yellow')
                
                print(f"  {package.name:<20} {status} - {package.description}")
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
        """Install all core packages and optionally install optional packages."""
        packages_to_install = []
        already_installed = []
        
        print(self._color("Checking core package installation status...", 'blue'))
        print()
        
        # Check which core packages need installation
        for package in self.PACKAGES:
            if self._is_package_installed(package):
                already_installed.append(package.name)
                print(f"  {self._color('✓', 'green')} {package.name} - already installed")
            else:
                packages_to_install.append(package)
                print(f"  {self._color('○', 'yellow')} {package.name} - needs installation")
        
        print()
        
        # Show core package summary
        if already_installed:
            print(f"{self._color('Already installed:', 'green')} {', '.join(already_installed)}")
        
        core_success = True
        if packages_to_install:
            print(f"{self._color('Core packages to install:', 'yellow')} {len(packages_to_install)}")
            for package in packages_to_install:
                print(f"  - {package.name}: {package.description}")
            print()
            
            # Confirmation prompt for core packages
            if not self.force and not self.dry_run:
                response = input("Proceed with core package installation? (y/N): ")
                if response.lower() != 'y':
                    print(self._color("Core installation cancelled", 'yellow'))
                    return False
            
            # Install core packages
            print(self._color("Installing core packages...", 'blue'))
            print()
            
            failed_packages = []
            for package in packages_to_install:
                if not self.install_package(package):
                    failed_packages.append(package.name)
                print()
            
            # Core installation summary
            print(self._color("Core Installation Summary:", 'blue'))
            print(f"  Total core packages: {len(self.PACKAGES)}")
            print(f"  Already installed: {len(already_installed)}")
            print(f"  Newly installed: {len(packages_to_install) - len(failed_packages)}")
            
            if failed_packages:
                print(f"  {self._color(f'Failed installations: {len(failed_packages)}', 'red')}")
                print(f"    Failed packages: {', '.join(failed_packages)}")
                core_success = False
            else:
                print(f"  {self._color('✓ All core installations successful!', 'green')}")
            
            print()
        else:
            print(self._color("All core packages are already installed!", 'green'))
            print()
        
        # Check and prompt for optional packages
        optional_packages_to_install = []
        optional_already_installed = []
        
        print(self._color("Checking optional packages...", 'blue'))
        for package in self.OPTIONAL_PACKAGES:
            if self._is_package_installed(package):
                optional_already_installed.append(package.name)
            else:
                optional_packages_to_install.append(package)
        
        if optional_packages_to_install:
            print(f"Found {len(optional_packages_to_install)} optional package(s) available:")
            for package in optional_packages_to_install:
                print(f"  - {package.name}: {package.description}")
            print()
            
            if not self.force and not self.dry_run:
                print("How would you like to handle optional packages?")
                print("  a) Install ALL optional packages")
                print("  s) Select individual packages to install")
                print("  n) Skip optional packages")
                response = input("Choose option (a/s/N): ").lower()
                
                if response == 'a':
                    # Install all optional packages
                    optional_success = self._install_optional_packages_internal(optional_packages_to_install, optional_already_installed)
                    return core_success and optional_success
                elif response == 's':
                    # Select individual packages
                    selected_packages = []
                    print()
                    print(self._color("Select packages to install (press Enter to skip):", 'blue'))
                    for package in optional_packages_to_install:
                        choice = input(f"Install {package.name}? ({package.description}) (y/N): ")
                        if choice.lower() == 'y':
                            selected_packages.append(package)
                    
                    if selected_packages:
                        print()
                        print(f"Selected {len(selected_packages)} package(s) for installation:")
                        for package in selected_packages:
                            print(f"  - {package.name}")
                        
                        optional_success = self._install_optional_packages_internal(selected_packages, optional_already_installed)
                        return core_success and optional_success
                    else:
                        print(self._color("No optional packages selected", 'yellow'))
                else:
                    print(self._color("Optional packages skipped", 'yellow'))
            elif self.dry_run or self.force:
                # In dry-run or force mode, show what would happen but don't auto-install
                print(self._color("Optional packages available but not auto-installed", 'blue'))
                print("Use --optionals flag to install them explicitly")
        elif optional_already_installed:
            print(self._color(f"All optional packages already installed: {', '.join(optional_already_installed)}", 'green'))
        else:
            print(self._color("No optional packages defined", 'blue'))
        
        return core_success
    
    def _install_optional_packages_internal(self, packages_to_install, already_installed) -> bool:
        """Internal method to install optional packages (used by install_all)."""
        print()
        print(self._color("Installing optional packages...", 'blue'))
        print()
        
        failed_packages = []
        for package in packages_to_install:
            if not self.install_package(package):
                failed_packages.append(package.name)
            print()
        
        # Optional installation summary
        print(self._color("Optional Installation Summary:", 'blue'))
        print(f"  Total optional packages: {len(self.OPTIONAL_PACKAGES)}")
        print(f"  Already installed: {len(already_installed)}")
        print(f"  Newly installed: {len(packages_to_install) - len(failed_packages)}")
        
        if failed_packages:
            print(f"  {self._color(f'Failed installations: {len(failed_packages)}', 'red')}")
            print(f"    Failed packages: {', '.join(failed_packages)}")
            return False
        else:
            print(f"  {self._color('✓ All optional installations successful!', 'green')}")
            return True
    
    def install_specific(self, package_name: str) -> bool:
        """Install a specific core package by name."""
        for package in self.PACKAGES:
            if package.name == package_name:
                print(f"{self._color(f'Installing specific core package: {package.name}', 'blue')}")
                print()
                
                if self._is_package_installed(package):
                    print(self._color(f"✓ {package.name} is already installed", 'green'))
                    return True
                
                return self.install_package(package)
        
        print(self._color(f"Error: Package '{package_name}' not found in core package list", 'red'))
        print("Available core packages:")
        for package in self.PACKAGES:
            print(f"  - {package.name}")
        return False
    
    def install_specific_optional(self, package_name: str) -> bool:
        """Install a specific optional package by name."""
        for package in self.OPTIONAL_PACKAGES:
            if package.name == package_name:
                print(f"{self._color(f'Installing specific optional package: {package.name}', 'blue')}")
                print()
                
                if self._is_package_installed(package):
                    print(self._color(f"✓ {package.name} is already installed", 'green'))
                    return True
                
                return self.install_package(package)
        
        print(self._color(f"Error: Package '{package_name}' not found in optional package list", 'red'))
        print("Available optional packages:")
        for package in self.OPTIONAL_PACKAGES:
            print(f"  - {package.name}")
        return False
    
    def install_optionals(self) -> bool:
        """Install all optional packages."""
        packages_to_install = []
        already_installed = []
        
        print(self._color("Checking optional package installation status...", 'blue'))
        print()
        
        # Check which optional packages need installation
        for package in self.OPTIONAL_PACKAGES:
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
            print(self._color("All optional packages are already installed!", 'green'))
            return True
        
        print(f"{self._color('Optional packages to install:', 'yellow')} {len(packages_to_install)}")
        for package in packages_to_install:
            print(f"  - {package.name}: {package.description}")
        print()
        
        # Confirmation prompt
        if not self.force and not self.dry_run:
            response = input("Proceed with optional package installation? (y/N): ")
            if response.lower() != 'y':
                print(self._color("Installation cancelled", 'yellow'))
                return False
        
        # Install packages
        print(self._color("Installing optional packages...", 'blue'))
        print()
        
        failed_packages = []
        for package in packages_to_install:
            if not self.install_package(package):
                failed_packages.append(package.name)
            print()
        
        # Final summary
        print(self._color("Optional Package Installation Summary:", 'blue'))
        print(f"  Total optional packages: {len(self.OPTIONAL_PACKAGES)}")
        print(f"  Already installed: {len(already_installed)}")
        print(f"  Newly installed: {len(packages_to_install) - len(failed_packages)}")
        
        if failed_packages:
            print(f"  {self._color(f'Failed installations: {len(failed_packages)}', 'red')}")
            print(f"    Failed packages: {', '.join(failed_packages)}")
            return False
        else:
            print(f"  {self._color('✓ All optional installations successful!', 'green')}")
            return True
    
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
    uv run scripts/install-cli-tools.py                       # Install core packages + prompt for optionals
    uv run scripts/install-cli-tools.py --optionals          # Install all optional packages interactively  
    uv run scripts/install-cli-tools.py --dry-run            # Preview what would be installed
    uv run scripts/install-cli-tools.py --list               # List all packages (core and optional)
    uv run scripts/install-cli-tools.py --list-optionals     # List only optional packages
    uv run scripts/install-cli-tools.py --install jq         # Install only jq (core package)
    uv run scripts/install-cli-tools.py --install-optional onedrive-abraunegg  # Install OneDrive
    uv run scripts/install-cli-tools.py --rollback           # Undo last installation session
    uv run scripts/install-cli-tools.py --force              # Install all without confirmation

EXTENDING:
    To add new core packages, edit the PACKAGES list:
    PACKAGES = [
        Package("new-package", "Description of the package"),
        ...
    ]
    
    To add new optional packages, edit the OPTIONAL_PACKAGES list:
    OPTIONAL_PACKAGES = [
        Package("new-optional", "Description of the optional package"),
        ...
    ]
        """
    )
    
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be installed without installing')
    parser.add_argument('--list', action='store_true',
                        help='List all available packages (both core and optional)')
    parser.add_argument('--list-optionals', action='store_true',
                        help='List only optional packages')
    parser.add_argument('--install', metavar='PACKAGE',
                        help='Install specific core package only')
    parser.add_argument('--install-optional', metavar='PACKAGE',
                        help='Install specific optional package only')
    parser.add_argument('--optionals', action='store_true',
                        help='Install all optional packages')
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
    elif args.list_optionals:
        installer.list_packages(optionals_only=True)
        return 0
    elif args.rollback:
        success = installer.rollback()
        return 0 if success else 1
    elif args.install:
        success = installer.install_specific(args.install)
        return 0 if success else 1
    elif args.install_optional:
        success = installer.install_specific_optional(args.install_optional)
        return 0 if success else 1
    elif args.optionals:
        success = installer.install_optionals()
        return 0 if success else 1
    else:
        success = installer.install_all()
        return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())

"""
Font Setup Script for Arch Linux

This script automates font installation and configuration, including Apple fonts
and high-quality alternatives. It sets up fontconfig and terminal configurations.

Usage:
    uv run setup_fonts.py [--dry-run] [--rollback] [--option N] [--help]
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
from typing import Dict, List, Optional, Tuple


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


class FontSetup:
    """Main class for font installation and configuration."""
    
    def __init__(self, repo_root: Path, dry_run: bool = False):
        self.repo_root = repo_root
        self.dry_run = dry_run
        self.config_dir = Path.home() / '.config'
        self.backup_dir = Path.home() / '.local' / 'share' / 'arch_dotfiles' / 'backups'
        self.state_file = Path.home() / '.local' / 'share' / 'arch_dotfiles' / 'font_setup_state.json'
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Configuration files to link
        self.link_map = {
            'fontconfig': {
                'source': self.repo_root / 'config' / 'fontconfig',
                'target': self.config_dir / 'fontconfig'
            },
            'kitty': {
                'source': self.repo_root / 'config' / 'kitty' / 'kitty.conf',
                'target': self.config_dir / 'kitty' / 'kitty.conf'
            }
        }
        
        # Font packages by option
        self.font_packages = {
            'apple': {
                'aur': [
                    'otf-san-francisco',
                    'otf-apple-sf-pro',
                    'otf-apple-sf-mono',
                    'nerd-fonts-sf-mono'
                ],
                'official': []
            },
            'alternatives': {
                'official': [
                    'inter-font',
                    'ttf-ibm-plex',
                    'ttf-jetbrains-mono'
                ],
                'aur': [
                    'ttf-jetbrains-mono-nerd'
                ]
            },
            'essential': {
                'official': [
                    'ttf-liberation',
                    'ttf-dejavu',
                    'noto-fonts',
                    'noto-fonts-emoji',
                    'ttf-font-awesome'
                ],
                'aur': []
            },
            'developer': {
                'official': [
                    'ttf-fira-code',
                    'ttf-hack'
                ],
                'aur': []
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
    
    def print_info(self, message: str) -> None:
        """Print info message."""
        self.print_colored(f"ℹ {message}", Colors.BLUE)
    
    def show_menu(self) -> int:
        """Display installation options menu."""
        self.print_colored("\n╔════════════════════════════════════════════╗", Colors.MAGENTA)
        self.print_colored("║         Font Installation Options          ║", Colors.MAGENTA)
        self.print_colored("╚════════════════════════════════════════════╝", Colors.MAGENTA)
        
        options = [
            ("Apple Fonts (SF Pro, SF Mono)", "Requires AUR, best macOS compatibility"),
            ("Open Source Alternatives", "Inter, IBM Plex - from official repos"),
            ("Both Apple + Alternatives", "Apple as primary, alternatives as fallback"),
            ("Complete Package", "All fonts including developer fonts"),
            ("Minimal Essential", "Just icons, emoji, and basic fonts")
        ]
        
        for i, (name, desc) in enumerate(options, 1):
            self.print_colored(f"\n  {i}. {name}", Colors.CYAN, bold=True)
            self.print_colored(f"     {desc}", Colors.WHITE)
        
        self.print_colored("\n" + "─" * 48, Colors.MAGENTA)
        
        while True:
            try:
                choice = input(f"\n{Colors.YELLOW}Select option [1-5]: {Colors.RESET}")
                choice_num = int(choice)
                if 1 <= choice_num <= 5:
                    return choice_num
                else:
                    self.print_error("Please enter a number between 1 and 5")
            except ValueError:
                self.print_error("Please enter a valid number")
    
    def get_packages_for_option(self, option: int) -> Tuple[List[str], List[str]]:
        """Get package lists based on selected option."""
        official = []
        aur = []
        
        # Always include essential packages
        official.extend(self.font_packages['essential']['official'])
        aur.extend(self.font_packages['essential']['aur'])
        
        if option == 1:  # Apple fonts
            aur.extend(self.font_packages['apple']['aur'])
        elif option == 2:  # Alternatives
            official.extend(self.font_packages['alternatives']['official'])
            aur.extend(self.font_packages['alternatives']['aur'])
        elif option == 3:  # Both
            aur.extend(self.font_packages['apple']['aur'])
            official.extend(self.font_packages['alternatives']['official'])
            aur.extend(self.font_packages['alternatives']['aur'])
        elif option == 4:  # Complete
            aur.extend(self.font_packages['apple']['aur'])
            official.extend(self.font_packages['alternatives']['official'])
            aur.extend(self.font_packages['alternatives']['aur'])
            official.extend(self.font_packages['developer']['official'])
            aur.extend(self.font_packages['developer']['aur'])
        # option 5 (minimal) only gets essentials, which are already added
        
        return (list(set(official)), list(set(aur)))  # Remove duplicates
    
    def check_installed_packages(self, packages: List[str]) -> List[str]:
        """Check which packages are already installed."""
        installed = []
        for package in packages:
            try:
                result = subprocess.run(
                    ['pacman', '-Q', package],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    installed.append(package)
            except Exception:
                pass
        return installed
    
    def install_packages(self, official: List[str], aur: List[str]) -> bool:
        """Install font packages."""
        self.print_step("Installing font packages")
        
        # Check what's already installed
        all_packages = official + aur
        installed = self.check_installed_packages(all_packages)
        
        official_to_install = [p for p in official if p not in installed]
        aur_to_install = [p for p in aur if p not in installed]
        
        if not official_to_install and not aur_to_install:
            self.print_success("All font packages are already installed")
            return True
        
        # Install official packages
        if official_to_install:
            self.print_info(f"Installing from official repos: {', '.join(official_to_install)}")
            if not self.dry_run:
                cmd = ['sudo', 'pacman', '-S', '--noconfirm'] + official_to_install
                try:
                    result = subprocess.run(cmd, check=True)
                    self.print_success(f"Installed {len(official_to_install)} official packages")
                except subprocess.CalledProcessError as e:
                    self.print_error(f"Failed to install official packages: {e}")
                    return False
            else:
                self.print_info("[DRY RUN] Would install official packages")
        
        # Install AUR packages
        if aur_to_install:
            self.print_info(f"Installing from AUR: {', '.join(aur_to_install)}")
            if not self.dry_run:
                for package in aur_to_install:
                    self.print_info(f"Installing {package}...")
                    cmd = ['paru', '-S', '--noconfirm', package]
                    try:
                        result = subprocess.run(cmd, check=True)
                        self.print_success(f"Installed {package}")
                    except subprocess.CalledProcessError as e:
                        self.print_warning(f"Failed to install {package}: {e}")
                        # Continue with other packages
            else:
                self.print_info("[DRY RUN] Would install AUR packages")
        
        return True
    
    def ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self.print_step("Creating necessary directories")
        
        directories = [
            self.backup_dir,
            self.state_file.parent,
            self.config_dir / 'fontconfig',
            self.config_dir / 'kitty'
        ]
        
        for directory in directories:
            if not self.dry_run:
                directory.mkdir(parents=True, exist_ok=True)
            self.print_info(f"  Ensured: {directory}")
    
    def backup_existing_config(self) -> Dict[str, str]:
        """Backup existing configuration files."""
        self.print_step("Backing up existing configuration")
        
        backup_info = {}
        
        for name, paths in self.link_map.items():
            target_path = paths['target']
            
            if target_path.exists():
                backup_name = f"{name}_{target_path.name}.backup.{self.timestamp}"
                backup_path = self.backup_dir / backup_name
                backup_info[str(target_path)] = str(backup_path)
                
                if not self.dry_run:
                    if target_path.is_dir():
                        shutil.copytree(target_path, backup_path)
                    else:
                        shutil.copy2(target_path, backup_path)
                
                self.print_info(f"  Backed up: {target_path.name} → {backup_path.name}")
        
        return backup_info
    
    def create_symlinks(self) -> bool:
        """Create symlinks for configuration files."""
        self.print_step("Creating configuration symlinks")
        
        for name, paths in self.link_map.items():
            source = paths['source']
            target = paths['target']
            
            # Skip if source doesn't exist
            if not source.exists():
                self.print_warning(f"  Source not found: {source}")
                continue
            
            # Remove existing target if it exists
            if target.exists():
                if not self.dry_run:
                    if target.is_symlink() or target.is_file():
                        target.unlink()
                    elif target.is_dir():
                        shutil.rmtree(target)
                self.print_info(f"  Removed existing: {target}")
            
            # Create parent directory if needed
            if not self.dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
            
            # Create symlink
            if not self.dry_run:
                target.symlink_to(source)
            
            self.print_success(f"  Linked: {name} → {target}")
        
        return True
    
    def update_font_cache(self) -> None:
        """Update the font cache."""
        self.print_step("Updating font cache")
        
        if not self.dry_run:
            try:
                subprocess.run(['fc-cache', '-fv'], check=True, capture_output=True)
                self.print_success("Font cache updated successfully")
            except subprocess.CalledProcessError as e:
                self.print_warning(f"Failed to update font cache: {e}")
        else:
            self.print_info("[DRY RUN] Would update font cache")
    
    def save_state(self, backup_info: Dict[str, str], option: int) -> None:
        """Save setup state for rollback."""
        state = {
            'timestamp': self.timestamp,
            'backup_info': backup_info,
            'option': option,
            'link_map': {k: str(v['target']) for k, v in self.link_map.items()}
        }
        
        if not self.dry_run:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        
        self.print_info(f"State saved to: {self.state_file}")
    
    def setup(self, option: Optional[int] = None) -> bool:
        """Main setup process."""
        self.print_colored("\n🔤 Font Setup Process Started", Colors.GREEN, bold=True)
        
        # Get installation option
        if option is None:
            option = self.show_menu()
        
        option_names = ["Apple Fonts", "Alternatives", "Both", "Complete", "Minimal"]
        self.print_info(f"Selected: {option_names[option-1]}")
        
        # Get package lists
        official, aur = self.get_packages_for_option(option)
        
        # Show what will be installed
        self.print_colored("\nPackages to install:", Colors.YELLOW)
        if official:
            self.print_info(f"Official: {', '.join(official)}")
        if aur:
            self.print_info(f"AUR: {', '.join(aur)}")
        
        if self.dry_run:
            self.print_warning("\n[DRY RUN MODE] No changes will be made")
        
        # Create directories
        self.ensure_directories()
        
        # Backup existing configs
        backup_info = self.backup_existing_config()
        
        # Install packages
        if not self.install_packages(official, aur):
            self.print_error("Package installation failed")
            return False
        
        # Create symlinks
        if not self.create_symlinks():
            self.print_error("Failed to create configuration symlinks")
            return False
        
        # Update font cache
        self.update_font_cache()
        
        # Save state
        self.save_state(backup_info, option)
        
        self.print_colored("\n✨ Font setup completed successfully!", Colors.GREEN, bold=True)
        self.print_info("\nNext steps:")
        self.print_info("  1. Restart your terminal to see font changes")
        self.print_info("  2. Reload waybar if running: pkill waybar && waybar &")
        self.print_info("  3. Test fonts: fc-match monospace")
        
        return True
    
    def rollback(self) -> bool:
        """Rollback to previous configuration."""
        self.print_colored("\n🔄 Starting rollback process", Colors.YELLOW, bold=True)
        
        if not self.state_file.exists():
            self.print_error("No previous state found for rollback")
            return False
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
        except Exception as e:
            self.print_error(f"Failed to read state file: {e}")
            return False
        
        backup_info = state.get('backup_info', {})
        link_map = state.get('link_map', {})
        
        # Remove current symlinks
        self.print_step("Removing current configuration")
        for name, target_str in link_map.items():
            target = Path(target_str)
            if target.exists() and target.is_symlink():
                if not self.dry_run:
                    target.unlink()
                self.print_info(f"  Removed: {target}")
        
        # Restore backups
        self.print_step("Restoring previous configuration")
        for original_str, backup_str in backup_info.items():
            original = Path(original_str)
            backup = Path(backup_str)
            
            if backup.exists():
                if not self.dry_run:
                    if backup.is_dir():
                        shutil.copytree(backup, original, dirs_exist_ok=True)
                    else:
                        shutil.copy2(backup, original)
                self.print_success(f"  Restored: {original.name}")
        
        # Update font cache
        self.update_font_cache()
        
        self.print_colored("\n✓ Rollback completed successfully", Colors.GREEN, bold=True)
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Setup fonts for Arch Linux with Apple fonts and alternatives'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without making them'
    )
    parser.add_argument(
        '--rollback',
        action='store_true',
        help='Rollback to previous configuration'
    )
    parser.add_argument(
        '--option',
        type=int,
        choices=[1, 2, 3, 4, 5],
        help='Select installation option directly (1-5)'
    )
    
    args = parser.parse_args()
    
    # Determine repository root
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent
    
    # Verify we're in the right place
    if not (repo_root / 'config').exists():
        print(f"{Colors.RED}Error: config directory not found. "
              f"Please run from the arch_dotfiles repository.{Colors.RESET}")
        sys.exit(1)
    
    # Create setup instance
    setup = FontSetup(repo_root, dry_run=args.dry_run)
    
    # Execute requested action
    if args.rollback:
        success = setup.rollback()
    else:
        success = setup.setup(option=args.option)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
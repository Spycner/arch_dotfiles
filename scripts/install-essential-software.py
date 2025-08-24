#!/usr/bin/env python3
"""
Essential Software Installation Script

Installs essential software, like browser, spotify, obsidian etc. that I need for my daily tasks.
Designed to be easily extensible with additional packages.

Usage:
    uv run scripts/install-essential-software.py [options]
"""

# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Color output functions
def red(text): return f"\033[31m{text}\033[0m"
def green(text): return f"\033[32m{text}\033[0m"
def yellow(text): return f"\033[33m{text}\033[0m"
def blue(text): return f"\033[34m{text}\033[0m"

class EssentialSoftwareInstaller:
    def __init__(self, dry_run=False, skip_aur=False):
        self.dry_run = dry_run
        self.skip_aur = skip_aur
        self.state_dir = Path.home() / ".local" / "share" / "arch_dotfiles"
        self.state_file = self.state_dir / "essential_software_state.json"
        
        # Essential packages from official repositories
        self.official_packages = [
            # Add official repo packages here when needed
        ]
        
        # AUR packages
        self.aur_packages = [
            "vivaldi",  # Vivaldi browser
            "qt5-wayland", # Required by wayland
            "qt6-wayland", # Also required by wayland
            "obsidian-bin", # Notetaking
        ]
    
    def ensure_directories(self):
        """Create necessary directories"""
        if not self.dry_run:
            self.state_dir.mkdir(parents=True, exist_ok=True)
        elif not self.state_dir.exists():
            print(f"{yellow('[DRY RUN]')} Would create directory: {self.state_dir}")
    
    def load_state(self):
        """Load installation state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except:
                return {"installed_official": [], "installed_aur": []}
        return {"installed_official": [], "installed_aur": []}
    
    def save_state(self, state):
        """Save installation state"""
        if not self.dry_run:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
    
    def check_package_installed(self, package):
        """Check if a package is already installed"""
        try:
            result = subprocess.run(['pacman', '-Q', package], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def install_official_package(self, package):
        """Install package from official repositories"""
        if self.check_package_installed(package):
            print(f"{blue('○')} Already installed: {package}")
            return True
        
        if self.dry_run:
            print(f"{yellow('[DRY RUN]')} Would install: {package}")
            return True
        
        print(f"{blue('→')} Installing {package}...")
        try:
            result = subprocess.run(['sudo', 'pacman', '-S', '--noconfirm', package],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"{green('✓')} Installed: {package}")
                return True
            else:
                print(f"{red('✗')} Failed to install {package}: {result.stderr}")
                return False
        except Exception as e:
            print(f"{red('✗')} Error installing {package}: {e}")
            return False
    
    def install_aur_package(self, package):
        """Install package from AUR using paru"""
        if self.check_package_installed(package):
            print(f"{blue('○')} Already installed: {package}")
            return True
        
        if self.dry_run:
            print(f"{yellow('[DRY RUN]')} Would install AUR package: {package}")
            return True
        
        # Check if paru is available
        try:
            subprocess.run(['which', 'paru'], capture_output=True, check=True)
        except subprocess.CalledProcessError:
            print(f"{red('✗')} paru not found. Please install paru AUR helper first.")
            return False
        
        print(f"{blue('→')} Installing AUR package {package}...")
        try:
            result = subprocess.run(['paru', '-S', '--noconfirm', package],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"{green('✓')} Installed AUR package: {package}")
                return True
            else:
                print(f"{red('✗')} Failed to install AUR package {package}: {result.stderr}")
                return False
        except Exception as e:
            print(f"{red('✗')} Error installing AUR package {package}: {e}")
            return False
    
    def install_packages(self):
        """Install all essential packages"""
        state = self.load_state()
        
        print(f"{blue('===')} Installing Essential Software {blue('===')}") 
        print()
        
        # Install official packages
        successful_official = []
        if self.official_packages:
            print(f"{blue('→')} Installing official repository packages...")
            for package in self.official_packages:
                if self.install_official_package(package):
                    if package not in state["installed_official"]:
                        successful_official.append(package)
        
        # Install AUR packages
        successful_aur = []
        if not self.skip_aur and self.aur_packages:
            if self.official_packages:
                print()
            print(f"{blue('→')} Installing AUR packages...")
            for package in self.aur_packages:
                if self.install_aur_package(package):
                    if package not in state["installed_aur"]:
                        successful_aur.append(package)
        elif self.skip_aur:
            print(f"{yellow('!')} Skipping AUR packages (--skip-aur flag used)")
        
        # Update state
        state["installed_official"].extend(successful_official)
        state["installed_aur"].extend(successful_aur)
        state["last_run"] = datetime.now().isoformat()
        
        self.save_state(state)
        
        print()
        print(f"{green('✓')} Installation complete!")
        if successful_official:
            print(f"  Official packages installed: {len(successful_official)}")
        if successful_aur:
            print(f"  AUR packages installed: {len(successful_aur)}")

def main():
    parser = argparse.ArgumentParser(description="Install essential software packages")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be installed without installing")
    parser.add_argument("--skip-aur", action="store_true",
                       help="Skip AUR packages, install only official repo packages")
    
    args = parser.parse_args()
    
    if args.dry_run:
        print(f"{yellow('DRY RUN MODE:')} No packages will be installed")
        print()
    
    installer = EssentialSoftwareInstaller(dry_run=args.dry_run, skip_aur=args.skip_aur)
    
    try:
        installer.ensure_directories()
        installer.install_packages()
    except KeyboardInterrupt:
        print(f"\n{yellow('!')} Installation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n{red('✗')} Installation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

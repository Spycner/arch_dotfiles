#!/usr/bin/env python3
"""
Setup DisplayLink DKMS drivers for USB-C docking station multi-monitor support

This script installs DisplayLink drivers using paru for:
- USB-C docking station multi-monitor support via DisplayLink
- EVDI DKMS kernel module for Enhanced Virtual Display Interface
- Automatic kernel update compatibility through DKMS

Requirements:
- paru (AUR helper) must be installed
- Internet connection for package downloads

Usage:
    uv run scripts/setup-docking-station.py [options]
    
Options:
    --dry-run           Preview what would be installed without making changes
    --skip-aur          Skip AUR packages (install only build dependencies)
    --help              Show this help message
"""

# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Tuple

# ANSI color codes
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
MAGENTA = '\033[0;35m'
CYAN = '\033[0;36m'
WHITE = '\033[1;37m'
RESET = '\033[0m'

class DisplayLinkSetup:
    """Setup DisplayLink drivers for USB docking station support"""
    
    def __init__(self, dry_run: bool = False, skip_aur: bool = False):
        self.dry_run = dry_run
        self.skip_aur = skip_aur
        self.kernel_variant = self.detect_kernel_variant()
        
        # All packages can be installed via paru (handles both official repos and AUR)
        self.packages = [
            # Build dependencies first
            'base-devel',           # Build tools required for DKMS
            'dkms',                 # Dynamic Kernel Module Support
            self.get_kernel_headers(),  # Kernel headers for current kernel
            # DisplayLink DKMS drivers
            'evdi-dkms',           # DKMS version of EVDI (Enhanced Virtual Display Interface)  
            'displaylink'          # Official DisplayLink driver
        ]
    
    def detect_kernel_variant(self) -> str:
        """Detect which kernel variant is currently running"""
        try:
            result = subprocess.run(['uname', '-r'], capture_output=True, text=True, check=True)
            kernel_release = result.stdout.strip()
            
            if 'lts' in kernel_release:
                return 'linux-lts'
            elif 'hardened' in kernel_release:
                return 'linux-hardened' 
            elif 'zen' in kernel_release:
                return 'linux-zen'
            else:
                return 'linux'
        except subprocess.CalledProcessError:
            return 'linux'  # Default fallback
    
    def get_kernel_headers(self) -> str:
        """Get the appropriate kernel headers package for current kernel"""
        return f'{self.kernel_variant}-headers'
    
    def check_command(self, command: str) -> bool:
        """Check if a command is available"""
        try:
            subprocess.run(['which', command], 
                         capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def run_command(self, cmd: List[str]) -> Tuple[bool, str]:
        """Run a command and return success status and output"""
        if self.dry_run:
            print(f"{CYAN}[DRY RUN] Would execute: {' '.join(cmd)}{RESET}")
            return True, ""
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr
    
    def install_packages(self, packages: List[str]) -> bool:
        """Install packages using paru (handles both official repos and AUR)"""
        if not packages:
            return True
        
        flags = '-S --noconfirm' if not self.dry_run else '-S --print'
        cmd = ['paru'] + flags.split() + packages
        
        print(f"{BLUE}Installing packages: {', '.join(packages)}{RESET}")
        success, output = self.run_command(cmd)
        
        if not success and not self.dry_run:
            print(f"{RED}Failed to install packages{RESET}")
            print(output)
            return False
        
        return True
    
    def check_dkms_module(self, module_name: str) -> Tuple[bool, str]:
        """Check DKMS module status"""
        if self.dry_run:
            return True, "dry-run"
        
        try:
            result = subprocess.run(['dkms', 'status', module_name], 
                                  capture_output=True, text=True, check=True)
            return True, result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return False, e.stderr.strip()
    
    def build_and_verify_dkms(self) -> bool:
        """Build and verify DKMS modules are properly installed and built"""
        print(f"\n{YELLOW}Building and verifying DKMS modules...{RESET}")
        
        if self.dry_run:
            print(f"{CYAN}[DRY RUN] Would build and verify DKMS modules{RESET}")
            return True
        
        kernel_version = subprocess.run(['uname', '-r'], capture_output=True, text=True, check=True).stdout.strip()
        
        # Build evdi DKMS module for current kernel
        print(f"{BLUE}Building evdi module for kernel {kernel_version}...{RESET}")
        try:
            result = subprocess.run(['sudo', 'dkms', 'install', 'evdi/1.14.10', '-k', kernel_version], 
                                  capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print(f"{GREEN}EVDI DKMS module built successfully{RESET}")
            else:
                # Module might already be built, check status
                if 'already installed' in result.stderr:
                    print(f"{GREEN}EVDI DKMS module already installed{RESET}")
                else:
                    print(f"{YELLOW}DKMS build output: {result.stderr}{RESET}")
        except subprocess.TimeoutExpired:
            print(f"{RED}DKMS build timed out after 5 minutes{RESET}")
            return False
        except subprocess.CalledProcessError as e:
            print(f"{YELLOW}DKMS build warning: {e.stderr}{RESET}")
        
        # Verify DKMS status
        success, output = self.check_dkms_module('evdi')
        if success and output:
            print(f"{GREEN}EVDI DKMS status: {output}{RESET}")
        else:
            print(f"{YELLOW}EVDI DKMS status check failed, but module may still work{RESET}")
        
        # Test if evdi module can be loaded
        print(f"{BLUE}Testing evdi kernel module loading...{RESET}")
        try:
            # Try to load the module
            result = subprocess.run(['sudo', 'modprobe', 'evdi'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"{GREEN}evdi kernel module loaded successfully{RESET}")
                # Unload it for now (DisplayLink service will load it when needed)
                subprocess.run(['sudo', 'modprobe', '-r', 'evdi'], capture_output=True)
                return True
            else:
                print(f"{RED}Failed to load evdi module: {result.stderr.strip()}{RESET}")
                print(f"{YELLOW}This may be resolved after a reboot{RESET}")
                return False
        except subprocess.CalledProcessError as e:
            print(f"{RED}Error testing evdi module: {e.stderr}{RESET}")
            return False
    
    def detect_display_server(self) -> str:
        """Detect if running Xorg or Wayland"""
        if self.dry_run:
            return "unknown"
        
        # Check for Wayland
        if os.environ.get('WAYLAND_DISPLAY'):
            return "wayland"
        
        # Check for Xorg
        if os.environ.get('DISPLAY'):
            return "xorg"
        
        return "unknown"
    
    def create_xorg_config(self):
        """Create Xorg configuration for DisplayLink if needed"""
        display_server = self.detect_display_server()
        
        if display_server != "xorg":
            return  # Skip Xorg config for Wayland or unknown
        
        config_dir = Path('/etc/X11/xorg.conf.d/')
        config_file = config_dir / '20-displaylink.conf'
        
        if self.dry_run:
            print(f"{CYAN}[DRY RUN] Would create Xorg config at {config_file}{RESET}")
            return
        
        xorg_config = '''Section "OutputClass"
    Identifier "DisplayLink"
    MatchDriver "evdi"
    Driver "modesetting"
    Option "AccelMethod" "none"
EndSection
'''
        
        try:
            if not config_file.exists():
                subprocess.run(['sudo', 'mkdir', '-p', str(config_dir)])
                with open('/tmp/20-displaylink.conf', 'w') as f:
                    f.write(xorg_config)
                subprocess.run(['sudo', 'mv', '/tmp/20-displaylink.conf', str(config_file)])
                print(f"{GREEN}Created Xorg DisplayLink configuration{RESET}")
            else:
                print(f"{YELLOW}Xorg DisplayLink config already exists{RESET}")
        except Exception as e:
            print(f"{YELLOW}Warning: Could not create Xorg config: {e}{RESET}")
    
    def setup_displaylink(self):
        """Setup DisplayLink driver and service"""
        print(f"\n{YELLOW}Setting up DisplayLink driver...{RESET}")
        
        if self.dry_run:
            print(f"{CYAN}[DRY RUN] Would enable displaylink.service{RESET}")
            print(f"{CYAN}[DRY RUN] Would test evdi kernel module{RESET}")
            return
        
        # Enable DisplayLink service (don't start yet if evdi module isn't working)
        print(f"{BLUE}Enabling DisplayLink service...{RESET}")
        subprocess.run(['sudo', 'systemctl', 'enable', 'displaylink.service'], capture_output=True)
        
        # Test if evdi module can be loaded
        print(f"{BLUE}Testing evdi kernel module...{RESET}")
        result = subprocess.run(['sudo', 'modprobe', 'evdi'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"{GREEN}evdi module loaded successfully{RESET}")
            # Start the service since module works
            start_result = subprocess.run(['sudo', 'systemctl', 'start', 'displaylink.service'], 
                                        capture_output=True, text=True)
            if start_result.returncode == 0:
                print(f"{GREEN}DisplayLink service started successfully{RESET}")
            else:
                print(f"{YELLOW}DisplayLink service enabled but failed to start{RESET}")
                print(f"{YELLOW}Check service status with: systemctl status displaylink{RESET}")
        else:
            print(f"{YELLOW}evdi module failed to load: {result.stderr.strip()}{RESET}")
            print(f"{YELLOW}DisplayLink service enabled but not started{RESET}")
            print(f"{YELLOW}Reboot required to activate DKMS module{RESET}")
        
        print(f"{GREEN}DisplayLink driver setup complete{RESET}")
    
    def create_udev_rule(self):
        """Create DisplayLink udev rule template"""
        config_dir = Path.home() / '.config' / 'displaylink'
        
        if self.dry_run:
            print(f"{CYAN}[DRY RUN] Would create udev rule template in {config_dir}{RESET}")
            return
        
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # DisplayLink USB device rules template
        udev_rules = """# DisplayLink USB Graphics Adapters
# Copy this file to /etc/udev/rules.d/99-displaylink.rules
# Then run: sudo udevadm control --reload-rules

ATTR{idVendor}=="17e9", ATTR{bInterfaceClass}=="ff", ATTR{bInterfaceProtocol}=="03", MODE="0660", GROUP="video", ENV{ID_DISPLAYLINK}="1"
"""
        
        udev_file = config_dir / '99-displaylink.rules.template'
        udev_file.write_text(udev_rules)
        
        print(f"{GREEN}DisplayLink udev rule template created in {config_dir}{RESET}")
    
    def print_post_install_instructions(self):
        """Print post-installation instructions"""
        print(f"\n{GREEN}{'='*60}{RESET}")
        print(f"{GREEN}DisplayLink Installation Complete!{RESET}")
        print(f"{GREEN}{'='*60}{RESET}\n")
        
        print(f"{YELLOW}Post-Installation Steps:{RESET}\n")
        
        print(f"{BLUE}1. Reboot Required:{RESET}")
        print(f"   - Reboot to load the evdi kernel module")
        print(f"   - DisplayLink service should auto-start\n")
        
        print(f"{BLUE}2. Verify Installation:{RESET}")
        print(f"   - Check DisplayLink status: systemctl status displaylink")
        print(f"   - View logs: journalctl -u displaylink")
        print(f"   - Check DKMS module: dkms status evdi")
        print(f"   - Test module loading: sudo modprobe evdi")
        print(f"   - List USB devices: lsusb | grep -i display\n")
        
        print(f"{BLUE}3. Connect Docking Station:{RESET}")
        print(f"   - Plug in your USB-C docking station")
        print(f"   - Connect monitors to the docking station")
        print(f"   - Displays should be detected automatically\n")
        
        print(f"{BLUE}4. Configure Displays (Hyprland):{RESET}")
        print(f"   - List displays: hyprctl monitors")
        print(f"   - Configure in Hyprland config or use wlr-randr")
        print(f"   - Example: wlr-randr --output DP-1 --mode 1920x1080\n")
        
        print(f"{MAGENTA}Udev rule template saved in:{RESET}")
        print(f"  ~/.config/displaylink/99-displaylink.rules.template\n")
        
        print(f"{MAGENTA}Troubleshooting:{RESET}")
        print(f"  If evdi module fails to load:")
        print(f"  - sudo dkms install evdi/1.14.10 -k $(uname -r)")
        print(f"  - sudo systemctl restart displaylink")
        print(f"  - Check logs: journalctl -u displaylink\n")
        
        print(f"{CYAN}Useful Commands:{RESET}")
        print(f"  lsusb                         # List USB devices")
        print(f"  dkms status evdi              # Check EVDI DKMS module status")
        print(f"  hyprctl monitors              # List connected displays (Hyprland)")
        print(f"  wlr-randr                     # Configure displays (Wayland)")
        print(f"  systemctl status displaylink  # Check DisplayLink service status")
        print(f"  journalctl -u displaylink     # View DisplayLink service logs")
        print(f"  modinfo evdi                  # Show EVDI kernel module info")
    
    def run(self) -> bool:
        """Run the installation process"""
        print(f"{GREEN}{'='*60}{RESET}")
        print(f"{GREEN}DisplayLink Driver Setup (DKMS-based){RESET}")
        print(f"{GREEN}{'='*60}{RESET}\n")
        
        print(f"{BLUE}Detected kernel: {self.kernel_variant}{RESET}")
        print(f"{BLUE}Kernel headers package: {self.get_kernel_headers()}{RESET}\n")
        
        if self.dry_run:
            print(f"{YELLOW}Running in DRY RUN mode - no changes will be made{RESET}\n")
        
        # Check for paru
        has_paru = self.check_command('paru')
        if not has_paru:
            print(f"{RED}Error: paru not found. Please install paru first:{RESET}")
            print(f"  sudo pacman -S --needed base-devel git")
            print(f"  git clone https://aur.archlinux.org/paru.git")
            print(f"  cd paru && makepkg -si")
            return False
        
        if self.skip_aur:
            print(f"{YELLOW}Skipping AUR packages - DisplayLink will not be fully functional{RESET}\n")
            # Install only dependencies from official repos
            deps_only = [pkg for pkg in self.packages if pkg in ['base-devel', 'dkms', self.get_kernel_headers()]]
            print(f"\n{CYAN}Installing build dependencies only...{RESET}")
            if not self.install_packages(deps_only):
                return False
            print(f"\n{YELLOW}DisplayLink drivers (evdi-dkms, displaylink) skipped{RESET}")
            return True
        
        # Install all packages with paru (handles both repos automatically)
        print(f"\n{CYAN}Installing all DisplayLink packages and dependencies...{RESET}")
        if not self.install_packages(self.packages):
            print(f"{RED}Failed to install packages{RESET}")
            return False
        
        # Build and verify DKMS installation
        if not self.build_and_verify_dkms():
            print(f"{YELLOW}Warning: DKMS module build had issues, but continuing...{RESET}")
            print(f"{YELLOW}Try rebooting after installation completes{RESET}")
        
        # Setup DisplayLink service and configuration
        self.setup_displaylink()
        
        # Create Xorg config if needed
        display_server = self.detect_display_server()
        print(f"\n{BLUE}Detected display server: {display_server}{RESET}")
        if display_server == "xorg":
            self.create_xorg_config()
        else:
            print(f"{GREEN}Wayland detected - no Xorg configuration needed{RESET}")
        
        # Create udev rule template
        if not self.dry_run:
            self.create_udev_rule()
        
        # Print post-installation instructions
        if not self.dry_run:
            self.print_post_install_instructions()
        
        return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Setup DisplayLink drivers for USB-C docking station',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview what would be installed without making changes')
    parser.add_argument('--skip-aur', action='store_true',
                       help='Skip AUR packages, only install from official repos')
    
    args = parser.parse_args()
    
    setup = DisplayLinkSetup(
        dry_run=args.dry_run,
        skip_aur=args.skip_aur
    )
    
    try:
        if setup.run():
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Installation cancelled by user{RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"{RED}Error: {e}{RESET}")
        sys.exit(1)

if __name__ == '__main__':
    main()
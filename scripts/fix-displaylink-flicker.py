#!/usr/bin/env python3
"""
DisplayLink Flicker Fix Script

Applies fixes for common DisplayLink monitor flickering issues based on diagnostic results.

Usage:
    uv run scripts/fix-displaylink-flicker.py [options]
"""
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import argparse
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
import sys

class DisplayLinkFlickerFixer:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.backup_dir = Path.home() / '.local' / 'share' / 'arch_dotfiles' / 'backups'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with color coding"""
        colors = {
            "INFO": "\033[32m",      # Green
            "WARNING": "\033[33m",   # Yellow  
            "ERROR": "\033[31m",     # Red
            "SUCCESS": "\033[92m",   # Bright Green
        }
        reset = "\033[0m"
        prefix = f"{colors.get(level, '')}{level}{reset}"
        print(f"[{prefix}] {message}")
    
    def run_command(self, command: list, description: str = "") -> tuple[bool, str]:
        """Execute command with dry-run support"""
        if self.dry_run:
            self.log(f"DRY-RUN: Would run: {' '.join(command)}")
            return True, "dry-run"
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            if description:
                self.log(f"✓ {description}")
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            self.log(f"✗ Failed {description}: {e.stderr}", "ERROR")
            return False, e.stderr
    
    def get_monitor_info(self) -> dict:
        """Get current monitor configuration"""
        try:
            result = subprocess.run(['hyprctl', 'monitors', '-j'], 
                                  capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except Exception as e:
            self.log(f"Failed to get monitor info: {e}", "ERROR")
            return []
    
    def fix_usb_power_management(self):
        """Disable USB autosuspend for DisplayLink devices"""
        self.log("=== Fixing USB Power Management ===")
        
        # Find USB devices that might be DisplayLink
        usb_path = Path('/sys/bus/usb/devices')
        displaylink_devices = []
        
        for device_path in usb_path.glob('*'):
            if not device_path.is_dir():
                continue
                
            # Check if this could be a DisplayLink device
            vendor_file = device_path / 'idVendor'
            product_file = device_path / 'idProduct'
            
            if vendor_file.exists() and product_file.exists():
                try:
                    vendor = vendor_file.read_text().strip()
                    product = product_file.read_text().strip()
                    
                    # DisplayLink vendor ID is 17e9
                    if vendor == '17e9':
                        displaylink_devices.append(device_path.name)
                        self.log(f"Found DisplayLink device: {device_path.name} (vendor: {vendor}, product: {product})")
                except Exception:
                    pass
        
        if not displaylink_devices:
            self.log("No DisplayLink USB devices found, disabling autosuspend for all USB hubs", "WARNING")
            # Disable for USB hubs and controllers
            for device_path in usb_path.glob('usb*'):
                control_file = device_path / 'power' / 'control'
                if control_file.exists():
                    success, _ = self.run_command(['sudo', 'bash', '-c', f'echo on > {control_file}'],
                                                f"Disable autosuspend for {device_path.name}")
        else:
            # Disable autosuspend for DisplayLink devices and their parent hubs
            for device in displaylink_devices:
                device_path = usb_path / device
                control_file = device_path / 'power' / 'control'
                
                if control_file.exists():
                    success, _ = self.run_command(['sudo', 'bash', '-c', f'echo on > {control_file}'],
                                                f"Disable autosuspend for DisplayLink device {device}")
    
    def fix_monitor_refresh_rates(self):
        """Set consistent refresh rates for DisplayLink monitors"""
        self.log("=== Fixing Monitor Refresh Rates ===")
        
        monitors = self.get_monitor_info()
        dp_monitors = [m for m in monitors if m['name'].startswith('DP-')]
        
        for monitor in dp_monitors:
            monitor_name = monitor['name']
            current_rate = monitor['refreshRate']
            
            # Try to set to 60Hz if not already
            if abs(current_rate - 60.0) > 0.1:  # Not 60Hz
                self.log(f"Monitor {monitor_name} is at {current_rate}Hz, trying to set to 60Hz")
                
                # Check available modes for 60Hz
                available_modes = monitor.get('availableModes', [])
                has_60hz = any('60.00Hz' in mode for mode in available_modes)
                
                if has_60hz:
                    success, _ = self.run_command(['hyprctl', 'keyword', 'monitor', 
                                                 f'{monitor_name},3840x2160@60,auto,1'],
                                                f"Set {monitor_name} to 60Hz")
                    if success:
                        self.log(f"✓ Successfully set {monitor_name} to 60Hz", "SUCCESS")
                    else:
                        self.log(f"Failed to set {monitor_name} to 60Hz, trying 30Hz", "WARNING")
                        # Fallback to explicit 30Hz to avoid auto-selection issues
                        self.run_command(['hyprctl', 'keyword', 'monitor', 
                                        f'{monitor_name},3840x2160@30,auto,1'],
                                        f"Set {monitor_name} to stable 30Hz")
                else:
                    self.log(f"60Hz not available for {monitor_name}, keeping current rate", "WARNING")
    
    def create_stable_monitor_config(self):
        """Create a stable monitor configuration"""
        self.log("=== Creating Stable Monitor Configuration ===")
        
        monitors = self.get_monitor_info()
        
        # Create monitor config based on current setup
        config_lines = [
            "# Monitor Configuration - Generated by DisplayLink Flicker Fix",
            "# See https://wiki.hyprland.Configuring/Monitors/",
            "",
            "# Laptop display",
            "monitor=eDP-1,1920x1080@60,0x0,1.5",
            "",
            "# External monitors (DisplayLink)",
        ]
        
        # Add external monitor configs
        dp_monitors = [m for m in monitors if m['name'].startswith('DP-')]
        x_offset = 1280  # After scaled laptop display
        
        for i, monitor in enumerate(dp_monitors):
            monitor_name = monitor['name']
            if monitor['refreshRate'] >= 60.0:
                config_lines.append(f"monitor={monitor_name},3840x2160@60,{x_offset}x0,1")
            else:
                config_lines.append(f"monitor={monitor_name},3840x2160@30,{x_offset}x0,1")
            x_offset += 3840
        
        # Add fallback
        config_lines.extend([
            "",
            "# Fallback for unknown monitors",
            "monitor=,preferred,auto,auto",
        ])
        
        config_content = "\\n".join(config_lines)
        
        # Backup existing Hyprland config
        hypr_config = Path.home() / '.config' / 'hypr' / 'hyprland.conf'
        if hypr_config.exists() and not self.dry_run:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.backup_dir / f"hyprland.conf.backup.{timestamp}"
            backup_path.write_text(hypr_config.read_text())
            self.log(f"Backed up Hyprland config to {backup_path}")
        
        # Create temporary monitor config
        temp_config = Path('/tmp/monitor_config.conf')
        if not self.dry_run:
            temp_config.write_text("\\n".join(config_lines))
        
        self.log(f"Monitor configuration would be:")
        for line in config_lines:
            if line.strip() and not line.startswith('#'):
                self.log(f"  {line}")
        
        self.log("To apply this configuration permanently, add these lines to your Hyprland config", "INFO")
    
    def fix_workspace_assignments(self):
        """Ensure stable workspace assignments"""
        self.log("=== Fixing Workspace Assignments ===")
        
        workspace_rules = [
            "# Workspace assignments for stable multi-monitor setup",
            "workspace=1,monitor:eDP-1,default:true",
            "workspace=2,monitor:DP-3,default:true", 
            "workspace=3,monitor:DP-4,default:true",
        ]
        
        for rule in workspace_rules:
            if not rule.startswith('#'):
                self.log(f"Would add: {rule}")
        
        self.log("Add these workspace rules to your Hyprland config for stable assignments", "INFO")
    
    def test_configuration(self):
        """Test the current configuration"""
        self.log("=== Testing Current Configuration ===")
        
        # Reload Hyprland config
        success, output = self.run_command(['hyprctl', 'reload'], "Reload Hyprland configuration")
        
        if success:
            time.sleep(2)  # Wait for reload
            
            # Check monitor status
            monitors = self.get_monitor_info()
            for monitor in monitors:
                status = "✓" if monitor['dpmsStatus'] else "✗"
                self.log(f"{status} {monitor['name']}: {monitor['width']}x{monitor['height']}@{monitor['refreshRate']:.2f}Hz")
        
        return success
    
    def apply_kernel_parameters(self):
        """Suggest kernel parameters for DisplayLink stability"""
        self.log("=== Kernel Parameter Recommendations ===")
        
        kernel_params = [
            "usbcore.autosuspend=-1",    # Disable USB autosuspend globally
            "video=efifb:off",           # Disable EFI framebuffer (can conflict)
            "pcie_aspm=off",             # Disable PCIe Active State Power Management
        ]
        
        self.log("Consider adding these kernel parameters to improve DisplayLink stability:")
        for param in kernel_params:
            self.log(f"  {param}")
        
        self.log("Add them to /etc/default/grub in GRUB_CMDLINE_LINUX_DEFAULT and run 'sudo grub-mkconfig -o /boot/grub/grub.cfg'")

def main():
    parser = argparse.ArgumentParser(description='Fix DisplayLink monitor flickering issues')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--usb-power', action='store_true',
                       help='Fix USB power management only')
    parser.add_argument('--refresh-rates', action='store_true',
                       help='Fix monitor refresh rates only')
    parser.add_argument('--all', action='store_true',
                       help='Apply all fixes (default if no specific fix chosen)')
    parser.add_argument('--test', action='store_true',
                       help='Test current configuration')
    
    args = parser.parse_args()
    
    # Default to all fixes if no specific fix chosen
    if not any([args.usb_power, args.refresh_rates, args.test]):
        args.all = True
    
    fixer = DisplayLinkFlickerFixer(dry_run=args.dry_run)
    
    if args.dry_run:
        fixer.log("=== DRY RUN MODE - No changes will be made ===", "WARNING")
    
    try:
        if args.all or args.usb_power:
            fixer.fix_usb_power_management()
        
        if args.all or args.refresh_rates:
            fixer.fix_monitor_refresh_rates()
        
        if args.all:
            fixer.create_stable_monitor_config()
            fixer.fix_workspace_assignments()
            fixer.apply_kernel_parameters()
        
        if args.test:
            fixer.test_configuration()
            
    except KeyboardInterrupt:
        fixer.log("Operation cancelled by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        fixer.log(f"Unexpected error: {e}", "ERROR")
        sys.exit(1)
    
    fixer.log("=== Fix process completed ===", "SUCCESS")
    fixer.log("Reboot may be required for all changes to take effect", "INFO")

if __name__ == "__main__":
    main()
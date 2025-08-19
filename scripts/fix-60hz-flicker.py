#!/usr/bin/env python3
"""
Fix 60Hz DisplayLink Monitor Flickering

Specific fixes for DP-3 (60Hz) monitor flickering issues.
This script addresses high-bandwidth DisplayLink stability problems.

Usage:
    uv run scripts/fix-60hz-flicker.py [options]
"""
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import argparse
import subprocess
import time
import json
from pathlib import Path

class DP3FlickerFixer:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
    
    def log(self, message: str, level: str = "INFO"):
        """Log with color coding"""
        colors = {
            "INFO": "\033[32m",      
            "WARNING": "\033[33m",   
            "ERROR": "\033[31m",     
            "SUCCESS": "\033[92m",   
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
    
    def get_monitor_info(self) -> list:
        """Get current monitor configuration"""
        try:
            result = subprocess.run(['hyprctl', 'monitors', '-j'], 
                                  capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except Exception as e:
            self.log(f"Failed to get monitor info: {e}", "ERROR")
            return []
    
    def check_dp3_status(self):
        """Check current DP-3 status and configuration"""
        self.log("=== Checking DP-3 Monitor Status ===")
        
        monitors = self.get_monitor_info()
        dp3_monitor = next((m for m in monitors if m['name'] == 'DP-3'), None)
        
        if not dp3_monitor:
            self.log("DP-3 monitor not found! Check connections.", "ERROR")
            return False
        
        self.log(f"DP-3 Status:")
        self.log(f"  Resolution: {dp3_monitor['width']}x{dp3_monitor['height']}")
        self.log(f"  Refresh Rate: {dp3_monitor['refreshRate']:.2f}Hz")
        self.log(f"  DPMS Status: {dp3_monitor['dpmsStatus']}")
        self.log(f"  Active Workspace: {dp3_monitor['activeWorkspace']['id']}")
        self.log(f"  Description: {dp3_monitor['description']}")
        
        # Check for issues
        if abs(dp3_monitor['refreshRate'] - 60.0) > 0.1:
            self.log(f"⚠️  DP-3 not running at exactly 60Hz", "WARNING")
        
        if not dp3_monitor['dpmsStatus']:
            self.log(f"⚠️  DP-3 DPMS is disabled", "WARNING")
        
        return True
    
    def stabilize_dp3_refresh_rate(self):
        """Apply specific refresh rate stabilization for DP-3"""
        self.log("=== Stabilizing DP-3 Refresh Rate ===")
        
        # Try multiple refresh rate configurations
        configurations = [
            "DP-3,3840x2160@60.00,1280x0,1",  # Exact 60Hz
            "DP-3,3840x2160@59.96,1280x0,1",  # NTSC 60Hz
            "DP-3,2560x1440@60,1280x0,1",     # Lower res but stable 60Hz
            "DP-3,1920x1080@60,1280x0,1",     # Much lower res for stability
        ]
        
        for i, config in enumerate(configurations):
            self.log(f"Trying configuration {i+1}: {config}")
            success, _ = self.run_command(['hyprctl', 'keyword', 'monitor', config],
                                        f"Set DP-3 configuration {i+1}")
            
            if success and not self.dry_run:
                time.sleep(2)  # Wait for mode change
                
                # Check if it worked
                monitors = self.get_monitor_info()
                dp3_monitor = next((m for m in monitors if m['name'] == 'DP-3'), None)
                
                if dp3_monitor and dp3_monitor['dpmsStatus']:
                    self.log(f"✓ Configuration {i+1} successful", "SUCCESS")
                    self.log(f"  DP-3 now: {dp3_monitor['width']}x{dp3_monitor['height']}@{dp3_monitor['refreshRate']:.2f}Hz")
                    return True
                else:
                    self.log(f"✗ Configuration {i+1} failed or monitor not active", "WARNING")
        
        self.log("All refresh rate configurations failed", "ERROR")
        return False
    
    def optimize_usb_for_high_bandwidth(self):
        """Optimize USB settings specifically for high bandwidth DisplayLink"""
        self.log("=== Optimizing USB for High Bandwidth ===")
        
        # Find the specific DisplayLink device
        usb_path = Path('/sys/bus/usb/devices')
        displaylink_device = None
        
        for device_path in usb_path.glob('*'):
            if not device_path.is_dir():
                continue
            
            vendor_file = device_path / 'idVendor'
            product_file = device_path / 'idProduct'
            
            if vendor_file.exists() and product_file.exists():
                try:
                    vendor = vendor_file.read_text().strip()
                    if vendor == '17e9':  # DisplayLink
                        displaylink_device = device_path
                        self.log(f"Found DisplayLink device: {device_path.name}")
                        break
                except Exception:
                    pass
        
        if displaylink_device:
            # Optimize this specific device
            optimizations = [
                ('power/control', 'on'),
                ('power/autosuspend_delay_ms', '-1'),
                ('power/wakeup', 'enabled'),
            ]
            
            for setting, value in optimizations:
                setting_file = displaylink_device / setting
                if setting_file.exists():
                    success, _ = self.run_command(['sudo', 'bash', '-c', f'echo {value} > {setting_file}'],
                                                f"Set {setting} to {value}")
        else:
            self.log("DisplayLink device not found for specific optimization", "WARNING")
    
    def test_dp3_stability(self, duration: int = 10):
        """Test DP-3 stability by monitoring for changes"""
        self.log(f"=== Testing DP-3 Stability for {duration} seconds ===")
        
        if self.dry_run:
            self.log("DRY-RUN: Would test stability")
            return True
        
        start_time = time.time()
        previous_state = None
        changes = 0
        
        while (time.time() - start_time) < duration:
            monitors = self.get_monitor_info()
            dp3_monitor = next((m for m in monitors if m['name'] == 'DP-3'), None)
            
            if dp3_monitor:
                current_state = {
                    'dpms': dp3_monitor['dpmsStatus'],
                    'refresh': dp3_monitor['refreshRate'],
                    'width': dp3_monitor['width'],
                    'height': dp3_monitor['height']
                }
                
                if previous_state and current_state != previous_state:
                    changes += 1
                    self.log(f"State change detected: {previous_state} -> {current_state}", "WARNING")
                
                previous_state = current_state
            else:
                changes += 1
                self.log("DP-3 monitor disappeared!", "ERROR")
            
            time.sleep(0.5)
        
        if changes == 0:
            self.log("✓ DP-3 remained stable during test", "SUCCESS")
            return True
        else:
            self.log(f"✗ DP-3 had {changes} state changes during test", "ERROR")
            return False
    
    def apply_dp3_workarounds(self):
        """Apply specific workarounds for DP-3 flickering"""
        self.log("=== Applying DP-3 Specific Workarounds ===")
        
        # Force explicit mode setting
        success, _ = self.run_command(['hyprctl', 'keyword', 'monitor', 'DP-3,disable'],
                                    "Disable DP-3 temporarily")
        
        if success and not self.dry_run:
            time.sleep(1)
            
            # Re-enable with explicit settings
            success, _ = self.run_command(['hyprctl', 'keyword', 'monitor', 'DP-3,3840x2160@60,1280x0,1'],
                                        "Re-enable DP-3 with stable settings")
            
            if success:
                time.sleep(2)
                
                # Verify workspace assignment
                success, _ = self.run_command(['hyprctl', 'keyword', 'workspace', '2,monitor:DP-3'],
                                            "Assign workspace 2 to DP-3")
        
        return success
    
    def create_dp3_startup_script(self):
        """Create a startup script for DP-3 stability"""
        self.log("=== Creating DP-3 Startup Script ===")
        
        script_content = '''#!/bin/bash
# DP-3 DisplayLink Stability Script
# Run this after connecting DisplayLink dock

sleep 3  # Wait for detection

# Force stable configuration
hyprctl keyword monitor DP-3,3840x2160@60,1280x0,1
sleep 1

# Assign workspace
hyprctl keyword workspace 2,monitor:DP-3

echo "DP-3 configuration applied"
'''
        
        script_path = Path.home() / '.local' / 'bin' / 'setup-dp3.sh'
        script_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.dry_run:
            script_path.write_text(script_content)
            script_path.chmod(0o755)
            self.log(f"✓ Created startup script: {script_path}")
        else:
            self.log(f"DRY-RUN: Would create script: {script_path}")
        
        self.log("Run this script after connecting DisplayLink dock:")
        self.log(f"  {script_path}")

def main():
    parser = argparse.ArgumentParser(description='Fix DP-3 (60Hz) DisplayLink flickering')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--test-only', action='store_true',
                       help='Only test current stability, no fixes')
    parser.add_argument('--quick-fix', action='store_true',
                       help='Apply quick workaround only')
    
    args = parser.parse_args()
    
    fixer = DP3FlickerFixer(dry_run=args.dry_run)
    
    if args.dry_run:
        fixer.log("=== DRY RUN MODE ===", "WARNING")
    
    # Always check status first
    if not fixer.check_dp3_status():
        return
    
    if args.test_only:
        fixer.test_dp3_stability(duration=15)
        return
    
    if args.quick_fix:
        fixer.apply_dp3_workarounds()
        return
    
    # Full fix sequence
    fixer.log("=== Starting DP-3 Flicker Fix Sequence ===")
    
    # Step 1: USB optimization
    fixer.optimize_usb_for_high_bandwidth()
    
    # Step 2: Refresh rate stabilization
    if fixer.stabilize_dp3_refresh_rate():
        # Step 3: Test stability
        if fixer.test_dp3_stability():
            fixer.log("✓ DP-3 appears stable after fixes", "SUCCESS")
        else:
            fixer.log("DP-3 still unstable, applying workarounds", "WARNING")
            fixer.apply_dp3_workarounds()
    
    # Step 4: Create startup script for persistence
    fixer.create_dp3_startup_script()
    
    fixer.log("=== Fix sequence complete ===", "SUCCESS")
    fixer.log("If flickering persists, try the quick-fix option:", "INFO")
    fixer.log("  uv run scripts/fix-60hz-flicker.py --quick-fix", "INFO")

if __name__ == "__main__":
    main()
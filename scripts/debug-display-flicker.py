#!/usr/bin/env python3
"""
Display Flicker Debug Script

A comprehensive debugging tool for DisplayLink monitor flickering issues.
This script monitors display status, logs events, and provides diagnostic information.

Usage:
    uv run scripts/debug-display-flicker.py [options]
"""
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "psutil>=5.8.0",
# ]
# ///

import argparse
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
import sys

class DisplayFlickerDebugger:
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"flicker_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')
    
    def get_monitor_info(self) -> dict:
        """Get current monitor configuration from Hyprland"""
        try:
            result = subprocess.run(['hyprctl', 'monitors', '-j'], 
                                  capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            self.log(f"Failed to get monitor info: {e}", "ERROR")
            return {}
    
    def get_workspace_info(self) -> dict:
        """Get current workspace configuration"""
        try:
            result = subprocess.run(['hyprctl', 'workspaces', '-j'], 
                                  capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            self.log(f"Failed to get workspace info: {e}", "ERROR")
            return {}
    
    def check_usb_power_management(self) -> dict:
        """Check USB power management settings"""
        usb_devices = {}
        try:
            # Check USB autosuspend settings
            usb_path = Path('/sys/bus/usb/devices')
            for device_path in usb_path.glob('*'):
                if device_path.is_dir():
                    power_path = device_path / 'power' / 'autosuspend_delay_ms'
                    control_path = device_path / 'power' / 'control'
                    
                    if power_path.exists() and control_path.exists():
                        try:
                            autosuspend = power_path.read_text().strip()
                            control = control_path.read_text().strip()
                            usb_devices[device_path.name] = {
                                'autosuspend_delay': autosuspend,
                                'control': control
                            }
                        except Exception:
                            pass
        except Exception as e:
            self.log(f"Failed to check USB power management: {e}", "ERROR")
        
        return usb_devices
    
    def monitor_continuously(self, duration: int = 300, interval: float = 1.0):
        """Monitor display status continuously with enhanced detection"""
        self.log(f"Starting enhanced continuous monitoring for {duration} seconds (interval: {interval}s)")
        
        start_time = time.time()
        previous_monitors = None
        flicker_count = 0
        anomaly_count = 0
        
        while time.time() - start_time < duration:
            current_monitors = self.get_monitor_info()
            current_time = time.time() - start_time
            
            if previous_monitors is not None:
                # Check for DPMS status changes
                prev_active = {m['name']: m['dpmsStatus'] for m in previous_monitors}
                curr_active = {m['name']: m['dpmsStatus'] for m in current_monitors}
                
                # Check for any monitor property changes
                for curr_monitor in current_monitors:
                    monitor_name = curr_monitor['name']
                    prev_monitor = next((m for m in previous_monitors if m['name'] == monitor_name), None)
                    
                    if prev_monitor:
                        # Check DPMS status change
                        if prev_monitor['dpmsStatus'] != curr_monitor['dpmsStatus']:
                            flicker_count += 1
                            self.log(f"FLICKER DETECTED at {current_time:.1f}s: Monitor {monitor_name} DPMS changed from {prev_monitor['dpmsStatus']} to {curr_monitor['dpmsStatus']}", "WARNING")
                        
                        # Check for resolution changes
                        if (prev_monitor['width'] != curr_monitor['width'] or 
                            prev_monitor['height'] != curr_monitor['height']):
                            anomaly_count += 1
                            self.log(f"RESOLUTION CHANGE at {current_time:.1f}s: Monitor {monitor_name} changed from {prev_monitor['width']}x{prev_monitor['height']} to {curr_monitor['width']}x{curr_monitor['height']}", "WARNING")
                        
                        # Check for refresh rate fluctuations
                        if abs(prev_monitor['refreshRate'] - curr_monitor['refreshRate']) > 0.1:
                            anomaly_count += 1
                            self.log(f"REFRESH RATE CHANGE at {current_time:.1f}s: Monitor {monitor_name} changed from {prev_monitor['refreshRate']:.2f}Hz to {curr_monitor['refreshRate']:.2f}Hz", "WARNING")
                        
                        # Check for workspace assignment changes (can indicate display issues)
                        prev_ws = prev_monitor.get('activeWorkspace', {}).get('id', 0)
                        curr_ws = curr_monitor.get('activeWorkspace', {}).get('id', 0)
                        if prev_ws != curr_ws and prev_ws != 0 and curr_ws != 0:
                            anomaly_count += 1
                            self.log(f"WORKSPACE CHANGE at {current_time:.1f}s: Monitor {monitor_name} workspace changed from {prev_ws} to {curr_ws}", "WARNING")
                
                # Check if monitor disappeared/reappeared
                prev_names = {m['name'] for m in previous_monitors}
                curr_names = {m['name'] for m in current_monitors}
                
                disappeared = prev_names - curr_names
                appeared = curr_names - prev_names
                
                for name in disappeared:
                    flicker_count += 1
                    self.log(f"MONITOR DISAPPEARED at {current_time:.1f}s: {name}", "WARNING")
                
                for name in appeared:
                    flicker_count += 1
                    self.log(f"MONITOR APPEARED at {current_time:.1f}s: {name}", "WARNING")
            
            previous_monitors = current_monitors
            time.sleep(interval)
        
        self.log(f"Monitoring complete. DPMS/disconnect events: {flicker_count}, Other anomalies: {anomaly_count}")
        
        # Also check system logs for recent DRM events
        self.check_recent_drm_events()
    
    def check_recent_drm_events(self):
        """Check recent DRM/graphics events in system logs"""
        try:
            # Check for recent DRM-related messages
            result = subprocess.run(['journalctl', '-k', '--since', '1 minute ago', '--no-pager'], 
                                  capture_output=True, text=True, check=False)
            
            if result.stdout:
                drm_lines = []
                for line in result.stdout.split('\n'):
                    if any(keyword in line.lower() for keyword in ['drm', 'displaylink', 'dp-', 'udl', 'usb disconnect', 'usb connect']):
                        drm_lines.append(line.strip())
                
                if drm_lines:
                    self.log("Recent DRM/DisplayLink events:")
                    for line in drm_lines[-10:]:  # Show last 10 events
                        self.log(f"  {line}")
                else:
                    self.log("No recent DRM events found in journal")
        except Exception as e:
            self.log(f"Could not check system logs: {e}", "WARNING")
    
    def run_diagnostic(self):
        """Run comprehensive diagnostic"""
        self.log("=== Display Flicker Diagnostic Report ===")
        
        # System info
        self.log("1. System Information:")
        try:
            result = subprocess.run(['uname', '-a'], capture_output=True, text=True, check=True)
            self.log(f"   Kernel: {result.stdout.strip()}")
        except Exception as e:
            self.log(f"   Failed to get kernel info: {e}", "ERROR")
        
        # Monitor configuration
        self.log("2. Current Monitor Configuration:")
        monitors = self.get_monitor_info()
        for monitor in monitors:
            self.log(f"   {monitor['name']}: {monitor['width']}x{monitor['height']}@{monitor['refreshRate']:.2f}Hz")
            self.log(f"      Description: {monitor['description']}")
            self.log(f"      Workspace: {monitor['activeWorkspace']}")
            self.log(f"      DPMS Status: {monitor['dpmsStatus']}")
            
            # Check for potential issues
            if monitor['refreshRate'] != 60.0 and monitor['name'].startswith('DP-'):
                self.log(f"      ⚠️  Non-standard refresh rate detected", "WARNING")
        
        # Workspace configuration
        self.log("3. Workspace Configuration:")
        workspaces = self.get_workspace_info()
        for workspace in workspaces:
            self.log(f"   Workspace {workspace['id']}: {workspace['name']} on monitor {workspace.get('monitor', 'unknown')}")
        
        # USB power management
        self.log("4. USB Power Management:")
        usb_devices = self.check_usb_power_management()
        for device, settings in usb_devices.items():
            if settings['control'] == 'auto':
                self.log(f"   ⚠️  Device {device}: autosuspend enabled (delay: {settings['autosuspend_delay']}ms)", "WARNING")
        
        # Check for DisplayLink specific issues
        self.log("5. DisplayLink Analysis:")
        dp_monitors = [m for m in monitors if m['name'].startswith('DP-')]
        if len(dp_monitors) >= 2:
            refresh_rates = [m['refreshRate'] for m in dp_monitors]
            if len(set(refresh_rates)) > 1:
                self.log("   ⚠️  Mixed refresh rates detected on DisplayPort monitors", "WARNING")
                for monitor in dp_monitors:
                    self.log(f"      {monitor['name']}: {monitor['refreshRate']:.2f}Hz")
        
        # Check for workspace assignment issues
        workspace_2_monitor = None
        for workspace in workspaces:
            if workspace['id'] == 2:
                workspace_2_monitor = workspace.get('monitor')
                break
        
        if workspace_2_monitor:
            self.log(f"   Workspace 2 is on monitor: {workspace_2_monitor}")
            ws2_monitor_info = next((m for m in monitors if m['name'] == workspace_2_monitor), None)
            if ws2_monitor_info and ws2_monitor_info['refreshRate'] == 30.0:
                self.log("   ⚠️  Workspace 2 monitor running at 30Hz - potential bandwidth issue", "WARNING")

def main():
    parser = argparse.ArgumentParser(description='Debug DisplayLink monitor flickering')
    parser.add_argument('--monitor', '-m', action='store_true', 
                       help='Start continuous monitoring')
    parser.add_argument('--duration', '-d', type=int, default=300,
                       help='Monitoring duration in seconds (default: 300)')
    parser.add_argument('--interval', '-i', type=float, default=1.0,
                       help='Monitoring interval in seconds (default: 1.0)')
    parser.add_argument('--log-dir', type=Path, 
                       default=Path.home() / '.local' / 'share' / 'arch_dotfiles' / 'debug_logs',
                       help='Directory for log files')
    
    args = parser.parse_args()
    
    debugger = DisplayFlickerDebugger(args.log_dir)
    
    if args.monitor:
        debugger.monitor_continuously(args.duration, args.interval)
    else:
        debugger.run_diagnostic()
    
    print(f"\nLog saved to: {debugger.log_file}")

if __name__ == "__main__":
    main()
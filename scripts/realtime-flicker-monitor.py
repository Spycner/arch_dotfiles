#!/usr/bin/env python3
"""
Real-time DisplayLink Flicker Monitor

Monitors for visual flickering events using multiple detection methods.
Designed to catch frequent 1-3 second flicker cycles that standard DPMS monitoring misses.

Usage:
    uv run scripts/realtime-flicker-monitor.py [options]
"""
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "psutil>=5.8.0",
# ]
# ///

import argparse
import subprocess
import time
import threading
from datetime import datetime
from pathlib import Path
import sys
import signal
import json

class RealtimeFlickerMonitor:
    def __init__(self):
        self.running = False
        self.flicker_events = []
        self.log_file = Path.home() / '.local' / 'share' / 'arch_dotfiles' / 'debug_logs' / f"realtime_flicker_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Signal handler for clean exit
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle interrupt signals gracefully"""
        self.log("Received interrupt signal, stopping monitoring...")
        self.running = False
    
    def log(self, message: str, level: str = "INFO"):
        """Thread-safe logging with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry, flush=True)
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry + '\n')
        except Exception:
            pass  # Don't let logging errors break monitoring
    
    def get_display_brightness(self, monitor_name: str) -> float:
        """Get display brightness as a proxy for visual state"""
        try:
            # Use hyprctl to get monitor info
            result = subprocess.run(['hyprctl', 'monitors', '-j'], 
                                  capture_output=True, text=True, check=True)
            monitors = json.loads(result.stdout)
            
            for monitor in monitors:
                if monitor['name'] == monitor_name:
                    # Use DPMS status as brightness proxy (True=1.0, False=0.0)
                    return 1.0 if monitor.get('dpmsStatus', True) else 0.0
            return -1.0  # Monitor not found
        except Exception:
            return -1.0
    
    def monitor_drm_events(self):
        """Monitor DRM events in real-time using journalctl"""
        try:
            # Follow kernel messages in real-time
            process = subprocess.Popen(['journalctl', '-k', '-f', '--no-pager', '-o', 'short-monotonic'],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     text=True, bufsize=1, universal_newlines=True)
            
            self.log("Started DRM event monitoring thread")
            
            while self.running and process.poll() is None:
                try:
                    line = process.stdout.readline()
                    if line:
                        line = line.strip()
                        # Look for DisplayLink-related events
                        if any(keyword in line.lower() for keyword in [
                            'drm', 'displaylink', 'dp-', 'udl', 'usb disconnect', 
                            'usb connect', 'gpu hang', 'timeout', 'failed'
                        ]):
                            current_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                            self.log(f"DRM EVENT: {line}", "WARNING")
                            self.flicker_events.append({
                                'time': current_time,
                                'type': 'drm_event',
                                'details': line
                            })
                except Exception as e:
                    if self.running:  # Only log if we're still supposed to be running
                        self.log(f"Error reading DRM events: {e}", "ERROR")
                    break
            
            process.terminate()
            process.wait()
            
        except Exception as e:
            self.log(f"Failed to start DRM monitoring: {e}", "ERROR")
    
    def monitor_display_state(self, target_monitor: str = "DP-3"):
        """Monitor specific display state changes rapidly"""
        self.log(f"Started display state monitoring for {target_monitor}")
        
        previous_state = None
        consecutive_changes = 0
        
        while self.running:
            try:
                brightness = self.get_display_brightness(target_monitor)
                current_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                
                if previous_state is not None and brightness != previous_state:
                    consecutive_changes += 1
                    self.log(f"DISPLAY STATE CHANGE: {target_monitor} brightness {previous_state} -> {brightness}", "WARNING")
                    
                    self.flicker_events.append({
                        'time': current_time,
                        'type': 'brightness_change',
                        'monitor': target_monitor,
                        'from': previous_state,
                        'to': brightness
                    })
                    
                    # If we see rapid changes, it's likely flickering
                    if consecutive_changes >= 3:
                        self.log(f"RAPID FLICKER DETECTED on {target_monitor}: {consecutive_changes} changes", "ERROR")
                        consecutive_changes = 0  # Reset counter
                else:
                    consecutive_changes = max(0, consecutive_changes - 1)  # Gradually reduce
                
                previous_state = brightness
                time.sleep(0.1)  # Very fast polling
                
            except Exception as e:
                self.log(f"Error in display state monitoring: {e}", "ERROR")
                time.sleep(0.5)
    
    def monitor_usb_events(self):
        """Monitor USB connection events that might affect DisplayLink"""
        self.log("Started USB event monitoring")
        
        try:
            # Monitor udev events for USB changes
            process = subprocess.Popen(['journalctl', '-f', '--no-pager', '-u', 'systemd-udevd', '-o', 'short-monotonic'],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     text=True, bufsize=1, universal_newlines=True)
            
            while self.running and process.poll() is None:
                try:
                    line = process.stdout.readline()
                    if line:
                        line = line.strip()
                        if any(keyword in line.lower() for keyword in ['usb', 'disconnect', 'connect', 'device']):
                            current_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                            self.log(f"USB EVENT: {line}", "INFO")
                            self.flicker_events.append({
                                'time': current_time,
                                'type': 'usb_event', 
                                'details': line
                            })
                except Exception as e:
                    if self.running:
                        self.log(f"Error reading USB events: {e}", "ERROR")
                    break
            
            process.terminate()
            process.wait()
            
        except Exception as e:
            self.log(f"Failed to start USB monitoring: {e}", "ERROR")
    
    def start_monitoring(self, duration: int = 60, target_monitor: str = "DP-3"):
        """Start comprehensive real-time monitoring"""
        self.log("=== Starting Real-time Flicker Monitoring ===")
        self.log(f"Monitoring duration: {duration} seconds")
        self.log(f"Focusing on monitor: {target_monitor} (the 60Hz DisplayLink monitor)")
        self.log("Press Ctrl+C to stop early")
        
        self.running = True
        start_time = time.time()
        
        # Start monitoring threads
        threads = [
            threading.Thread(target=self.monitor_drm_events, daemon=True),
            threading.Thread(target=self.monitor_display_state, args=(target_monitor,), daemon=True),
            threading.Thread(target=self.monitor_usb_events, daemon=True),
        ]
        
        for thread in threads:
            thread.start()
        
        # Main monitoring loop with periodic status
        try:
            while self.running and (time.time() - start_time) < duration:
                elapsed = time.time() - start_time
                if int(elapsed) % 10 == 0 and elapsed > 0:  # Every 10 seconds
                    event_count = len(self.flicker_events)
                    self.log(f"Status: {elapsed:.0f}s elapsed, {event_count} events detected")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.log("Monitoring interrupted by user")
        
        self.running = False
        
        # Wait a moment for threads to finish
        time.sleep(1)
        
        # Report results
        self.log("=== Monitoring Complete ===")
        self.log(f"Total events detected: {len(self.flicker_events)}")
        
        # Categorize events
        event_types = {}
        for event in self.flicker_events:
            event_type = event['type']
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        for event_type, count in event_types.items():
            self.log(f"  {event_type}: {count} events")
        
        # Show recent events
        if self.flicker_events:
            self.log("Recent events:")
            for event in self.flicker_events[-5:]:
                self.log(f"  [{event['time']}] {event['type']}: {event.get('details', 'N/A')}")
        
        self.log(f"Full log saved to: {self.log_file}")
        
        # Analysis
        brightness_changes = [e for e in self.flicker_events if e['type'] == 'brightness_change']
        if len(brightness_changes) > 5:
            self.log(f"⚠️  High number of brightness changes detected ({len(brightness_changes)})", "WARNING")
            self.log("This likely indicates visual flickering", "WARNING")
        
        return len(self.flicker_events)

def main():
    parser = argparse.ArgumentParser(description='Real-time DisplayLink flicker monitoring')
    parser.add_argument('--duration', '-d', type=int, default=30,
                       help='Monitoring duration in seconds (default: 30)')
    parser.add_argument('--monitor', '-m', type=str, default='DP-3',
                       help='Monitor to focus on (default: DP-3)')
    
    args = parser.parse_args()
    
    monitor = RealtimeFlickerMonitor()
    
    try:
        event_count = monitor.start_monitoring(args.duration, args.monitor)
        
        if event_count > 10:
            print(f"\n🔥 High activity detected! ({event_count} events)")
            print("Consider applying DisplayLink fixes with:")
            print("  uv run scripts/fix-displaylink-flicker.py --all")
        elif event_count > 0:
            print(f"\n⚠️  Some activity detected ({event_count} events)")
            print("Monitor the situation and apply fixes if needed")
        else:
            print(f"\n✅ No flicker events detected during monitoring")
    
    except Exception as e:
        print(f"Monitoring failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
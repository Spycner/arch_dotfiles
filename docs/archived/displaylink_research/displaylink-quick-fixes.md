# DisplayLink Quick Fixes Guide

## Overview

This guide provides the **top 5 highest-priority solutions** ready for immediate testing to resolve DisplayLink flickering on DP-3 (4K@60Hz). Solutions are ordered by priority score and implementation complexity.

**🚨 CRITICAL**: Start with **Fix #1 - Hyprland Aquamarine Update** as it addresses the root architectural issue.

---

## Fix #1: Hyprland Aquamarine evdi Fix (CRITICAL - 9.5/10 Priority)

**Problem**: DisplayLink monitors detected but show black screens due to incorrect GPU handling in Hyprland's rendering backend.

**Root Cause**: evdi drivers treated as primary GPU despite lacking rendering capabilities.

### Implementation Steps

```bash
# Step 1: Check current versions
echo "=== Current Hyprland/Aquamarine Versions ==="
pacman -Q hyprland hyprland-git aquamarine-git 2>/dev/null || echo "Some packages not found"

# Step 2: Update to latest git versions with the fix
echo "=== Updating to latest versions with evdi fix ==="
paru -S hyprland-git aquamarine-git

# Step 3: Verify update success
echo "=== Updated Versions ==="
pacman -Q hyprland-git aquamarine-git

# Step 4: Restart Hyprland to apply changes
echo "=== Restarting Hyprland ==="
hyprctl reload
```

### Validation Steps
```bash
# Check if DisplayLink monitors are now receiving signal
hyprctl monitors | grep -A15 "DP-3"

# Verify workspace assignment
hyprctl workspaces | grep -A5 "workspace ID 2"

# Test window movement to DisplayLink monitor
hyprctl dispatch movetoworkspace 2
```

### Expected Outcome
- ✅ DP-3 should display signal instead of black screen
- ✅ Windows should be movable to DisplayLink monitor  
- ✅ 60Hz refresh rate should remain stable

### Rollback Procedure
```bash
# If issues occur, rollback to stable versions
paru -S hyprland
sudo pacman -R aquamarine-git
```

---

## Fix #2: KWIN_DRM_NO_AMS Environment Variable (7.8/10 Priority)

**Problem**: Wayland compositor compatibility issues with DisplayLink causing freezing/flickering.

**Root Cause**: ARGB8888 pixel format incompatibility on Wayland sessions.

### Implementation Steps

```bash
# Step 1: Test temporarily (immediate effect)
echo "=== Testing KWIN_DRM_NO_AMS temporarily ==="
KWIN_DRM_NO_AMS=1 Hyprland

# If improvement observed during temporary test, make permanent:

# Step 2: Add to Hyprland configuration (permanent)
echo "env = KWIN_DRM_NO_AMS,1" >> ~/.config/hypr/hyprland.conf

# Step 3: Alternative - Add to system environment
echo "export KWIN_DRM_NO_AMS=1" >> ~/.profile

# Step 4: Restart Hyprland to apply permanent changes
hyprctl reload
```

### Validation Steps  
```bash
# Verify environment variable is set
echo $KWIN_DRM_NO_AMS

# Check DisplayLink monitor stability over time
echo "Monitor DP-3 for 60 seconds for flickering..."
# Visual observation test - watch for 1-3 second flicker pattern
```

### Expected Outcome
- ✅ Reduced DisplayLink monitor freezing after 1-2 seconds
- ✅ More stable Wayland session with DisplayLink
- ✅ Potential reduction in flickering frequency

### Rollback Procedure
```bash
# Remove from Hyprland config
sed -i '/KWIN_DRM_NO_AMS/d' ~/.config/hypr/hyprland.conf

# Remove from profile  
sed -i '/KWIN_DRM_NO_AMS/d' ~/.profile

# Restart Hyprland
hyprctl reload
```

---

## Fix #3: USB Power Management Optimization (8.0/10 Priority)

**Problem**: USB autosuspend causing DisplayLink intermittent disconnections similar to flickering.

**Root Cause**: Power management conflicts with DisplayLink's continuous bandwidth requirements.

### Implementation Steps

```bash
# Step 1: Apply immediate USB power optimization
echo "=== Disabling USB autosuspend for all controllers ==="
for usb in /sys/bus/usb/devices/usb*; do
    echo "on" | sudo tee $usb/power/control
    echo "Disabled autosuspend for: $usb"
done

# Step 2: Create permanent systemd service
echo "=== Creating permanent USB power management service ==="
sudo tee /etc/systemd/system/displaylink-usb-pm.service << 'EOF'
[Unit]
Description=Disable USB autosuspend for DisplayLink
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'for usb in /sys/bus/usb/devices/usb*; do echo "on" > $usb/power/control; done'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# Step 3: Enable and start the service
sudo systemctl enable displaylink-usb-pm.service
sudo systemctl start displaylink-usb-pm.service

# Step 4: Verify service status
sudo systemctl status displaylink-usb-pm.service
```

### Validation Steps
```bash
# Check USB power control status
for usb in /sys/bus/usb/devices/usb*; do
    echo "$usb: $(cat $usb/power/control)"
done

# Verify DisplayLink USB device power status
lsusb | grep -i displaylink
```

### Expected Outcome  
- ✅ Elimination of USB-related display interruptions
- ✅ More stable DisplayLink connection
- ✅ Foundation for other fixes to be effective

### Rollback Procedure
```bash
# Disable and remove service
sudo systemctl stop displaylink-usb-pm.service
sudo systemctl disable displaylink-usb-pm.service  
sudo rm /etc/systemd/system/displaylink-usb-pm.service

# Re-enable auto suspend (system default)
for usb in /sys/bus/usb/devices/usb*; do
    echo "auto" | sudo tee $usb/power/control
done
```

---

## Fix #4: Refresh Rate Enforcement (8.2/10 Priority)

**Problem**: DisplayLink timing synchronization issues causing periodic flickering at 60Hz.

**Root Cause**: Refresh rate instability between DisplayLink adapter and Hyprland.

### Implementation Steps

```bash
# Step 1: Force exact 60Hz refresh rate for DP-3
echo "=== Enforcing exact 60Hz refresh rate ==="
hyprctl keyword monitor DP-3,3840x2160@60.00,1280x0,1

# Step 2: Make permanent in Hyprland configuration
echo "=== Adding to permanent Hyprland config ==="
# Check if monitor config already exists
if grep -q "monitor.*DP-3" ~/.config/hypr/hyprland.conf; then
    echo "Monitor config exists, updating..."
    sed -i 's/monitor.*DP-3.*/monitor=DP-3,3840x2160@60.00,1280x0,1/' ~/.config/hypr/hyprland.conf
else
    echo "Adding new monitor config..."
    echo "monitor=DP-3,3840x2160@60.00,1280x0,1" >> ~/.config/hypr/hyprland.conf
fi

# Step 3: Verify workspace assignment
echo "=== Ensuring workspace 2 assigned to DP-3 ==="
if grep -q "workspace.*2.*DP-3" ~/.config/hypr/hyprland.conf; then
    echo "Workspace assignment already configured"
else
    echo "workspace=2,monitor:DP-3" >> ~/.config/hypr/hyprland.conf
fi

# Step 4: Restart Hyprland to apply changes
hyprctl reload
```

### Validation Steps
```bash
# Verify monitor configuration
echo "=== Current Monitor Configuration ==="
hyprctl monitors | grep -A15 "DP-3"

# Check for exact 60Hz rate
hyprctl monitors | grep -A5 "DP-3" | grep "60.00"

# Verify workspace assignment  
hyprctl workspaces | grep -A3 "workspace ID 2"
```

### Expected Outcome
- ✅ Exact 60.00Hz refresh rate maintained consistently
- ✅ Improved DisplayLink timing synchronization
- ✅ Reduced periodic flickering due to timing issues

### Rollback Procedure
```bash
# Remove specific monitor config (revert to auto-detection)
sed -i '/monitor.*DP-3/d' ~/.config/hypr/hyprland.conf
sed -i '/workspace.*2.*DP-3/d' ~/.config/hypr/hyprland.conf

# Restart Hyprland
hyprctl reload
```

---

## Fix #5: DisplayLink Driver Version Management (7.0/10 Priority)

**Problem**: Kernel compatibility issues with evdi driver causing instability.

**Root Cause**: Version mismatches between Linux kernel and evdi driver.

### Implementation Steps

```bash
# Step 1: Check current versions
echo "=== Current System Versions ==="
uname -r
pacman -Q linux evdi-dkms displaylink 2>/dev/null || echo "Some packages not found"

# Step 2: Install evdi-git for latest fixes
echo "=== Installing latest evdi-git version ==="
paru -S evdi-git

# Step 3: Rebuild evdi module for current kernel  
echo "=== Rebuilding evdi module ==="
sudo dkms remove evdi --all 2>/dev/null || echo "No existing evdi modules to remove"
sudo dkms install evdi/$(pacman -Q evdi-git | awk '{print $2}' | sed 's/-[0-9]*$//')

# Step 4: Verify module compilation and loading
echo "=== Verifying evdi module ==="
sudo modprobe evdi
lsmod | grep evdi

# Step 5: Restart DisplayLink service if available
sudo systemctl restart displaylink 2>/dev/null || echo "DisplayLink service not found/needed"
```

### Validation Steps
```bash
# Check evdi module status
dkms status evdi

# Verify DisplayLink device detection
lsusb | grep -i displaylink  

# Check kernel logs for evdi messages
dmesg | grep -i evdi | tail -10
```

### Expected Outcome
- ✅ Current kernel compatibility with evdi driver
- ✅ Elimination of driver-related stability issues  
- ✅ Proper DisplayLink device initialization

### Rollback Procedure
```bash
# Remove evdi-git and reinstall stable version
paru -R evdi-git
paru -S evdi-dkms

# Rebuild with stable version
sudo dkms remove evdi --all
sudo dkms install evdi/$(pacman -Q evdi-dkms | awk '{print $2}' | sed 's/-[0-9]*$//')
sudo modprobe evdi
```

---

## Complete Implementation Script

For automated testing of all fixes in sequence:

```bash
#!/bin/bash
# DisplayLink Quick Fixes - Complete Implementation
# Run with: bash displaylink-quick-fixes.sh

echo "🚀 Starting DisplayLink Quick Fixes Implementation"
echo "================================================"

# Fix #1: Hyprland Aquamarine Update (CRITICAL)
echo "Fix #1: Updating Hyprland/Aquamarine..."
paru -S hyprland-git aquamarine-git

# Fix #2: KWIN_DRM_NO_AMS Environment Variable  
echo "Fix #2: Adding KWIN_DRM_NO_AMS environment variable..."
if ! grep -q "KWIN_DRM_NO_AMS" ~/.config/hypr/hyprland.conf; then
    echo "env = KWIN_DRM_NO_AMS,1" >> ~/.config/hypr/hyprland.conf
fi

# Fix #3: USB Power Management
echo "Fix #3: Optimizing USB power management..."
for usb in /sys/bus/usb/devices/usb*; do
    echo "on" | sudo tee $usb/power/control > /dev/null
done

# Fix #4: Refresh Rate Enforcement
echo "Fix #4: Enforcing 60Hz refresh rate..."
if ! grep -q "monitor.*DP-3" ~/.config/hypr/hyprland.conf; then
    echo "monitor=DP-3,3840x2160@60.00,1280x0,1" >> ~/.config/hypr/hyprland.conf
fi

# Fix #5: Driver Version Management
echo "Fix #5: Updating to evdi-git..."
paru -S evdi-git

echo "✅ All fixes applied! Reloading Hyprland..."
hyprctl reload

echo "🔍 Verification: Check DP-3 monitor status:"
hyprctl monitors | grep -A10 "DP-3"

echo "✨ Implementation complete! Monitor DP-3 for flickering improvements."
```

---

## Integration with Existing Diagnostic Tools

### Before Implementation
```bash
# Run baseline measurement using existing investigation tools
uv run scripts/debug-display-flicker.py
uv run scripts/realtime-flicker-monitor.py --duration=30
```

### After Each Fix
```bash
# Validate changes using investigation diagnostic tools
uv run scripts/fix-60hz-flicker.py --test-only
hyprctl monitors | grep -A5 "DP-3"

# User observation: Check for visual flickering reduction
echo "Visually monitor DP-3 for 60 seconds - note any 1-3 second flicker pattern"
```

### Success Criteria
- ✅ **Visual**: No 1-3 second flickering pattern on DP-3
- ✅ **Technical**: Stable 60.00Hz refresh rate maintained
- ✅ **Functional**: Windows move normally to DisplayLink monitor
- ✅ **System**: No new errors in system logs

---

## Troubleshooting

### If Fix #1 Doesn't Resolve Issue
1. Verify Aquamarine version contains the evdi fix
2. Check for conflicting DisplayLink packages
3. Test temporarily with different Wayland compositor (GNOME/KDE)

### If Multiple Fixes Don't Help
1. Consider hardware factors (cable quality, USB port, power delivery)
2. Test with different DisplayLink adapter if available
3. Refer to community solutions database for additional options

### Emergency Rollback
```bash
# Quick rollback all changes
sed -i '/KWIN_DRM_NO_AMS/d' ~/.config/hypr/hyprland.conf
sed -i '/monitor.*DP-3/d' ~/.config/hypr/hyprland.conf
paru -S hyprland evdi-dkms
hyprctl reload
```

---

**Implementation Priority**: Execute fixes in order 1→2→3→4→5  
**Expected Resolution**: Fix #1 should resolve the core issue  
**Total Implementation Time**: 15-30 minutes  
**Success Rate**: High confidence based on community validation
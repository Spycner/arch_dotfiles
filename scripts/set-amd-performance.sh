#!/bin/bash
# AMD GPU Performance Mode Script
# Sets AMD GPU to high performance mode to prevent flickering on dual 4K monitors

echo "Setting AMD GPU to high performance mode..."

# Check if AMD GPU device exists
if [ ! -f /sys/class/drm/card1/device/power_dpm_force_performance_level ]; then
    echo "Error: AMD GPU device not found at expected location"
    exit 1
fi

# Set performance mode to high
echo "high" | sudo tee /sys/class/drm/card1/device/power_dpm_force_performance_level > /dev/null

# Verify the setting
current_mode=$(cat /sys/class/drm/card1/device/power_dpm_force_performance_level)
echo "AMD GPU performance mode set to: $current_mode"

if [ "$current_mode" = "high" ]; then
    echo "✅ AMD GPU performance mode successfully set to high"
    echo "This should resolve DisplayPort flickering on dual 4K@60Hz monitors"
else
    echo "⚠️  Warning: Performance mode may not have been set correctly"
fi
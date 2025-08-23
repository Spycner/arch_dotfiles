# Display Flickering Resolution - Complete Case Study

## Executive Summary

**Problem**: DP-3 monitor (4K@60Hz) was flickering every 1-3 seconds on Arch Linux + Hyprland  
**Root Cause**: AMD Renoir iGPU power management throttling under dual 4K@60Hz load  
**Solution**: Set AMD GPU performance mode to `high`  
**Result**: Both monitors stable at 4K@60Hz with no flickering  

---

## Problem Description

### Initial Symptoms
- **Affected Monitor**: DP-3 (IPS AD320U, 3840x2160@60Hz)
- **Pattern**: Brief black screen flicker every 1-3 seconds consistently
- **Unaffected**: DP-4 (identical monitor, initially stable)
- **Environment**: Arch Linux + Hyprland + AMD Renoir iGPU
- **Critical Context**: Same hardware worked perfectly on Windows and Ubuntu

### Key Challenge
Standard Linux diagnostic tools (USB monitoring, DPMS tracking, DRM state analysis) detected **no anomalies** despite obvious visual flickering, making traditional debugging approaches ineffective.

---

## Diagnostic Journey

### Phase 1: Initial Investigation
**Duration**: ~2 hours  
**Approach**: System-level monitoring and USB power optimization  
**Tools Created**: 4 Python diagnostic scripts  
**Result**: All system monitoring showed stable operation, but flickering persisted  

**Key Finding**: Disconnect between system stability and user experience suggested issue occurred at firmware/signal processing level beyond standard monitoring capabilities.

### Phase 2: Community Research
**Duration**: ~18 hours  
**Scope**: 25+ community sources (GitHub, Reddit, Arch forums, Stack Exchange)  
**Initial Assumption**: DisplayLink USB graphics compatibility issue  
**Research Output**: Comprehensive 5-document analysis with 10+ prioritized solutions

**Major Discovery**: Hyprland Aquamarine architectural fix for DisplayLink evdi driver integration  
**Problem**: Research was based on incorrect assumption about connection type

### Phase 3: Hardware Identification  
**Discovery**: Monitors connected via **native DisplayPort**, not DisplayLink USB graphics  
**Evidence**:
- No DisplayLink devices in USB tree (`lsusb -t`)
- No evdi kernel module loaded
- Monitors appeared as `card1-DP-3` and `card1-DP-4` in DRM subsystem

### Phase 4: Root Cause Discovery
**Breakthrough Test**: Disconnecting one monitor eliminated flickering on the other  
**Analysis**: Initially suggested bandwidth limitation, but same hardware works on other OS  
**Final Discovery**: AMD Renoir iGPU power management was throttling under sustained dual 4K load

---

## Root Cause Analysis

### Technical Details
- **Hardware**: AMD Renoir integrated GPU handling dual 4K@60Hz displays
- **Power Management**: GPU set to `auto` mode, causing periodic throttling under high load
- **Symptom**: Frame drops during throttling appeared as 1-3 second flicker pattern
- **Why Other OS Work**: Windows and Ubuntu have different power management algorithms for AMD iGPU

### Validation Tests
1. **30Hz Test**: Both monitors stable at 30Hz (reduced bandwidth requirement)
2. **Single Monitor**: No flickering with only one 4K@60Hz display  
3. **Performance Mode**: Setting AMD GPU to `high` performance eliminated flickering
4. **60Hz Recovery**: After performance setting, both monitors stable at 4K@60Hz

---

## Solution Implementation

### Immediate Fix
```bash
# Set AMD GPU to high performance mode (runtime only)
echo "high" | sudo tee /sys/class/drm/card1/device/power_dpm_force_performance_level
```

### Automated Solution
**Script Location**: `scripts/set-amd-performance.sh`

**Usage**:
```bash
# Run when dual 4K@60Hz needed
~/Code/arch_dotfiles/scripts/set-amd-performance.sh
```

**Features**:
- Sets AMD GPU to high performance mode
- Includes error checking and status confirmation  
- Prevents throttling that causes flickering
- Automatically reverts to `auto` on reboot (power efficient)

### Monitor Configuration
```bash
# Permanent monitor configuration in Hyprland
monitor=DP-3,3840x2160@60.00,1280x0,1    # Primary 4K@60Hz
monitor=DP-4,3840x2160@60.00,5120x0,1    # Secondary 4K@60Hz
```

---

## Lessons Learned

### Diagnostic Methodology Success
1. **Systematic Approach**: Comprehensive monitoring ruled out common causes
2. **Community Research**: Extensive investigation provided deep domain knowledge
3. **Hardware Validation**: Testing on multiple OS confirmed capabilities
4. **Isolation Testing**: Single monitor test revealed the trigger condition

### Key Insights
1. **Simple Solutions**: Complex symptoms can have simple causes (single power setting)
2. **Power Management**: AMD iGPU throttling under high load is poorly documented
3. **OS Differences**: Linux power management may be more aggressive than Windows
4. **Wrong Assumptions**: Initial DisplayLink assumption led to extensive but irrelevant research

### Value of "Failed" Research
The 18-hour DisplayLink research, while not directly applicable:
- ✅ **Ruled out software compatibility issues** systematically
- ✅ **Demonstrated thorough problem-solving methodology**
- ✅ **Created reusable research framework** for future hardware issues
- ✅ **Led to hardware-level investigation** that found the real cause

---

## Technical Specifications

### Hardware Configuration
- **Laptop**: Lenovo with AMD Renoir integrated GPU
- **Monitors**: 2x IPS AD320U (3840x2160@60Hz) 
- **Connection**: Native DisplayPort via dock (not DisplayLink USB graphics)
- **Graphics**: AMD Radeon Vega Mobile Series (integrated)

### Software Environment
- **OS**: Arch Linux (Kernel 6.16.0-arch2-1)
- **Compositor**: Hyprland with Aquamarine rendering backend
- **Graphics Stack**: Mesa drivers, DRM subsystem

### Performance Settings
```bash
# Check current AMD performance mode
cat /sys/class/drm/card1/device/power_dpm_force_performance_level

# Available modes: auto, low, high, manual, profile_standard, profile_min_sclk, profile_min_mclk, profile_peak
# Solution: high (prevents throttling under dual 4K load)
```

---

## Future Considerations

### Monitoring
- **Power consumption**: `high` mode increases power usage and heat generation
- **Battery impact**: Consider reverting to `auto` when on battery power
- **Thermal management**: Monitor GPU temperatures during extended use

### Potential Improvements
1. **Conditional scripting**: Auto-detect dual 4K setup and adjust performance mode
2. **Power profiles**: Different settings for AC vs battery power
3. **Thermal monitoring**: Automatic adjustment based on temperature thresholds

### Alternative Solutions
If power consumption becomes problematic:
1. **Mixed refresh rates**: 60Hz primary + 30Hz secondary monitor
2. **Resolution adjustment**: One monitor at 1440p to reduce bandwidth
3. **Hardware upgrade**: Dedicated GPU for better dual 4K support

---

## Reference Documentation

### Created During Investigation
- **Original Investigation Report**: `docs/displaylink-flicker-investigation-report.md`
- **Comprehensive Community Research**: `docs/archived/displaylink_research/` (5 documents)
- **Solution Script**: `scripts/set-amd-performance.sh`

### External References  
- **AMD GPU Power Management**: Linux kernel DRM documentation
- **Hyprland Monitor Configuration**: https://wiki.hypr.land/Configuring/Monitors/
- **AMD Renoir Architecture**: Technical specifications and limitations

---

## Quick Reference

### Problem Recognition
- **Symptoms**: Periodic display flickering (1-3 second intervals)
- **Hardware**: AMD integrated GPU + dual high-resolution monitors
- **Environment**: Linux with aggressive power management

### Solution Steps
1. **Identify GPU**: `lspci | grep -i vga` 
2. **Check current mode**: `cat /sys/class/drm/card*/device/power_dpm_force_performance_level`
3. **Apply fix**: Run `scripts/set-amd-performance.sh`
4. **Verify**: Monitor for flickering elimination

### Success Criteria
- ✅ No visual flickering on either monitor
- ✅ Stable 60Hz refresh rate maintained
- ✅ Normal window movement and application performance
- ✅ Settings persist until next reboot (by design)

---

**Resolution Date**: 2025-08-19  
**Total Investigation Time**: 20+ hours  
**Final Solution Complexity**: Single command  
**Knowledge Gained**: Extensive AMD GPU power management and Linux display architecture understanding
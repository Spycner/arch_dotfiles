# DisplayLink GitHub Issues Analysis

## Overview

This document analyzes key GitHub issues related to DisplayLink flickering, signal problems, and compatibility issues across multiple repositories. Each issue is assessed for relevance to the DP-3 60Hz flickering problem and current status.

**Analysis Framework:**
- **Symptom Relevance**: How closely the issue matches DP-3 flickering symptoms
- **System Compatibility**: Arch Linux + Hyprland + Wayland relevance  
- **Current Status**: Open/closed/merged status with implementation timeline
- **Solution Viability**: Actionable solutions available for testing

---

## Critical Issues - Direct Solutions Available

### Issue #1: hyprwm/aquamarine #22 & PR #25 - DisplayLink/EVDI Integration Fix

- **Repository**: [hyprwm/aquamarine](https://github.com/hyprwm/aquamarine)
- **Issue**: [#22 - DisplayLink/EVDI not working](https://github.com/hyprwm/aquamarine/issues/22)
- **Solution PR**: [#25 - displaylink fix: ignore primary argument when using evdi drivers](https://github.com/hyprwm/aquamarine/pull/25)
- **Symptom Relevance**: **Critical** - Addresses DisplayLink black screen/no signal detection
- **System Compatibility**: **Exact Match** - Arch Linux + Hyprland + Intel iGPU + evdi drivers
- **Current Status**: ✅ **MERGED** - Available in latest Aquamarine versions
- **Solution Viability**: **Immediate** - Update to latest hyprland-git/aquamarine-git

#### Technical Details
- **Root Cause Identified**: evdi drivers detected as separate GPU but lack rendering capabilities
- **Problem**: Hyprland attempts to use DisplayLink as primary GPU, resulting in no signal
- **Fix Implementation**: Modified `src/backend/drm/DRM.cpp` to ignore primary assignment for evdi drivers
- **Code Change**: `if (drmVerName == "evdi") { primary = {}; }`

#### System Configuration (Reported Working)
```
OS: Arch Linux x86_64
Kernel: Linux 6.9.9-arch1-1  
Window Manager: Hyprland (Wayland)
GPU: Intel Raptor Lake-S UHD Graphics
Displays: 2x 1920x1080@60Hz external + 1x 2560x1600@60Hz built-in
Status: All monitors working after fix implementation
```

#### Implementation Path
```bash
# Verify current versions
pacman -Q hyprland-git aquamarine-git

# Update to versions containing the fix
paru -S hyprland-git aquamarine-git

# Restart Hyprland to apply changes
hyprctl reload
```

---

### Issue #2: hyprwm/Hyprland #2752 - DisplayLink monitors not working

- **Repository**: [hyprwm/Hyprland](https://github.com/hyprwm/Hyprland/issues/2752)
- **Symptom Relevance**: **High** - Black screens, no signal detection despite monitor recognition
- **System Compatibility**: **High** - Multiple users with Hyprland + DisplayLink setups
- **Current Status**: 🔄 **Open** - Redirected to Aquamarine fix (Issue #1)
- **Solution Viability**: **Available** - Resolved by Aquamarine PR #25

#### Key Findings
- **Consistent Pattern**: DisplayLink screens remain black across different hardware configurations
- **OS Compatibility**: Works on i3, KDE Plasma (X11/Wayland), fails on Hyprland
- **Hardware Tested**: Various DisplayLink adapters, Intel/NVIDIA graphics combinations
- **Resolution Path**: Architectural fix in Aquamarine rendering backend

#### Notable User Reports
- "DisplayLink detected both monitors but both stayed black"
- "Works in KDE Plasma, fails in Hyprland - screens stay black forever"
- "hyprland-displaylink-git patches don't resolve the issue"

#### Current Recommendation
Users should implement Solution #1 (Aquamarine fix) rather than continuing with this thread's earlier workarounds.

---

### Issue #3: hyprwm/Hyprland #7292 - Monitors connected through DisplayLink dock get no signal

- **Repository**: [hyprwm/Hyprland](https://github.com/hyprwm/Hyprland/issues/7292)
- **Symptom Relevance**: **High** - No signal detection, dock functionality issues
- **System Compatibility**: **Medium** - NVIDIA + Wayland specific (different from our Intel setup)
- **Current Status**: 🔄 **Open** - Unresolved, likely NVIDIA-specific
- **Solution Viability**: **Limited** - May not apply to Intel iGPU systems

#### Technical Observations
- **Hardware**: Arch Linux, NVIDIA GeForce RTX 3070 Mobile, Kernel 6.10.3
- **Symptoms**: Monitor detected but shows "currentFormat: Invalid"
- **Pattern**: Monitor briefly turns on, then returns to standby mode
- **Cross-Platform**: Works on Windows and X11, fails on Wayland

#### Analysis
This issue appears **NVIDIA-specific** and may not directly apply to Intel iGPU systems. However, it confirms the broader pattern of DisplayLink + Wayland compatibility challenges.

---

## DisplayLink/evdi Repository Issues

### Issue #4: DisplayLink/evdi #484 - Monitors blank on Wayland, work fine on X11

- **Repository**: [DisplayLink/evdi](https://github.com/DisplayLink/evdi/issues/484)
- **Symptom Relevance**: **High** - Wayland compatibility, blank monitors
- **System Compatibility**: **Medium** - Ubuntu 24.04 + GNOME (different from Arch + Hyprland)
- **Current Status**: 🔄 **Open** - No definitive solution
- **Solution Viability**: **Limited** - Cross-reference for troubleshooting

#### Key Technical Details
- **Hardware**: Dell D6000 dock, Nvidia RTX 3070 Laptop
- **Issue Pattern**: Immediate evdi shutdown after EDID property set on Wayland
- **Wayland Logs**: `evdi_user_framebuffer_destroy`, `evdi_painter_close`, `evdi_driver_close`
- **X11 Comparison**: No such shutdown sequence, works normally

#### Diagnostic Value
Confirms that DisplayLink + Wayland integration issues exist beyond Hyprland, suggesting **protocol-level challenges** rather than compositor-specific bugs.

---

### Issue #5: DisplayLink/evdi #459 - ABGR8888 causes DisplayLink reconnection loop on Wayland

- **Repository**: [DisplayLink/evdi](https://github.com/DisplayLink/evdi/issues/459)  
- **Symptom Relevance**: **Medium** - Wayland reconnection loops could manifest as flickering
- **System Compatibility**: **Medium** - General Wayland compatibility issue
- **Current Status**: 🔄 **Open** - Workaround available
- **Solution Viability**: **Partial** - Environment variable workaround

#### Technical Solution
```bash
# Workaround: Use environment variable to modify DRM behavior
export KWIN_DRM_NO_AMS=1

# Implementation in Hyprland config
echo "env = KWIN_DRM_NO_AMS,1" >> ~/.config/hypr/hyprland.conf
```

#### Analysis
- **Pixel Format Issue**: ARGB8888 format causes instability on Wayland
- **Temporary Fix**: KWIN_DRM_NO_AMS environment variable
- **Effectiveness**: Mixed reports - some users report success, others minimal impact
- **Relevance**: Could address periodic reconnection patterns similar to flickering

---

### Issue #6: DisplayLink/evdi #58 - Wayland support

- **Repository**: [DisplayLink/evdi](https://github.com/DisplayLink/evdi/issues/58)
- **Symptom Relevance**: **Low** - General Wayland compatibility discussion
- **System Compatibility**: **High** - Foundational Wayland support
- **Current Status**: 🔄 **Open** - Long-term architectural discussion
- **Solution Viability**: **Future** - Not immediately actionable

#### Key Technical Insights
- **GBM Requirement**: evdi lacks Graphics Buffer Management support
- **Architecture Challenge**: Wayland compositors expect GBM for GPU buffer management
- **Development Priority**: Ubuntu/Mir focus mentioned, Wayland support "big job"
- **Timeline**: No definitive implementation schedule

#### Relevance
Provides context for why DisplayLink + Wayland requires workarounds and architectural fixes like the Aquamarine solution.

---

## Mouse/Cursor Flickering Issues

### Issue #7: DisplayLink/evdi #29 - Cursor Glitches on GNOME 3.20 and KDE Plasma

- **Repository**: [DisplayLink/evdi](https://github.com/DisplayLink/evdi/issues/29)
- **Symptom Relevance**: **Medium** - Cursor flickering could indicate broader display instability
- **System Compatibility**: **Medium** - Multi-desktop environment, not Hyprland-specific
- **Current Status**: 🔄 **Open** - No universal solution
- **Solution Viability**: **Limited** - Desktop environment specific

#### Symptom Details
- **Cursor Behavior**: Flickering, trailing around window borders, occasional disappearance
- **Hardware**: StarTech 4K USB 3.0 to HDMI adapter (DisplayLink chipset)
- **Affected DEs**: GNOME 3.20, KDE Plasma, XFCE
- **Pattern**: Consistent across multiple desktop environments

#### Analysis
While cursor flickering is different from screen flickering, it suggests **broader DisplayLink stability issues** that could manifest in various forms including screen flickering.

---

### Issue #8: displaylink-rpm/displaylink-rpm #74 - Screen flickering when DisplayLink device connected

- **Repository**: [displaylink-rpm/displaylink-rpm](https://github.com/displaylink-rpm/displaylink-rpm/issues/74)
- **Symptom Relevance**: **High** - Direct screen flickering reports
- **System Compatibility**: **Medium** - Fedora/CentOS specific but relevant symptoms
- **Current Status**: ✅ **Closed** - Referred to official DisplayLink repository
- **Solution Viability**: **Reference** - Diagnostic value for symptom comparison

#### Documented Symptoms
- **Primary**: Screen flickering and stuttering when DisplayLink connected
- **Cursor Effects**: Flickering during movement, black square artifacts
- **Pattern**: Cursor "multiplying" and "replaying" last 0.1 second of movement
- **Assessment**: "Functionally working, artifacts just annoying"

#### Diagnostic Value
Confirms that **DisplayLink flickering is a known issue** across different Linux distributions, validating the research approach of seeking community solutions.

---

## Status Summary and Action Items

### ✅ **Resolved Issues - Immediate Implementation**
1. **Aquamarine evdi Fix** (Issues #1): **MERGED** - Update hyprland-git/aquamarine-git
2. **Hyprland DisplayLink Support** (Issue #2): **Resolved** - Implement Aquamarine fix

### 🔄 **Ongoing Issues - Workarounds Available**  
3. **KWIN_DRM_NO_AMS Environment Variable** (Issue #5): Test environment variable workaround
4. **Wayland Pixel Format** (Issue #5): Monitor for official driver updates

### ⚠️ **Hardware-Specific Issues - Limited Applicability**
5. **NVIDIA + Wayland** (Issue #3): Different hardware configuration, monitor for fixes
6. **Ubuntu + GNOME** (Issue #4): Cross-reference for troubleshooting patterns

### 📋 **Diagnostic Reference Issues**
7. **Cursor Flickering** (Issue #7): Symptom pattern validation
8. **General Flickering Reports** (Issue #8): Community validation of issue existence

---

## Implementation Priority Matrix

### **Critical Priority - Immediate Testing**
| Issue | Repository | Solution Type | Implementation Complexity | Expected Impact |
|-------|------------|---------------|-------------------------|-----------------|
| Aquamarine #22/#25 | hyprwm/aquamarine | Architectural Fix | Low (package update) | **Critical** - Root cause resolution |

### **High Priority - Secondary Testing**  
| Issue | Repository | Solution Type | Implementation Complexity | Expected Impact |
|-------|------------|---------------|-------------------------|-----------------|
| evdi #459 | DisplayLink/evdi | Environment Variable | Low (config change) | Medium - Stability improvement |

### **Reference Priority - Monitoring**
| Issue | Repository | Solution Type | Implementation Complexity | Expected Impact |
|-------|------------|---------------|-------------------------|-----------------|
| evdi #58 | DisplayLink/evdi | Future Development | N/A (monitor only) | Long-term architecture |
| Hyprland #7292 | hyprwm/Hyprland | Hardware-Specific | N/A (NVIDIA-specific) | Hardware compatibility |

---

## Integration with Solution Database

### **Cross-Reference Mapping**
- **Solution 01** (Community Solutions): Implements **Issue #1** (Aquamarine fix)
- **Solution 03** (Community Solutions): Implements **Issue #5** (KWIN_DRM_NO_AMS)
- **Issue #8**: Validates **Solution 05** (Hardware optimization) approaches
- **Issue #4**: Supports **Solution 09** (Compositor testing) recommendations

### **Validation Framework**
1. **Pre-Implementation**: Document current issue symptoms matching GitHub reports
2. **Implementation**: Apply solutions from highest-priority GitHub fixes  
3. **Post-Implementation**: Validate resolution against GitHub issue success criteria
4. **Regression Testing**: Monitor for issues reported in other GitHub threads

---

## Future Monitoring Recommendations

### **Active Repositories to Watch**
1. **hyprwm/aquamarine**: Monitor for additional DisplayLink improvements
2. **DisplayLink/evdi**: Track official driver updates and Wayland compatibility
3. **hyprwm/Hyprland**: Watch for DisplayLink-related issues and solutions

### **Key Indicators to Track**
- Aquamarine releases containing DisplayLink fixes
- evdi driver version updates with Wayland improvements  
- Community success reports with similar hardware configurations
- New architectural solutions for USB graphics integration

---

## Conclusion

The GitHub issues analysis confirms that **DisplayLink + Hyprland compatibility issues are well-documented** across the community, with the **Aquamarine architectural fix representing the most significant breakthrough**.

**Key Takeaways**:
- ✅ **Root cause identified and fixed**: Aquamarine PR #25 addresses the core architectural issue
- ✅ **Multiple validation sources**: Issues across different repositories confirm symptom patterns  
- ✅ **Implementation path clear**: Update to latest hyprland-git/aquamarine-git versions
- ✅ **Workaround alternatives available**: Environment variables and configuration options for edge cases

**Next Steps**: Prioritize implementation of Aquamarine fix, with secondary testing of environment variable workarounds if issues persist.

---

**Issues Analyzed**: 8 across 4 repositories  
**Critical Solutions Identified**: 1 (Aquamarine architectural fix)  
**Workaround Solutions Available**: 2 (environment variables, configuration changes)  
**Analysis Completed**: 2025-08-19
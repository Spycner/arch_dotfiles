# Archived Documentation

## DisplayLink Research Collection

**Directory**: `displaylink_research/`  
**Created**: 2025-08-19  
**Status**: **Archived - Based on Incorrect Assumptions**

### Background
This collection contains comprehensive community research conducted under the assumption that monitor flickering was caused by DisplayLink USB graphics compatibility issues. The research involved:

- **18+ hours** of community investigation
- **25+ sources** analyzed (GitHub issues, Reddit, Arch forums, Stack Exchange)
- **5 comprehensive documents** with implementation guides
- **10+ prioritized solutions** for DisplayLink issues

### Why Archived
The research was based on the **incorrect assumption** that the monitors were connected via DisplayLink USB graphics. In reality, the monitors were connected via **native DisplayPort**, making the DisplayLink-specific solutions inapplicable.

### Value of the Research
While not directly applicable to the actual problem, this research:
- ✅ **Demonstrated thorough investigation methodology**  
- ✅ **Systematically ruled out software compatibility issues**
- ✅ **Created reusable research framework** for future hardware problems
- ✅ **Led to hardware-level investigation** that discovered the real cause

### Actual Resolution
The display flickering was resolved by setting AMD GPU performance mode from `auto` to `high`, preventing power management throttling under dual 4K@60Hz load.

**See**: `../display-flickering-resolution.md` for the complete case study and solution.

### Documents in This Archive
1. **README.md** - Navigation guide for DisplayLink research
2. **displaylink-community-research-report.md** - Comprehensive research findings  
3. **displaylink-community-solutions.md** - Database of 10+ DisplayLink solutions
4. **displaylink-github-issues-analysis.md** - GitHub issues analysis across multiple repos
5. **displaylink-quick-fixes.md** - Top 5 ready-to-implement DisplayLink solutions

**Note**: These documents remain valuable as examples of systematic community research methodology, even though the premise was incorrect.
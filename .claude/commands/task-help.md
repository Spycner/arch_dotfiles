---
allowed-tools: Read, Write
description: Documentation and usage examples for the intelligent task management system
model: claude-opus-4-1
---

# Task Management System - Usage Guide

Comprehensive guide for the intelligent task management system combining TodoWrite and Task Master AI.

## System Overview

This task management system provides intelligent routing between TodoWrite (immediate execution) and Task Master AI (strategic planning) based on automatic complexity assessment.

## Core Commands

### `/task [description]`
**Primary command** for all task management with automatic routing.

**Usage Examples:**

#### Simple Tasks (Complexity 1-3) → TodoWrite Direct
```bash
/task "Fix the CSS spacing on the header"
/task "Update the README with installation instructions"  
/task "Run the test suite and check for failures"
```

**Expected Behavior:**
- Immediate TodoWrite creation with 2-3 specific steps
- Direct execution without methodology overhead
- Quick completion focus

#### Moderate Coding Tasks (Complexity 4-7) → TodoWrite + TDD
```bash
/task "Implement user authentication with JWT tokens"
/task "Add data validation to the user registration form"
/task "Create a REST API endpoint for user profiles"
```

**Expected Behavior:**
- TodoWrite with TDD methodology applied
- Test-first development approach
- 4-7 structured tasks including testing steps

#### Moderate Research Tasks (Complexity 4-7) → TodoWrite + Research Focus
```bash
/task "Research best practices for React state management"
/task "Compare different database options for this project"
/task "Investigate performance optimization techniques"
```

**Expected Behavior:**
- TodoWrite with research methodology
- No TDD application (research focused)
- Exploration and documentation emphasis

#### Complex Strategic Tasks (Complexity 8-10) → Task Master Consideration
```bash
/task "Design and implement a complete e-commerce platform"
/task "Build a microservices architecture with user management"
/task "Create a data analytics dashboard with real-time updates"
```

**Expected Behavior:**
- Recognition of high complexity (8-10/10)
- Recommendation for Task Master PRD creation
- Initial TodoWrite for immediate planning steps
- Guidance on strategic project setup

### `/task-status [focus]`
**Dashboard command** providing unified view across all task management systems.

**Usage Examples:**
```bash
/task-status                    # Complete overview
/task-status todos              # Focus on TodoWrite status
/task-status projects           # Focus on Task Master projects
/task-status integration        # Focus on cross-system opportunities
/task-status trends             # Focus on productivity patterns
```

**Output Includes:**
- Current TodoWrite task distribution and progress
- Task Master project status and health
- Integration opportunities between systems
- Productivity insights and recommendations

### `/prd-from-todo [context]`
**Escalation command** for converting TodoWrite tasks to Task Master PRD when complexity grows.

**Usage Examples:**
```bash
/prd-from-todo                          # Analyze all current todos
/prd-from-todo "authentication system"  # Focus on specific feature area
/prd-from-todo "user management"        # Context-specific analysis
```

**Triggers for Use:**
- TodoWrite tasks have grown beyond 8-10 items
- Tasks span multiple domains or systems
- Implementation reveals architectural decisions needed
- Project timeline extends beyond 2-3 sessions

## Decision Matrix Reference

### Complexity Assessment Criteria

**1-2 Complexity: Ultra Simple**
- Single action or obvious change
- No research or planning required
- Immediate execution possible
- Examples: Fix typo, update config value, run existing command

**3-4 Complexity: Simple**
- Few clear steps in sequence
- Single session completion
- Well-understood domain
- Examples: Style updates, documentation changes, small bug fixes

**5-6 Complexity: Moderate**
- Multiple steps with some planning
- May require research or learning
- Single domain expertise
- Examples: Feature implementation, API integration, component creation

**7-8 Complexity: Complex**
- Cross-domain requirements
- Architecture decisions needed
- Multiple session timeline
- Examples: System design, complex features, integration projects

**9-10 Complexity: Strategic**
- Multi-system impact
- Long-term strategic importance
- Formal planning beneficial
- Examples: Platform development, major architecture changes, product initiatives

### Tool Selection Logic

```
Task Request
     ↓
Complexity Assessment (1-10)
     ↓
┌────────────────────────────────────────────────────┐
│ 1-3: TodoWrite Direct                             │
│ • Immediate execution                             │
│ • No methodology overhead                        │
│ • Quick completion focus                         │
└────────────────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────────────────┐
│ 4-7: TodoWrite + Methodology                     │
│ • Coding task? → Apply TDD                       │
│ • Research task? → Research focus                │
│ • Mixed task? → Appropriate methodology          │
└────────────────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────────────────┐
│ 8-10: Task Master Consideration                   │
│ • Recommend PRD creation                          │
│ • Create immediate planning todos                │
│ • Provide strategic guidance                     │
└────────────────────────────────────────────────────┘
```

## TDD Application Guidelines

### When TDD Applies:
- Task involves writing or modifying code
- New testable functionality being created
- Quality assurance is critical
- Integration with existing tested codebase

### When TDD Does NOT Apply:
- Research and exploration tasks
- Documentation creation
- Configuration changes
- Proof of concept development
- Creative or design work

### TDD Task Structure Example:
```
1. Write failing test for login validation
2. Implement minimal validation logic to pass test
3. Write test for password hashing
4. Implement secure password hashing
5. Write integration test for full login flow
6. Implement complete login endpoint
7. Refactor while maintaining green tests
```

## Integration Patterns

### TodoWrite → Task Master Escalation
**When TodoWrite grows complex:**
1. Use `/prd-from-todo` to assess escalation need
2. Create PRD document if warranted
3. Initialize Task Master project structure
4. Preserve existing progress and context
5. Establish new strategic workflow

### Task Master → TodoWrite Execution  
**When Task Master needs immediate action:**
1. Extract specific implementable tasks from strategic plans
2. Create focused TodoWrite lists for immediate execution
3. Maintain connection to broader project context
4. Update Task Master with implementation progress

### Hybrid Workflow
**Using both systems complementarily:**
1. Task Master for strategic planning and project management
2. TodoWrite for tactical execution and immediate tasks
3. Regular sync points between systems
4. Clear handoff protocols and context preservation

## Productivity Optimization Tips

### Effective Usage Patterns:
1. **Start with `/task`** - Let the system route appropriately
2. **Use `/task-status` regularly** - Monitor workflow health
3. **Escalate proactively** - Use `/prd-from-todo` when todos grow
4. **Trust the routing** - System learns from your patterns
5. **Maintain both systems** - Each serves different needs

### Common Anti-Patterns to Avoid:
- Forcing complex tasks into TodoWrite without escalation
- Over-engineering simple tasks with unnecessary methodology
- Ignoring cross-system integration opportunities
- Abandoning one system entirely instead of using both
- Not reviewing and optimizing workflow patterns regularly

## Success Metrics

### TodoWrite Effectiveness:
- Task completion velocity
- Clarity and actionability of task descriptions
- Appropriate methodology application
- Successful single-session completions

### Task Master Integration:
- Strategic project success rates
- PRD quality and completeness
- Long-term project momentum
- Cross-system workflow coherence

### Overall System Health:
- Appropriate tool selection accuracy
- Complexity assessment reliability
- User productivity and satisfaction
- Workflow optimization implementation

## Troubleshooting

### Command Not Working:
```bash
# Check if commands exist
ls ~/.claude/commands/task*.md

# Verify Claude Code recognizes commands
claude --help | grep -A 5 "Available commands"

# Test with simple example
/task "test the task routing system"
```

### Incorrect Routing:
- Review complexity assessment criteria
- Consider task context and scope
- Provide more specific task descriptions
- Use manual routing if automatic fails

### Integration Issues:
- Use `/task-status` to identify problems
- Check Task Master project setup
- Verify TodoWrite state consistency
- Consider workflow pattern adjustments

Remember: This system learns from usage patterns. The more you use it consistently, the better it becomes at routing tasks appropriately for your specific work style and project contexts.

Arguments: $ARGUMENTS (optional: specific topic like "examples", "troubleshooting", "integration")
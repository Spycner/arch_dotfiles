---
allowed-tools: TodoWrite, Read, Write
description: Test the task management routing system with various scenarios
model: claude-opus-4-1
---

# Task Management System Testing

Test various complexity scenarios to validate routing logic:

## Test Scenarios for: $ARGUMENTS

### Scenario 1: Simple Task (Expected Route: TodoWrite Direct)
**Test Input**: "Fix the button color on the login page"
**Expected Complexity**: 2/10
**Expected Route**: TodoWrite Direct
**Expected Behavior**: Create 2-3 simple todos, execute immediately

### Scenario 2: Moderate Coding Task (Expected Route: TodoWrite + TDD)
**Test Input**: "Implement user password reset functionality"  
**Expected Complexity**: 6/10
**Expected Route**: TodoWrite + TDD
**Expected Behavior**: Create 5-7 todos with test-first approach

### Scenario 3: Complex Strategic Task (Expected Route: Task Master Consideration)
**Test Input**: "Design and implement a complete user management system with roles, permissions, and audit logging"
**Expected Complexity**: 9/10  
**Expected Route**: Task Master Consideration
**Expected Behavior**: Recommend PRD creation, initial planning todos

### Scenario 4: Research Task (Expected Route: TodoWrite + Research Focus)
**Test Input**: "Research best practices for API authentication in microservices"
**Expected Complexity**: 5/10
**Expected Route**: TodoWrite + Research Focus (no TDD)
**Expected Behavior**: Create research-focused todos without TDD methodology

## Test Execution

Run each scenario and verify:
1. Correct complexity assessment
2. Appropriate tool routing
3. TDD application (when appropriate)
4. Task structure quality
5. Decision transparency

Report results for scenario: $ARGUMENTS
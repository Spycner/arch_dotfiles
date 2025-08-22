---
allowed-tools: Read, Write, Edit
description: Build structured prompts using Anthropic's 10-step framework from Prompting 101
model: claude-opus-4-1
---

# Prompt Builder - Anthropic's 10-Step Framework

I'll help you build a production-ready prompt using XML tags and best practices from Anthropic's Prompting 101 workshop. This creates a `.prompt.md` working document containing an actual prompt you can copy and use with Claude.

## User Request Analysis

**Request**: $ARGUMENTS

I'll create a complete prompt using XML structure following the 10-step framework:

1. **Task Context** - Role definition using `<role>` tags
2. **Tone Context** - Confidence expectations in `<guidelines>`  
3. **Background Data** - Reference materials in `<context>` and `<background>`
4. **Detailed Instructions** - Step-by-step process in `<instructions>`
5. **Examples** - Few-shot learning in `<examples>` with `<case>` tags
6. **Conversation History** - Prior context in `<history>`
7. **Immediate Task** - Current request in `<task>` tags
8. **Thinking Process** - Reasoning guidance with `<thinking>` structure
9. **Output Formatting** - Response format using `<analysis>`, `<reasoning>`, `<conclusion>`
10. **Prefilled Response** - Template structure to shape output

## XML-Structured Prompt Creation

I'll generate a `.prompt.md` file with two main sections:

**System Prompt** (consistent background):
```xml
<context>Background information and forms</context>
<role>Your role and responsibilities</role>
<guidelines>Behavior constraints and confidence levels</guidelines>
<examples>Few-shot learning cases</examples>
```

**User Prompt** (variable request):
```xml
<task>Specific request</task>
<thinking>Step-by-step reasoning approach</thinking>
<format>Required response structure</format>
```

### Key XML Benefits from Workshop:

- **Clear organization**: XML tags help Claude parse different information types
- **Reference structure**: Instructions can reference specific tags ("analyze the `<form>` first, then the `<sketch>`")
- **Reasoning guidance**: `<thinking>` tags guide the analysis order and approach
- **Format enforcement**: Response structure using `<analysis>`, `<reasoning>`, `<conclusion>`
- **Prevent hallucination**: Clear constraints and confidence requirements

Creating your XML-structured, copy-ready prompt now...
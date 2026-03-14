---
name: semantic-view-optimization
description: "Use for **ALL** requests that mention: create, build, debug, fix, troubleshoot, optimize, improve, or analyze a semantic view. This is the **REQUIRED** entry point - even if the request seems simple. DO NOT attempt to create or debug semantic views manually - always invoke this skill first. This skill guides users through creation, setup, auditing, and SQL generation debugging workflows for semantic views with Cortex Analyst."
---

# Semantic View Optimization Skill

## When to Use

When a user wants to create, debug, or optimize semantic views for Cortex Analyst. This is the entry point for all semantic view workflows.

## Prerequisites

- Fully qualified semantic view name (DATABASE.SCHEMA.VIEW_NAME)
- Snowflake access configured
- Python dependencies: `tomli`, `urllib3`, `requests`, `pyyaml`, `snowflake-connector-python`
  - Install via: `uv pip install tomli urllib3 requests pyyaml snowflake-connector-python`

## ⚠️ MANDATORY INITIALIZATION (Required Before ANY Workflow)

**Before creating, auditing, or debugging semantic views, you MUST complete initialization:**

### Step 1: Load Core Concepts ✋ BLOCKING

**Load**: [semantic_view_concepts.md](reference/semantic_view_concepts.md)

**After loading, confirm you understand:**

- Logical vs physical table/column names
- Which semantic model elements can be added vs enhanced only
- Required use of semantic_view_get.py and semantic_view_set.py tools

**DO NOT PROCEED until you have loaded semantic_view_concepts.md.**

### Step 2: Complete Setup ✋ BLOCKING

**Load**: [setup/SKILL.md](setup/SKILL.md)

**After loading:**

- Create workspace directory as instructed
- Record completion in your working context

**DO NOT PROCEED until setup is complete.**

## Core Capabilities

### Creation

**Load**: [creation/SKILL.md](creation/SKILL.md) - Create new semantic views from scratch using table metadata and VQRs

### Three Primary Workflows

#### 0. Creation Mode

Create new semantic views from scratch with proper structure, relationships, and validation.

**Load**: [creation/SKILL.md](creation/SKILL.md) when user wants to CREATE a new semantic view

#### 1. Audit and Optimize Loop

Comprehensive audit system for semantic views including

1. VQR testing
2. Best Practices verification
3. Custom Criteria evaluation.

**Load**: [audit/SKILL.md](audit/SKILL.md) when user chooses AUDIT MODE

#### 2. Debug Loop

Targeted problem-solving for specific issues with SQL generation from natural language queries.

**Load**: [debug/SKILL.md](debug/SKILL.md) when user chooses DEBUG MODE

## Supporting Skills

### Validation

**Load**: [validation/SKILL.md](validation/SKILL.md) - Validation procedures used by both audit and debug workflows

### Optimization Patterns

**Load**: [optimization/SKILL.md](optimization/SKILL.md) - Library of optimization patterns for semantic view improvements

### Time Tracking (Optional)

**Load**: [time_tracking/SKILL.md](time_tracking/SKILL.md) - Track execution time for tool calls and workflow steps (only load if user explicitly requests time tracking)

### Upload

**Load**: [upload/SKILL.md](upload/SKILL.md) - Upload optimized semantic view YAML to Snowflake (only load when user wants to deploy/upload)

## Workflow Decision Tree

```
Start Session
    ↓
MANDATORY: Complete Initialization
    ├─ Load semantic_view_concepts.md ✋
    └─ Load setup/SKILL.md ✋
    ↓
Is this a NEW semantic view?
    ↓
    YES → Load creation/SKILL.md (CREATION MODE)
    ↓
    NO → Present Mode Selection to User
        ↓
        ├─→ AUDIT MODE → Load audit/SKILL.md
        └─→ DEBUG MODE → Load debug/SKILL.md
```

## Key Principles

1. **Progressive Disclosure**: Load skills incrementally as needed
2. **Modularity**: Each skill is self-contained and reusable
3. **User Confirmation**: Stop at mandatory checkpoints for user input
4. **Validation First**: Always validate before applying changes

## Rules

1. **⚠️ Test Locally First**: By default, test with local YAML files using `semantic_model_file` parameter. Only upload to Snowflake when user explicitly requests deployment.
2. **⚠️ MANDATORY CHECKPOINT FOR ALL OPTIMIZATIONS**: Before any actual semantic view optimization:
   - Wait for explicit user approval (e.g., "approved", "looks good", "proceed")
   - NEVER chain separate optimization edits without user approval between them
3. **⚠️ Always use `uv run python` for scripts**. DO NOT use `python script.py` or `python3 script.py`.

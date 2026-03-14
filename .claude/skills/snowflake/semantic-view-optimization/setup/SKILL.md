---
name: semantic-view-optimization-setup
description: Initial setup for optimization sessions. Downloads semantic view YAML, extracts verified queries, and prepares optimization directory. Required first step before audit or debug workflows.
required_for: All optimization workflows
---

# Setup

## ⚠️ STOP - Prerequisites Check (BLOCKING)

**Before reading ANY of this skill, you MUST have loaded:**

1. ✋ **[reference/semantic_view_concepts.md](../reference/semantic_view_concepts.md)**

   - **Verify**: Can you explain the difference between logical vs physical table/column names? (If no, load it now)
   - **Verify**: Which semantic model elements can be added vs enhanced only? (If no, load it now)

2. ✋ **[reference/semantic_view_get.md](../reference/semantic_view_get.md)**
   - **Verify**: What are the required parameters for semantic_view_get.py? (If you don't know, load it now)
   - **Verify**: What does the `--component` parameter accept? (If you don't know, load it now)

**❌ If you have NOT loaded both files above, STOP and load them NOW.**

**✅ If you HAVE loaded both, state: "Prerequisites verified - proceeding with setup" and continue below.**

---

## When to Load

Start of new optimization session.

## Prerequisites

- Fully qualified semantic view name (DATABASE.SCHEMA.VIEW_NAME)
- Snowflake access configured
- Python environment (managed automatically via `uv`)

## Process

### 1. Semantic View Name

If the user already provided the semantic view name in the conversation (in any format: `DATABASE.SCHEMA.VIEW_NAME`, `database.schema.view_name`, or just `VIEW_NAME` with separate database/schema mentions), then move to step 2.

Otherwise, ask.

### 2. Create Optimization Directory

Create timestamped directory: `semantic_view_optimization_{YYYYMMDD_HHMMSS}/`.

Use the timestamp variable consistently when referencing the directory and do not use global patterns like `*`.

### 3. Download Semantic Model

Use [download_semantic_view_yaml.py](../scripts/download_semantic_view_yaml.py) to download semantic model YAML to optimization directory.

```bash
cd semantic_view_optimization_TIMESTAMP && \
SNOWFLAKE_CONNECTION_NAME=<connection> uv run python ../scripts/download_semantic_view_yaml.py <SEMANTIC_VIEW_NAME> .
```

**Use semantic_view_get.py** (from prerequisites) to extract components as needed:

- Tables: `--component tables`
- Verified queries: `--component verified_queries`
- Custom instructions: `--component custom_instructions`
- Module custom instructions: `--component module_custom_instructions`
- Relationships: `--component relationships`

All commands require both `--file` and `--component` arguments.

Handle Python environment issues if they arise (clean environment approach available).

### 4. Present Summary

Present ONLY this summary:

```
✅ Setup Complete
Directory: semantic_view_optimization_TIMESTAMP/
Semantic Model: X KB
VQRs: Y queries
Ready to proceed.
```

**🛑 MANDATORY STOP - DO NOT PROCEED FURTHER**

Present mode selection.

## Next Skills

- AUDIT MODE → [audit/SKILL.md](../audit/SKILL.md)
- DEBUG MODE → [debug/SKILL.md](../debug/SKILL.md)

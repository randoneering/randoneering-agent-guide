---
name: semantic-view-creation
description: Create new semantic views using FastGen API for automated generation from SQL queries and table metadata. Falls back to manual approach if FastGen fails.
required_skills: [reference/semantic_view_concepts]
---

# Creation Mode

## When to Load

User wants to CREATE a new semantic view (not optimize an existing one).

## ⚠️ CRITICAL: Create TODOs

**MANDATORY**: Use `system_todo_write` to create TODOs for all workflow phases.
All steps below are MANDATORY and cannot be skipped.

## Purpose

Generate a complete, validated semantic view using FastGen API, which automatically:

- Extracts table metadata from Snowflake
- Infers primary keys and relationships
- Generates dimensions, measures, and metrics
- Creates VQRs from SQL queries

Falls back to manual approach if FastGen fails.

## Workflow

### Phase 1: Context Gathering

#### Step 1.1: Get Semantic View Name

Ask user for semantic view name (will be used as model name).

**Format**: Valid identifier (no spaces, lowercase with underscores recommended)

**Example**: `cortex_analyst_usage_analytics`

#### Step 1.2: Get Snowflake Context

Ask user for Snowflake configuration:

1. **Target Database** (required): Database for semantic view
2. **Target Schema** (required): Schema for semantic view

**Note**: Warehouse will be automatically retrieved from the active Snowflake connection settings. No need to ask the user for it.

**Example**:

- Database: `ANALYTICS_DB`
- Schema: `SEMANTIC_MODELS`

#### Step 1.3: Get SQL Context and Business Information

Ask user to provide context in ONE request. They can provide:

- SQL queries
- Table references
- Business context
- Any combination of the above

**⚠️ CRITICAL**: Never generate SQL queries on your own - always wait for user to provide them.

**What to Accept:**

**SQL Queries:**

- Supported: SQL strings, .sql files, .py files with SQL, VQR YAML files
- Extract: Table references, column names, complete SQL statements
- FastGen will use these to generate VQRs

```sql
SELECT account_id, DATE_TRUNC('day', logged_at) as ds,
  COUNT(DISTINCT user_id) as active_users
FROM analytics.logs.usage_logs
WHERE logged_at >= '2024-01-01' GROUP BY account_id, ds;
```

**Table References:**

- Accept fully qualified names: `database.schema.table`
- Query Snowflake to get all columns via `DESCRIBE TABLE`
- Set `sql_source.queries` to empty array in config

**Business Context:**

- Purpose of semantic view
- Key metrics to track
- Important filters or dimensions
- Time granularity (daily, hourly, etc.)

**⚠️ MANDATORY STOPPING POINT**: Wait for user to provide all context before proceeding.

### Phases 2-3: FastGen Workflow

**⚠️ LOAD FASTGEN WORKFLOW**: For detailed FastGen steps, load [fastgen_workflow.md](fastgen_workflow.md).

**Summary**: FastGen automates semantic model generation by:
1. Building and validating a config JSON from extracted SQL tables/queries
2. Calling the FastGen API to generate complete semantic model YAML
3. Handling common errors (permissions, syntax, timeouts)

**If FastGen fails**: Fall back to manual workflow in [fallback_creation.md](fallback_creation.md).

### Phase 4: Validation and Results

#### Step 4.1: Review FastGen Output

Check generated files:

- **YAML**: `<semantic_view_name>_semantic_model.yaml` (complete semantic model with tables, dimensions, measures, metrics, relationships, VQRs)
- **Metadata JSON**: `<semantic_view_name>_metadata.json` containing:
  - `warnings` - Any warnings from FastGen
  - `errors` - Any errors encountered
  - `request_id` - Unique identifier for debugging FastGen requests
  - `suggestions` - Relationship and primary key suggestions from FastGen (if any)

**Inspect the semantic model using `semantic_view_get.py`**:

```bash
cd /Users/joliang/sva_copilot/cortex/snowpilot/semantic_view_autopilot/snova/skills/scripts

# Get overview of all tables
uv run python semantic_view_get.py \
  --file ../../.claude/skills/semantic-view-optimization/creation/<semantic_view_name>_semantic_model.yaml \
  --component tables

# Get all relationships
uv run python semantic_view_get.py \
  --file ../../.claude/skills/semantic-view-optimization/creation/<semantic_view_name>_semantic_model.yaml \
  --component relationships

# Get all verified queries
uv run python semantic_view_get.py \
  --file ../../.claude/skills/semantic-view-optimization/creation/<semantic_view_name>_semantic_model.yaml \
  --component verified_queries
```

**Reference**: See `reference/semantic_view_get.md` for complete tool documentation.

Present warnings/errors to user and determine if fixes needed.

#### Step 4.2: Validate Semantic Model

Run: `reflect_semantic_model(semantic_model_file="creation/<semantic_view_name>_semantic_model.yaml")`

Expected: "Semantic model validated successfully"

If validation fails, options:

- **Minor fixes**: Use `semantic_view_set.py` for targeted edits
- **Major issues**: Regenerate with modified config
- **Structural problems**: Fall back to manual approach

Apply fixes and re-validate until successful.

#### Step 4.3: Present Final Results

Present summary: name, location, counts (tables, columns, relationships, metrics, VQRs), warnings/errors, and file paths (YAML, metadata JSON, config JSON).

**⚠️ MANDATORY STOPPING POINT**: Ask user what they want to do next:

**User Options:**

1. **Enhance relationships and primary keys** → Proceed to Phase 5
2. **Skip to testing/deployment** → Proceed to Phase 6

### Phase 5: Optional Enhancement - Primary Keys and Relationships

**⚠️ OPTIONAL**: Only proceed if user selected option 1 from Step 4.3.

**⚠️ LOAD ENHANCEMENT WORKFLOW**: For detailed enhancement steps, load [primary_keys_and_relationships.md](primary_keys_and_relationships.md).

**Summary**: This optional phase automatically:
1. Identifies potential relationships by analyzing column naming patterns
2. Verifies primary keys using `infer_primary_keys.py` (95% uniqueness threshold)
3. Generates relationships using `relationship_creation.py`
4. Adds verified primary keys and relationships to the semantic model
5. Validates the enhanced model

### Phase 6: Next Steps

**Present user with options for next steps:**

**Option 1: Test with AUDIT MODE** (Recommended)

- Run AUDIT MODE to test VQRs and identify optimization opportunities
- Load `../audit/SKILL.md`

**Option 2: Debug SQL Generation**

- Run DEBUG MODE to troubleshoot specific SQL generation issues
- Load `../debug/SKILL.md`

**Option 3: Deploy to Snowflake**

- Upload semantic view to Snowflake
- Load `../upload/SKILL.md`

**Option 4: Manual Refinement**

- Use `semantic_view_set.py` for targeted edits
- Use `semantic_view_get.py` to inspect specific elements

**⚠️ MANDATORY STOPPING POINT**: Wait for user to select next action.

## Config JSON Reference

See [fastgen_config_spec.md](fastgen_config_spec.md) for complete FastGen configuration schema and examples.

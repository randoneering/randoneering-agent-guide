---
name: deploying-streamlit-to-snowflake
description: 'Deploy Streamlit applications to Snowflake using the `snow` CLI tool. Covers snowflake.yml manifest configuration, compute pools, container runtime, and deployment workflow.'
---

# Deploying Streamlit to Snowflake

Deploy local Streamlit apps to Snowflake using the `snow` CLI.

## Prerequisites

- **Snowflake CLI v3.14.0+**: Run `snow --version` to verify
- **A Streamlit app**: Your main entry point file (e.g., `streamlit_app.py`)
- **A configured Snowflake connection**: Run `snow connection list` to verify

## Deployment Workflow

### Step 1: Create Project Structure

```text
my_streamlit_app/
  snowflake.yml        # Deployment manifest (required)
  streamlit_app.py     # Main entry point
  pyproject.toml       # Python dependencies
  src/                 # Additional modules
    helpers.py
  data/                # Data files
    sample.csv
```

**Quick start with templates:**
```bash
# Single-page app
snow init my_app --template streamlit_vnext_single_page

# Multi-page app
snow init my_app --template streamlit_vnext_multi_page
```

### Step 2: Create `snowflake.yml`

```yaml
definition_version: 2
entities:
  my_streamlit:
    type: streamlit
    identifier:
      name: MY_APP_NAME           # App name in Snowflake
      database: MY_DATABASE
      schema: MY_SCHEMA
    query_warehouse: MY_WAREHOUSE
    compute_pool: STREAMLIT_DEDICATED_POOL
    runtime_name: SYSTEM$ST_CONTAINER_RUNTIME_PY3_11
    external_access_integrations:
      - PYPI_ACCESS_INTEGRATION   # For pip installs
    main_file: streamlit_app.py
    artifacts:
      - streamlit_app.py
      - pyproject.toml
      - src/helpers.py            # Include ALL files your app needs
      - data/sample.csv
```

### Step 3: Deploy

```bash
cd my_streamlit_app
snow streamlit deploy --replace
```

The `--replace` flag updates an existing app with the same name.

### Step 4: Access Your App

After deployment, `snow` outputs the app URL. You can also find it in Snowsight under **Projects > Streamlit**.

## Configuration Reference

| Parameter | Description | Example |
|-----------|-------------|---------|
| `name` | Unique app identifier | `MY_DASHBOARD` |
| `database` | Target database | `ANALYTICS_DB` |
| `schema` | Target schema | `DASHBOARDS` |
| `query_warehouse` | Warehouse for SQL queries | `COMPUTE_WH` |
| `compute_pool` | Pool running the Python runtime | `STREAMLIT_DEDICATED_POOL` |
| `runtime_name` | Container runtime version | `SYSTEM$ST_CONTAINER_RUNTIME_PY3_11` |
| `main_file` | Entry point script | `streamlit_app.py` |
| `artifacts` | All files to upload (must include main_file) | See example above |
| `external_access_integrations` | Network access for pip, APIs | `PYPI_ACCESS_INTEGRATION` |

## Key Points

1. **Always use container runtime** (`runtime_name`) for best performance
2. **List ALL files** in `artifacts` - anything not listed won't be deployed
3. **Dependencies go in `pyproject.toml`** - installed automatically on deploy
4. **Iterate with `--replace`** - redeploy without creating duplicates

## Troubleshooting

**App not updating?**
- Ensure you're using `--replace`
- Check that changed files are in `artifacts`

**Import errors?**
- Verify all modules are in `artifacts`
- Check `pyproject.toml` has all pip dependencies

**Network/pip errors?**
- Add `PYPI_ACCESS_INTEGRATION` to `external_access_integrations`

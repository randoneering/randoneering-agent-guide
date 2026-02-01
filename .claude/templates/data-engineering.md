# Data Engineering Project (DBT + Snowflake)

## Project Context

**Project Name:** [Pipeline/Warehouse Name]

**Description:** [What data this pipeline processes]

**Tech Stack:**
- Snowflake (data warehouse)
- DBT Core (transformations)
- Python (orchestration/extraction)
- [Scheduler: Airflow / Dagster / Prefect]

---

## Project Structure

```
├── dbt/
│   ├── dbt_project.yml
│   ├── models/
│   │   ├── staging/         # 1:1 with sources, light cleaning
│   │   ├── intermediate/    # Business logic, joins
│   │   └── marts/           # Final tables for consumption
│   ├── seeds/               # Static reference data
│   ├── snapshots/           # SCD Type 2 tracking
│   ├── macros/              # Reusable SQL
│   └── tests/               # Custom data tests
├── scripts/                 # Python extraction scripts
├── orchestration/           # DAGs or flow definitions
└── profiles.yml             # (gitignored) connection config
```

---

## Snowflake Configuration

### Warehouse Sizing

| Workload | Warehouse | Size | Auto-suspend |
|----------|-----------|------|--------------|
| Dev/ad-hoc | DEV_WH | X-Small | 60s |
| DBT runs | TRANSFORM_WH | Small | 120s |
| BI queries | ANALYTICS_WH | Medium | 300s |
| Heavy loads | LOAD_WH | Large | 60s |

### Query Result Caching

Snowflake caches results for 24 hours. To maximize cache hits:
- Use deterministic queries (avoid `CURRENT_TIMESTAMP()` in main query)
- Query from same warehouse when possible
- Avoid `ORDER BY` on non-deterministic columns

### Cost Control

```sql
-- Set statement timeout
ALTER WAREHOUSE TRANSFORM_WH SET STATEMENT_TIMEOUT_IN_SECONDS = 3600;

-- Resource monitors
CREATE RESOURCE MONITOR monthly_limit
  WITH CREDIT_QUOTA = 1000
  TRIGGERS
    ON 75 PERCENT DO NOTIFY
    ON 100 PERCENT DO SUSPEND;
```

---

## DBT Guidelines

### Model Naming

```
staging/
  stg_{source}__{table}.sql      # stg_stripe__customers.sql

intermediate/
  int_{domain}__{description}.sql # int_orders__joined.sql

marts/
  {domain}/
    dim_{entity}.sql              # dim_customers.sql
    fct_{event}.sql               # fct_orders.sql
```

### Model Configuration

```yaml
# dbt_project.yml
models:
  project_name:
    staging:
      +materialized: view
      +schema: staging
    intermediate:
      +materialized: ephemeral  # or view
    marts:
      +materialized: table
      +schema: analytics
```

### Staging Models

```sql
-- models/staging/stg_stripe__customers.sql
with source as (
    select * from {{ source('stripe', 'customers') }}
),

renamed as (
    select
        id as customer_id,
        email,
        created as created_at,
        -- Clean and cast here
        nullif(trim(name), '') as customer_name
    from source
)

select * from renamed
```

### Data Quality Tests

```yaml
# models/staging/_stg_stripe__models.yml
version: 2

models:
  - name: stg_stripe__customers
    columns:
      - name: customer_id
        tests:
          - unique
          - not_null
      - name: email
        tests:
          - not_null
          - accepted_values:
              values: ['%@%.%']
              config:
                where: "email is not null"
```

### Custom Tests

```sql
-- tests/assert_positive_amounts.sql
select order_id, amount
from {{ ref('fct_orders') }}
where amount < 0
```

---

## Development Workflow

### Setup

```bash
cd dbt/
python -m venv .venv && source .venv/bin/activate
pip install dbt-snowflake

# Configure profiles.yml (not committed)
dbt debug  # Verify connection
```

### Daily Commands

```bash
# Run all models
dbt run

# Run specific model and downstream
dbt run --select stg_stripe__customers+

# Test everything
dbt test

# Generate docs
dbt docs generate && dbt docs serve
```

### Before Merging

```bash
dbt run --full-refresh  # Test full refresh works
dbt test                 # All tests pass
dbt build               # Run + test together
```

---

## STAR Schema Design

### Dimension Tables (dim_)

```sql
-- dim_customers.sql
select
    customer_id,
    customer_name,
    email,
    segment,
    created_at,
    -- SCD Type 2 fields if needed
    valid_from,
    valid_to,
    is_current
from {{ ref('int_customers__enriched') }}
```

### Fact Tables (fct_)

```sql
-- fct_orders.sql
select
    -- Surrogate key
    {{ dbt_utils.generate_surrogate_key(['order_id']) }} as order_key,

    -- Foreign keys to dimensions
    customer_id,
    product_id,
    date_id,

    -- Measures
    quantity,
    unit_price,
    discount_amount,
    total_amount,

    -- Metadata
    created_at
from {{ ref('int_orders__joined') }}
```

---

## Incremental Models

```sql
-- models/marts/fct_events.sql
{{
    config(
        materialized='incremental',
        unique_key='event_id',
        incremental_strategy='merge'
    )
}}

select
    event_id,
    user_id,
    event_type,
    event_timestamp,
    properties
from {{ ref('stg_analytics__events') }}

{% if is_incremental() %}
where event_timestamp > (select max(event_timestamp) from {{ this }})
{% endif %}
```

---

## Snapshots (SCD Type 2)

```sql
-- snapshots/customers_snapshot.sql
{% snapshot customers_snapshot %}

{{
    config(
        target_schema='snapshots',
        unique_key='customer_id',
        strategy='timestamp',
        updated_at='updated_at'
    )
}}

select * from {{ source('app', 'customers') }}

{% endsnapshot %}
```

---

## Common Tasks

### Add New Source

1. Add to `models/staging/_sources.yml`
2. Create staging model `stg_{source}__{table}.sql`
3. Add schema tests in `_stg_{source}__models.yml`
4. Run `dbt run --select stg_{source}__{table}`
5. Run `dbt test --select stg_{source}__{table}`

### Debug Failing Model

```bash
# Compile to see generated SQL
dbt compile --select model_name

# Check compiled SQL
cat target/compiled/project/models/path/model_name.sql

# Run with debug logging
dbt --debug run --select model_name
```

---

## Do Not

- Store credentials in code (use environment variables)
- Run `dbt run` without `--select` in production
- Skip tests before merging
- Use `SELECT *` in staging models (explicit columns only)
- Create circular dependencies between models
- Modify source tables directly

---

## Verification Before Completion

```bash
dbt compile           # Syntax valid
dbt run --select +model_name+  # Model and dependencies work
dbt test --select +model_name+ # Tests pass
```

Check Snowflake query history for unexpected full table scans.

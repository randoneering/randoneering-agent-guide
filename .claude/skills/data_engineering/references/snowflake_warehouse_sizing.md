# Snowflake Warehouse Sizing Guide

## Warehouse Size Reference

| Size | Credits/Hour | Servers | Memory/Server | Use Case |
|------|--------------|---------|---------------|----------|
| X-Small | 1 | 1 | ~8GB | Dev/test, small queries |
| Small | 2 | 2 | ~16GB | Dashboards, light BI |
| Medium | 4 | 4 | ~32GB | Standard ETL, moderate queries |
| Large | 8 | 8 | ~64GB | Heavy transformations, large joins |
| X-Large | 16 | 16 | ~128GB | Very large datasets, complex analytics |
| 2X-Large | 32 | 32 | ~256GB | Massive datasets, ML workloads |
| 3X-Large | 64 | 64 | ~512GB | Enterprise-scale analytics |
| 4X-Large | 128 | 128 | ~1TB | Extreme workloads |

**Key insight:** Doubling warehouse size = 2× cost but 2× performance (linear scaling for single query).

## Sizing Decision Framework

### Step 1: Identify Workload Type

**OLTP-style (Small-Medium):**
- Characteristics: Many small, concurrent queries
- Pattern: Point lookups, simple aggregations
- Example: Customer lookup, order status check
- Recommendation: Scale OUT (multi-cluster) not UP

**ETL/ELT (Medium-Large):**
- Characteristics: Batch processing, table scans
- Pattern: Large INSERT/UPDATE/MERGE operations
- Example: Daily data loads, transformations
- Recommendation: Scale UP for faster processing

**Analytics/BI (Small-X-Large):**
- Characteristics: Ad-hoc queries, complex aggregations
- Pattern: Multi-table joins, window functions
- Example: Business intelligence dashboards
- Recommendation: Size based on data volume and complexity

**Data Science/ML (Large-4X-Large):**
- Characteristics: Feature engineering, model training
- Pattern: Statistical functions, pivots, large datasets
- Example: Training data preparation, correlation analysis
- Recommendation: Scale UP, leverage Snowpark

### Step 2: Data Volume Guidelines

**Row count-based sizing:**
- < 100K rows → X-Small to Small
- 100K - 1M rows → Small to Medium
- 1M - 10M rows → Medium to Large
- 10M - 100M rows → Large to X-Large
- 100M - 1B rows → X-Large to 2X-Large
- > 1B rows → 2X-Large and above

**Data size-based sizing:**
- < 1GB → X-Small to Small
- 1GB - 10GB → Small to Medium
- 10GB - 100GB → Medium to Large
- 100GB - 1TB → Large to X-Large
- > 1TB → X-Large and above

### Step 3: Query Complexity Factor

Multiply base size recommendation by complexity:

**Low complexity (1x):**
- Single table scans
- Simple filters and aggregations
- Pre-aggregated data

**Medium complexity (1.5x):**
- 2-3 table joins
- GROUP BY with multiple dimensions
- Window functions on moderate data

**High complexity (2x):**
- 5+ table joins
- Complex window functions
- Multiple nested subqueries
- PIVOT/UNPIVOT operations

**Very high complexity (3x):**
- Cartesian products (unintentional)
- Recursive CTEs on large datasets
- Complex statistical functions
- Machine learning operations

## Workload-Specific Recommendations

### DBT Transformations

**Development (X-Small to Small):**
```sql
-- dbt_project.yml
models:
  my_project:
    +target: dev
    +warehouse: DBT_DEV_XS
```

**Production Incremental Models (Small to Medium):**
```sql
-- config for incremental models
{{ config(
    materialized='incremental',
    warehouse='DBT_PROD_S',
    incremental_strategy='merge'
) }}
```

**Full Refresh/Backfill (Medium to Large):**
```bash
# Use larger warehouse for full refresh
dbt run --full-refresh --target prod_large
```

**Sizing matrix for DBT:**
- Staging models (< 10M rows): X-Small to Small
- Intermediate models (10M-100M rows): Small to Medium
- Fact tables (100M+ rows): Medium to Large
- Dimension tables: X-Small to Small (usually small)

### Dashboard/BI Workloads

**Single user (X-Small to Small):**
- Pre-aggregated data via materialized views
- Simple filtering and sorting
- Cache hits from result cache

**Team dashboards (Small to Medium):**
- 10-50 concurrent users
- Enable multi-cluster auto-scaling
- Min clusters: 1, Max clusters: 3-5

**Company-wide reports (Medium to Large):**
- 50+ concurrent users
- Multi-cluster warehouse required
- Min clusters: 2, Max clusters: 10

**Configuration example:**
```sql
CREATE WAREHOUSE REPORTING_WH WITH
    WAREHOUSE_SIZE = 'SMALL'
    AUTO_SUSPEND = 300                    -- 5 minutes
    AUTO_RESUME = TRUE
    MIN_CLUSTER_COUNT = 1
    MAX_CLUSTER_COUNT = 5
    SCALING_POLICY = 'STANDARD'           -- Queue up to 1 minute before scaling
    COMMENT = 'Multi-cluster for BI tools';
```

### ETL/Data Loading

**Continuous micro-batches (Small):**
- Streaming ingestion
- Small file loads every few minutes
- Keep warehouse running with auto-suspend = 60s

**Hourly batch loads (Small to Medium):**
- Moderate data volumes (< 1GB/hour)
- Standard transformations
- Auto-suspend after 5-10 minutes

**Daily batch processing (Medium to X-Large):**
- Large data volumes (10GB+ per day)
- Complex transformations and joins
- Size based on SLA requirements

**Pattern - Separate load and transform warehouses:**
```sql
-- Small warehouse for COPY INTO (I/O bound)
CREATE WAREHOUSE LOAD_WH WITH 
    WAREHOUSE_SIZE = 'SMALL'
    AUTO_SUSPEND = 60;

-- Larger warehouse for transformations (compute bound)
CREATE WAREHOUSE TRANSFORM_WH WITH 
    WAREHOUSE_SIZE = 'MEDIUM'
    AUTO_SUSPEND = 300;

-- ETL script
USE WAREHOUSE LOAD_WH;
COPY INTO staging_table FROM @my_stage;

USE WAREHOUSE TRANSFORM_WH;
INSERT INTO fact_table 
SELECT ... FROM staging_table;  -- Complex transformation
```

## Cost Optimization Strategies

### 1. Auto-Suspend Tuning

**Aggressive (30-60 seconds):**
- Development environments
- Infrequent query patterns
- Cost-sensitive workloads

**Moderate (5-10 minutes):**
- Production ETL jobs
- Scheduled reporting
- Balance between cost and cache

**Conservative (30-60 minutes):**
- Active business hours only
- Frequent dashboard usage
- Cache persistence is critical

**Calculation example:**
```sql
-- Estimate cost impact of auto-suspend settings
WITH warehouse_sessions AS (
    SELECT 
        WAREHOUSE_NAME,
        START_TIME,
        END_TIME,
        TIMESTAMPDIFF(second, START_TIME, END_TIME) as session_seconds
    FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
    WHERE START_TIME >= DATEADD(day, -30, CURRENT_DATE())
)
SELECT 
    WAREHOUSE_NAME,
    COUNT(*) as session_count,
    SUM(session_seconds) / 3600 as actual_hours,
    -- Simulate 1-minute auto-suspend
    SUM(GREATEST(session_seconds, 60)) / 3600 as cost_with_1min_suspend,
    -- Simulate 10-minute auto-suspend  
    SUM(GREATEST(session_seconds, 600)) / 3600 as cost_with_10min_suspend
FROM warehouse_sessions
GROUP BY WAREHOUSE_NAME;
```

### 2. Resource Monitors

**Set up spending limits:**
```sql
-- Create monthly budget
CREATE RESOURCE MONITOR monthly_limit WITH
    CREDIT_QUOTA = 1000                   -- 1000 credits per month
    FREQUENCY = MONTHLY
    START_TIMESTAMP = IMMEDIATELY
    TRIGGERS 
        ON 75 PERCENT DO NOTIFY            -- Alert at 75%
        ON 90 PERCENT DO SUSPEND           -- Suspend at 90%
        ON 100 PERCENT DO SUSPEND_IMMEDIATE;  -- Kill queries at 100%

-- Apply to warehouse
ALTER WAREHOUSE PRODUCTION_WH SET RESOURCE_MONITOR = monthly_limit;

-- Monitor usage
SELECT * FROM TABLE(INFORMATION_SCHEMA.RESOURCE_MONITOR_USAGE('monthly_limit'));
```

### 3. Workload Separation

**Anti-pattern - Single warehouse for everything:**
- ETL, BI, and ad-hoc queries compete
- Unpredictable costs
- Performance interference

**Best practice - Dedicated warehouses:**
```sql
-- Development (X-Small)
CREATE WAREHOUSE DEV_WH WITH WAREHOUSE_SIZE = 'X-SMALL' AUTO_SUSPEND = 60;

-- ETL (Medium)
CREATE WAREHOUSE ETL_WH WITH WAREHOUSE_SIZE = 'MEDIUM' AUTO_SUSPEND = 300;

-- BI Reporting (Small, multi-cluster)
CREATE WAREHOUSE BI_WH WITH 
    WAREHOUSE_SIZE = 'SMALL'
    MIN_CLUSTER_COUNT = 1
    MAX_CLUSTER_COUNT = 3;

-- Ad-hoc Analytics (Medium)
CREATE WAREHOUSE ANALYTICS_WH WITH WAREHOUSE_SIZE = 'MEDIUM' AUTO_SUSPEND = 600;

-- Data Science (Large)
CREATE WAREHOUSE DS_WH WITH WAREHOUSE_SIZE = 'LARGE' AUTO_SUSPEND = 1800;
```

### 4. Query-Level Optimization

**Before sizing up, optimize queries:**
- Add WHERE clauses to filter early
- Use clustering keys for large tables
- Avoid SELECT * in production
- Leverage materialized views
- Use QUALIFY instead of subqueries for window functions

**Example - Inefficient query:**
```sql
-- Bad: Scans entire 1TB table
SELECT customer_id, order_date, amount
FROM orders
ORDER BY order_date DESC
LIMIT 100;

-- Good: Partition pruning + clustering
SELECT customer_id, order_date, amount
FROM orders
WHERE order_date >= DATEADD(day, -7, CURRENT_DATE())
ORDER BY order_date DESC
LIMIT 100;
-- Execution time: 30s → 2s (no warehouse resize needed)
```

## Monitoring and Right-Sizing

### Key Metrics to Track

```sql
-- Warehouse utilization by hour
SELECT 
    WAREHOUSE_NAME,
    DATE_TRUNC('hour', START_TIME) as hour,
    WAREHOUSE_SIZE,
    SUM(CREDITS_USED) as credits,
    COUNT(DISTINCT QUERY_ID) as query_count,
    AVG(EXECUTION_TIME / 1000) as avg_execution_seconds,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXECUTION_TIME / 1000) as p95_seconds
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE START_TIME >= DATEADD(day, -7, CURRENT_DATE())
  AND WAREHOUSE_NAME IS NOT NULL
GROUP BY 1, 2, 3
ORDER BY 1, 2 DESC;
```

### Signs You Need to Resize

**Scale UP (larger warehouse) when:**
- Queries consistently exceed SLA (e.g., > 30s for dashboards)
- CPU utilization consistently > 80%
- Spillage to remote disk occurs (check BYTES_SPILLED_TO_REMOTE_STORAGE)
- Users complain about slow performance

```sql
-- Detect spillage issues
SELECT 
    QUERY_ID,
    EXECUTION_TIME / 1000 as seconds,
    BYTES_SPILLED_TO_LOCAL_STORAGE / 1024 / 1024 / 1024 as gb_spilled_local,
    BYTES_SPILLED_TO_REMOTE_STORAGE / 1024 / 1024 / 1024 as gb_spilled_remote
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE START_TIME >= DATEADD(day, -1, CURRENT_DATE())
  AND BYTES_SPILLED_TO_REMOTE_STORAGE > 0  -- Remote spill = bad
ORDER BY BYTES_SPILLED_TO_REMOTE_STORAGE DESC
LIMIT 20;
```

**Scale OUT (multi-cluster) when:**
- Queries queue frequently (check QUEUED_PROVISIONING_TIME)
- Concurrent user count exceeds warehouse capacity
- BI dashboards timeout during peak hours

```sql
-- Detect queuing
SELECT 
    WAREHOUSE_NAME,
    DATE_TRUNC('hour', START_TIME) as hour,
    COUNT(*) as total_queries,
    SUM(CASE WHEN QUEUED_PROVISIONING_TIME > 0 THEN 1 ELSE 0 END) as queued_count,
    AVG(QUEUED_PROVISIONING_TIME / 1000) as avg_queue_seconds
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE START_TIME >= DATEADD(day, -7, CURRENT_DATE())
GROUP BY 1, 2
HAVING queued_count > 0
ORDER BY avg_queue_seconds DESC;
```

**Scale DOWN when:**
- Average query execution time << 5 seconds
- Warehouse idle time > 50% during active hours
- Credit usage low relative to warehouse size

```sql
-- Find underutilized warehouses
WITH warehouse_stats AS (
    SELECT 
        WAREHOUSE_NAME,
        COUNT(*) as query_count,
        AVG(EXECUTION_TIME / 1000) as avg_exec_seconds,
        SUM(CREDITS_USED) as total_credits
    FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
    WHERE START_TIME >= DATEADD(day, -30, CURRENT_DATE())
    GROUP BY 1
)
SELECT 
    WAREHOUSE_NAME,
    query_count,
    ROUND(avg_exec_seconds, 2) as avg_seconds,
    total_credits,
    CASE 
        WHEN avg_exec_seconds < 2 THEN 'Consider downsizing'
        WHEN avg_exec_seconds > 30 THEN 'Consider upsizing'
        ELSE 'Right-sized'
    END as recommendation
FROM warehouse_stats
ORDER BY total_credits DESC;
```

## Advanced Patterns

### Pattern 1: Time-Based Warehouse Sizing

**Use case:** Different sizes for business vs off-hours

```sql
-- Create task to resize warehouse
CREATE OR REPLACE TASK resize_warehouse_daytime
    WAREHOUSE = ADMIN_WH
    SCHEDULE = 'USING CRON 0 8 * * MON-FRI America/New_York'  -- 8 AM weekdays
AS
    ALTER WAREHOUSE REPORTING_WH SET WAREHOUSE_SIZE = 'MEDIUM';

CREATE OR REPLACE TASK resize_warehouse_night
    WAREHOUSE = ADMIN_WH
    SCHEDULE = 'USING CRON 0 18 * * MON-FRI America/New_York'  -- 6 PM weekdays
AS
    ALTER WAREHOUSE REPORTING_WH SET WAREHOUSE_SIZE = 'SMALL';

ALTER TASK resize_warehouse_daytime RESUME;
ALTER TASK resize_warehouse_night RESUME;
```

### Pattern 2: Query Tags for Warehouse Routing

**Use case:** Route specific query types to appropriate warehouses

```sql
-- DBT macro to set query tags
{% macro set_query_tag(model_type) %}
    ALTER SESSION SET QUERY_TAG = '{"model_type": "{{ model_type }}"}';
{% endmacro %}

-- In DBT model
{{ config(
    pre_hook=set_query_tag('fact_table')
) }}

-- Route based on tags (application logic)
-- Fact tables → Large warehouse
-- Dimensions → Small warehouse
```

### Pattern 3: Warehouse Pools

**Use case:** Isolate team workloads

```sql
-- Team-specific warehouses
CREATE WAREHOUSE DATA_SCIENCE_WH WITH WAREHOUSE_SIZE = 'LARGE';
CREATE WAREHOUSE ANALYTICS_WH WITH WAREHOUSE_SIZE = 'MEDIUM';
CREATE WAREHOUSE DEV_TEAM_WH WITH WAREHOUSE_SIZE = 'SMALL';

-- Assign via roles
GRANT USAGE ON WAREHOUSE DATA_SCIENCE_WH TO ROLE DATA_SCIENTIST;
GRANT USAGE ON WAREHOUSE ANALYTICS_WH TO ROLE ANALYST;
GRANT USAGE ON WAREHOUSE DEV_TEAM_WH TO ROLE DEVELOPER;
```

## Quick Reference Checklist

- [ ] Identified workload type (OLTP, ETL, Analytics, ML)
- [ ] Estimated data volume and query complexity
- [ ] Set appropriate auto-suspend (30s-60min based on usage)
- [ ] Configured auto-resume = TRUE
- [ ] Separated workloads into dedicated warehouses
- [ ] Set up resource monitors for cost control
- [ ] Enabled multi-cluster for concurrent BI workloads
- [ ] Monitored query performance and spillage
- [ ] Optimized queries before resizing warehouse
- [ ] Documented sizing decisions for future reference

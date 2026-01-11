---
name: data-engineering
description: Snowflake and DBT data engineering workflows covering warehouse sizing, query result caching optimization, STAR schema design, and DBT data quality testing patterns. Use when working with Snowflake for query optimization or warehouse configuration, or when developing DBT models with focus on data quality testing and validation.
---

# Data Engineering: Snowflake & DBT

Modern data warehouse engineering with Snowflake optimization and DBT best practices for data quality.

## Core Capabilities

### 1. Snowflake Query Result Caching

**When to use:** Optimizing query performance, reducing compute costs, understanding cache behavior.

**Key concepts:**
- Result cache: Stores query results for 24 hours
- Metadata cache: Stores object metadata (tables, columns)
- Warehouse cache: Stores raw data on local SSD

**Quick reference:**
```sql
-- Check if query used result cache
SELECT * FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE QUERY_ID = 'your-query-id';
-- Look at BYTES_SCANNED (0 = result cache hit)

-- Disable result cache for testing
ALTER SESSION SET USE_CACHED_RESULT = FALSE;

-- Clear result cache (change schema/table)
ALTER TABLE my_table SET COMMENT = 'cache bust';
```

**Optimization strategies:**
- Identical queries (same SQL text) hit result cache
- Add CURRENT_TIMESTAMP() to prevent caching for real-time data
- Use time-based clustering for time-series queries
- Schedule recurring queries to keep cache warm

**See `references/snowflake_caching.md` for detailed cache behavior and optimization patterns.**

### 2. Snowflake Warehouse Sizing

**When to use:** Right-sizing warehouses, optimizing costs, troubleshooting performance.

**Quick sizing guide:**
- **XS (1 credit/hr)**: Development, small queries (<100k rows)
- **S (2 credits/hr)**: Dashboards, regular reporting (100k-1M rows)
- **M (4 credits/hr)**: ETL jobs, moderate data volumes (1M-10M rows)
- **L (8 credits/hr)**: Large transformations, complex joins (10M-100M rows)
- **XL+ (16+ credits/hr)**: Heavy analytics, massive datasets (>100M rows)

**Scaling strategies:**
- **Scale up**: Faster individual queries (larger warehouse size)
- **Scale out**: More concurrent queries (multi-cluster warehouse)
- **Auto-suspend**: Set to 60-300 seconds for most workloads
- **Auto-resume**: Always enable

**Monitoring:**
```sql
-- Warehouse usage by size
SELECT WAREHOUSE_NAME, WAREHOUSE_SIZE, 
       SUM(CREDITS_USED) as total_credits,
       COUNT(*) as query_count
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE START_TIME >= DATEADD(day, -7, CURRENT_DATE())
GROUP BY 1, 2
ORDER BY 3 DESC;
```

**See `references/snowflake_warehouse_sizing.md` for workload-specific recommendations and cost optimization.**

### 3. DBT Data Quality Testing

**When to use:** Implementing data validation, ensuring data quality, preventing bad data in production.

**Test hierarchy:**
1. **Generic tests** (built-in): unique, not_null, accepted_values, relationships
2. **Custom generic tests**: Reusable across models
3. **Singular tests**: One-off SQL validation queries

**Quick implementation:**
```yaml
# models/schema.yml
models:
  - name: dim_customers
    columns:
      - name: customer_id
        tests:
          - unique
          - not_null
      - name: status
        tests:
          - accepted_values:
              values: ['active', 'inactive', 'pending']
      - name: country_code
        tests:
          - relationships:
              to: ref('countries')
              field: country_code
```

**Common test patterns:**
- Freshness checks: `freshness: {warn_after: {count: 24, period: hour}}`
- Row count validation: Custom test comparing source vs target
- Referential integrity: `relationships` test for foreign keys
- Business logic: Singular tests for complex rules

**See `references/dbt_testing_patterns.md` for comprehensive testing strategies, custom test examples, and STAR schema validation.**

**Use `scripts/generate_dbt_tests.py` to scaffold test configurations for existing models.**

### 4. STAR Schema Design

**When to use:** Building dimensional models, designing fact and dimension tables.

**Key principles:**
- **Fact tables**: Measurements, metrics, foreign keys to dimensions
- **Dimension tables**: Descriptive attributes, slowly changing dimensions
- **Grain**: Define the level of detail (one row per transaction, per day, etc.)
- **Surrogate keys**: Use generated keys, not natural keys from source

**DBT implementation pattern:**
```sql
-- models/marts/fct_sales.sql
WITH source AS (
    SELECT * FROM {{ ref('stg_orders') }}
),

final AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['order_id', 'order_date']) }} AS sales_key,
        order_id,
        {{ dbt_date.to_date('order_date') }} AS order_date_key,
        customer_id AS customer_key,
        product_id AS product_key,
        quantity,
        amount,
        CURRENT_TIMESTAMP() AS _loaded_at
    FROM source
)

SELECT * FROM final
```

**Testing for STAR schemas:**
- Unique surrogate keys in all tables
- Not null on all foreign keys
- Relationships between fact and dimension tables
- Accepted values for status/type columns
- Row count validation against source

## Resources

### references/
- **snowflake_caching.md**: Detailed query result caching behavior, optimization strategies
- **snowflake_warehouse_sizing.md**: Workload-specific sizing recommendations, cost optimization
- **dbt_testing_patterns.md**: Comprehensive DBT testing patterns, custom test examples, STAR schema validation

### scripts/
- **generate_dbt_tests.py**: Generate schema.yml test configurations from existing models

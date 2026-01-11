# Snowflake Query Result Caching

## Cache Types Overview

Snowflake uses three types of caching to optimize query performance:

### 1. Result Cache (24 hours)
- Stores complete query results
- Shared across all warehouses and users
- **Hit conditions:**
  - Exact SQL text match (case-sensitive)
  - Same role and warehouse context
  - Underlying data hasn't changed
  - Within 24-hour window
- **Bypass:** `USE_CACHED_RESULT = FALSE` or `CURRENT_TIMESTAMP()` in query

### 2. Metadata Cache
- Stores table/column information
- Speeds up compilation and optimization
- Always active, no configuration needed

### 3. Warehouse Cache (Local SSD)
- Stores raw data blocks on warehouse compute nodes
- Persists while warehouse is running
- Cleared on warehouse suspension
- Speeds up repeated scans of same data

## Cache Hit Detection

```sql
-- Check if query used result cache
SELECT 
    QUERY_ID,
    QUERY_TEXT,
    EXECUTION_STATUS,
    BYTES_SCANNED,           -- 0 = result cache hit
    PERCENTAGE_SCANNED_FROM_CACHE,
    COMPILATION_TIME,
    EXECUTION_TIME,
    WAREHOUSE_SIZE
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE QUERY_ID = 'your-query-id';

-- Find queries with high cache hit rates
SELECT 
    QUERY_TYPE,
    COUNT(*) as query_count,
    SUM(CASE WHEN BYTES_SCANNED = 0 THEN 1 ELSE 0 END) as result_cache_hits,
    AVG(PERCENTAGE_SCANNED_FROM_CACHE) as avg_warehouse_cache_hit_pct
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY_BY_WAREHOUSE('MY_WH'))
WHERE START_TIME >= DATEADD(hour, -24, CURRENT_TIMESTAMP())
GROUP BY QUERY_TYPE
ORDER BY query_count DESC;
```

## Optimization Strategies

### 1. Maximize Result Cache Hits

**Do:**
- Use parameterized queries with identical SQL text
- Schedule recurring reports to keep cache warm
- Use views to standardize query patterns
- Enable `USE_CACHED_RESULT` at session level (default)

**Don't:**
- Add unnecessary LIMIT clauses (different = different query)
- Use `CURRENT_TIMESTAMP()` unless real-time data required
- Format SQL inconsistently (whitespace matters)
- Use session-specific variables in shared reports

**Example - Cache-friendly pattern:**
```sql
-- Good: Reusable pattern
CREATE VIEW daily_sales AS
SELECT 
    DATE_TRUNC('day', order_date) as order_day,
    SUM(amount) as total_sales
FROM orders
WHERE order_date >= DATEADD(day, -30, CURRENT_DATE())
GROUP BY 1;

-- Users querying this view hit same result cache
SELECT * FROM daily_sales WHERE order_day = '2024-01-15';
```

**Example - Cache-unfriendly pattern:**
```sql
-- Bad: Each execution creates different query
SELECT * FROM orders 
WHERE created_at > CURRENT_TIMESTAMP() - INTERVAL '1 hour';

-- Better: Use CURRENT_DATE() for daily freshness
SELECT * FROM orders 
WHERE created_at >= CURRENT_DATE();
```

### 2. Leverage Clustering for Warehouse Cache

**When to cluster:**
- Large tables (>1TB or billions of rows)
- Queries frequently filter on specific columns
- Data has natural ordering (timestamps, IDs)

**Best clustering key candidates:**
- Timestamp columns for time-series data
- High-cardinality columns used in WHERE/JOIN
- Columns used in GROUP BY operations

**Implementation:**
```sql
-- Enable clustering
ALTER TABLE large_fact_table 
CLUSTER BY (event_date, customer_id);

-- Monitor clustering effectiveness
SELECT 
    TABLE_NAME,
    CLUSTERING_KEY,
    AVG_DEPTH,              -- Target: <5 for optimal
    TOTAL_CONSTANT_PARTITION_COUNT,
    NOTES
FROM TABLE(INFORMATION_SCHEMA.CLUSTERING_INFORMATION('large_fact_table'));

-- Manual reclustering if needed
ALTER TABLE large_fact_table RECLUSTER;
```

### 3. Optimize for Warehouse Cache Persistence

**Strategies:**
- Keep warehouses running during business hours (disable auto-suspend)
- Use dedicated warehouses for heavy analytical workloads
- Size warehouses appropriately (larger = more cache)
- Separate ETL and BI workloads to different warehouses

**Cost-benefit example:**
```sql
-- Scenario: Reports run every 15 minutes during business hours (8 hours)
-- Option A: Auto-suspend after 60 seconds
--   - 8 hours × 4 queries/hour = 32 cache misses per day
--   - More compute time per query
-- Option B: Keep running during business hours
--   - 1 cache miss + 31 cache hits
--   - 8 hours × warehouse cost but faster queries

-- Monitor to decide
SELECT 
    WAREHOUSE_NAME,
    COUNT(*) as queries,
    AVG(PERCENTAGE_SCANNED_FROM_CACHE) as avg_cache_hit,
    SUM(EXECUTION_TIME) / 1000 as total_seconds
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY_BY_WAREHOUSE('REPORTING_WH'))
WHERE START_TIME >= CURRENT_DATE()
GROUP BY WAREHOUSE_NAME;
```

## Cache Invalidation Scenarios

Result cache is automatically invalidated when:
- Underlying table data changes (INSERT, UPDATE, DELETE, MERGE)
- Table metadata changes (ALTER TABLE)
- 24-hour expiration
- Access control changes affect query results

**Force cache invalidation:**
```sql
-- Method 1: Modify table metadata
ALTER TABLE my_table SET COMMENT = 'Updated at ' || CURRENT_TIMESTAMP();

-- Method 2: Session-level disable
ALTER SESSION SET USE_CACHED_RESULT = FALSE;
SELECT * FROM my_table;
ALTER SESSION SET USE_CACHED_RESULT = TRUE;

-- Method 3: Add cache-busting comment
SELECT * FROM my_table /* cache_bust_2024_01_15_v1 */;
```

## Common Patterns

### Pattern 1: Dashboard Acceleration
```sql
-- Create materialized view for expensive dashboard query
CREATE MATERIALIZED VIEW mv_daily_kpis AS
SELECT 
    DATE_TRUNC('day', event_timestamp) as event_date,
    user_segment,
    COUNT(DISTINCT user_id) as active_users,
    SUM(revenue) as total_revenue,
    AVG(session_duration) as avg_session_seconds
FROM events
WHERE event_timestamp >= DATEADD(day, -90, CURRENT_DATE())
GROUP BY 1, 2;

-- Dashboard queries hit materialized view (fast + cached)
SELECT * FROM mv_daily_kpis 
WHERE event_date >= DATEADD(day, -7, CURRENT_DATE());
```

### Pattern 2: ETL Pipeline Optimization
```sql
-- Use COPY INTO with ON_ERROR = CONTINUE for idempotent loads
COPY INTO staging_table
FROM @my_stage/data/
FILE_FORMAT = (TYPE = 'PARQUET')
ON_ERROR = 'CONTINUE'
PATTERN = '.*\.parquet';

-- Transform with MERGE for cache-friendly incremental processing
MERGE INTO target_table t
USING staging_table s ON t.id = s.id
WHEN MATCHED THEN UPDATE SET t.value = s.value, t.updated_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN INSERT (id, value, created_at) VALUES (s.id, s.value, CURRENT_TIMESTAMP());
```

### Pattern 3: Real-time vs Cached Trade-offs
```sql
-- Cached query for historical analysis (24-hour freshness acceptable)
CREATE VIEW historical_trends AS
SELECT 
    DATE_TRUNC('month', order_date) as month,
    category,
    SUM(revenue) as revenue
FROM orders
WHERE order_date < CURRENT_DATE()  -- Excludes today = cache-friendly
GROUP BY 1, 2;

-- Real-time query for current day (bypass cache)
CREATE VIEW today_revenue AS
SELECT 
    category,
    SUM(revenue) as revenue,
    MAX(order_timestamp) as last_order
FROM orders
WHERE order_date = CURRENT_DATE()  -- Always fresh
GROUP BY 1;

-- Combined view uses both caches effectively
CREATE VIEW complete_revenue AS
SELECT * FROM historical_trends
UNION ALL
SELECT 
    DATE_TRUNC('month', CURRENT_DATE()) as month,
    category,
    revenue
FROM today_revenue;
```

## Monitoring and Troubleshooting

### Key Metrics
```sql
-- Cache effectiveness by warehouse
SELECT 
    WAREHOUSE_NAME,
    DATE_TRUNC('hour', START_TIME) as hour,
    COUNT(*) as total_queries,
    SUM(CASE WHEN BYTES_SCANNED = 0 THEN 1 ELSE 0 END) as result_cache_hits,
    AVG(PERCENTAGE_SCANNED_FROM_CACHE) as avg_warehouse_cache_pct,
    ROUND(result_cache_hits / total_queries * 100, 2) as result_cache_hit_rate
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE START_TIME >= DATEADD(day, -7, CURRENT_TIMESTAMP())
  AND EXECUTION_STATUS = 'SUCCESS'
GROUP BY 1, 2
ORDER BY 1, 2 DESC;
```

### Troubleshooting Low Cache Hits

**Symptom:** `PERCENTAGE_SCANNED_FROM_CACHE` consistently < 50%

**Diagnosis:**
1. Check if queries are cache-friendly (identical SQL text)
2. Verify warehouse isn't constantly suspending
3. Look for large table scans without clustering
4. Check if queries access different partitions

**Resolution:**
- Standardize query patterns via views
- Increase auto-suspend timeout
- Add clustering keys to large tables
- Use partition pruning with date filters

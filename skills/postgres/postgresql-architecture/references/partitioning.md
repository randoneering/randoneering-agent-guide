# PostgreSQL Partitioning Strategies

Comprehensive guide to table partitioning in PostgreSQL including strategy selection, implementation patterns, and best practices.

## Overview

**Partitioning Benefits:**
- Improved query performance (partition pruning)
- Easier data management (drop old partitions instead of DELETE)
- Parallel query execution across partitions
- Reduced index sizes (indexes per partition)
- Archival and retention management

**When to Partition:**
- Table > 100GB (or >10M rows as rough guideline)
- Time-series data with retention policies
- Clear partitioning key in most queries
- Data archival requirements
- Multi-tenant applications

**When NOT to Partition:**
- Small tables (< 10GB)
- No clear partitioning key
- Queries span all partitions frequently
- Complexity outweighs benefits

## Partitioning Types

### Range Partitioning

**Use case:** Time-series data, sequential data, data with natural ranges

**Examples:**
- Logs by date/month/year
- Orders by order_date
- Sensor data by timestamp
- Financial transactions by date

**Advantages:**
- Natural data lifecycle management
- Easy to add/drop partitions
- Partition pruning works well with date ranges

**Implementation:**

```sql
-- Parent table
CREATE TABLE events (
    id BIGSERIAL,
    event_time TIMESTAMP NOT NULL,
    event_type VARCHAR(50),
    data JSONB,
    PRIMARY KEY (id, event_time)
) PARTITION BY RANGE (event_time);

-- Create partitions (monthly example)
CREATE TABLE events_2024_01 PARTITION OF events
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE events_2024_02 PARTITION OF events
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Indexes on partitions
CREATE INDEX idx_events_2024_01_type ON events_2024_01(event_type);
CREATE INDEX idx_events_2024_02_type ON events_2024_02(event_type);

-- Default partition for data outside ranges
CREATE TABLE events_default PARTITION OF events DEFAULT;
```

**Automated Partition Creation:**

```sql
-- Using pg_partman extension
CREATE EXTENSION pg_partman;

SELECT partman.create_parent(
    'public.events',
    'event_time',
    'native',
    'monthly',
    p_premake := 3,  -- Create 3 partitions ahead
    p_start_partition := '2024-01-01'
);

-- Configure automatic maintenance
UPDATE partman.part_config 
SET infinite_time_partitions = true,
    retention = '12 months',
    retention_keep_table = false
WHERE parent_table = 'public.events';
```

### List Partitioning

**Use case:** Discrete categorical data, multi-tenant, geographic regions

**Examples:**
- Data by country/region
- Multi-tenant by tenant_id
- Status-based partitioning (active/archived)
- Product categories

**Advantages:**
- Clear data separation
- Easy to add new categories
- Good for multi-tenancy

**Implementation:**

```sql
-- Multi-tenant example
CREATE TABLE tenant_data (
    id BIGSERIAL,
    tenant_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL,
    data JSONB,
    PRIMARY KEY (id, tenant_id)
) PARTITION BY LIST (tenant_id);

-- Create partition per tenant
CREATE TABLE tenant_data_1 PARTITION OF tenant_data
    FOR VALUES IN (1);

CREATE TABLE tenant_data_2 PARTITION OF tenant_data
    FOR VALUES IN (2);

-- Multiple values per partition (grouped tenants)
CREATE TABLE tenant_data_small PARTITION OF tenant_data
    FOR VALUES IN (100, 101, 102, 103, 104);

-- Default partition
CREATE TABLE tenant_data_default PARTITION OF tenant_data DEFAULT;
```

**Geographic partitioning:**

```sql
CREATE TABLE orders (
    id BIGSERIAL,
    order_date DATE NOT NULL,
    country_code VARCHAR(2) NOT NULL,
    amount DECIMAL(10,2),
    PRIMARY KEY (id, country_code)
) PARTITION BY LIST (country_code);

-- North America
CREATE TABLE orders_na PARTITION OF orders
    FOR VALUES IN ('US', 'CA', 'MX');

-- Europe
CREATE TABLE orders_eu PARTITION OF orders
    FOR VALUES IN ('GB', 'FR', 'DE', 'IT', 'ES');

-- Asia Pacific
CREATE TABLE orders_apac PARTITION OF orders
    FOR VALUES IN ('JP', 'CN', 'AU', 'SG', 'IN');
```

### Hash Partitioning

**Use case:** Evenly distribute data when no natural partitioning key exists

**Examples:**
- User data distributed by user_id hash
- Session data
- Cache tables
- Load balancing across partitions

**Advantages:**
- Even data distribution
- Automatic balancing
- Good for parallel processing

**Disadvantages:**
- Cannot drop partitions selectively
- Less intuitive data location
- No partition pruning without exact match

**Implementation:**

```sql
CREATE TABLE user_sessions (
    id BIGSERIAL,
    user_id BIGINT NOT NULL,
    session_data JSONB,
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (id, user_id)
) PARTITION BY HASH (user_id);

-- Create 8 partitions (power of 2 recommended)
CREATE TABLE user_sessions_0 PARTITION OF user_sessions
    FOR VALUES WITH (MODULUS 8, REMAINDER 0);

CREATE TABLE user_sessions_1 PARTITION OF user_sessions
    FOR VALUES WITH (MODULUS 8, REMAINDER 1);

-- ... up to 7

-- Note: Adding partitions later requires repartitioning
```

**Number of partitions:**
- Power of 2 (2, 4, 8, 16, 32) for easier expansion
- Start with 4-8 partitions for most use cases
- Too many partitions (>100) can hurt performance
- Cannot change modulus without recreating table

### Multi-Level (Sub-Partitioning)

**Use case:** Combine strategies for complex requirements

**Examples:**
- Range by date, then list by tenant
- Range by date, then hash for distribution
- List by region, then range by date

**Implementation:**

```sql
-- Range by month, then list by tenant
CREATE TABLE metrics (
    id BIGSERIAL,
    tenant_id INTEGER NOT NULL,
    metric_time TIMESTAMP NOT NULL,
    metric_value NUMERIC,
    PRIMARY KEY (id, tenant_id, metric_time)
) PARTITION BY RANGE (metric_time);

-- Monthly partition
CREATE TABLE metrics_2024_01 PARTITION OF metrics
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01')
    PARTITION BY LIST (tenant_id);

-- Sub-partitions per tenant
CREATE TABLE metrics_2024_01_tenant_1 PARTITION OF metrics_2024_01
    FOR VALUES IN (1);

CREATE TABLE metrics_2024_01_tenant_2 PARTITION OF metrics_2024_01
    FOR VALUES IN (2);

-- Repeat for other months...
```

**Range by date, hash for distribution:**

```sql
CREATE TABLE large_events (
    id BIGSERIAL,
    event_time TIMESTAMP NOT NULL,
    event_id UUID NOT NULL,
    data JSONB,
    PRIMARY KEY (id, event_time, event_id)
) PARTITION BY RANGE (event_time);

-- Monthly partition
CREATE TABLE large_events_2024_01 PARTITION OF large_events
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01')
    PARTITION BY HASH (event_id);

-- Hash sub-partitions for parallel processing
CREATE TABLE large_events_2024_01_0 PARTITION OF large_events_2024_01
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);

CREATE TABLE large_events_2024_01_1 PARTITION OF large_events_2024_01
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);
-- ... up to 3
```

## Partition Key Selection

### Critical Rules

**Partition key MUST be in PRIMARY KEY and UNIQUE constraints:**

```sql
-- WRONG: Partition key not in primary key
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,  -- ❌ Error
    order_date DATE NOT NULL
) PARTITION BY RANGE (order_date);

-- CORRECT: Include partition key in primary key
CREATE TABLE orders (
    id SERIAL,
    order_date DATE NOT NULL,
    PRIMARY KEY (id, order_date)  -- ✅
) PARTITION BY RANGE (order_date);
```

**Partition key should appear in WHERE clauses:**

```sql
-- Good: Uses partition key
SELECT * FROM events WHERE event_time >= '2024-01-01' AND event_time < '2024-02-01';
-- Partition pruning: Only scans events_2024_01

-- Bad: No partition key
SELECT * FROM events WHERE event_type = 'click';
-- Scans ALL partitions
```

### Common Partition Key Patterns

**Time-series data:**
```sql
-- Daily partitions for high-volume data
PARTITION BY RANGE (created_at)

-- Monthly for medium volume
PARTITION BY RANGE (DATE_TRUNC('month', created_at))

-- Yearly for low volume, long retention
PARTITION BY RANGE (DATE_TRUNC('year', created_at))
```

**Multi-tenant:**
```sql
-- Single tenant per partition
PARTITION BY LIST (tenant_id)

-- Grouped tenants (small tenants together)
-- Requires manual assignment
```

**Geographic:**
```sql
PARTITION BY LIST (country_code)
PARTITION BY LIST (region)
```

## Partition Management

### Creating New Partitions

**Manual creation:**
```sql
-- Add next month's partition
CREATE TABLE events_2024_03 PARTITION OF events
    FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');

-- Create indexes
CREATE INDEX idx_events_2024_03_type ON events_2024_03(event_type);
```

**Automated with pg_partman:**
```sql
-- Run maintenance (typically via cron)
SELECT partman.run_maintenance('public.events');

-- Creates future partitions, drops old ones per retention policy
```

**Function-based automation:**
```sql
CREATE OR REPLACE FUNCTION create_monthly_partition(
    parent_table TEXT,
    partition_date DATE
) RETURNS VOID AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    partition_name := parent_table || '_' || TO_CHAR(partition_date, 'YYYY_MM');
    start_date := DATE_TRUNC('month', partition_date);
    end_date := start_date + INTERVAL '1 month';
    
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
        partition_name, parent_table, start_date, end_date
    );
    
    EXECUTE format(
        'CREATE INDEX IF NOT EXISTS %I ON %I(event_type)',
        'idx_' || partition_name || '_type', partition_name
    );
END;
$$ LANGUAGE plpgsql;

-- Use in scheduled job
SELECT create_monthly_partition('events', CURRENT_DATE + INTERVAL '1 month');
```

### Dropping Old Partitions

**Manual drop:**
```sql
-- Detach first (PostgreSQL 12+)
ALTER TABLE events DETACH PARTITION events_2023_01;

-- Then drop
DROP TABLE events_2023_01;

-- Or drop directly (locks parent briefly)
DROP TABLE events_2023_01;
```

**With pg_partman retention:**
```sql
UPDATE partman.part_config 
SET retention = '12 months',
    retention_keep_table = false  -- Drop completely
WHERE parent_table = 'public.events';

-- Keep as standalone table for archival
UPDATE partman.part_config 
SET retention_keep_table = true,
    retention_schema = 'archive'
WHERE parent_table = 'public.events';
```

**Archive before drop:**
```sql
-- Move to archive schema
ALTER TABLE events_2023_01 SET SCHEMA archive;

-- Or export to file
COPY events_2023_01 TO '/backup/events_2023_01.csv' CSV HEADER;

-- Then drop
DROP TABLE archive.events_2023_01;
```

### Attaching Existing Tables

**Use case:** Migrate existing data to partitioned structure

```sql
-- Create table with same structure
CREATE TABLE events_2023_12 (LIKE events INCLUDING ALL);

-- Load data
INSERT INTO events_2023_12 SELECT * FROM old_events WHERE event_time >= '2023-12-01' AND event_time < '2024-01-01';

-- Validate constraint (important!)
ALTER TABLE events_2023_12 ADD CONSTRAINT events_2023_12_check
    CHECK (event_time >= '2023-12-01' AND event_time < '2024-01-01');

-- Attach (PostgreSQL 11+: avoids table lock)
ALTER TABLE events ATTACH PARTITION events_2023_12
    FOR VALUES FROM ('2023-12-01') TO ('2024-01-01');
```

## Indexes on Partitioned Tables

### Index Strategies

**Option 1: Indexes on parent (PostgreSQL 11+)**
```sql
-- Create index on parent, automatically creates on all partitions
CREATE INDEX idx_events_type ON events(event_type);

-- Applies to existing and future partitions
-- Slower initial creation but easier management
```

**Option 2: Indexes on each partition**
```sql
-- More control, can customize per partition
CREATE INDEX idx_events_2024_01_type ON events_2024_01(event_type);
CREATE INDEX idx_events_2024_01_data_gin ON events_2024_01 USING gin(data);

-- Good for different index strategies per partition
-- Faster parallel creation
```

**Recommendation:**
- Use parent indexes for uniform strategy
- Use partition indexes when strategies differ
- Create partition indexes in parallel for large tables

### Partition-Specific Index Optimization

```sql
-- Partial indexes on hot partitions
CREATE INDEX idx_events_current_active ON events_2024_01(event_type)
    WHERE status = 'active';

-- Different index types per partition age
-- Recent: B-tree for precision
CREATE INDEX idx_events_2024_01_time ON events_2024_01(event_time);

-- Archive: BRIN for space efficiency
CREATE INDEX idx_events_2020_01_time ON events_2020_01 USING brin(event_time);
```

## Query Performance

### Partition Pruning

**PostgreSQL automatically excludes irrelevant partitions:**

```sql
EXPLAIN SELECT * FROM events WHERE event_time >= '2024-01-15' AND event_time < '2024-01-20';

-- Output shows only events_2024_01 is scanned
-- Partitions Pruned: 11 (if 12 total partitions)
```

**For effective pruning:**
- Include partition key in WHERE clause
- Use compatible operators (=, <, >, <=, >=, BETWEEN)
- Avoid functions on partition key: `DATE(event_time)` prevents pruning

**Check pruning in EXPLAIN:**
```sql
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM events WHERE event_time >= '2024-01-01';

-- Look for "Partitions Pruned: N"
```

### Parallel Query on Partitions

**PostgreSQL can parallelize across partitions:**

```sql
-- Enable parallel query
SET max_parallel_workers_per_gather = 4;
SET parallel_setup_cost = 100;

-- Query scans multiple partitions in parallel
SELECT COUNT(*) FROM events WHERE event_type = 'click';
```

**Optimization:**
- Ensure partitions are large enough for parallelism benefit
- Set appropriate `max_parallel_workers_per_gather`
- Monitor with EXPLAIN ANALYZE

## Common Patterns and Anti-Patterns

### ✅ Good Patterns

**1. Time-series with retention:**
```sql
-- Daily partitions, 90-day retention
CREATE TABLE logs (...) PARTITION BY RANGE (log_date);

-- Automated with pg_partman
SELECT partman.create_parent('public.logs', 'log_date', 'native', 'daily',
    p_retention := '90 days', p_premake := 7);
```

**2. Multi-tenant isolation:**
```sql
-- Separate partition per major tenant
CREATE TABLE tenant_data (...) PARTITION BY LIST (tenant_id);

-- Partitions: 1, 2, 3 (big), others grouped in 'small'
```

**3. Archive old data:**
```sql
-- Detach instead of DELETE
ALTER TABLE events DETACH PARTITION events_2020_01;
ALTER TABLE events_2020_01 SET SCHEMA archive;
```

**4. Hot/cold data separation:**
```sql
-- Recent months: standard indexes
-- Old months: BRIN indexes, compressed tablespaces
```

### ❌ Anti-Patterns

**1. Too many partitions:**
```sql
-- ❌ Daily partitions for 10 years = 3650 partitions
-- Excessive overhead, slower planning

-- ✅ Monthly or quarterly partitions instead
```

**2. Wrong partition key:**
```sql
-- ❌ Partition by column never in WHERE
CREATE TABLE orders (...) PARTITION BY RANGE (id);

-- Queries always filter by order_date, never id
SELECT * FROM orders WHERE order_date = '2024-01-01';  -- Scans all partitions!
```

**3. Partition key not in queries:**
```sql
-- ❌ Query doesn't use partition key
SELECT * FROM events WHERE user_id = 123;  -- Scans all partitions

-- ✅ Include partition key
SELECT * FROM events WHERE user_id = 123 AND event_time >= '2024-01-01';
```

**4. Unique constraints without partition key:**
```sql
-- ❌ UNIQUE without partition key
CREATE TABLE orders (
    order_number VARCHAR(50) UNIQUE,  -- Error!
    order_date DATE
) PARTITION BY RANGE (order_date);

-- ✅ Include partition key
CREATE TABLE orders (
    order_number VARCHAR(50),
    order_date DATE,
    UNIQUE (order_number, order_date)
);
```

## Migration to Partitioned Tables

### Strategy 1: CREATE + COPY (downtime)

```sql
-- 1. Rename existing table
ALTER TABLE events RENAME TO events_old;

-- 2. Create partitioned table
CREATE TABLE events (...) PARTITION BY RANGE (event_time);

-- 3. Create partitions
-- (automated or manual)

-- 4. Copy data
INSERT INTO events SELECT * FROM events_old;

-- 5. Drop old table
DROP TABLE events_old;
```

### Strategy 2: pg_partman + ATTACH (minimal downtime)

```sql
-- 1. Create partitioned table (different name)
CREATE TABLE events_partitioned (...) PARTITION BY RANGE (event_time);

-- 2. Create partitions
SELECT partman.create_parent(...);

-- 3. Copy data in batches (during off-peak)
INSERT INTO events_partitioned 
SELECT * FROM events 
WHERE event_time >= '2024-01-01' AND event_time < '2024-02-01';

-- 4. Rename tables (brief lock)
BEGIN;
ALTER TABLE events RENAME TO events_old;
ALTER TABLE events_partitioned RENAME TO events;
COMMIT;

-- 5. Copy remaining data
-- 6. Drop old table
```

### Strategy 3: Logical Replication (zero downtime)

```sql
-- 1. Create partitioned table on new system
-- 2. Setup logical replication from old to new
-- 3. Let it sync
-- 4. Switch application to new table
-- 5. Decommission old table
```

## Monitoring Partitioned Tables

### Partition Size Tracking

```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE tablename LIKE 'events_%'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Partition Scan Statistics

```sql
SELECT 
    schemaname,
    tablename,
    seq_scan,
    idx_scan,
    n_tup_ins,
    n_tup_upd,
    n_tup_del
FROM pg_stat_user_tables
WHERE tablename LIKE 'events_%'
ORDER BY seq_scan DESC;
```

### Identify Missing Partitions

```sql
-- Find date gaps in range partitions
WITH partition_dates AS (
    SELECT 
        tablename,
        regexp_replace(tablename, '.*_(\d{4}_\d{2})$', '\1') as year_month
    FROM pg_tables
    WHERE tablename LIKE 'events_%'
)
SELECT * FROM partition_dates ORDER BY year_month;
```

## Partitioning Best Practices

1. **Start with monthly partitions** - easier to manage than daily for most use cases
2. **Use pg_partman** - automates creation and retention
3. **Include partition key in WHERE clauses** - enable pruning
4. **Partition key must be in PRIMARY KEY** - PostgreSQL requirement
5. **Monitor partition count** - too many (>100) impacts performance
6. **Create indexes on parent** - automatically applies to partitions (PG 11+)
7. **Plan for growth** - automate partition creation ahead of time
8. **Document partition strategy** - future maintainers will thank you
9. **Test queries with EXPLAIN** - verify partition pruning works
10. **Consider sub-partitioning carefully** - adds complexity

## Troubleshooting

**Query scans all partitions:**
- Check partition key in WHERE clause
- Avoid functions on partition key
- Use EXPLAIN to verify pruning

**Cannot create UNIQUE without partition key:**
- Add partition key to UNIQUE constraint
- Or use application-level uniqueness

**Slow partition creation:**
- Create indexes after attaching partition
- Use CONCURRENTLY for index creation
- Consider parallel index creation

**Too many partitions:**
- Consolidate to larger ranges (monthly → quarterly)
- Use pg_partman to drop old partitions
- Consider archival strategy

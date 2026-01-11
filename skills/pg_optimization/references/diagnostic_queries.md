# PostgreSQL Diagnostic Queries

Collection of essential queries for database health monitoring, performance analysis, and troubleshooting.

## Table of Contents
1. [Connection and Activity](#connection-and-activity)
2. [Table and Index Bloat](#table-and-index-bloat)
3. [Index Analysis](#index-analysis)
4. [Query Performance](#query-performance)
5. [Vacuum and Autovacuum](#vacuum-and-autovacuum)
6. [Replication Monitoring](#replication-monitoring)
7. [Lock Analysis](#lock-analysis)
8. [Database Size and Growth](#database-size-and-growth)
9. [Cache Hit Ratios](#cache-hit-ratios)
10. [Configuration Validation](#configuration-validation)

---

## Connection and Activity

### Current Connections by State

```sql
SELECT 
  state,
  count(*) as connection_count
FROM pg_stat_activity
WHERE pid != pg_backend_pid()  -- Exclude current connection
GROUP BY state
ORDER BY connection_count DESC;
```

### Active Queries with Duration

```sql
SELECT 
  pid,
  now() - query_start AS duration,
  usename,
  state,
  wait_event_type,
  wait_event,
  query
FROM pg_stat_activity
WHERE state != 'idle'
  AND pid != pg_backend_pid()
ORDER BY duration DESC;
```

### Long-Running Queries (>5 minutes)

```sql
SELECT 
  pid,
  now() - query_start AS duration,
  usename,
  datname,
  state,
  query
FROM pg_stat_activity
WHERE state != 'idle'
  AND now() - query_start > interval '5 minutes'
  AND pid != pg_backend_pid()
ORDER BY duration DESC;
```

### Idle in Transaction Connections

```sql
SELECT 
  pid,
  now() - state_change AS idle_duration,
  usename,
  datname,
  state,
  query
FROM pg_stat_activity
WHERE state = 'idle in transaction'
  AND now() - state_change > interval '5 minutes'
ORDER BY idle_duration DESC;
```

### Connection Count vs Max Connections

```sql
SELECT 
  count(*) as current_connections,
  (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections,
  round(100.0 * count(*) / (SELECT setting::int FROM pg_settings WHERE name = 'max_connections'), 2) as pct_used
FROM pg_stat_activity;
```

### Kill Idle in Transaction Connections

```sql
-- View candidates first
SELECT pid, usename, state, now() - state_change AS duration
FROM pg_stat_activity
WHERE state = 'idle in transaction'
  AND now() - state_change > interval '10 minutes';

-- Terminate connections (BE CAREFUL!)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle in transaction'
  AND now() - state_change > interval '10 minutes'
  AND pid != pg_backend_pid();
```

---

## Table and Index Bloat

### Table Bloat Estimate

```sql
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
  pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
  n_live_tup,
  n_dead_tup,
  round(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_pct,
  last_vacuum,
  last_autovacuum,
  last_analyze,
  last_autoanalyze
FROM pg_stat_user_tables
WHERE n_dead_tup > 10000  -- Focus on tables with significant dead tuples
ORDER BY n_dead_tup DESC
LIMIT 20;
```

### Detailed Bloat Analysis (More Accurate)

```sql
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
  pg_size_pretty(
    (CASE WHEN otta = 0 OR sml.relpages = 0 OR sml.relpages = otta THEN 0
      ELSE sml.relpages::bigint - otta END) * current_setting('block_size')::bigint
  ) AS bloat_size,
  CASE WHEN otta = 0 OR sml.relpages = 0 OR sml.relpages = otta THEN 0
    ELSE 100 * (sml.relpages - otta)::numeric / sml.relpages END AS bloat_pct
FROM (
  SELECT
    schemaname, tablename, cc.relpages, bs,
    CEIL((cc.reltuples*((datahdr+ma-
      (CASE WHEN datahdr%ma=0 THEN ma ELSE datahdr%ma END))+nullhdr2+4))/(bs-20::float)) AS otta
  FROM (
    SELECT
      ma,bs,schemaname,tablename,
      (datawidth+(hdr+ma-(case when hdr%ma=0 THEN ma ELSE hdr%ma END)))::numeric AS datahdr,
      (maxfracsum*(nullhdr+ma-(case when nullhdr%ma=0 THEN ma ELSE nullhdr%ma END))) AS nullhdr2
    FROM (
      SELECT
        schemaname, tablename, hdr, ma, bs,
        SUM((1-null_frac)*avg_width) AS datawidth,
        MAX(null_frac) AS maxfracsum,
        hdr+(
          SELECT 1+count(*)/8
          FROM pg_stats s2
          WHERE null_frac<>0 AND s2.schemaname = s.schemaname AND s2.tablename = s.tablename
        ) AS nullhdr
      FROM pg_stats s, (
        SELECT
          (SELECT current_setting('block_size')::numeric) AS bs,
          CASE WHEN substring(v,12,3) IN ('8.0','8.1','8.2') THEN 27 ELSE 23 END AS hdr,
          CASE WHEN v ~ 'mingw32' THEN 8 ELSE 4 END AS ma
        FROM (SELECT version() AS v) AS foo
      ) AS constants
      GROUP BY 1,2,3,4,5
    ) AS foo
  ) AS rs
  JOIN pg_class cc ON cc.relname = rs.tablename
  JOIN pg_namespace nn ON cc.relnamespace = nn.oid AND nn.nspname = rs.schemaname AND nn.nspname <> 'information_schema'
) AS sml
WHERE sml.relpages - otta > 100  -- Only tables with significant bloat (100+ pages)
  AND 100 * (sml.relpages - otta) / sml.relpages > 10  -- >10% bloat
ORDER BY (sml.relpages - otta) DESC
LIMIT 20;
```

### Index Bloat Estimate

```sql
SELECT
  schemaname,
  tablename,
  indexname,
  pg_size_pretty(pg_relation_size(schemaname||'.'||indexname)) AS index_size,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
JOIN pg_indexes USING (schemaname, tablename, indexname)
WHERE pg_relation_size(schemaname||'.'||indexname) > 100000  -- > ~800KB
ORDER BY pg_relation_size(schemaname||'.'||indexname) DESC
LIMIT 20;
```

---

## Index Analysis

### Missing Indexes (Frequent Sequential Scans)

```sql
SELECT 
  schemaname,
  tablename,
  seq_scan,
  seq_tup_read,
  idx_scan,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as table_size,
  CASE 
    WHEN seq_scan = 0 THEN 0
    ELSE seq_tup_read / seq_scan 
  END AS avg_seq_tup_read
FROM pg_stat_user_tables
WHERE seq_scan > 0
  AND pg_total_relation_size(schemaname||'.'||tablename) > 1000000  -- > ~8MB
ORDER BY seq_tup_read DESC
LIMIT 20;
```

### Unused Indexes

```sql
SELECT 
  schemaname,
  tablename,
  indexname,
  idx_scan,
  pg_size_pretty(pg_relation_size(schemaname||'.'||indexname)) AS index_size,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS table_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexname NOT LIKE '%_pkey'  -- Exclude primary keys
  AND schemaname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
ORDER BY pg_relation_size(schemaname||'.'||indexname) DESC
LIMIT 20;
```

### Duplicate Indexes

```sql
SELECT 
  pg_size_pretty(SUM(pg_relation_size(idx))::bigint) AS size,
  (array_agg(idx))[1] AS idx1,
  (array_agg(idx))[2] AS idx2,
  (array_agg(idx))[3] AS idx3,
  (array_agg(idx))[4] AS idx4
FROM (
  SELECT 
    indexrelid::regclass AS idx,
    (indrelid::text ||E'\n'|| indclass::text ||E'\n'|| indkey::text ||E'\n'|| coalesce(indexprs::text,'')||E'\n'|| coalesce(indpred::text,'')) AS key
  FROM pg_index
) sub
GROUP BY key
HAVING COUNT(*) > 1
ORDER BY SUM(pg_relation_size(idx)) DESC;
```

### Tables Without Primary Keys

```sql
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as table_size
FROM pg_tables t
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
  AND NOT EXISTS (
    SELECT 1 FROM pg_constraint c
    WHERE c.conrelid = (t.schemaname||'.'||t.tablename)::regclass
      AND c.contype = 'p'
  )
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Index Usage Statistics

```sql
SELECT 
  schemaname,
  tablename,
  indexname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch,
  pg_size_pretty(pg_relation_size(schemaname||'.'||indexname)) AS index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC
LIMIT 20;
```

---

## Query Performance

### Slow Queries (Requires pg_stat_statements)

```sql
-- Enable extension first: CREATE EXTENSION pg_stat_statements;

SELECT 
  round(total_exec_time::numeric, 2) AS total_time_ms,
  calls,
  round(mean_exec_time::numeric, 2) AS mean_time_ms,
  round((100 * total_exec_time / SUM(total_exec_time) OVER ())::numeric, 2) AS pct_total_time,
  query
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat_statements%'
ORDER BY total_exec_time DESC
LIMIT 20;
```

### Queries by Average Execution Time

```sql
SELECT 
  round(mean_exec_time::numeric, 2) AS mean_time_ms,
  calls,
  round(total_exec_time::numeric, 2) AS total_time_ms,
  query
FROM pg_stat_statements
WHERE calls > 10  -- At least 10 executions
  AND query NOT LIKE '%pg_stat_statements%'
ORDER BY mean_exec_time DESC
LIMIT 20;
```

### Most Frequently Called Queries

```sql
SELECT 
  calls,
  round(mean_exec_time::numeric, 2) AS mean_time_ms,
  round(total_exec_time::numeric, 2) AS total_time_ms,
  query
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat_statements%'
ORDER BY calls DESC
LIMIT 20;
```

### Queries Creating Temporary Files

```sql
SELECT 
  round(mean_exec_time::numeric, 2) AS mean_time_ms,
  calls,
  temp_blks_written,
  pg_size_pretty(temp_blks_written * 8192) AS temp_data_written,
  query
FROM pg_stat_statements
WHERE temp_blks_written > 0
ORDER BY temp_blks_written DESC
LIMIT 20;
```

### Reset pg_stat_statements

```sql
-- Reset all query statistics (use with caution)
SELECT pg_stat_statements_reset();
```

---

## Vacuum and Autovacuum

### Tables Needing Vacuum

```sql
SELECT 
  schemaname,
  tablename,
  n_dead_tup,
  n_live_tup,
  round(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_pct,
  last_vacuum,
  last_autovacuum
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
  AND (n_dead_tup::float / NULLIF(n_live_tup, 0)) > 0.05  -- >5% dead tuples
ORDER BY n_dead_tup DESC
LIMIT 20;
```

### Autovacuum Running Status

```sql
SELECT 
  pid,
  now() - xact_start AS duration,
  usename,
  state,
  wait_event_type,
  wait_event,
  query
FROM pg_stat_activity
WHERE query LIKE '%autovacuum%'
  AND pid != pg_backend_pid()
ORDER BY xact_start;
```

### Table-Level Autovacuum Settings

```sql
SELECT 
  schemaname,
  tablename,
  n_live_tup,
  n_dead_tup,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as table_size,
  (SELECT setting FROM pg_settings WHERE name = 'autovacuum_vacuum_scale_factor') as default_scale,
  (SELECT option_value FROM pg_options_to_table(reloptions) WHERE option_name = 'autovacuum_vacuum_scale_factor') as table_scale
FROM pg_stat_user_tables pst
JOIN pg_class pc ON pst.relid = pc.oid
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC
LIMIT 20;
```

### Tables Never Vacuumed

```sql
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as table_size,
  n_live_tup,
  n_dead_tup,
  last_vacuum,
  last_autovacuum
FROM pg_stat_user_tables
WHERE last_vacuum IS NULL
  AND last_autovacuum IS NULL
  AND pg_total_relation_size(schemaname||'.'||tablename) > 1000000  -- > ~8MB
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Replication Monitoring

### Replication Lag (Primary)

```sql
SELECT 
  client_addr,
  usename,
  application_name,
  state,
  sync_state,
  pg_wal_lsn_diff(pg_current_wal_lsn(), sent_lsn) AS sent_lag_bytes,
  pg_wal_lsn_diff(sent_lsn, write_lsn) AS write_lag_bytes,
  pg_wal_lsn_diff(write_lsn, flush_lsn) AS flush_lag_bytes,
  pg_wal_lsn_diff(flush_lsn, replay_lsn) AS replay_lag_bytes,
  write_lag,
  flush_lag,
  replay_lag
FROM pg_stat_replication
ORDER BY replay_lag DESC NULLS LAST;
```

### Replication Lag (Replica)

```sql
SELECT 
  CASE 
    WHEN pg_last_wal_receive_lsn() = pg_last_wal_replay_lsn() THEN 0
    ELSE EXTRACT(EPOCH FROM now() - pg_last_xact_replay_timestamp())
  END AS replication_lag_seconds,
  pg_last_wal_receive_lsn(),
  pg_last_wal_replay_lsn(),
  pg_last_xact_replay_timestamp();
```

### Replication Slots

```sql
SELECT 
  slot_name,
  slot_type,
  database,
  active,
  pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) AS retained_wal_bytes,
  pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained_wal_size
FROM pg_replication_slots
ORDER BY pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) DESC;
```

### Inactive Replication Slots (Potential WAL Bloat)

```sql
SELECT 
  slot_name,
  slot_type,
  database,
  active,
  pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained_wal_size
FROM pg_replication_slots
WHERE active = false
  AND pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) > 1073741824  -- > 1GB
ORDER BY pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) DESC;
```

---

## Lock Analysis

### Current Locks and Blocking Queries

```sql
SELECT 
  blocked_locks.pid AS blocked_pid,
  blocked_activity.usename AS blocked_user,
  blocking_locks.pid AS blocking_pid,
  blocking_activity.usename AS blocking_user,
  blocked_activity.query AS blocked_statement,
  blocking_activity.query AS blocking_statement,
  blocked_activity.application_name AS blocked_application
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks 
  ON blocking_locks.locktype = blocked_locks.locktype
  AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
  AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
  AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
  AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
  AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
  AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
  AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
  AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
  AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
  AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
```

### Lock Summary by Type

```sql
SELECT 
  locktype,
  mode,
  count(*) as lock_count
FROM pg_locks
GROUP BY locktype, mode
ORDER BY lock_count DESC;
```

### Long-Held Locks

```sql
SELECT 
  pl.pid,
  pa.usename,
  pa.application_name,
  pl.locktype,
  pl.relation::regclass,
  pl.mode,
  pa.state,
  pa.query,
  now() - pa.query_start AS duration
FROM pg_locks pl
JOIN pg_stat_activity pa ON pl.pid = pa.pid
WHERE pa.state != 'idle'
  AND now() - pa.query_start > interval '5 minutes'
ORDER BY duration DESC;
```

---

## Database Size and Growth

### Database Sizes

```sql
SELECT 
  datname,
  pg_size_pretty(pg_database_size(datname)) as size
FROM pg_database
WHERE datistemplate = false
ORDER BY pg_database_size(datname) DESC;
```

### Table Sizes (Top 20)

```sql
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
  pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS indexes_size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 20;
```

### Index Sizes (Top 20)

```sql
SELECT 
  schemaname,
  tablename,
  indexname,
  pg_size_pretty(pg_relation_size(schemaname||'.'||indexname)) AS index_size
FROM pg_indexes
WHERE schemaname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
ORDER BY pg_relation_size(schemaname||'.'||indexname) DESC
LIMIT 20;
```

### Database Growth Trend (Requires Historical Data)

```sql
-- Track database size over time (run periodically and store results)
CREATE TABLE IF NOT EXISTS database_size_history (
  recorded_at timestamp DEFAULT now(),
  datname text,
  size_bytes bigint
);

-- Insert current sizes
INSERT INTO database_size_history (datname, size_bytes)
SELECT datname, pg_database_size(datname)
FROM pg_database
WHERE datistemplate = false;

-- Query growth over last 30 days
SELECT 
  datname,
  pg_size_pretty(MAX(size_bytes)) as current_size,
  pg_size_pretty(MAX(size_bytes) - MIN(size_bytes)) as growth_30d,
  round(100.0 * (MAX(size_bytes) - MIN(size_bytes)) / NULLIF(MIN(size_bytes), 0), 2) as growth_pct
FROM database_size_history
WHERE recorded_at > now() - interval '30 days'
GROUP BY datname
ORDER BY (MAX(size_bytes) - MIN(size_bytes)) DESC;
```

---

## Cache Hit Ratios

### Buffer Cache Hit Ratio (Target: >99%)

```sql
SELECT 
  sum(blks_hit) / nullif(sum(blks_hit + blks_read), 0) AS cache_hit_ratio,
  round(100.0 * sum(blks_hit) / nullif(sum(blks_hit + blks_read), 0), 2) AS cache_hit_pct
FROM pg_stat_database;
```

### Per-Database Cache Hit Ratio

```sql
SELECT 
  datname,
  blks_hit,
  blks_read,
  round(100.0 * blks_hit / nullif(blks_hit + blks_read, 0), 2) AS cache_hit_pct
FROM pg_stat_database
WHERE datname NOT IN ('template0', 'template1')
ORDER BY cache_hit_pct;
```

### Index Cache Hit Ratio

```sql
SELECT 
  sum(idx_blks_hit) / nullif(sum(idx_blks_hit + idx_blks_read), 0) AS idx_cache_hit_ratio,
  round(100.0 * sum(idx_blks_hit) / nullif(sum(idx_blks_hit + idx_blks_read), 0), 2) AS idx_cache_hit_pct
FROM pg_statio_user_indexes;
```

---

## Configuration Validation

### Non-Default Settings

```sql
SELECT 
  name,
  setting,
  unit,
  source,
  sourcefile,
  sourceline
FROM pg_settings
WHERE source NOT IN ('default', 'override')
ORDER BY source, name;
```

### Memory Allocation

```sql
SELECT 
  name,
  setting,
  unit,
  pg_size_pretty((setting::bigint * 
    CASE unit 
      WHEN 'kB' THEN 1024
      WHEN 'MB' THEN 1024 * 1024
      WHEN '8kB' THEN 8192
      ELSE 1
    END)::bigint) AS size
FROM pg_settings
WHERE name IN ('shared_buffers', 'effective_cache_size', 'work_mem', 'maintenance_work_mem', 'wal_buffers')
ORDER BY name;
```

### Recommended Settings Check

```sql
SELECT 
  'shared_buffers' as parameter,
  setting as current_value,
  CASE 
    WHEN setting::bigint * 8192 < 134217728 THEN 'TOO LOW: Increase to at least 128MB'
    WHEN setting::bigint * 8192 > 17179869184 THEN 'TOO HIGH: Consider capping at 16GB'
    ELSE 'OK'
  END as recommendation
FROM pg_settings WHERE name = 'shared_buffers'
UNION ALL
SELECT 
  'random_page_cost',
  setting,
  CASE 
    WHEN setting::numeric > 2.0 THEN 'Consider lowering to 1.1-1.5 for SSD storage'
    ELSE 'OK'
  END
FROM pg_settings WHERE name = 'random_page_cost';
```

### Checkpoint Activity

```sql
-- Check logs for checkpoint warnings
-- Look for: "checkpoints are occurring too frequently"

SELECT 
  name,
  setting,
  unit
FROM pg_settings
WHERE name IN ('checkpoint_completion_target', 'max_wal_size', 'checkpoint_timeout')
ORDER BY name;
```

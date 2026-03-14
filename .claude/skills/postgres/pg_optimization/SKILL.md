---
name: postgresql
description: "Comprehensive PostgreSQL database engineering skill covering configuration tuning (postgresql.conf, memory, WAL, autovacuum), query optimization (EXPLAIN analysis, index design, rewriting patterns), cloud providers (AWS RDS, GCP Cloud SQL, Azure), database health monitoring (bloat detection, replication lag, vacuum status), performance analysis, and troubleshooting. Use when working with PostgreSQL databases for: (1) Tuning configuration parameters, (2) Analyzing slow queries, (3) Optimizing query performance, (4) Working with cloud-managed PostgreSQL (RDS/Cloud SQL/Azure), (5) Monitoring database health, (6) Detecting bloat or missing indexes, (7) Troubleshooting performance issues, (8) Designing indexes, or (9) Managing replication."
---

# PostgreSQL Database Engineering

Comprehensive PostgreSQL skill for database configuration, query optimization, cloud provider management, and health monitoring.

## Core Workflows

### 1. Configuration Tuning

**When to use:** Tuning postgresql.conf for workload, right-sizing cloud instances, optimizing memory settings.

**Workflow:**
1. Identify workload type (OLTP, Analytics, or Mixed)
2. Gather system information:
   - Total RAM
   - Storage type (SSD, NVMe, HDD)
   - Cloud provider (if applicable)
   - Expected max_connections
3. Consult `references/postgresql_conf_tuning.md` for parameter recommendations
4. Apply changes incrementally (ONE parameter at a time)
5. Monitor for 24-48 hours before next change
6. Use `scripts/config_validator.py` for validation

**Key parameters to tune:**
- Memory: `shared_buffers`, `effective_cache_size`, `work_mem`, `maintenance_work_mem`
- WAL: `max_wal_size`, `checkpoint_completion_target`, `wal_compression`
- Planner: `random_page_cost`, `effective_io_concurrency`, `default_statistics_target`
- Autovacuum: `autovacuum_max_workers`, `autovacuum_naptime`, scale factors

**Quick validation:**
```bash
# Generate recommendations
python scripts/config_validator.py --memory 64GB --storage ssd --workload mixed

# Check current non-default settings
psql -c "SELECT name, setting, unit, source FROM pg_settings WHERE source != 'default' ORDER BY name;"
```

### 2. Query Optimization

**When to use:** Slow queries, high CPU usage, investigating performance degradation.

**Workflow:**
1. Identify slow query via:
   - `pg_stat_statements` (recommended)
   - Application logs
   - `log_min_duration_statement` logs
2. Run `EXPLAIN (ANALYZE, BUFFERS)` on the query
3. Analyze EXPLAIN output:
   - Look for sequential scans on large tables
   - Check estimated vs actual row counts
   - Identify expensive operations (sorts, nested loops)
   - Review buffer usage
4. Use `scripts/explain_analyzer.py` for automated analysis
5. Consult `references/query_optimization.md` for rewriting patterns
6. Apply optimization:
   - Add indexes
   - Rewrite query (see Pattern library)
   - Update statistics (ANALYZE)
7. Verify improvement with EXPLAIN ANALYZE

**Common optimizations:**
- Replace correlated subqueries with JOINs
- Use EXISTS instead of IN for subqueries
- Use covering indexes for index-only scans
- Keyset pagination instead of OFFSET
- Partial indexes for selective queries
- Avoid functions on indexed columns in WHERE

**Quick analysis:**
```bash
# Capture EXPLAIN output and analyze
psql -c "EXPLAIN (ANALYZE, BUFFERS) SELECT ..." | python scripts/explain_analyzer.py

# Find slow queries (requires pg_stat_statements)
psql -c "SELECT round(mean_exec_time::numeric, 2) AS mean_ms, calls, query 
         FROM pg_stat_statements 
         ORDER BY mean_exec_time DESC LIMIT 10;"
```

### 3. Cloud Provider Management

**When to use:** Working with AWS RDS, GCP Cloud SQL, or Azure Database for PostgreSQL.

**Workflow:**
1. Identify cloud provider and deployment type
2. Consult `references/cloud_providers.md` for provider-specific details
3. Check provider-specific limitations:
   - Parameter restrictions
   - Extension availability
   - Connection limits
   - Storage constraints
4. Apply best practices for the platform:
   - AWS: RDS Proxy for connection pooling, Performance Insights
   - GCP: Cloud SQL Proxy, Query Insights
   - Azure: VNet integration, Flexible Server
5. Monitor using provider-native tools

**Key cloud differences:**
- AWS RDS: max_connections formula based on DBInstanceClassMemory
- GCP Cloud SQL: max 4000 connections, managed autovacuum
- Azure: Zone-redundant HA, geo-restore capabilities

**Cloud-specific considerations:**
- Use appropriate storage types (GP3 on AWS, SSD persistent on GCP)
- Configure HA/failover for production
- Set backup retention appropriately
- Use private networking (VPC/VNet)
- Enable SSL/TLS connections

### 4. Database Health Monitoring

**When to use:** Regular health checks, troubleshooting issues, preventive maintenance.

**Workflow:**
1. Run `scripts/health_check.sql` for comprehensive overview
2. Review key metrics:
   - Connection usage vs max_connections
   - Cache hit ratio (target >99%)
   - Tables needing vacuum
   - Bloat levels
   - Unused indexes
   - Long-running queries
   - Blocking locks
3. Consult `references/diagnostic_queries.md` for specific checks
4. Address findings based on severity

**Critical health indicators:**
- Cache hit ratio < 95% → Tune memory settings
- Dead tuples > 10% → Check autovacuum settings
- Connection usage > 80% → Implement connection pooling
- Replication lag > 30s → Investigate replication issues
- Unused indexes → Consider dropping (save maintenance overhead)

**Quick health check:**
```bash
# Run comprehensive health check
psql -f scripts/health_check.sql

# Check specific issues
psql -c "SELECT schemaname, tablename, n_dead_tup, 
         round(100.0 * n_dead_tup / NULLIF(n_live_tup, 0), 2) AS dead_pct
         FROM pg_stat_user_tables WHERE n_dead_tup > 10000 ORDER BY n_dead_tup DESC;"
```

### 5. Index Design and Analysis

**When to use:** Adding indexes, finding unused indexes, optimizing index structure.

**Workflow:**
1. Identify candidate columns for indexing:
   - Frequent WHERE clause columns
   - JOIN columns
   - ORDER BY columns
   - Foreign keys
2. Check for existing indexes on the table
3. Determine index type:
   - B-tree (default): Most common, supports =, <, >, <=, >=
   - GIN: Full-text search, JSONB, arrays
   - GiST: Geometric, full-text
   - BRIN: Very large tables with natural ordering
   - Hash: Only equality (=)
4. Consider advanced index features:
   - Partial indexes (WHERE clause)
   - Covering indexes (INCLUDE columns)
   - Multi-column indexes (column order matters)
5. Create index and monitor usage
6. Use diagnostic queries to find:
   - Missing indexes (frequent sequential scans)
   - Unused indexes (idx_scan = 0)
   - Duplicate indexes

**Index best practices:**
- Most selective column first in multi-column indexes
- Use partial indexes for queries on table subsets
- Add covering indexes for frequently accessed columns
- Monitor index usage before removing
- Avoid indexes on low-cardinality columns (e.g., boolean)

**Quick index analysis:**
```sql
-- Find tables with frequent sequential scans
SELECT schemaname, tablename, seq_scan, seq_tup_read, idx_scan
FROM pg_stat_user_tables
WHERE seq_scan > 0 AND pg_total_relation_size(schemaname||'.'||tablename) > 1000000
ORDER BY seq_tup_read DESC LIMIT 20;

-- Find unused indexes
SELECT schemaname, tablename, indexname, idx_scan, 
       pg_size_pretty(pg_relation_size(schemaname||'.'||indexname)) AS size
FROM pg_stat_user_indexes
WHERE idx_scan = 0 AND indexname NOT LIKE '%_pkey'
ORDER BY pg_relation_size(schemaname||'.'||indexname) DESC;
```

### 6. Vacuum and Bloat Management

**When to use:** Tables with high dead tuple ratios, performance degradation, disk space issues.

**Workflow:**
1. Identify bloated tables using diagnostic queries
2. Check autovacuum configuration
3. Determine if manual VACUUM needed
4. For severe bloat, consider:
   - VACUUM FULL (locks table, rewrites completely)
   - pg_repack (online rebuild, less disruptive)
5. Tune autovacuum for large tables:
   - Lower `autovacuum_vacuum_scale_factor` (per-table)
   - Increase `autovacuum_max_workers`
   - Decrease `autovacuum_naptime`
6. Monitor vacuum progress and impact

**Vacuum commands:**
```sql
-- Standard vacuum (non-blocking)
VACUUM ANALYZE table_name;

-- Verbose output
VACUUM VERBOSE table_name;

-- Full vacuum (blocking, reclaims space)
VACUUM FULL table_name;  -- USE WITH CAUTION

-- Analyze only (update statistics)
ANALYZE table_name;

-- Tune autovacuum for specific table
ALTER TABLE large_table SET (
  autovacuum_vacuum_scale_factor = 0.01,  -- Trigger at 1% dead tuples
  autovacuum_analyze_scale_factor = 0.005
);
```

### 7. Replication Monitoring

**When to use:** Managing replicas, troubleshooting replication lag, verifying replication status.

**Workflow:**
1. Check replication status on primary
2. Monitor replication lag
3. Verify replication slots
4. Check for inactive slots (WAL bloat risk)
5. On replicas, verify replay status
6. Consult `references/diagnostic_queries.md` for detailed queries

**Key metrics:**
- Replication lag < 30 seconds (normal)
- Replication lag 30-300 seconds (investigate)
- Replication lag > 300 seconds (critical)

**Quick replication check:**
```sql
-- On primary: Check replication status
SELECT client_addr, application_name, state, sync_state, 
       write_lag, flush_lag, replay_lag
FROM pg_stat_replication;

-- On replica: Check lag
SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) AS lag_seconds;

-- Check replication slots
SELECT slot_name, active, 
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained_wal
FROM pg_replication_slots;
```

## Using Bundled Resources

### Scripts

**health_check.sql** - Comprehensive database health report
```bash
psql -U username -d database -f scripts/health_check.sql
```
Use for: Regular monitoring, troubleshooting sessions, pre/post-change validation.

**explain_analyzer.py** - Automated EXPLAIN plan analysis
```bash
psql -c "EXPLAIN (ANALYZE, BUFFERS) SELECT ..." | python scripts/explain_analyzer.py
```
Use for: Quick query analysis, identifying optimization opportunities.

**config_validator.py** - Configuration parameter validation
```bash
python scripts/config_validator.py --memory 64GB --storage ssd --workload mixed
```
Use for: Validating postgresql.conf settings, generating recommendations.

### References

**postgresql_conf_tuning.md** - Comprehensive parameter tuning guide
- Memory settings (shared_buffers, work_mem, etc.)
- WAL configuration
- Autovacuum tuning
- Workload-specific configurations
- Cloud provider considerations

**query_optimization.md** - Query rewriting and optimization patterns
- EXPLAIN analysis fundamentals
- 13 query rewriting patterns
- Index design patterns
- JOIN optimization strategies
- Common anti-patterns

**cloud_providers.md** - AWS RDS, GCP Cloud SQL, Azure specifics
- Provider-specific limitations
- Configuration differences
- Connection management
- Backup/recovery procedures
- Monitoring tools
- Cost optimization strategies

**diagnostic_queries.md** - Essential monitoring queries
- Connection and activity monitoring
- Bloat detection
- Index analysis
- Query performance tracking
- Vacuum monitoring
- Replication status
- Lock analysis
- Cache hit ratios

**Load references as needed:**
- For configuration: Read postgresql_conf_tuning.md
- For slow queries: Read query_optimization.md
- For cloud instances: Read cloud_providers.md
- For monitoring: Read diagnostic_queries.md

## Common Patterns

### Pattern: Investigating Slow Query

```bash
# 1. Identify slow query
psql -c "SELECT query, calls, mean_exec_time FROM pg_stat_statements 
         ORDER BY mean_exec_time DESC LIMIT 5;"

# 2. Get EXPLAIN plan
psql -c "EXPLAIN (ANALYZE, BUFFERS) <query>" | python scripts/explain_analyzer.py

# 3. Check table statistics
psql -c "ANALYZE table_name;"

# 4. Apply optimization (e.g., add index)
psql -c "CREATE INDEX idx_name ON table_name(column);"

# 5. Verify improvement
psql -c "EXPLAIN (ANALYZE, BUFFERS) <query>"
```

### Pattern: Monthly Health Check

```bash
# 1. Run health check
psql -f scripts/health_check.sql > health_report_$(date +%Y%m%d).txt

# 2. Review bloat
psql -c "SELECT * FROM bloat_check;"  # From diagnostic_queries.md

# 3. Check unused indexes
psql -c "SELECT * FROM unused_indexes;"  # From diagnostic_queries.md

# 4. Verify autovacuum is running
psql -c "SELECT * FROM autovacuum_status;"  # From diagnostic_queries.md

# 5. Reset pg_stat_statements if needed
psql -c "SELECT pg_stat_statements_reset();"
```

### Pattern: Tuning for Cloud Migration

```bash
# 1. Identify target cloud provider
# AWS RDS / GCP Cloud SQL / Azure

# 2. Read cloud provider reference
# view references/cloud_providers.md

# 3. Check extension compatibility
psql -c "SELECT * FROM pg_available_extensions WHERE name = 'extension_name';"

# 4. Adjust configuration for cloud limits
python scripts/config_validator.py --memory <instance_ram> --storage ssd

# 5. Plan connection pooling strategy
# AWS: RDS Proxy
# GCP: PgBouncer
# Azure: PgBouncer
```

## Best Practices

**Configuration Management:**
- Change ONE parameter at a time
- Monitor for 24-48 hours after changes
- Document all configuration changes
- Use parameter groups/flags in cloud environments
- Keep postgresql.conf in version control

**Query Optimization:**
- Always run ANALYZE after bulk data loads
- Use EXPLAIN (ANALYZE, BUFFERS) for comprehensive analysis
- Test optimizations in staging before production
- Monitor query performance with pg_stat_statements
- Set appropriate `log_min_duration_statement`

**Index Management:**
- Monitor index usage regularly
- Remove unused indexes (saves write overhead)
- Create indexes during off-peak hours for large tables
- Use CONCURRENTLY for production index creation
- Document index rationale

**Vacuum Management:**
- Never disable autovacuum
- Tune autovacuum for large tables (per-table settings)
- Monitor dead tuple ratios
- Consider pg_repack for severe bloat
- Schedule manual VACUUM during maintenance windows

**Replication:**
- Monitor replication lag continuously
- Alert on lag > 30 seconds
- Remove inactive replication slots
- Use replication slots (safer than wal_keep_size)
- Test failover procedures regularly

**Cloud-Specific:**
- Use provider-native monitoring tools
- Enable automated backups with appropriate retention
- Configure HA for production workloads
- Use private networking (VPC/VNet)
- Enable SSL/TLS connections
- Right-size instances based on actual usage

## Troubleshooting

**High CPU Usage:**
1. Check for slow queries in pg_stat_statements
2. Look for missing indexes causing sequential scans
3. Check for lock contention
4. Review autovacuum activity
5. Verify statistics are up-to-date (ANALYZE)

**High Memory Usage:**
1. Check work_mem setting (can multiply with connections)
2. Review maintenance_work_mem for VACUUM operations
3. Check for connection leaks (idle in transaction)
4. Monitor shared_buffers usage
5. Review temp_buffers for temp table operations

**Slow Queries After Migration:**
1. Run ANALYZE on all tables
2. Verify indexes were recreated
3. Check random_page_cost for storage type
4. Compare EXPLAIN plans between old and new systems
5. Review cloud-specific limitations

**Replication Lag:**
1. Check network bandwidth between primary and replica
2. Verify replica has sufficient CPU/I/O capacity
3. Check for long-running transactions on primary
4. Review wal_sender_timeout setting
5. Consider increasing wal_keep_size or using replication slots

**Connection Exhaustion:**
1. Implement connection pooling (PgBouncer, RDS Proxy)
2. Find and kill idle in transaction connections
3. Review application connection management
4. Check for connection leaks
5. Consider increasing max_connections (with memory implications)

**Bloat Issues:**
1. Check autovacuum is running and not blocked
2. Verify autovacuum settings are appropriate for table size
3. Look for long-running transactions preventing vacuum
4. Consider manual VACUUM for immediate relief
5. For severe cases, use pg_repack or VACUUM FULL

## Critical Reminders

- **ALWAYS** test configuration changes in non-production first
- **NEVER** disable autovacuum
- **NEVER** use VACUUM FULL on large production tables without maintenance window
- **ALWAYS** use CONCURRENTLY for index creation on production tables
- **ALWAYS** run ANALYZE after bulk data loads
- **ALWAYS** monitor for 24-48 hours after configuration changes
- **NEVER** change multiple parameters simultaneously
- **ALWAYS** take a backup before major changes
- **ALWAYS** document the rationale for configuration decisions

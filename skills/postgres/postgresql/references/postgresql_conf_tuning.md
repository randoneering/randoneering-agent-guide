# PostgreSQL Configuration Tuning Reference

Comprehensive guide for tuning postgresql.conf parameters based on workload type, hardware, and cloud provider constraints.

## Critical Parameters by Category

### Memory Settings

#### shared_buffers
**Purpose:** Main PostgreSQL cache for data pages  
**Default:** 128MB (too low for production)  
**Recommended:**
- Dedicated server: 25% of total RAM (up to 40% for read-heavy workloads)
- Mixed workload server: 15-25% of total RAM
- Cloud instances: Check provider limits (RDS has max ~75% of RAM)

**Tuning guidelines:**
- Start: 25% of RAM for dedicated DB servers
- Monitor: `pg_stat_database.blks_hit / (blks_hit + blks_read)` (target >99%)
- Too high: Diminishing returns above 40GB; OS cache becomes more important
- Too low: Excessive disk I/O, poor performance

**Example values:**
```
# 16GB RAM dedicated server
shared_buffers = 4GB

# 64GB RAM dedicated server  
shared_buffers = 16GB

# 128GB RAM server (diminishing returns kick in)
shared_buffers = 32GB  # Not 50GB - leave room for OS cache
```

#### effective_cache_size
**Purpose:** Planner hint about total available OS + PG cache  
**Not allocated memory** - just tells planner what to expect  
**Recommended:**
- Dedicated: 50-75% of total RAM
- Shared: 25-50% of total RAM

**Example:**
```
# 64GB RAM dedicated server
effective_cache_size = 48GB  # 75% of RAM
```

#### work_mem
**Purpose:** Memory per operation (sort, hash, etc.) PER CONNECTION  
**Default:** 4MB (usually too low)  
**Danger:** Per-operation allocation; query can use work_mem × operation_count  
**Recommended:**
- Start: (Total RAM × 0.25) / max_connections / 2
- OLTP: 8-32MB
- Reporting/Analytics: 64-256MB
- Complex queries: 512MB-2GB (monitor carefully)

**Tuning:**
- Monitor: Check for "temporary file" entries in logs
- Set per-session: `SET work_mem = '256MB';` for heavy queries
- Too high: Risk of OOM if many concurrent complex queries
- Too low: Disk-based sorts/hashes (slow)

**Examples:**
```
# OLTP workload (many small queries)
work_mem = 16MB

# Mixed workload
work_mem = 64MB

# Analytics/reporting
work_mem = 256MB
```

#### maintenance_work_mem
**Purpose:** Memory for VACUUM, CREATE INDEX, ALTER TABLE  
**Default:** 64MB (too low)  
**Recommended:**
- 5-10% of RAM, up to 2GB
- Consider cloud provider limits

**Example:**
```
maintenance_work_mem = 1GB  # For 16GB+ RAM systems
```

### Write-Ahead Log (WAL) Settings

#### wal_buffers
**Purpose:** Buffers for WAL writes  
**Default:** -1 (auto: 1/32 of shared_buffers, max 16MB)  
**Recommended:** Usually auto is fine; manual setting: 16MB for write-heavy workloads

```
wal_buffers = 16MB
```

#### checkpoint_completion_target
**Purpose:** Spread checkpoint I/O over this fraction of checkpoint interval  
**Default:** 0.9 (good for most workloads)  
**Range:** 0.0-1.0  
**Tuning:** Higher = smoother I/O but longer recovery time

```
checkpoint_completion_target = 0.9
```

#### max_wal_size
**Purpose:** Trigger checkpoint when WAL exceeds this size  
**Default:** 1GB (too small for production)  
**Recommended:**
- Light writes: 2-4GB
- Moderate writes: 4-8GB
- Heavy writes: 16-32GB

**Trade-off:** Larger = fewer checkpoints (better performance) but longer recovery

```
# Moderate write workload
max_wal_size = 8GB
min_wal_size = 2GB
```

#### wal_compression
**Purpose:** Compress full page writes in WAL  
**Default:** off  
**Recommended:** on (especially for cloud storage)  
**Benefit:** Reduces WAL size, improves replication performance

```
wal_compression = on
```

### Connection Settings

#### max_connections
**Purpose:** Maximum concurrent connections  
**Default:** 100  
**Cloud limits:**
- AWS RDS: Based on instance class (see DBInstanceClassMemory formula)
- GCP Cloud SQL: 4000 max for larger instances
- Azure: Based on tier

**Recommended:**
- Use connection pooling (PgBouncer, pgpool) instead of increasing this
- OLTP: 100-300 (with pooler)
- Without pooler: Calculate based on workload needs
- Each connection uses ~10MB RAM (approximately)

**Formula:**
```
Available RAM for connections = (Total RAM - shared_buffers - OS overhead)
Safe max_connections = Available RAM / (10MB + work_mem)
```

**Example:**
```
# With PgBouncer in front
max_connections = 200

# Direct connections (not recommended for high concurrency)
max_connections = 100
```

### Query Planner Settings

#### random_page_cost
**Purpose:** Cost estimate for random disk I/O  
**Default:** 4.0 (HDD assumption)  
**Recommended:**
- SSD: 1.1-1.5
- NVMe: 1.0-1.1
- Cloud storage (EBS, persistent disk): 1.1-1.3

**Impact:** Lower values favor index scans over sequential scans

```
# SSD or cloud storage
random_page_cost = 1.1
```

#### effective_io_concurrency
**Purpose:** Number of simultaneous I/O operations  
**Default:** 1  
**Recommended:**
- HDD RAID: Number of drives
- SSD: 200-300
- NVMe: 500-1000
- Cloud: 200 (varies by instance type)

```
# SSD or cloud storage
effective_io_concurrency = 200
```

#### default_statistics_target
**Purpose:** Histogram detail for query planner  
**Default:** 100  
**Range:** 1-10000  
**Recommended:**
- Standard: 100-250
- High cardinality columns: 500-1000 (per-column basis)
- Data warehouse: 500

**Trade-off:** Higher = better plans but slower ANALYZE

```
default_statistics_target = 250
```

### Autovacuum Settings

#### autovacuum
**Purpose:** Enable automatic VACUUM and ANALYZE  
**Default:** on  
**Recommendation:** NEVER turn off

```
autovacuum = on
```

#### autovacuum_max_workers
**Purpose:** Concurrent autovacuum processes  
**Default:** 3  
**Recommended:**
- Small DBs: 3-5
- Large DBs (100+ tables): 6-10
- Cloud: Check instance vCPU count

```
autovacuum_max_workers = 6
```

#### autovacuum_naptime
**Purpose:** Sleep time between autovacuum runs  
**Default:** 1min  
**Recommended:**
- Write-heavy: 10-30s
- Standard: 30-60s

```
autovacuum_naptime = 30s
```

#### autovacuum_vacuum_scale_factor
**Purpose:** Fraction of table to trigger autovacuum  
**Default:** 0.2 (20% of table)  
**Recommended:**
- Large tables: 0.01-0.05 (1-5%)
- Standard tables: 0.1 (10%)
- Small tables: 0.2 (default)

**Per-table tuning preferred for large tables:**
```sql
ALTER TABLE large_table SET (autovacuum_vacuum_scale_factor = 0.01);
```

#### autovacuum_analyze_scale_factor
**Purpose:** Fraction of table to trigger ANALYZE  
**Default:** 0.1 (10%)  
**Recommended:** Same as vacuum_scale_factor or slightly lower

```
autovacuum_analyze_scale_factor = 0.05
```

### Logging and Monitoring

#### log_min_duration_statement
**Purpose:** Log queries taking longer than this threshold  
**Default:** -1 (disabled)  
**Recommended:**
- OLTP: 500-1000ms
- Analytics: 5000-10000ms
- Development: 100ms

```
log_min_duration_statement = 1000  # 1 second
```

#### log_checkpoints
**Purpose:** Log checkpoint activity  
**Default:** off  
**Recommended:** on (essential for tuning)

```
log_checkpoints = on
```

#### log_connections / log_disconnections
**Purpose:** Log connection events  
**Default:** off  
**Recommended:** on for security auditing (high volume in OLTP)

```
log_connections = on
log_disconnections = on
```

#### log_lock_waits
**Purpose:** Log when query waits for lock  
**Default:** off  
**Recommended:** on (helps identify contention)

```
log_lock_waits = on
```

#### log_temp_files
**Purpose:** Log creation of temporary files above size threshold  
**Default:** -1 (disabled)  
**Recommended:** 0 or 10MB (catches work_mem issues)

```
log_temp_files = 0  # Log all temp files
```

### Replication Settings

#### wal_level
**Purpose:** WAL detail level  
**Options:** minimal, replica, logical  
**Recommended:** replica (or logical if using logical replication)

```
wal_level = replica
```

#### max_wal_senders
**Purpose:** Max concurrent replication connections  
**Default:** 10  
**Recommended:** Number of replicas + 2 (for failover/backup)

```
max_wal_senders = 5  # 3 replicas + 2 buffer
```

#### max_replication_slots
**Purpose:** Max replication slots (safer than wal_keep_size)  
**Default:** 10  
**Recommended:** Number of replicas + logical subscriptions

```
max_replication_slots = 10
```

#### hot_standby
**Purpose:** Allow read queries on replicas  
**Default:** on  
**Recommended:** on (for read replicas)

```
hot_standby = on
```

## Workload-Specific Configurations

### OLTP Workload (High Concurrency, Small Transactions)

```ini
# Memory (16GB RAM example)
shared_buffers = 4GB
effective_cache_size = 12GB
work_mem = 16MB
maintenance_work_mem = 1GB

# WAL
wal_buffers = 16MB
max_wal_size = 4GB
checkpoint_completion_target = 0.9

# Connections
max_connections = 200  # With PgBouncer

# Planner
random_page_cost = 1.1
effective_io_concurrency = 200

# Autovacuum (aggressive for high writes)
autovacuum_max_workers = 6
autovacuum_naptime = 30s

# Logging
log_min_duration_statement = 1000
log_checkpoints = on
log_lock_waits = on
```

### Analytics/Data Warehouse (Complex Queries, Low Concurrency)

```ini
# Memory (64GB RAM example)
shared_buffers = 16GB
effective_cache_size = 48GB
work_mem = 256MB  # Higher for complex queries
maintenance_work_mem = 2GB

# WAL
max_wal_size = 16GB  # Large batch loads

# Connections
max_connections = 50  # Lower concurrency

# Planner
random_page_cost = 1.1
effective_io_concurrency = 200
default_statistics_target = 500  # Better stats for complex queries

# Autovacuum
autovacuum_naptime = 60s  # Less frequent (fewer writes)

# Logging
log_min_duration_statement = 5000  # 5 seconds
```

### Mixed Workload

```ini
# Memory (32GB RAM example)
shared_buffers = 8GB
effective_cache_size = 24GB
work_mem = 64MB
maintenance_work_mem = 2GB

# WAL
max_wal_size = 8GB
checkpoint_completion_target = 0.9

# Connections
max_connections = 150

# Planner
random_page_cost = 1.1
effective_io_concurrency = 200
default_statistics_target = 250

# Autovacuum
autovacuum_max_workers = 6
autovacuum_naptime = 30s

# Logging
log_min_duration_statement = 1000
log_checkpoints = on
```

## Cloud Provider Considerations

### AWS RDS

**Key differences:**
- Cannot edit: `shared_preload_libraries` partially (limited to RDS-approved extensions)
- Cannot edit: `log_destination`, `logging_collector`
- max_connections formula: `DBInstanceClassMemory / 9531392`
- Use parameter groups for changes
- Some parameters require reboot

**RDS-specific parameters:**
```ini
# Enable enhanced monitoring
shared_preload_libraries = 'pg_stat_statements'

# Logging (use CloudWatch)
log_statement = 'ddl'  # Or 'all' for debugging
log_min_duration_statement = 1000
```

### GCP Cloud SQL

**Key differences:**
- Managed autovacuum (less control)
- Cannot edit some networking parameters
- Use Cloud SQL flags for configuration
- max_connections: Up to 4000 for larger instances

**Cloud SQL considerations:**
- Persistent disk I/O is network-based
- Use `random_page_cost = 1.1` for SSD persistent disks

### Azure Database for PostgreSQL

**Key differences:**
- Flexible Server vs Single Server (prefer Flexible)
- Some parameters require server restart
- max_connections varies by tier

## Tuning Workflow

1. **Baseline:** Capture current performance metrics
2. **Identify bottleneck:** CPU, I/O, memory, or locks?
3. **Change ONE parameter at a time**
4. **Test under realistic load**
5. **Monitor for 24-48 hours**
6. **Document changes and impact**

## Common Mistakes

❌ Setting work_mem too high (OOM risk with concurrent queries)  
❌ Leaving shared_buffers at default 128MB  
❌ Disabling autovacuum  
❌ Using default random_page_cost (4.0) on SSDs  
❌ Changing multiple parameters simultaneously  
❌ Not monitoring after changes  
❌ Ignoring cloud provider limits  

## Validation Queries

```sql
-- Show all non-default settings
SELECT name, setting, unit, source 
FROM pg_settings 
WHERE source != 'default' 
ORDER BY name;

-- Memory allocation check
SELECT 
  setting AS shared_buffers,
  pg_size_pretty(setting::bigint * 8192) AS size
FROM pg_settings 
WHERE name = 'shared_buffers';

-- Connection usage
SELECT count(*) as current_connections, 
       max_connections 
FROM pg_stat_activity, 
     (SELECT setting::int AS max_connections FROM pg_settings WHERE name = 'max_connections') mc;

-- Cache hit ratio (target > 99%)
SELECT 
  sum(blks_hit) / nullif(sum(blks_hit + blks_read), 0) AS cache_hit_ratio
FROM pg_stat_database;
```

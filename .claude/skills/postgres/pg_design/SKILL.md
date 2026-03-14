---
name: postgresql-architecture
description: "PostgreSQL architecture and design patterns skill covering database schema design, partitioning strategies (range, list, hash, multi-level), high availability architectures (streaming replication, Patroni, failover), multi-tenancy models (shared schema, separate schemas, separate databases), data modeling patterns (normalization, temporal data, event sourcing), and connection pooling/load balancing. Use when: (1) Designing database schemas, (2) Implementing table partitioning, (3) Setting up HA/DR with replication, (4) Building multi-tenant SaaS applications, (5) Architecting scalable PostgreSQL systems, (6) Planning failover strategies, or (7) Designing data models and choosing appropriate data types."
---

# PostgreSQL Architecture and Design

Comprehensive PostgreSQL skill for database architecture, schema design, partitioning, high availability, and multi-tenancy patterns.

## Core Workflows

### 1. Table Partitioning Design

**When to use:** Tables >100GB, time-series data, multi-tenant architectures, data lifecycle management.

**Workflow:**
1. Identify partitioning need:
   - Large table causing slow queries
   - Time-based data with retention policy
   - Multi-tenant isolation requirements
   - Data archival needs
2. Select partitioning type:
   - **Range:** Time-series, sequential data (most common)
   - **List:** Categories, multi-tenant by tenant_id, regions
   - **Hash:** Even distribution when no natural key
3. Choose partition key (must be in PRIMARY KEY)
4. Determine partition size:
   - Daily: High-volume data (>1M rows/day)
   - Monthly: Medium-volume (most common)
   - Quarterly/Yearly: Low-volume, long retention
5. Implement partitioning
6. Create indexes (on parent or per partition)
7. Set up automated partition creation/retention
8. Verify partition pruning in queries

**Reference:** `references/partitioning.md` for detailed patterns and examples.

**Key decisions:**
```sql
-- Time-series: Range by date
PARTITION BY RANGE (created_at)

-- Multi-tenant: List by tenant_id
PARTITION BY LIST (tenant_id)

-- Load balancing: Hash by user_id
PARTITION BY HASH (user_id)

-- Complex: Range + List (date, then tenant)
-- Parent: PARTITION BY RANGE (created_at)
-- Child: PARTITION BY LIST (tenant_id)
```

### 2. High Availability Architecture Design

**When to use:** Production systems, uptime requirements >99%, disaster recovery planning.

**Workflow:**
1. Define availability requirements:
   - RTO (Recovery Time Objective): Max acceptable downtime
   - RPO (Recovery Point Objective): Max acceptable data loss
   - Availability target (99.9%, 99.99%, etc.)
2. Choose replication strategy:
   - **Asynchronous:** Better performance, potential data loss
   - **Synchronous:** Zero data loss, higher latency
   - **Quorum:** Balance between sync and async
3. Select HA architecture:
   - **Manual failover:** Simple, slower RTO (5-15 min)
   - **Patroni/etcd:** Automatic failover, faster RTO (30-60 sec)
   - **Multi-region:** Geographic redundancy, DR
4. Implement connection pooling/load balancing
5. Set up monitoring and alerting
6. Document and test failover procedures

**Reference:** `references/ha_replication.md` for architectures and setup.

**Architecture selection:**
```
Single Primary + Async Replicas
├─ RTO: Manual (5-15 min)
├─ RPO: Seconds to minutes
└─ Cost: Low

Patroni + etcd Cluster
├─ RTO: Automatic (30-60 sec)
├─ RPO: Configurable (sync/async)
└─ Cost: Medium-High

Multi-Region Cascading
├─ RTO: Minutes (cross-region)
├─ RPO: Seconds to minutes
└─ Cost: High
```

### 3. Multi-Tenancy Architecture

**When to use:** SaaS applications, B2B platforms, any system serving multiple isolated customers.

**Workflow:**
1. Assess tenant profile:
   - Number of tenants (10s, 100s, 1000s+)
   - Tenant size (users, data volume)
   - Isolation requirements (compliance, security)
   - Customization needs
2. Select multi-tenancy model:
   - **Shared Schema:** Many small tenants, cost-effective
   - **Separate Schemas:** Medium tenants, some customization
   - **Separate Databases:** Few large tenants, strong isolation
   - **Hybrid:** Mix of models based on tenant tier
3. Implement data isolation:
   - Row-Level Security (RLS) for shared schema
   - Schema routing for separate schemas
   - Connection routing for separate databases
4. Design tenant onboarding/offboarding
5. Plan for tenant-specific scaling
6. Implement usage tracking and billing

**Reference:** `references/multi_tenancy.md` for detailed patterns.

**Decision matrix:**
```
Shared Schema (tenant_id column + RLS)
├─ Best for: 100-10,000+ tenants
├─ Isolation: Low
├─ Cost: Low
└─ Complexity: Low

Separate Schemas (one schema per tenant)
├─ Best for: 10-100 tenants
├─ Isolation: Medium
├─ Cost: Medium
└─ Complexity: Medium

Separate Databases (one DB per tenant)
├─ Best for: 1-50 tenants
├─ Isolation: High
├─ Cost: High
└─ Complexity: High
```

### 4. Schema Design and Data Modeling

**When to use:** New projects, schema refactoring, adding features, data model optimization.

**Workflow:**
1. Identify entities and relationships
2. Apply normalization (typically 3NF):
   - 1NF: Atomic values
   - 2NF: No partial dependencies
   - 3NF: No transitive dependencies
3. Consider strategic denormalization:
   - Materialized aggregates
   - Cached lookups
   - Snapshot tables
4. Choose appropriate data types:
   - Use BIGSERIAL for high-volume tables
   - TIMESTAMPTZ for timestamps
   - JSONB for flexible attributes
   - UUID for distributed systems
5. Design constraints and indexes:
   - Primary keys
   - Foreign keys with cascade rules
   - CHECK constraints
   - Unique constraints
   - Indexes on foreign keys
6. Plan for common query patterns

**Reference:** `references/schema_design.md` for patterns and anti-patterns.

**Common patterns:**
```sql
-- Polymorphic associations: Exclusive arcs
post_id INTEGER REFERENCES posts(id),
photo_id INTEGER REFERENCES photos(id),
CHECK ((post_id IS NOT NULL AND photo_id IS NULL) OR 
       (post_id IS NULL AND photo_id IS NOT NULL))

-- Temporal data: Audit trails
CREATE TABLE user_audit (
    user_id INTEGER,
    field_name VARCHAR(50),
    old_value TEXT,
    new_value TEXT,
    changed_at TIMESTAMP
);

-- Soft deletes
deleted_at TIMESTAMP,  -- NULL = active
CREATE INDEX idx_active ON table(id) WHERE deleted_at IS NULL;

-- Tags/hierarchies: ltree extension
path ltree NOT NULL,
CREATE INDEX idx_path ON categories USING gist(path);
```

### 5. Connection Pooling and Load Balancing

**When to use:** High connection counts, read scaling, automatic failover routing.

**Workflow:**
1. Assess connection needs:
   - Max concurrent connections expected
   - Current max_connections setting
   - Connection lifecycle (long-lived vs short-lived)
2. Choose pooling strategy:
   - **PgBouncer:** Most common, transaction pooling
   - **pgpool-II:** Load balancing + pooling
   - **Application-level:** For specific needs
3. Configure pooling mode:
   - Session: One server conn per client (safest)
   - Transaction: Conn released after txn (recommended)
   - Statement: Released after statement (rarely used)
4. Set up load balancing (if needed):
   - HAProxy for read/write split
   - Route reads to replicas
   - Health checks and failover
5. Monitor connection usage
6. Tune pool sizes

**Configuration:**
```ini
# PgBouncer
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25  # Per database

# HAProxy
frontend postgres_write
    bind *:5432
    server primary primary:5432 check

frontend postgres_read
    bind *:5433
    balance roundrobin
    server replica1 replica1:5432 check
    server replica2 replica2:5432 check
```

### 6. Failover and Disaster Recovery Planning

**When to use:** Production systems, business continuity planning, compliance requirements.

**Workflow:**
1. Define DR objectives:
   - RTO and RPO requirements
   - Geographic requirements
   - Compliance needs
2. Design backup strategy:
   - Continuous WAL archiving
   - Regular base backups
   - Test restores
3. Implement replication:
   - Local replicas for HA
   - Remote replicas for DR
4. Document runbooks:
   - Failover procedures
   - Rollback procedures
   - Contact information
5. Test failover regularly:
   - Quarterly drills
   - Document lessons learned
   - Update procedures
6. Monitor replication health:
   - Replication lag
   - Slot status
   - Backup age

**Failover scenarios:**
```bash
# Manual promotion (replica → primary)
pg_ctl promote

# Patroni automatic failover
# Detects failure, elects new primary (30-60s)

# PITR for data corruption
pgbackrest --stanza=main --type=time \
  --target="2024-01-15 14:20:00" restore
```

## Using References

**partitioning.md** - Table partitioning strategies
- Range, list, hash partitioning
- Multi-level partitioning
- Partition key selection
- Partition management (create, drop, attach)
- Migration strategies
- Performance optimization

**ha_replication.md** - High availability architectures  
- Streaming replication (sync/async)
- Logical replication
- Patroni cluster setup
- Connection pooling (PgBouncer)
- Load balancing (HAProxy)
- Failover procedures
- Monitoring replication

**multi_tenancy.md** - Multi-tenant patterns
- Shared schema with RLS
- Separate schemas per tenant
- Separate databases per tenant
- Hybrid approaches
- Tenant onboarding/offboarding
- Scaling strategies
- Security and isolation

**schema_design.md** - Data modeling patterns
- Normalization (1NF, 2NF, 3NF)
- Strategic denormalization
- Common design patterns
- PostgreSQL-specific types
- Constraints and integrity
- Temporal data and versioning

**Load references as needed:**
- For partitioning: Read partitioning.md
- For HA/replication: Read ha_replication.md
- For multi-tenancy: Read multi_tenancy.md
- For schema design: Read schema_design.md

## Common Patterns

### Pattern: Designing Time-Series Table

```sql
-- 1. Create partitioned table
CREATE TABLE sensor_data (
    sensor_id INTEGER,
    reading_time TIMESTAMPTZ NOT NULL,
    temperature DECIMAL(5,2),
    PRIMARY KEY (sensor_id, reading_time)
) PARTITION BY RANGE (reading_time);

-- 2. Create monthly partitions (automated with pg_partman)
CREATE EXTENSION pg_partman;
SELECT partman.create_parent(
    'public.sensor_data',
    'reading_time',
    'native',
    'monthly',
    p_premake := 3,
    p_retention := '12 months'
);

-- 3. Add indexes
CREATE INDEX ON sensor_data(sensor_id, reading_time DESC);

-- 4. Schedule partition maintenance
SELECT partman.run_maintenance('public.sensor_data');
```

### Pattern: Setting Up Patroni HA Cluster

```bash
# 1. Install etcd cluster (3+ nodes for quorum)
# 2. Install Patroni on all PostgreSQL nodes
# 3. Configure patroni.yml with etcd endpoints
# 4. Start Patroni (auto-bootstraps cluster)
patronictl -c patroni.yml init

# 5. Check cluster status
patronictl -c patroni.yml list

# 6. Set up HAProxy for connection routing
# 7. Test failover
patronictl -c patroni.yml switchover
```

### Pattern: Implementing Multi-Tenant with RLS

```sql
-- 1. Add tenant_id to all tables
ALTER TABLE users ADD COLUMN tenant_id INTEGER NOT NULL;
ALTER TABLE orders ADD COLUMN tenant_id INTEGER NOT NULL;

-- 2. Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- 3. Create policies
CREATE POLICY tenant_isolation_users ON users
    USING (tenant_id = current_setting('app.current_tenant')::integer);

CREATE POLICY tenant_isolation_orders ON orders
    USING (tenant_id = current_setting('app.current_tenant')::integer);

-- 4. Application sets context per session
SET app.current_tenant = '123';

-- 5. Queries automatically filtered
SELECT * FROM orders;  -- Only tenant 123's data
```

## Best Practices

**Partitioning:**
- Start with monthly partitions for time-series
- Include partition key in PRIMARY KEY
- Use pg_partman for automation
- Monitor partition count (<100 recommended)
- Plan partition creation ahead of time
- Document partition strategy

**High Availability:**
- Use replication slots (not wal_keep_size)
- Monitor replication lag continuously
- Test failover quarterly
- Document runbooks
- Use synchronous for zero data loss
- Automate with Patroni for production

**Multi-Tenancy:**
- Choose model based on tenant count
- Use RLS for shared schema isolation
- Validate tenant access in application
- Plan for schema migrations
- Monitor per-tenant usage
- Design for tenant migration

**Schema Design:**
- Normalize to 3NF by default
- Denormalize strategically for performance
- Use appropriate PostgreSQL types
- Add indexes on foreign keys
- Use constraints for data integrity
- Consider JSONB for flexible attributes

**Connection Pooling:**
- Use PgBouncer for transaction pooling
- Size pools appropriately (25-50 per DB)
- Monitor connection usage
- Route reads to replicas
- Configure health checks in load balancers

## Critical Reminders

- **ALWAYS include partition key in PRIMARY KEY**
- **NEVER partition without query analysis** - ensure queries use partition key
- **ALWAYS test failover procedures** - quarterly drills minimum
- **NEVER trust client-provided tenant_id** - validate in application
- **ALWAYS use replication slots** - prevent WAL deletion
- **NEVER disable RLS** once enabled - security risk
- **ALWAYS monitor replication lag** - alert on >30 seconds
- **NEVER create too many partitions** - keep under 100 if possible
- **ALWAYS document architecture decisions** - rationale matters
- **NEVER skip migration testing** - test on production-like data

## Troubleshooting

**Partition pruning not working:**
- Check partition key in WHERE clause
- Avoid functions on partition key
- Use EXPLAIN to verify
- Ensure partition key data type matches

**Replication lag increasing:**
- Check network bandwidth
- Verify replica I/O capacity
- Look for long-running transactions
- Consider increasing wal_sender_timeout

**Multi-tenant data leakage:**
- Verify RLS policies enabled
- Test with different tenant contexts
- Check for missing tenant_id columns
- Audit queries for tenant_id filters

**Slow queries after partitioning:**
- Ensure partition pruning working
- Add indexes to partitions
- Check statistics are up-to-date
- Consider partition-specific index strategies

**Connection pool exhaustion:**
- Increase pool size
- Check for connection leaks
- Monitor transaction duration
- Consider separating read/write pools

**Failover not working:**
- Check replication slots active
- Verify network connectivity
- Ensure Patroni/etcd quorum
- Check for blocking transactions

# High Availability and Replication Architectures

Comprehensive guide to PostgreSQL HA/DR architectures including streaming replication, logical replication, failover strategies, and cluster management.

## Overview

**High Availability Goals:**
- Minimize downtime (target: 99.9%+ uptime)
- Automatic failover
- Data durability
- Read scalability
- Disaster recovery

**Key Metrics:**
- **RTO (Recovery Time Objective):** Max acceptable downtime
- **RPO (Recovery Point Objective):** Max acceptable data loss
- **Availability:** Percentage uptime (99.9% = 43 minutes/month downtime)

## Replication Types

### Physical (Streaming) Replication

**How it works:**
- Binary WAL (Write-Ahead Log) shipped from primary to replicas
- Byte-for-byte identical copy
- Entire cluster replicated (all databases)

**Characteristics:**
- **Pros:**
  - Low overhead
  - Consistent across all databases
  - Simple to set up
  - Supports synchronous and asynchronous modes
- **Cons:**
  - All or nothing (cannot replicate subset)
  - Same PostgreSQL major version required
  - Read-only replicas (cannot write)
  - DDL replicates (cannot filter)

**Configuration:**

Primary server (postgresql.conf):
```ini
# WAL settings
wal_level = replica  # or 'logical' for logical replication too
max_wal_senders = 10  # Max replication connections
max_replication_slots = 10  # Recommended over wal_keep_size

# Synchronous replication (optional)
synchronous_standby_names = 'replica1,replica2'  # Names in recovery.conf
synchronous_commit = on  # Wait for replica confirmation

# Archiving (recommended)
archive_mode = on
archive_command = 'cp %p /archive/%f'
```

Replica server (recovery.conf or postgresql.auto.conf in PG 12+):
```ini
# Connection to primary
primary_conninfo = 'host=primary-host port=5432 user=replicator password=secret'

# Replication slot (recommended)
primary_slot_name = 'replica1_slot'

# Hot standby (allow reads)
hot_standby = on
```

**Create replication slot on primary:**
```sql
SELECT pg_create_physical_replication_slot('replica1_slot');
```

**Setup replica:**
```bash
# 1. Base backup from primary
pg_basebackup -h primary-host -D /var/lib/postgresql/data -U replicator -P -Xs -R

# 2. Start replica
pg_ctl start
```

### Synchronous vs Asynchronous Replication

**Asynchronous (default):**
- Primary doesn't wait for replica confirmation
- Better write performance
- Risk of data loss if primary fails before WAL ships
- RPO: Seconds to minutes

**Synchronous:**
- Primary waits for replica to confirm write
- Zero data loss (RPO = 0)
- Higher write latency
- RTO: Failover time

**Configuration:**
```sql
-- Synchronous (wait for 1 replica)
synchronous_standby_names = 'FIRST 1 (replica1, replica2)';

-- Wait for 2 replicas
synchronous_standby_names = 'FIRST 2 (replica1, replica2, replica3)';

-- Wait for ANY (first to respond)
synchronous_standby_names = 'ANY 1 (replica1, replica2)';
```

**Quorum commit (PostgreSQL 10+):**
```sql
-- Require majority (2 of 3)
synchronous_standby_names = 'ANY 2 (replica1, replica2, replica3)';
```

### Logical Replication

**How it works:**
- Table-level replication using logical decoding
- Replicates DML (INSERT, UPDATE, DELETE) not DDL
- Selective table replication
- Different PostgreSQL versions supported (10+)

**Characteristics:**
- **Pros:**
  - Selective replication (specific tables/databases)
  - Cross-version replication
  - Can write to replica (different use cases)
  - Multiple sources → single target (data consolidation)
- **Cons:**
  - More overhead than physical
  - DDL not replicated (schema changes manual)
  - Requires PRIMARY KEY or REPLICA IDENTITY
  - More complex troubleshooting

**Setup:**

Publisher (source):
```sql
-- Enable logical replication
-- postgresql.conf: wal_level = logical

-- Create publication
CREATE PUBLICATION my_pub FOR ALL TABLES;

-- Or selective tables
CREATE PUBLICATION orders_pub FOR TABLE orders, order_items;

-- Or with filter (PostgreSQL 15+)
CREATE PUBLICATION active_orders_pub FOR TABLE orders WHERE (status = 'active');
```

Subscriber (target):
```sql
-- Create empty tables (matching schema)
CREATE TABLE orders (...);

-- Create subscription
CREATE SUBSCRIPTION my_sub
    CONNECTION 'host=publisher-host port=5432 dbname=mydb user=replicator password=secret'
    PUBLICATION my_pub;

-- Check replication status
SELECT * FROM pg_stat_subscription;
```

**Conflict resolution:**
Subscriber wins by default. Configure:
```sql
ALTER SUBSCRIPTION my_sub SET (disable_on_error = true);  -- Stop on conflict
```

**Use cases:**
- Multi-master setups (with conflict resolution)
- Selective replication
- Database upgrades (replicate to newer version)
- Data consolidation from multiple sources
- Cross-region replication with filtering

## High Availability Architectures

### Architecture 1: Single Primary + Async Replicas

```
┌─────────────┐
│   Primary   │
│  (read/write)│
└──────┬──────┘
       │ Async WAL streaming
       ├──────────────┬──────────────┐
       │              │              │
┌──────▼──────┐ ┌────▼──────┐ ┌─────▼─────┐
│  Replica 1  │ │ Replica 2 │ │ Replica 3 │
│ (read-only) │ │(read-only)│ │(read-only)│
└─────────────┘ └───────────┘ └───────────┘
```

**Characteristics:**
- RTO: Manual failover (minutes to hours)
- RPO: Seconds to minutes (potential data loss)
- Cost: Low (no special software)
- Complexity: Low

**Use case:**
- Read scaling
- Basic DR
- Development/staging environments

**Failover:**
Manual promotion of replica:
```bash
# On replica
pg_ctl promote

# Or use recovery signal file (PG 12+)
touch /var/lib/postgresql/data/standby.signal
```

### Architecture 2: Synchronous Replication + Manual Failover

```
┌─────────────┐
│   Primary   │
│  (read/write)│
└──────┬──────┘
       │ Sync WAL (FIRST 1)
       │
┌──────▼───────┐  Async ┌───────────┐
│  Replica 1   │◄───────│ Replica 2 │
│   (sync)     │        │  (async)  │
└──────────────┘        └───────────┘
```

**Characteristics:**
- RTO: Manual failover (5-15 minutes)
- RPO: Zero (synchronous replica)
- Cost: Medium
- Complexity: Medium

**Configuration:**
```ini
# Primary
synchronous_standby_names = 'FIRST 1 (replica1, replica2)';
synchronous_commit = on
```

**Use case:**
- Zero data loss requirement
- Acceptable manual failover
- Financial systems

### Architecture 3: Patroni/etcd Cluster (Automated Failover)

```
┌──────────┐  ┌──────────┐  ┌──────────┐
│   etcd   │  │   etcd   │  │   etcd   │
│  (consensus) │  (quorum) │  (quorum) │
└─────┬────┘  └─────┬────┘  └─────┬────┘
      │             │             │
      └──────┬──────┴──────┬──────┘
             │             │
      ┌──────▼────┐   ┌────▼──────┐   ┌───────────┐
      │  Patroni  │   │  Patroni  │   │  Patroni  │
      │ +PostgreSQL│   │+PostgreSQL│   │+PostgreSQL│
      │  (Primary)│   │ (Replica) │   │ (Replica) │
      └───────────┘   └───────────┘   └───────────┘
```

**Characteristics:**
- RTO: 30-60 seconds (automatic failover)
- RPO: Configurable (sync/async)
- Cost: Medium to High
- Complexity: High

**Components:**
- **Patroni:** Manages PostgreSQL cluster, handles failover
- **etcd/Consul/ZooKeeper:** Distributed consensus for leader election
- **HAProxy/PgBouncer:** Connection pooling and routing

**Setup (basic Patroni config):**
```yaml
# patroni.yml
scope: postgres-cluster
name: node1

restapi:
  listen: 0.0.0.0:8008
  connect_address: node1:8008

etcd:
  hosts: etcd1:2379,etcd2:2379,etcd3:2379

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576
    postgresql:
      use_pg_rewind: true
      parameters:
        wal_level: replica
        max_wal_senders: 10
        max_replication_slots: 10

postgresql:
  listen: 0.0.0.0:5432
  connect_address: node1:5432
  data_dir: /var/lib/postgresql/14/main
  authentication:
    replication:
      username: replicator
      password: secret
    superuser:
      username: postgres
      password: secret
```

**Use case:**
- Production systems requiring HA
- Automatic failover requirement
- Acceptable complexity trade-off

### Architecture 4: Multi-Region with Cascading Replication

```
Region 1 (US-East)        Region 2 (US-West)       Region 3 (EU)
┌─────────────┐           ┌─────────────┐          ┌─────────────┐
│   Primary   │──Async───▶│  Replica 1  │──Async──▶│  Replica 2  │
│  (read/write)│           │(read-only)  │          │(read-only)  │
└─────────────┘           └─────────────┘          └─────────────┘
```

**Characteristics:**
- RTO: Regional failover (minutes)
- RPO: Seconds to minutes (async cross-region)
- Cost: High (multi-region)
- Complexity: High

**Configuration:**
Replica 1 (receives from Primary, sends to Replica 2):
```ini
# Receive from primary
primary_conninfo = 'host=primary-us-east ...'

# Send to cascading replica
wal_level = replica
max_wal_senders = 5
```

Replica 2 (receives from Replica 1):
```ini
primary_conninfo = 'host=replica1-us-west ...'
```

**Use case:**
- Global applications
- Disaster recovery across regions
- Read replicas close to users

### Architecture 5: Citus Distributed PostgreSQL

```
┌───────────────────────────────────────┐
│        Coordinator Node               │
│     (Query Planning & Routing)        │
└───────────┬───────────────────────────┘
            │
     ┌──────┴──────────┬─────────────┐
     │                 │             │
┌────▼────┐      ┌─────▼───┐   ┌────▼────┐
│ Worker 1│      │Worker 2 │   │Worker 3 │
│ (shards)│      │(shards) │   │(shards) │
└─────────┘      └─────────┘   └─────────┘
   │  │             │  │          │  │
   │  └─Replica 1   │  └─Replica │  └─Replica
```

**Characteristics:**
- Horizontal scalability
- Sharding across worker nodes
- Each worker can have replicas
- Query parallelization

**Use case:**
- Multi-tenant SaaS (shard by tenant_id)
- Time-series data (shard by time)
- Very large datasets (>1TB)

## Connection Pooling and Load Balancing

### PgBouncer (Connection Pooler)

**Why use PgBouncer:**
- Reduce connection overhead
- Handle connection spikes
- Connection reuse
- Support more clients than max_connections

**Pooling modes:**
- **Session:** One server connection per client (safest)
- **Transaction:** Server connection released after transaction (most common)
- **Statement:** Connection released after each statement (rarely used)

**Configuration (pgbouncer.ini):**
```ini
[databases]
mydb = host=localhost port=5432 dbname=mydb

[pgbouncer]
listen_addr = *
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
reserve_pool_size = 5
```

**Architecture with PgBouncer:**
```
Apps (1000 connections)
       │
       ▼
   PgBouncer (pools to 25)
       │
       ▼
   PostgreSQL (max_connections = 100)
```

### HAProxy (Load Balancer)

**Use cases:**
- Route reads to replicas
- Automatic failover routing
- Health checks

**Configuration (haproxy.cfg):**
```
frontend postgres_front
    bind *:5432
    mode tcp
    default_backend postgres_primary

backend postgres_primary
    mode tcp
    option pgsql-check user postgres
    server pg-primary primary-host:5432 check
    server pg-replica1 replica1-host:5432 check backup
    server pg-replica2 replica2-host:5432 check backup

frontend postgres_read
    bind *:5433
    mode tcp
    default_backend postgres_replicas

backend postgres_replicas
    mode tcp
    balance roundrobin
    option pgsql-check user postgres
    server pg-replica1 replica1-host:5432 check
    server pg-replica2 replica2-host:5432 check
```

**Usage:**
- Write traffic → :5432 (primary)
- Read traffic → :5433 (replicas, load balanced)

### Combined Architecture: Patroni + PgBouncer + HAProxy

```
             ┌──────────┐
             │ HAProxy  │
             │(5432,5433)│
             └─────┬────┘
                   │
       ┌───────────┼───────────┐
       │           │           │
  ┌────▼────┐ ┌───▼─────┐ ┌───▼─────┐
  │PgBouncer│ │PgBouncer│ │PgBouncer│
  └────┬────┘ └────┬────┘ └────┬────┘
       │           │           │
  ┌────▼────┐ ┌───▼─────┐ ┌───▼─────┐
  │ Patroni │ │ Patroni │ │ Patroni │
  │+Postgres│ │+Postgres│ │+Postgres│
  │(Primary)│ │(Replica)│ │(Replica)│
  └─────────┘ └─────────┘ └─────────┘
```

## Failover and Switchover

### Manual Failover

**Promote replica to primary:**
```bash
# On replica
pg_ctl promote -D /var/lib/postgresql/data

# Or with recovery signal (PG 12+)
pg_ctl promote
```

**Redirect clients:**
- Update DNS (slow, TTL dependent)
- Update HAProxy config
- Update application connection strings

**Reconfigure old primary as replica:**
```bash
# After old primary recovers
pg_rewind --target-pgdata=/var/lib/postgresql/data \
          --source-server='host=new-primary port=5432 user=postgres'

# Configure as replica
cat > /var/lib/postgresql/data/standby.signal
# Update primary_conninfo

pg_ctl start
```

### Patroni Automatic Failover

**Patroni detects failure:**
1. Primary node misses heartbeat to etcd
2. Leader lease expires (default: 30 seconds)
3. Patroni elects new leader from replicas
4. Promotes new primary
5. Reconfigures other replicas

**Configuration:**
```yaml
# patroni.yml
bootstrap:
  dcs:
    ttl: 30  # Time before failover
    maximum_lag_on_failover: 1048576  # Max lag for eligible replica (1MB)
```

**Manual switchover (planned maintenance):**
```bash
# Graceful switchover to specific node
patronictl switchover postgres-cluster --candidate node2
```

### Monitoring Failover Health

**Check replication lag:**
```sql
-- On primary
SELECT 
    client_addr,
    application_name,
    state,
    sync_state,
    replay_lag
FROM pg_stat_replication;
```

**Check Patroni cluster status:**
```bash
patronictl -c /etc/patroni/patroni.yml list postgres-cluster

# Output:
# + Cluster: postgres-cluster ---+--------+---------+----+-----------+
# | Member | Host    | Role      | State  | Lag in MB |
# +--------+---------+-----------+--------+-----------+
# | node1  | 10.0.1.1| Leader    | running|           |
# | node2  | 10.0.1.2| Replica   | running| 0         |
# | node3  | 10.0.1.3| Replica   | running| 0         |
```

## Backup Integration with HA

**Continuous archiving (recommended):**
```ini
# postgresql.conf on primary
archive_mode = on
archive_command = 'pgbackrest --stanza=main archive-push %p'

# Or use wal-g
archive_command = 'wal-g wal-push %p'
```

**Point-in-time recovery (PITR):**
```bash
# Restore base backup
pgbackrest --stanza=main restore

# Configure recovery target
cat > /var/lib/postgresql/data/recovery.conf
recovery_target_time = '2024-01-15 14:30:00'
recovery_target_action = 'promote'

# Start recovery
pg_ctl start
```

## Disaster Recovery Scenarios

### Scenario 1: Primary Failure (with replicas)

**With Patroni:**
1. Automatic failover (30-60s)
2. New primary elected
3. Applications reconnect via HAProxy

**Without Patroni:**
1. Detect failure (monitoring)
2. Promote replica manually
3. Update DNS/load balancer
4. Redirect applications
5. Investigate failure
6. Repair/replace old primary

### Scenario 2: Complete Region Failure

**With cross-region replica:**
1. Promote remote replica to primary
2. Update global load balancer
3. Create new local replicas
4. Redirect traffic

**Without replica:**
1. Restore from backup (longer RTO)
2. Apply WAL archives (PITR)
3. Promote restored instance
4. Resume operations

### Scenario 3: Data Corruption

**Point-in-time recovery:**
```bash
# Identify corruption time: 2024-01-15 14:25
# Restore to just before: 14:20

pgbackrest --stanza=main --type=time \
  --target="2024-01-15 14:20:00" restore

# Start in recovery mode
# Verify data integrity
# Promote when satisfied
```

### Scenario 4: Split-Brain Prevention

**Patroni with quorum:**
- Requires majority of etcd nodes
- Old primary cannot accept writes without quorum
- Fencing prevents dual-primary

**Manual setup:**
- STONITH (Shoot The Other Node In The Head)
- Network-based fencing
- Application-level checks

## Best Practices

1. **Use replication slots** - Prevents WAL deletion before replica consumption
2. **Monitor replication lag** - Alert on lag > 30 seconds
3. **Test failover regularly** - Quarterly drills
4. **Automate with Patroni** - For production HA requirements
5. **Use synchronous for zero data loss** - Accept latency trade-off
6. **Connection pooling** - PgBouncer for scalability
7. **Document runbooks** - Failover procedures
8. **Monitor pg_stat_replication** - Continuous health checks
9. **Cross-region for DR** - Geographic redundancy
10. **Backup != HA** - Need both backup AND replication

## Troubleshooting

**Replication lag increasing:**
- Check network bandwidth
- Verify replica I/O capacity
- Check for long-running transactions on primary
- Increase wal_sender_timeout if network is slow

**Replica too far behind:**
```sql
-- On primary
SELECT 
    slot_name, 
    pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) AS bytes_behind
FROM pg_replication_slots;

-- If too far behind, re-clone with pg_basebackup
```

**Patroni failover not working:**
- Check etcd cluster health
- Verify network connectivity between nodes
- Check Patroni logs for errors
- Ensure majority quorum (3 node minimum)

**Synchronous replica blocking commits:**
```sql
-- Temporarily switch to async
SET synchronous_commit = local;

-- Or change synchronous_standby_names
ALTER SYSTEM SET synchronous_standby_names = '';
SELECT pg_reload_conf();
```

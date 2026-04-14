# Cloud Provider PostgreSQL Specifics

Comprehensive guide for working with managed PostgreSQL on AWS RDS, GCP Cloud SQL, and Azure Database for PostgreSQL.

## AWS RDS for PostgreSQL

### Key Characteristics

**Managed features:**
- Automated backups with point-in-time recovery (PITR)
- Multi-AZ deployments for HA
- Read replicas for scaling reads
- Automated minor version upgrades
- Performance Insights for query monitoring

**Limitations:**
- No superuser access (use `rds_superuser` role)
- Cannot install custom PostgreSQL extensions (limited to AWS-approved list)
- Cannot modify some configuration parameters
- File system access restricted
- Cannot use certain extensions requiring superuser

### Configuration Management

**Parameter Groups:**
- Default parameter group is read-only
- Create custom parameter group for modifications
- Changes marked as "Static" require reboot
- Changes marked as "Dynamic" apply immediately or at next connection

```sql
-- Check current parameter group
SELECT name, setting FROM pg_settings WHERE name = 'rds.extensions';

-- Check pending parameter changes
-- (Use RDS Console or AWS CLI)
```

**Common RDS-specific parameters:**
```ini
# Enable pg_stat_statements (requires reboot)
shared_preload_libraries = 'pg_stat_statements'

# RDS-specific logging
log_statement = 'ddl'  # or 'all' for debugging
log_min_duration_statement = 1000

# Connection pooling with RDS Proxy
rds.force_ssl = 1  # Enforce SSL connections
```

### Instance Classes and max_connections

**Formula:**
```
max_connections = DBInstanceClassMemory / 9531392
```

**Examples:**
- db.t3.micro (1 GB RAM): ~87 connections
- db.t3.medium (4 GB RAM): ~437 connections
- db.r5.large (16 GB RAM): ~1749 connections
- db.r5.xlarge (32 GB RAM): ~3498 connections

**Override formula:**
- Can set max_connections lower (but not higher than formula allows)
- Use RDS Proxy for connection pooling (recommended)

### Storage Types

**GP2 (General Purpose SSD):**
- Baseline: 3 IOPS per GB (min 100 IOPS)
- Burst: Up to 3000 IOPS (for volumes < 1TB)
- Use case: Most workloads

**GP3 (General Purpose SSD v3):**
- Baseline: 3000 IOPS (regardless of size)
- Configurable: Up to 16,000 IOPS and 1000 MB/s throughput
- Cost: More cost-effective than GP2
- Use case: Production workloads (preferred)

**IOPS (Provisioned IOPS SSD):**
- Dedicated IOPS: Up to 80,000 IOPS (io2) or 64,000 (io1)
- Latency: Sub-millisecond
- Use case: High-performance OLTP

**Magnetic (deprecated):**
- Don't use for new instances

**Storage autoscaling:**
```
Enable storage autoscaling
Maximum storage threshold: Set based on growth projections
```

### Backup and Recovery

**Automated Backups:**
- Retention: 1-35 days (35 recommended for production)
- Backup window: Specify to minimize impact
- Point-in-time recovery: To any second within retention
- Stored in S3 (no additional charge for backup storage up to DB size)

**Manual Snapshots:**
- Persist beyond automated backup retention
- Useful before major changes
- Can share across accounts

**Restore process:**
```bash
# Restore creates NEW instance (cannot restore in-place)
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier mydb \
  --target-db-instance-identifier mydb-restored \
  --restore-time 2024-01-15T10:30:00Z
```

### Read Replicas

**Characteristics:**
- Asynchronous replication
- Up to 15 read replicas per primary (5 in same region + 10 cross-region)
- Can promote to standalone instance
- Supports cross-region replication

**Replication lag monitoring:**
```sql
-- On replica, check lag
SELECT 
  CASE 
    WHEN pg_last_wal_receive_lsn() = pg_last_wal_replay_lsn() THEN 0
    ELSE EXTRACT(EPOCH FROM now() - pg_last_xact_replay_timestamp())
  END AS replication_lag_seconds;
```

**Creating read replica:**
```bash
aws rds create-db-instance-read-replica \
  --db-instance-identifier mydb-replica \
  --source-db-instance-identifier mydb \
  --db-instance-class db.r5.large
```

### Multi-AZ Deployments

**Characteristics:**
- Synchronous replication to standby
- Automatic failover (60-120 seconds)
- Standby is NOT readable (use read replicas for that)
- Same region, different AZ

**Failover triggers:**
- Primary instance failure
- AZ outage
- Network connectivity loss
- Storage failure
- Manual failover (for testing)

**Initiate manual failover:**
```bash
aws rds reboot-db-instance \
  --db-instance-identifier mydb \
  --force-failover
```

### RDS Proxy (Connection Pooling)

**Benefits:**
- Connection pooling (reduces connection overhead)
- Graceful failover (maintains connections during failover)
- IAM authentication support
- Lambda-friendly (handles serverless bursts)

**Typical configuration:**
```
Max connections percentage: 100
Connection borrow timeout: 120 seconds
Idle client timeout: 1800 seconds
```

**Connection string:**
```
postgresql://proxy-endpoint:5432/dbname
# Instead of instance endpoint
```

### Performance Insights

**Key metrics:**
- Database load (average active sessions)
- Top SQL statements by load
- Wait events (I/O, CPU, lock, etc.)

**Access:**
- RDS Console → Performance Insights
- API: `describe-db-instances` → PerformanceInsightsEnabled
- CloudWatch metrics integration

### Extensions

**Popular available extensions:**
- pg_stat_statements (query monitoring)
- postgis (geospatial)
- pg_trgm (fuzzy matching)
- uuid-ossp (UUID generation)
- hstore (key-value store)
- pgcrypto (encryption)

**NOT available:**
- File-based extensions (file_fdw)
- Extensions requiring superuser (some dblink features)
- Custom compiled extensions

**Enable extension:**
```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

### Monitoring and Alerting

**Essential CloudWatch metrics:**
- CPUUtilization
- DatabaseConnections
- FreeableMemory
- ReadIOPS / WriteIOPS
- ReadLatency / WriteLatency
- FreeStorageSpace

**CloudWatch Logs:**
- Enable postgresql.log export to CloudWatch
- Configure log retention

**Sample alert:**
```
Metric: DatabaseConnections
Threshold: > 80% of max_connections
Period: 5 minutes
Action: SNS notification
```

### Cost Optimization

**Strategies:**
- Right-size instance class (use Performance Insights)
- Use GP3 instead of GP2 for cost savings
- Delete unnecessary snapshots
- Use Reserved Instances (1-year or 3-year commitment)
- Enable storage autoscaling to avoid over-provisioning
- Use RDS Proxy instead of increasing instance size for connections

### Security Best Practices

**Network:**
- Use VPC (not EC2-Classic)
- Private subnets for databases
- Security groups: Allow only necessary sources
- No public accessibility for production

**Encryption:**
- Enable encryption at rest (cannot enable after creation)
- Use SSL/TLS for connections: `sslmode=require`
- Rotate passwords regularly

**IAM Authentication:**
```sql
-- Create IAM-authenticated user
CREATE USER iamuser;
GRANT rds_iam TO iamuser;
```

**Audit logging:**
```ini
# Parameter group
log_connections = 1
log_disconnections = 1
log_statement = 'ddl'
```

---

## GCP Cloud SQL for PostgreSQL

### Key Characteristics

**Managed features:**
- Automated backups with point-in-time recovery
- High availability (HA) configuration
- Read replicas
- Automatic storage increase
- Integration with Google Cloud services

**Limitations:**
- No superuser access (use `cloudsqlsuperuser` role)
- Limited extension support (Google-approved list)
- Some configuration flags restricted
- Regional availability constraints

### Configuration Management

**Flags (Configuration):**
- Use Cloud SQL flags (equivalent to postgresql.conf)
- Changes may require restart (check documentation)
- Some flags not configurable

```bash
# Set flags via gcloud
gcloud sql instances patch INSTANCE_NAME \
  --database-flags max_connections=200,shared_buffers=2GB
```

**Common Cloud SQL flags:**
```ini
# Enable pg_stat_statements
cloudsql.enable_pg_stat_statements = on

# Logging
log_min_duration_statement = 1000
log_connections = on
log_disconnections = on

# Memory
shared_buffers = 2GB
work_mem = 64MB
```

### Machine Types and Scaling

**Machine types:**
- Shared-core: db-f1-micro, db-g1-small (development only)
- Standard: db-n1-standard-{1,2,4,8,16,32,64,96}
- High-memory: db-n1-highmem-{2,4,8,16,32,64,96}
- Custom: Configure vCPUs and memory

**max_connections:**
- Default: Automatically calculated based on memory
- Can be overridden with flag
- Maximum: 4000 (for largest instances)

**Storage:**
- SSD (default) or HDD (not recommended)
- Auto-increase storage enabled by default
- Max size: 64 TB

### High Availability (HA)

**Characteristics:**
- Synchronous replication to standby
- Same region, different zone
- Automatic failover (60-120 seconds)
- Standby is NOT readable
- Costs ~2x single instance

**Enable HA:**
```bash
gcloud sql instances patch INSTANCE_NAME --availability-type=REGIONAL
```

**Failover testing:**
```bash
gcloud sql instances failover INSTANCE_NAME
```

### Read Replicas

**Types:**
1. **Read replica:** Asynchronous, same region
2. **Cross-region replica:** Asynchronous, different region
3. **External replica:** On-premises or other cloud

**Creating replica:**
```bash
gcloud sql instances create REPLICA_NAME \
  --master-instance-name=MASTER_NAME \
  --tier=db-n1-standard-2
```

**Monitoring replication lag:**
```sql
SELECT 
  EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) AS lag_seconds;
```

### Backup and Recovery

**Automated backups:**
- On-demand or scheduled
- Retention: 1-365 days (7 default)
- Point-in-time recovery (PITR)
- Stored in multi-region Google Cloud Storage

**Binary logging:**
- Required for PITR
- Enable: `cloudsql.enable_pglogical = on`

**Restore process:**
```bash
# Restore to new instance
gcloud sql backups restore BACKUP_ID \
  --backup-instance=SOURCE_INSTANCE \
  --backup-instance=TARGET_INSTANCE

# Point-in-time recovery
gcloud sql instances clone SOURCE_INSTANCE TARGET_INSTANCE \
  --point-in-time='2024-01-15T10:30:00.000Z'
```

### Connection Management

**Connection options:**
1. **Public IP:** Direct internet connection (not recommended for production)
2. **Private IP:** VPC peering (recommended)
3. **Cloud SQL Proxy:** Secure tunnel without SSL config

**Cloud SQL Proxy (recommended):**
```bash
# Download and run proxy
./cloud_sql_proxy -instances=PROJECT:REGION:INSTANCE=tcp:5432

# Connect via proxy
psql "host=127.0.0.1 port=5432 dbname=mydb user=postgres"
```

**Private IP setup:**
```bash
# Enable private IP
gcloud sql instances patch INSTANCE_NAME \
  --network=projects/PROJECT_ID/global/networks/NETWORK_NAME \
  --no-assign-ip
```

**Connection pooling:**
- Use PgBouncer or application-level pooling
- Cloud SQL does not provide managed connection pooling (unlike RDS Proxy)

### Monitoring

**Cloud Monitoring (Stackdriver) metrics:**
- `cloudsql.googleapis.com/database/up` (instance health)
- `cloudsql.googleapis.com/database/cpu/utilization`
- `cloudsql.googleapis.com/database/memory/utilization`
- `cloudsql.googleapis.com/database/disk/bytes_used`
- `cloudsql.googleapis.com/database/postgresql/num_backends`

**Query Insights:**
- Identify slow queries
- Similar to RDS Performance Insights
- Enable via Console → Query Insights

**Logging:**
```bash
# Enable postgresql.log export to Cloud Logging
gcloud sql instances patch INSTANCE_NAME \
  --database-flags cloudsql.enable_pgaudit=on
```

### Extensions

**Popular available extensions:**
- pg_stat_statements
- postgis
- pg_trgm
- uuid-ossp
- hstore
- pgcrypto
- pg_partman

**Enable extension:**
```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
```

### Maintenance Windows

**Maintenance types:**
- OS updates
- Database minor version updates
- Hardware maintenance

**Configure window:**
```bash
gcloud sql instances patch INSTANCE_NAME \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=2
```

### Cost Optimization

**Strategies:**
- Right-size machine type
- Use committed use discounts (1 or 3 years)
- Stop instances when not needed (dev/test)
- Delete old backups
- Use SSD storage efficiently
- Monitor with recommendations (GCP Console)

### Security Best Practices

**Network:**
- Use private IP (VPC peering)
- Cloud SQL Proxy for secure connections
- Firewall rules: Restrict to known IPs

**Encryption:**
- Encryption at rest: Default with Google-managed keys
- Customer-managed keys (CMEK): Use Cloud KMS
- SSL/TLS: `sslmode=require`

**IAM Integration:**
- Cloud SQL IAM database authentication (PostgreSQL 14+)
- Fine-grained access control

**Audit logging:**
- Enable Cloud Audit Logs
- pgAudit extension for query-level auditing

---

## Azure Database for PostgreSQL

### Deployment Options

**Flexible Server (Recommended):**
- Most feature-rich
- Zone-redundant HA
- Better price/performance
- More configuration options

**Single Server (Legacy):**
- Being retired (migrations required)
- Limited features
- Do NOT use for new deployments

**Note:** This guide focuses on Flexible Server.

### Key Characteristics

**Managed features:**
- Automated backups with PITR
- Zone-redundant HA
- Read replicas
- Automated patching
- Integration with Azure services

**Limitations:**
- No superuser access (use `azure_pg_admin` role)
- Limited extension support
- Some configuration parameters restricted

### Configuration Management

**Server Parameters:**
- Modify via Azure Portal, CLI, or ARM templates
- Static parameters require restart
- Dynamic parameters apply immediately

```bash
# Set parameter via Azure CLI
az postgres flexible-server parameter set \
  --resource-group myResourceGroup \
  --server-name myserver \
  --name max_connections \
  --value 200
```

**Common parameters:**
```ini
# Memory
shared_buffers = 2GB
work_mem = 64MB
effective_cache_size = 8GB

# Logging
log_min_duration_statement = 1000
log_connections = on
log_checkpoints = on

# WAL
wal_level = replica
```

### Compute and Storage

**Compute tiers:**
- **Burstable:** B1ms, B2s (dev/test)
- **General Purpose:** D-series (balanced)
- **Memory Optimized:** E-series (memory-intensive)

**Storage:**
- Size: 32 GB - 16 TB
- IOPS: Scale with storage size
- Auto-grow: Enable to prevent storage full

**max_connections:**
- Calculated based on SKU
- General Purpose 2 vCore: ~859 connections
- General Purpose 64 vCore: ~5000 connections

### High Availability (Zone-Redundant)

**Characteristics:**
- Synchronous replication
- Automatic failover (60-120 seconds)
- Standby in different availability zone
- ~2x cost

**Enable HA:**
```bash
az postgres flexible-server update \
  --resource-group myResourceGroup \
  --name myserver \
  --high-availability ZoneRedundant \
  --standby-availability-zone 2
```

**Planned failover:**
```bash
az postgres flexible-server restart \
  --resource-group myResourceGroup \
  --name myserver \
  --failover Forced
```

### Read Replicas

**Characteristics:**
- Asynchronous replication
- Up to 5 replicas per primary
- Cross-region support
- Can promote to standalone server

**Create replica:**
```bash
az postgres flexible-server replica create \
  --replica-name myReplica \
  --resource-group myResourceGroup \
  --source-server myserver
```

**Monitor replication lag:**
```sql
SELECT 
  EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) AS lag_seconds;
```

### Backup and Recovery

**Automated backups:**
- Retention: 7-35 days
- Geo-redundant backup: Optional
- Point-in-time restore (PITR)

**Restore process:**
```bash
# Restore to point in time (creates new server)
az postgres flexible-server restore \
  --resource-group myResourceGroup \
  --name myRestoredServer \
  --source-server myserver \
  --restore-time "2024-01-15T10:30:00Z"
```

**Geo-restore (if geo-redundant enabled):**
```bash
az postgres flexible-server geo-restore \
  --resource-group myResourceGroup \
  --name myGeoRestoredServer \
  --source-server myserver \
  --location eastus2
```

### Networking

**Private access (VNet integration - Recommended):**
```bash
az postgres flexible-server create \
  --resource-group myResourceGroup \
  --name myserver \
  --vnet myVnet \
  --subnet mySubnet \
  --private-dns-zone myPrivateDnsZone
```

**Public access:**
- Firewall rules control access
- Not recommended for production

**Connection string:**
```
postgresql://username@myserver:password@myserver.postgres.database.azure.com:5432/dbname?sslmode=require
```

### Monitoring

**Azure Monitor metrics:**
- CPU percent
- Memory percent
- Storage percent
- Active connections
- IOPS
- Network in/out

**Query Performance Insight:**
- Identify slow queries
- Resource consumption by query
- Enable via Azure Portal

**Diagnostic logs:**
- PostgreSQL logs
- Query Store logs
- Export to Log Analytics or Storage

### Extensions

**Popular available extensions:**
- pg_stat_statements
- postgis
- pg_trgm
- uuid-ossp
- pgcrypto
- pg_partman
- pgaudit

**Enable extension:**
```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
```

**Allow-list extensions:**
```bash
az postgres flexible-server parameter set \
  --resource-group myResourceGroup \
  --server-name myserver \
  --name azure.extensions \
  --value pg_stat_statements,pg_trgm
```

### Maintenance Windows

**Configure maintenance:**
```bash
az postgres flexible-server update \
  --resource-group myResourceGroup \
  --name myserver \
  --maintenance-window day=0 hour=2  # Sunday 2 AM
```

### Cost Optimization

**Strategies:**
- Right-size compute tier
- Use reserved capacity (1 or 3 years)
- Stop server when not in use (dev/test)
- Optimize storage size
- Disable geo-redundant backup if not required

### Security Best Practices

**Network:**
- Use private access (VNet integration)
- NSG rules for additional control
- Firewall rules for public access (if required)

**Encryption:**
- Encryption at rest: Default (Microsoft-managed keys)
- Customer-managed keys: Use Azure Key Vault
- SSL/TLS: Enforced by default

**Azure AD Authentication:**
```bash
# Enable Azure AD admin
az postgres flexible-server ad-admin create \
  --resource-group myResourceGroup \
  --server-name myserver \
  --display-name myAzureADUser \
  --object-id <object-id>
```

**Audit logging:**
- Enable pgaudit extension
- Configure audit logs in server parameters

---

## Cloud Provider Comparison Matrix

| Feature | AWS RDS | GCP Cloud SQL | Azure Flexible Server |
|---------|---------|---------------|----------------------|
| **Max Instance Size** | 32 TB RAM, 128 vCPU | 624 GB RAM, 96 vCPU | 672 GB RAM, 64 vCPU |
| **Max Storage** | 64 TB | 64 TB | 16 TB |
| **Max Connections** | ~50,000 | 4,000 | ~5,000 |
| **Read Replicas** | 15 (5 same-region) | Unlimited | 5 |
| **Cross-Region Replica** | Yes | Yes | Yes |
| **Connection Pooling** | RDS Proxy | Manual (PgBouncer) | Manual (PgBouncer) |
| **Backup Retention** | 35 days | 365 days | 35 days |
| **HA Failover Time** | 60-120s | 60-120s | 60-120s |
| **Private Networking** | VPC | VPC peering | VNet integration |
| **IAM Auth** | Yes | Yes (PG 14+) | Azure AD |
| **Encryption at Rest** | Yes (KMS) | Yes (default) | Yes (default) |
| **Encryption in Transit** | SSL/TLS | SSL/TLS | SSL/TLS (enforced) |
| **Extension Support** | ~80 extensions | ~60 extensions | ~70 extensions |
| **Query Insights** | Performance Insights | Query Insights | Query Performance Insight |

## Cloud Migration Considerations

**From on-premises to cloud:**
1. **Compatibility check:** Ensure PostgreSQL version parity
2. **Extension availability:** Verify all extensions supported
3. **Configuration review:** Some parameters unavailable in managed services
4. **Data migration:** Use pg_dump/restore or AWS DMS / GCP Database Migration / Azure Database Migration
5. **Connection pooling:** Plan for RDS Proxy or separate PgBouncer
6. **Monitoring:** Transition to cloud-native tools

**Cross-cloud migration:**
- Logical replication (for minimal downtime)
- pg_dump/pg_restore (for full migration)
- Third-party tools (e.g., AWS DMS works for cross-cloud)

**Testing checklist:**
- Connection pooling performance
- Replication lag under load
- Failover time
- Backup and restore procedures
- Query performance (EXPLAIN plans may differ)
- Extension functionality

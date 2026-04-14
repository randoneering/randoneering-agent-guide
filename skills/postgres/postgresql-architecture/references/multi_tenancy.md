# Multi-Tenancy Strategies for PostgreSQL

Comprehensive guide to implementing multi-tenant architectures in PostgreSQL, including isolation strategies, data modeling, and scalability patterns.

## Multi-Tenancy Models

### Model 1: Shared Database, Shared Schema

**Architecture:**
All tenants share the same database and tables. Tenant isolation via `tenant_id` column.

```
Database
├── Table: users
│   ├── id, tenant_id, username, email
├── Table: orders
│   ├── id, tenant_id, customer_id, total
```

**Implementation:**
```sql
CREATE TABLE tenants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    UNIQUE (tenant_id, username),
    UNIQUE (tenant_id, email)
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    user_id INTEGER NOT NULL,
    total DECIMAL(10,2),
    FOREIGN KEY (tenant_id, user_id) REFERENCES users(tenant_id, id)
);

-- Essential indexes
CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_orders_tenant ON orders(tenant_id);
```

**Row-Level Security (RLS):**
```sql
-- Enable RLS on tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Create policy
CREATE POLICY tenant_isolation_users ON users
    USING (tenant_id = current_setting('app.current_tenant')::integer);

CREATE POLICY tenant_isolation_orders ON orders
    USING (tenant_id = current_setting('app.current_tenant')::integer);

-- Application sets tenant context
SET app.current_tenant = '123';

-- Now queries automatically filtered
SELECT * FROM users;  -- Only sees tenant 123's users
```

**Pros:**
- ✅ Simple to manage
- ✅ Cost-effective
- ✅ Easy to add new tenants
- ✅ Efficient resource usage
- ✅ Cross-tenant queries possible (analytics)

**Cons:**
- ❌ No strong isolation (bug could expose data)
- ❌ Noisy neighbor problem (one tenant can impact others)
- ❌ All tenants must share same schema version
- ❌ Difficult to move tenant to different database

**Best for:**
- SaaS with many small tenants
- B2B with similar requirements
- Budget-conscious projects
- Tenants with similar data volumes

### Model 2: Shared Database, Separate Schemas

**Architecture:**
All tenants share database but have dedicated schemas.

```
Database
├── Schema: tenant_123
│   ├── users
│   ├── orders
├── Schema: tenant_456
│   ├── users
│   ├── orders
```

**Implementation:**
```sql
-- Create schema per tenant
CREATE SCHEMA tenant_123;
CREATE SCHEMA tenant_456;

-- Create tables in each schema
CREATE TABLE tenant_123.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL
);

CREATE TABLE tenant_123.orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES tenant_123.users(id),
    total DECIMAL(10,2)
);

-- Repeat for tenant_456...

-- Set search path per session
SET search_path TO tenant_123, public;
SELECT * FROM users;  -- Queries tenant_123.users
```

**Automated schema creation:**
```sql
CREATE OR REPLACE FUNCTION create_tenant_schema(tenant_id INTEGER)
RETURNS VOID AS $$
DECLARE
    schema_name TEXT := 'tenant_' || tenant_id;
BEGIN
    -- Create schema
    EXECUTE format('CREATE SCHEMA %I', schema_name);
    
    -- Create tables
    EXECUTE format('
        CREATE TABLE %I.users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) NOT NULL,
            email VARCHAR(100) NOT NULL
        )', schema_name);
    
    EXECUTE format('
        CREATE TABLE %I.orders (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES %I.users(id),
            total DECIMAL(10,2)
        )', schema_name, schema_name);
    
    -- Create indexes
    EXECUTE format('CREATE INDEX idx_users_email ON %I.users(email)', schema_name);
END;
$$ LANGUAGE plpgsql;

-- Use function
SELECT create_tenant_schema(123);
```

**Pros:**
- ✅ Better isolation than shared schema
- ✅ Can customize schema per tenant
- ✅ Easier to backup single tenant
- ✅ Moderate resource usage

**Cons:**
- ❌ Schema migration complexity (must update all schemas)
- ❌ More complex to manage (hundreds of schemas)
- ❌ Cross-tenant queries harder
- ❌ PostgreSQL limits (thousands of schemas possible but not ideal)

**Best for:**
- Medium number of tenants (10-100)
- Tenants needing schema customization
- Compliance requirements for data separation
- Tenants with significantly different data volumes

### Model 3: Separate Databases

**Architecture:**
Each tenant gets a dedicated database.

```
Server
├── Database: tenant_123
│   ├── users
│   ├── orders
├── Database: tenant_456
│   ├── users
│   ├── orders
```

**Implementation:**
```sql
-- Create database per tenant
CREATE DATABASE tenant_123;
CREATE DATABASE tenant_456;

-- Connect to specific database
\c tenant_123

-- Create tables (same schema across all tenant DBs)
CREATE TABLE users (...);
CREATE TABLE orders (...);
```

**Connection routing:**
```python
# Application code
def get_tenant_connection(tenant_id):
    return psycopg2.connect(
        host='localhost',
        database=f'tenant_{tenant_id}',
        user='app_user',
        password='secret'
    )

# Use tenant-specific connection
conn = get_tenant_connection(123)
cursor = conn.cursor()
cursor.execute("SELECT * FROM users")
```

**Pros:**
- ✅ Strong isolation
- ✅ Easy to backup/restore individual tenants
- ✅ Easy to scale (move tenant to different server)
- ✅ Performance isolation
- ✅ Can use different PostgreSQL versions per tenant

**Cons:**
- ❌ Higher resource overhead
- ❌ Complex connection management
- ❌ Schema migrations across all databases
- ❌ Cross-tenant queries very difficult

**Best for:**
- Small number of large tenants (<50)
- Enterprise customers
- Strong isolation requirements
- Tenants with very different SLAs
- Regulated industries (healthcare, finance)

### Model 4: Hybrid Approach

**Small tenants:** Shared schema  
**Large tenants:** Dedicated database

```sql
-- Routing table
CREATE TABLE tenant_routing (
    tenant_id INTEGER PRIMARY KEY,
    isolation_level VARCHAR(20), -- 'shared' or 'dedicated'
    database_name VARCHAR(100),  -- NULL for shared, DB name for dedicated
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Small tenants
INSERT INTO tenant_routing (tenant_id, isolation_level) VALUES
    (1, 'shared'),
    (2, 'shared');

-- Large tenants
INSERT INTO tenant_routing (tenant_id, isolation_level, database_name) VALUES
    (100, 'dedicated', 'tenant_100'),
    (200, 'dedicated', 'tenant_200');
```

**Application logic:**
```python
def get_connection(tenant_id):
    routing = query("SELECT * FROM tenant_routing WHERE tenant_id = %s", tenant_id)
    
    if routing['isolation_level'] == 'shared':
        conn = get_shared_connection()
        # Set RLS context
        conn.execute(f"SET app.current_tenant = {tenant_id}")
        return conn
    else:
        return get_tenant_connection(routing['database_name'])
```

## Partitioning for Multi-Tenancy

### List Partitioning by Tenant

```sql
CREATE TABLE orders (
    id BIGSERIAL,
    tenant_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    total DECIMAL(10,2),
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (id, tenant_id)
) PARTITION BY LIST (tenant_id);

-- Major tenants get dedicated partitions
CREATE TABLE orders_tenant_100 PARTITION OF orders
    FOR VALUES IN (100);

CREATE TABLE orders_tenant_200 PARTITION OF orders
    FOR VALUES IN (200);

-- Small tenants grouped together
CREATE TABLE orders_tenant_small PARTITION OF orders
    FOR VALUES IN (1, 2, 3, 4, 5);

-- Default partition
CREATE TABLE orders_tenant_default PARTITION OF orders DEFAULT;
```

**Benefits:**
- Partition pruning for tenant-specific queries
- Easy to drop tenant data (detach partition)
- Can have different index strategies per tenant
- Large tenant performance isolated

### Range + List Multi-Level Partitioning

```sql
-- Partition by date, then by tenant
CREATE TABLE events (
    id BIGSERIAL,
    tenant_id INTEGER NOT NULL,
    event_time TIMESTAMP NOT NULL,
    data JSONB,
    PRIMARY KEY (id, tenant_id, event_time)
) PARTITION BY RANGE (event_time);

-- Monthly partition
CREATE TABLE events_2024_01 PARTITION OF events
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01')
    PARTITION BY LIST (tenant_id);

-- Sub-partitions by tenant
CREATE TABLE events_2024_01_tenant_100 PARTITION OF events_2024_01
    FOR VALUES IN (100);

CREATE TABLE events_2024_01_tenant_small PARTITION OF events_2024_01
    FOR VALUES IN (1, 2, 3, 4, 5);
```

## Row-Level Security (RLS) Deep Dive

### Basic RLS Setup

```sql
-- Enable RLS
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Create policy
CREATE POLICY tenant_isolation ON orders
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant')::integer)
    WITH CHECK (tenant_id = current_setting('app.current_tenant')::integer);

-- USING: Determines which rows are visible
-- WITH CHECK: Determines which rows can be inserted/updated
```

### Advanced RLS Patterns

**Admin bypass:**
```sql
CREATE POLICY admin_all_access ON orders
    FOR ALL
    TO admin_role
    USING (true)
    WITH CHECK (true);

-- Admins see everything
```

**Read vs Write policies:**
```sql
-- Read policy: Can see own tenant + tenant 1 (shared resources)
CREATE POLICY tenant_read ON orders
    FOR SELECT
    USING (
        tenant_id = current_setting('app.current_tenant')::integer
        OR tenant_id = 1  -- Shared resources
    );

-- Write policy: Can only write to own tenant
CREATE POLICY tenant_write ON orders
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.current_tenant')::integer);
```

**Time-based policies:**
```sql
CREATE POLICY recent_data ON orders
    FOR SELECT
    USING (
        tenant_id = current_setting('app.current_tenant')::integer
        AND created_at > NOW() - INTERVAL '90 days'
    );
```

**Performance considerations:**
- RLS adds overhead (additional WHERE clause)
- Ensure tenant_id column is indexed
- Policies run for every row accessed
- Use EXPLAIN to verify execution plan

## Tenant Onboarding and Offboarding

### Onboarding Automation

```sql
CREATE OR REPLACE FUNCTION onboard_tenant(
    p_tenant_name VARCHAR(100),
    p_admin_email VARCHAR(100)
) RETURNS INTEGER AS $$
DECLARE
    v_tenant_id INTEGER;
BEGIN
    -- Create tenant record
    INSERT INTO tenants (name, created_at)
    VALUES (p_tenant_name, CURRENT_TIMESTAMP)
    RETURNING id INTO v_tenant_id;
    
    -- Create admin user
    INSERT INTO users (tenant_id, email, role)
    VALUES (v_tenant_id, p_admin_email, 'admin');
    
    -- Create default settings
    INSERT INTO tenant_settings (tenant_id, key, value)
    VALUES 
        (v_tenant_id, 'theme', 'default'),
        (v_tenant_id, 'language', 'en');
    
    -- For separate schema model: create schema
    -- EXECUTE format('CREATE SCHEMA tenant_%s', v_tenant_id);
    
    -- For separate DB model: create database
    -- EXECUTE format('CREATE DATABASE tenant_%s', v_tenant_id);
    
    RETURN v_tenant_id;
END;
$$ LANGUAGE plpgsql;

-- Use
SELECT onboard_tenant('Acme Corp', 'admin@acme.com');
```

### Offboarding / Data Deletion

```sql
CREATE OR REPLACE FUNCTION offboard_tenant(p_tenant_id INTEGER)
RETURNS VOID AS $$
BEGIN
    -- Soft delete approach
    UPDATE tenants SET deleted_at = CURRENT_TIMESTAMP WHERE id = p_tenant_id;
    
    -- OR hard delete (cascading if FKs set up correctly)
    -- DELETE FROM tenants WHERE id = p_tenant_id;
    
    -- For partitioned model: detach and archive
    -- EXECUTE format('ALTER TABLE orders DETACH PARTITION orders_tenant_%s', p_tenant_id);
    -- EXECUTE format('ALTER TABLE orders_tenant_%s SET SCHEMA archive', p_tenant_id);
    
    -- For separate schema:
    -- EXECUTE format('DROP SCHEMA tenant_%s CASCADE', p_tenant_id);
    
    -- For separate DB:
    -- EXECUTE format('DROP DATABASE tenant_%s', p_tenant_id);
END;
$$ LANGUAGE plpgsql;
```

## Scaling Strategies

### Horizontal Scaling (Sharding)

**Tenant-based sharding:**
```
Shard 1 (tenants 1-1000)
Shard 2 (tenants 1001-2000)
Shard 3 (tenants 2001-3000)
```

**Routing logic:**
```python
def get_shard_connection(tenant_id):
    shard_num = (tenant_id - 1) // 1000 + 1
    return connect_to_shard(shard_num)

# Use Citus for distributed PostgreSQL
# Or implement custom sharding logic
```

**Using Citus (distributed PostgreSQL):**
```sql
-- Create distributed table
SELECT create_distributed_table('orders', 'tenant_id');

-- Automatically shards data across worker nodes
-- Queries automatically routed to correct shards
```

### Vertical Scaling (Premium Tiers)

```sql
-- Tenant tiers
CREATE TABLE tenant_tiers (
    tenant_id INTEGER PRIMARY KEY REFERENCES tenants(id),
    tier VARCHAR(20) NOT NULL,  -- 'free', 'basic', 'premium'
    database_pool VARCHAR(50),  -- 'shared', 'dedicated_small', 'dedicated_large'
    max_users INTEGER,
    max_storage_gb INTEGER
);

-- Route based on tier
-- Free/Basic: Shared database
-- Premium: Dedicated database
```

## Monitoring and Management

### Tenant Usage Tracking

```sql
CREATE TABLE tenant_usage (
    tenant_id INTEGER,
    metric_date DATE,
    api_calls INTEGER,
    storage_bytes BIGINT,
    active_users INTEGER,
    PRIMARY KEY (tenant_id, metric_date)
);

-- Daily aggregation job
INSERT INTO tenant_usage (tenant_id, metric_date, api_calls, storage_bytes, active_users)
SELECT 
    tenant_id,
    CURRENT_DATE,
    (SELECT COUNT(*) FROM api_logs WHERE tenant_id = t.id AND DATE(created_at) = CURRENT_DATE),
    (SELECT SUM(pg_column_size(data)) FROM tenant_data WHERE tenant_id = t.id),
    (SELECT COUNT(DISTINCT user_id) FROM user_activity WHERE tenant_id = t.id AND DATE(created_at) = CURRENT_DATE)
FROM tenants t;
```

### Per-Tenant Performance Monitoring

```sql
-- Slow queries by tenant
SELECT 
    o.tenant_id,
    pss.query,
    pss.mean_exec_time,
    pss.calls
FROM pg_stat_statements pss
JOIN orders o ON true  -- Correlate with tenant_id if possible
WHERE pss.mean_exec_time > 1000  -- > 1 second
ORDER BY pss.mean_exec_time DESC;

-- Table sizes by tenant (partitioned approach)
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE tablename LIKE 'orders_tenant_%'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Schema Migration Management

**For shared schema model:**
```sql
-- Single migration affects all tenants
ALTER TABLE orders ADD COLUMN shipping_address TEXT;
```

**For separate schema model:**
```sql
-- Migrate all tenant schemas
DO $$
DECLARE
    schema_rec RECORD;
BEGIN
    FOR schema_rec IN 
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name LIKE 'tenant_%'
    LOOP
        EXECUTE format('ALTER TABLE %I.orders ADD COLUMN shipping_address TEXT', 
                      schema_rec.schema_name);
    END LOOP;
END $$;
```

**For separate database model:**
```bash
# Script to migrate all tenant databases
for db in $(psql -t -c "SELECT datname FROM pg_database WHERE datname LIKE 'tenant_%'")
do
    psql -d $db -c "ALTER TABLE orders ADD COLUMN shipping_address TEXT"
done
```

## Security Best Practices

### Data Isolation Verification

```sql
-- Test RLS policies
SET app.current_tenant = '123';
SELECT COUNT(*) FROM orders;  -- Should only see tenant 123

SET app.current_tenant = '456';
SELECT COUNT(*) FROM orders;  -- Should only see tenant 456

-- Audit: Find rows without tenant_id
SELECT 'orders' as table_name, COUNT(*) as orphaned_rows
FROM orders WHERE tenant_id IS NULL
UNION ALL
SELECT 'users', COUNT(*) FROM users WHERE tenant_id IS NULL;
```

### Preventing Tenant ID Tampering

```sql
-- Application-level validation
-- NEVER trust client-provided tenant_id

-- Validate user belongs to tenant
CREATE OR REPLACE FUNCTION validate_tenant_access(
    p_user_id INTEGER,
    p_tenant_id INTEGER
) RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM users 
        WHERE id = p_user_id AND tenant_id = p_tenant_id
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Use in application before setting context
IF NOT validate_tenant_access(session_user_id, requested_tenant_id) THEN
    RAISE EXCEPTION 'Unauthorized access to tenant %', requested_tenant_id;
END IF;
```

### Encryption at Rest (Per-Tenant Keys)

```sql
-- Using pgcrypto extension
CREATE EXTENSION pgcrypto;

CREATE TABLE tenant_encryption_keys (
    tenant_id INTEGER PRIMARY KEY,
    encryption_key BYTEA NOT NULL
);

-- Encrypt data per tenant
CREATE OR REPLACE FUNCTION encrypt_tenant_data(
    p_tenant_id INTEGER,
    p_plaintext TEXT
) RETURNS BYTEA AS $$
DECLARE
    v_key BYTEA;
BEGIN
    SELECT encryption_key INTO v_key 
    FROM tenant_encryption_keys 
    WHERE tenant_id = p_tenant_id;
    
    RETURN pgp_sym_encrypt(p_plaintext, v_key);
END;
$$ LANGUAGE plpgsql;
```

## Decision Matrix

| Criterion | Shared Schema | Separate Schemas | Separate Databases |
|-----------|---------------|------------------|--------------------|
| **Number of Tenants** | 100-10,000+ | 10-100 | 1-50 |
| **Data Isolation** | Low | Medium | High |
| **Resource Efficiency** | High | Medium | Low |
| **Scaling Complexity** | Low | Medium | High |
| **Schema Customization** | None | Per-schema | Per-database |
| **Compliance** | Difficult | Moderate | Easy |
| **Cost** | Low | Medium | High |
| **Onboarding Speed** | Fast | Medium | Slow |
| **Tenant Migration** | Difficult | Medium | Easy |

**Recommendations:**

**Use Shared Schema when:**
- Many small tenants (SaaS)
- Cost-sensitive
- Tenants have similar needs
- Rapid tenant onboarding required

**Use Separate Schemas when:**
- Medium number of tenants
- Need some customization
- Compliance requires separation
- Willing to manage complexity

**Use Separate Databases when:**
- Few large enterprise tenants
- Strong isolation required
- Different SLAs per tenant
- Regulated industries
- Need tenant-specific scaling

**Use Hybrid when:**
- Mix of small and large tenants
- Want cost efficiency + isolation
- Can manage routing complexity

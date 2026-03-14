# PostgreSQL Schema Design Patterns

Comprehensive guide to database schema design patterns, normalization, data modeling, and PostgreSQL-specific features.

## Normalization and Denormalization

### Normal Forms

**First Normal Form (1NF):**
- Atomic values (no arrays in columns, unless intentionally using PostgreSQL arrays)
- Each column contains values of a single type
- Unique column names
- Order of rows/columns doesn't matter

```sql
-- ❌ Not 1NF: Multiple values in one column
CREATE TABLE orders (
    id INTEGER,
    product_ids TEXT  -- '1,2,3,4'
);

-- ✅ 1NF: Separate rows or use array type
CREATE TABLE orders (
    id INTEGER,
    product_ids INTEGER[]  -- PostgreSQL array
);

-- Or proper normalization:
CREATE TABLE order_items (
    order_id INTEGER,
    product_id INTEGER,
    PRIMARY KEY (order_id, product_id)
);
```

**Second Normal Form (2NF):**
- Must be in 1NF
- No partial dependencies (all non-key columns depend on entire primary key)

```sql
-- ❌ Not 2NF: customer_name depends only on customer_id, not (order_id, product_id)
CREATE TABLE order_items (
    order_id INTEGER,
    product_id INTEGER,
    customer_id INTEGER,
    customer_name VARCHAR(100),  -- Partial dependency
    quantity INTEGER,
    PRIMARY KEY (order_id, product_id)
);

-- ✅ 2NF: Separate customer data
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id)
);

CREATE TABLE order_items (
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    PRIMARY KEY (order_id, product_id),
    FOREIGN KEY (order_id) REFERENCES orders(id)
);
```

**Third Normal Form (3NF):**
- Must be in 2NF
- No transitive dependencies (non-key columns don't depend on other non-key columns)

```sql
-- ❌ Not 3NF: city depends on zip_code (transitive)
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100),
    zip_code VARCHAR(10),
    city VARCHAR(50),  -- Transitive: city → zip_code → id
    state VARCHAR(2)
);

-- ✅ 3NF: Separate location data
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100),
    zip_code VARCHAR(10) REFERENCES zip_codes(code)
);

CREATE TABLE zip_codes (
    code VARCHAR(10) PRIMARY KEY,
    city VARCHAR(50),
    state VARCHAR(2)
);
```

### Strategic Denormalization

**When to denormalize:**
- Read-heavy workloads (10:1 read:write ratio or higher)
- Expensive JOIN operations
- Frequently accessed summary data
- Performance critical paths

**Patterns:**

**1. Materialized Aggregates:**
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER,
    total_amount DECIMAL(10,2),  -- Denormalized sum
    created_at TIMESTAMP
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    price DECIMAL(10,2),
    quantity INTEGER
);

-- Trigger to maintain denormalized total
CREATE OR REPLACE FUNCTION update_order_total()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE orders
    SET total_amount = (
        SELECT SUM(price * quantity)
        FROM order_items
        WHERE order_id = COALESCE(NEW.order_id, OLD.order_id)
    )
    WHERE id = COALESCE(NEW.order_id, OLD.order_id);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_order_total
AFTER INSERT OR UPDATE OR DELETE ON order_items
FOR EACH ROW EXECUTE FUNCTION update_order_total();
```

**2. Cached Lookups:**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50),
    country_code CHAR(2),
    country_name VARCHAR(100),  -- Denormalized from countries table
    created_at TIMESTAMP
);

-- Maintain with trigger or application logic
```

**3. Snapshot Tables:**
```sql
-- Historical snapshots for reporting
CREATE TABLE daily_metrics_snapshot (
    snapshot_date DATE PRIMARY KEY,
    total_users INTEGER,
    total_orders INTEGER,
    revenue DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Populated daily via scheduled job
INSERT INTO daily_metrics_snapshot (snapshot_date, total_users, total_orders, revenue)
SELECT 
    CURRENT_DATE,
    (SELECT COUNT(*) FROM users),
    (SELECT COUNT(*) FROM orders WHERE DATE(created_at) = CURRENT_DATE),
    (SELECT SUM(total) FROM orders WHERE DATE(created_at) = CURRENT_DATE);
```

## Common Design Patterns

### Pattern 1: Polymorphic Associations

**Problem:** A table can belong to multiple parent types

**Anti-Pattern (avoid):**
```sql
-- ❌ Comments can belong to posts OR photos
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    commentable_type VARCHAR(50),  -- 'Post' or 'Photo'
    commentable_id INTEGER,  -- ID of post or photo
    content TEXT
);

-- Issues:
-- - No foreign key constraints
-- - Type safety lost
-- - Cannot enforce referential integrity
```

**Better Pattern 1: Exclusive Arcs (mutually exclusive FKs):**
```sql
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id),
    photo_id INTEGER REFERENCES photos(id),
    content TEXT,
    CONSTRAINT check_one_parent CHECK (
        (post_id IS NOT NULL AND photo_id IS NULL) OR
        (post_id IS NULL AND photo_id IS NOT NULL)
    )
);

-- Index on non-null values
CREATE INDEX idx_comments_post ON comments(post_id) WHERE post_id IS NOT NULL;
CREATE INDEX idx_comments_photo ON comments(photo_id) WHERE photo_id IS NOT NULL;
```

**Better Pattern 2: Separate tables:**
```sql
CREATE TABLE post_comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id) NOT NULL,
    content TEXT
);

CREATE TABLE photo_comments (
    id SERIAL PRIMARY KEY,
    photo_id INTEGER REFERENCES photos(id) NOT NULL,
    content TEXT
);

-- Union view for convenience
CREATE VIEW all_comments AS
    SELECT id, post_id AS parent_id, 'post' AS parent_type, content FROM post_comments
    UNION ALL
    SELECT id, photo_id AS parent_id, 'photo' AS parent_type, content FROM photo_comments;
```

### Pattern 2: Tagging and Hierarchies

**Simple tagging:**
```sql
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100)
);

CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE
);

CREATE TABLE item_tags (
    item_id INTEGER REFERENCES items(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (item_id, tag_id)
);

-- Query items by tag
SELECT i.* FROM items i
JOIN item_tags it ON i.id = it.item_id
JOIN tags t ON it.tag_id = t.id
WHERE t.name = 'electronics';
```

**Hierarchical tags (categories):**
```sql
-- Using ltree extension
CREATE EXTENSION ltree;

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    path ltree NOT NULL
);

-- Create index on path for hierarchy queries
CREATE INDEX idx_categories_path ON categories USING gist(path);

-- Insert examples
INSERT INTO categories (name, path) VALUES
    ('Electronics', 'electronics'),
    ('Computers', 'electronics.computers'),
    ('Laptops', 'electronics.computers.laptops'),
    ('Gaming', 'electronics.computers.laptops.gaming');

-- Find all descendants
SELECT * FROM categories WHERE path <@ 'electronics.computers';

-- Find all ancestors
SELECT * FROM categories WHERE path @> 'electronics.computers.laptops.gaming';
```

**Alternative: Closure Table:**
```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100)
);

CREATE TABLE category_paths (
    ancestor_id INTEGER REFERENCES categories(id),
    descendant_id INTEGER REFERENCES categories(id),
    depth INTEGER NOT NULL,
    PRIMARY KEY (ancestor_id, descendant_id)
);

-- Insert category and all ancestor relationships
-- (Requires trigger or application logic)

-- Find all subcategories of "Electronics" (id=1)
SELECT c.* FROM categories c
JOIN category_paths cp ON c.id = cp.descendant_id
WHERE cp.ancestor_id = 1;
```

### Pattern 3: Temporal Data (Time-Series and Versioning)

**Audit trail (who changed what when):**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER
);

CREATE TABLE user_audit (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    field_name VARCHAR(50),
    old_value TEXT,
    new_value TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by INTEGER
);

-- Trigger to populate audit table
CREATE OR REPLACE FUNCTION audit_user_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'UPDATE') THEN
        IF OLD.username != NEW.username THEN
            INSERT INTO user_audit (user_id, field_name, old_value, new_value, changed_by)
            VALUES (NEW.id, 'username', OLD.username, NEW.username, NEW.updated_by);
        END IF;
        IF OLD.email != NEW.email THEN
            INSERT INTO user_audit (user_id, field_name, old_value, new_value, changed_by)
            VALUES (NEW.id, 'email', OLD.email, NEW.email, NEW.updated_by);
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_users
AFTER UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION audit_user_changes();
```

**Temporal tables (system versioning):**
```sql
-- Current data
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    price DECIMAL(10,2),
    sys_period tstzrange NOT NULL DEFAULT tstzrange(CURRENT_TIMESTAMP, NULL)
);

-- Historical data
CREATE TABLE products_history (
    LIKE products
);

-- Trigger to move old versions to history
CREATE OR REPLACE FUNCTION versioning_trigger()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'UPDATE' OR TG_OP = 'DELETE') THEN
        INSERT INTO products_history SELECT OLD.*;
    END IF;
    
    IF (TG_OP = 'UPDATE') THEN
        NEW.sys_period = tstzrange(CURRENT_TIMESTAMP, NULL);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER versioning_products
BEFORE UPDATE OR DELETE ON products
FOR EACH ROW EXECUTE FUNCTION versioning_trigger();

-- Query historical data
SELECT * FROM products_history WHERE id = 1 AND sys_period @> '2024-01-01'::timestamptz;
```

**Time-series data:**
```sql
CREATE TABLE sensor_readings (
    sensor_id INTEGER,
    reading_time TIMESTAMP NOT NULL,
    temperature DECIMAL(5,2),
    humidity DECIMAL(5,2),
    PRIMARY KEY (sensor_id, reading_time)
) PARTITION BY RANGE (reading_time);

-- Create monthly partitions
CREATE TABLE sensor_readings_2024_01 PARTITION OF sensor_readings
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- BRIN index for time-series (space efficient)
CREATE INDEX idx_readings_time ON sensor_readings USING brin(reading_time);
```

### Pattern 4: Soft Deletes

**Basic soft delete:**
```sql
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200),
    content TEXT,
    deleted_at TIMESTAMP,  -- NULL = not deleted
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for active records
CREATE INDEX idx_posts_active ON posts(id) WHERE deleted_at IS NULL;

-- Queries
SELECT * FROM posts WHERE deleted_at IS NULL;  -- Active posts
SELECT * FROM posts WHERE deleted_at IS NOT NULL;  -- Deleted posts

-- "Undelete"
UPDATE posts SET deleted_at = NULL WHERE id = 123;
```

**Soft delete with views:**
```sql
CREATE VIEW active_posts AS
    SELECT * FROM posts WHERE deleted_at IS NULL;

CREATE VIEW deleted_posts AS
    SELECT * FROM posts WHERE deleted_at IS NOT NULL;

-- Application uses views
SELECT * FROM active_posts;
```

**Soft delete with partitioning:**
```sql
CREATE TABLE posts (
    id SERIAL,
    title VARCHAR(200),
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    PRIMARY KEY (id, is_deleted)
) PARTITION BY LIST (is_deleted);

CREATE TABLE posts_active PARTITION OF posts FOR VALUES IN (false);
CREATE TABLE posts_deleted PARTITION OF posts FOR VALUES IN (true);

-- Partition pruning automatically filters
SELECT * FROM posts WHERE is_deleted = false;  -- Only scans posts_active
```

### Pattern 5: JSON/JSONB for Flexible Schemas

**When to use JSONB:**
- Variable attributes (product catalogs, user preferences)
- Sparse data (most fields NULL)
- Schema evolution without migrations
- API data storage

**Product catalog example:**
```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200),
    category VARCHAR(50),
    price DECIMAL(10,2),
    attributes JSONB  -- Flexible attributes per product type
);

-- Electronics might have: {"brand": "Sony", "warranty": "2 years", "ports": ["HDMI", "USB-C"]}
-- Clothing might have: {"size": "M", "color": "blue", "material": "cotton"}

-- GIN index for JSONB queries
CREATE INDEX idx_products_attributes ON products USING gin(attributes);

-- Query by JSON key
SELECT * FROM products WHERE attributes->>'brand' = 'Sony';

-- Query array contains
SELECT * FROM products WHERE attributes->'ports' ? 'HDMI';

-- Partial index for common queries
CREATE INDEX idx_products_brand ON products((attributes->>'brand'))
    WHERE attributes ? 'brand';
```

**User preferences:**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50),
    email VARCHAR(100),
    preferences JSONB DEFAULT '{}'::jsonb
);

-- Update specific preference
UPDATE users 
SET preferences = jsonb_set(preferences, '{theme}', '"dark"')
WHERE id = 1;

-- Merge preferences
UPDATE users
SET preferences = preferences || '{"notifications": {"email": true, "push": false}}'::jsonb
WHERE id = 1;
```

### Pattern 6: Event Sourcing

**Events table:**
```sql
CREATE TABLE account_events (
    id BIGSERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (created_at);

-- Index for event replay
CREATE INDEX idx_events_account ON account_events(account_id, created_at);

-- Example events
INSERT INTO account_events (account_id, event_type, event_data) VALUES
    (1, 'account_created', '{"initial_balance": 1000}'),
    (1, 'deposit', '{"amount": 500, "source": "transfer"}'),
    (1, 'withdrawal', '{"amount": 200, "destination": "ATM"}');

-- Rebuild current state from events
SELECT 
    account_id,
    (event_data->>'initial_balance')::decimal +
    COALESCE(SUM(CASE 
        WHEN event_type = 'deposit' THEN (event_data->>'amount')::decimal
        WHEN event_type = 'withdrawal' THEN -(event_data->>'amount')::decimal
        ELSE 0
    END), 0) as current_balance
FROM account_events
WHERE account_id = 1
GROUP BY account_id, event_data->>'initial_balance';
```

**Snapshot + events (performance):**
```sql
CREATE TABLE account_snapshots (
    account_id INTEGER PRIMARY KEY,
    balance DECIMAL(10,2),
    snapshot_at TIMESTAMP
);

-- Rebuild from snapshot + events after snapshot
SELECT 
    s.balance +
    COALESCE(SUM(CASE 
        WHEN e.event_type = 'deposit' THEN (e.event_data->>'amount')::decimal
        WHEN e.event_type = 'withdrawal' THEN -(e.event_data->>'amount')::decimal
        ELSE 0
    END), 0) as current_balance
FROM account_snapshots s
LEFT JOIN account_events e ON e.account_id = s.account_id 
    AND e.created_at > s.snapshot_at
WHERE s.account_id = 1
GROUP BY s.balance;
```

## Data Types Best Practices

### Choosing the Right Type

**Integers:**
```sql
SMALLINT    -- 2 bytes, -32768 to 32767
INTEGER     -- 4 bytes, -2.1B to 2.1B (default choice)
BIGINT      -- 8 bytes, very large numbers
SERIAL      -- Auto-incrementing INTEGER
BIGSERIAL   -- Auto-incrementing BIGINT
```

**Text:**
```sql
CHAR(n)        -- Fixed length, rarely useful
VARCHAR(n)     -- Variable length with limit
TEXT           -- Unlimited length (recommended for most use cases)
```

**Numeric:**
```sql
NUMERIC(precision, scale)  -- Exact decimal (use for money)
REAL           -- 4 bytes, 6 decimal digits precision
DOUBLE PRECISION  -- 8 bytes, 15 decimal digits precision
```

**Date/Time:**
```sql
DATE           -- Date only
TIME           -- Time only
TIMESTAMP      -- Date + time without timezone
TIMESTAMPTZ    -- Date + time with timezone (recommended)
INTERVAL       -- Time span
```

**Boolean:**
```sql
BOOLEAN        -- true/false/null
-- Don't use: CHAR(1), INTEGER for booleans
```

**UUID:**
```sql
UUID           -- Universally unique identifier
-- Use for distributed systems, public IDs

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50)
);
```

### PostgreSQL-Specific Types

**Arrays:**
```sql
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    tags TEXT[]
);

INSERT INTO posts (tags) VALUES (ARRAY['postgresql', 'database', 'sql']);

-- Query
SELECT * FROM posts WHERE 'postgresql' = ANY(tags);
SELECT * FROM posts WHERE tags @> ARRAY['postgresql'];  -- Contains
SELECT * FROM posts WHERE tags && ARRAY['postgresql', 'mysql'];  -- Overlap
```

**JSONB:**
```sql
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    data JSONB
);

-- GIN index for performance
CREATE INDEX idx_events_data ON events USING gin(data);

-- Queries
SELECT * FROM events WHERE data->>'type' = 'click';
SELECT * FROM events WHERE data @> '{"user_id": 123}';
```

**Range Types:**
```sql
CREATE TABLE reservations (
    id SERIAL PRIMARY KEY,
    room_id INTEGER,
    during tstzrange,  -- Timestamp with timezone range
    EXCLUDE USING gist (room_id WITH =, during WITH &&)  -- No overlaps
);

INSERT INTO reservations (room_id, during) VALUES
    (1, '[2024-01-01 14:00, 2024-01-01 16:00)');

-- Check availability
SELECT * FROM reservations 
WHERE room_id = 1 
  AND during && '[2024-01-01 15:00, 2024-01-01 17:00)';
```

**Enums:**
```sql
CREATE TYPE order_status AS ENUM ('pending', 'processing', 'shipped', 'delivered');

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    status order_status NOT NULL DEFAULT 'pending'
);

-- Note: Enums are difficult to change, consider using CHECK constraints or lookup tables instead for evolving schemas
```

## Constraints and Data Integrity

### Primary Keys

```sql
-- Serial (auto-increment)
id SERIAL PRIMARY KEY

-- UUID
id UUID PRIMARY KEY DEFAULT gen_random_uuid()

-- Composite
PRIMARY KEY (tenant_id, user_id)

-- Natural key (use cautiously)
email VARCHAR(100) PRIMARY KEY
```

### Foreign Keys

```sql
-- Basic FK
customer_id INTEGER REFERENCES customers(id)

-- With cascading delete
customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE

-- With set null
customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL

-- Deferred constraints (checked at transaction end)
customer_id INTEGER REFERENCES customers(id) DEFERRABLE INITIALLY DEFERRED
```

### Check Constraints

```sql
-- Value constraints
price DECIMAL(10,2) CHECK (price > 0)
age INTEGER CHECK (age >= 0 AND age <= 120)

-- Conditional constraints
CHECK (
    (status = 'shipped' AND shipped_date IS NOT NULL) OR
    (status != 'shipped' AND shipped_date IS NULL)
)

-- Table-level CHECK
CREATE TABLE discounts (
    percentage DECIMAL(5,2),
    amount DECIMAL(10,2),
    CHECK (
        (percentage IS NOT NULL AND amount IS NULL) OR
        (percentage IS NULL AND amount IS NOT NULL)
    )
);
```

### Unique Constraints

```sql
-- Single column
email VARCHAR(100) UNIQUE

-- Composite unique
UNIQUE (tenant_id, username)

-- Partial unique (PostgreSQL-specific)
CREATE UNIQUE INDEX idx_active_users ON users(email) WHERE deleted_at IS NULL;
```

## Performance Considerations

**Indexing strategy:**
1. Primary keys: Automatic index
2. Foreign keys: Add index explicitly
3. Frequently queried columns: Add B-tree index
4. Text search: GIN index with to_tsvector
5. JSONB queries: GIN index
6. Partial indexes: For frequently filtered subsets

**Avoid:**
- Indexes on every column
- Indexes on low-cardinality columns (few distinct values)
- Over-normalization requiring many JOINs
- Large VARCHAR limits when TEXT works better

**Schema migrations:**
- Use transactions
- Test on production-like data
- Consider online schema changes (pg_repack, online DDL tools)
- Plan for rollback

# Query Optimization and Rewriting Patterns

Comprehensive guide for analyzing and rewriting PostgreSQL queries for better performance.

## EXPLAIN Analysis Fundamentals

### Reading EXPLAIN Output

**Key metrics to examine:**
- **Cost:** Estimated total cost (startup_cost..total_cost)
- **Rows:** Estimated row count
- **Width:** Average row width in bytes
- **Actual time:** Real execution time (requires EXPLAIN ANALYZE)
- **Loops:** Number of times node executed

**Node types (from slowest to fastest):**
1. Sequential Scan → Full table scan
2. Index Scan → Read index then table (random I/O)
3. Index Only Scan → Read only index (fast)
4. Bitmap Index/Heap Scan → Batch index lookups
5. Nested Loop → Join via loops (good for small datasets)
6. Hash Join → Build hash table (good for large datasets)
7. Merge Join → Sorted inputs (good for pre-sorted data)

### Essential EXPLAIN Commands

```sql
-- Basic plan (estimated costs)
EXPLAIN SELECT ...;

-- Actual execution with timing
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;

-- JSON output for tools
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) SELECT ...;

-- Show ALL query details
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, SETTINGS) SELECT ...;
```

### Red Flags in EXPLAIN Output

🚩 **Sequential Scan on large tables** (>1M rows)
```
Seq Scan on large_table  (cost=0.00..50000.00 rows=1000000)
```
**Fix:** Add appropriate index

🚩 **High actual time vs estimated**
```
Index Scan ... (cost=0.42..8.44 rows=1 width=...) (actual time=0.035..234.123 rows=50000 loops=1)
```
**Fix:** Run ANALYZE; statistics are outdated

🚩 **Nested Loop with large outer side**
```
Nested Loop  (cost=0.29..500000.00 rows=100000)
  ->  Seq Scan on table1  (cost=0.00..10000.00 rows=100000)
  ->  Index Scan on table2  (cost=0.29..4.50 rows=1)
```
**Fix:** Change join strategy or reorder joins

🚩 **Bitmap Heap Scan with low Heap Blocks: exact**
```
Bitmap Heap Scan on table (actual rows=100000)
  Heap Blocks: exact=1234 lossy=45678
```
**Fix:** Increase work_mem or improve selectivity

🚩 **Subplan/InitPlan executed in loops**
```
Nested Loop
  ->  Seq Scan on table1
  SubPlan 1
    ->  Index Scan on table2  (executed 50000 times)
```
**Fix:** Rewrite as JOIN or use LATERAL

## Query Rewriting Patterns

### Pattern 1: Replace Subqueries with JOINs

❌ **Before: Correlated subquery (slow)**
```sql
SELECT o.order_id, o.total,
  (SELECT c.name FROM customers c WHERE c.id = o.customer_id) as customer_name
FROM orders o
WHERE o.created_at > NOW() - INTERVAL '30 days';
```

✅ **After: JOIN (fast)**
```sql
SELECT o.order_id, o.total, c.name as customer_name
FROM orders o
JOIN customers c ON c.id = o.customer_id
WHERE o.created_at > NOW() - INTERVAL '30 days';
```

**Why:** Eliminates repeated subquery execution (once per row)

### Pattern 2: Use EXISTS instead of IN with subqueries

❌ **Before: IN with subquery (can be slow)**
```sql
SELECT * FROM users
WHERE id IN (
  SELECT user_id FROM orders 
  WHERE created_at > NOW() - INTERVAL '7 days'
);
```

✅ **After: EXISTS (faster)**
```sql
SELECT * FROM users u
WHERE EXISTS (
  SELECT 1 FROM orders o 
  WHERE o.user_id = u.id 
    AND o.created_at > NOW() - INTERVAL '7 days'
);
```

**Why:** EXISTS can short-circuit; IN must evaluate all rows

### Pattern 3: Use NOT EXISTS instead of NOT IN

❌ **Before: NOT IN (NULL handling issues + slow)**
```sql
SELECT * FROM users
WHERE id NOT IN (SELECT user_id FROM banned_users);
```

✅ **After: NOT EXISTS (faster and NULL-safe)**
```sql
SELECT * FROM users u
WHERE NOT EXISTS (
  SELECT 1 FROM banned_users b WHERE b.user_id = u.id
);
```

**Why:** NOT IN returns no rows if subquery contains NULL

### Pattern 4: Replace DISTINCT with GROUP BY

❌ **Before: DISTINCT (can be slow with many columns)**
```sql
SELECT DISTINCT user_id, created_at::date
FROM events
WHERE created_at > NOW() - INTERVAL '30 days';
```

✅ **After: GROUP BY (explicit and often faster)**
```sql
SELECT user_id, created_at::date
FROM events
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY user_id, created_at::date;
```

**Why:** GROUP BY gives planner more optimization options

### Pattern 5: Avoid SELECT *

❌ **Before: SELECT * (wasteful)**
```sql
SELECT * FROM large_table
WHERE id = 123;
```

✅ **After: Explicit columns (enables index-only scans)**
```sql
SELECT id, name, email, created_at
FROM large_table
WHERE id = 123;
```

**Why:** Index-only scans possible if all columns in index

### Pattern 6: Use LIMIT for pagination with offset alternative

❌ **Before: OFFSET (slow for large offsets)**
```sql
SELECT * FROM orders
ORDER BY created_at DESC
LIMIT 20 OFFSET 100000;  -- Still scans first 100,020 rows
```

✅ **After: Keyset pagination (fast)**
```sql
-- First page
SELECT * FROM orders
ORDER BY created_at DESC
LIMIT 20;

-- Subsequent pages (using last created_at from previous page)
SELECT * FROM orders
WHERE created_at < '2024-01-01 12:34:56'
ORDER BY created_at DESC
LIMIT 20;
```

**Why:** Avoids scanning skipped rows

### Pattern 7: Partial indexes for selective queries

❌ **Before: Full index (large)**
```sql
CREATE INDEX idx_orders_status ON orders(status);

SELECT * FROM orders WHERE status = 'active';  -- Only 2% of rows
```

✅ **After: Partial index (smaller, faster)**
```sql
CREATE INDEX idx_orders_active ON orders(id, created_at) 
WHERE status = 'active';

SELECT * FROM orders WHERE status = 'active';
```

**Why:** Smaller index, faster scans, less maintenance overhead

### Pattern 8: Use covering indexes

❌ **Before: Index + table lookup**
```sql
CREATE INDEX idx_users_email ON users(email);

SELECT id, email, name FROM users WHERE email = 'user@example.com';
-- Index Scan + Heap Fetch
```

✅ **After: Covering index (index-only scan)**
```sql
CREATE INDEX idx_users_email_covering ON users(email) INCLUDE (id, name);

SELECT id, email, name FROM users WHERE email = 'user@example.com';
-- Index Only Scan (no heap access)
```

**Why:** Avoids table lookups (significantly faster)

### Pattern 9: Rewrite OR conditions with UNION

❌ **Before: OR condition (may not use indexes well)**
```sql
SELECT * FROM orders
WHERE customer_id = 123 OR status = 'pending';
```

✅ **After: UNION (can use multiple indexes)**
```sql
SELECT * FROM orders WHERE customer_id = 123
UNION
SELECT * FROM orders WHERE status = 'pending';
```

**Why:** Each UNION branch can use different index

### Pattern 10: Use CTEs for readability but watch for optimization fence

⚠️ **CTEs in PostgreSQL < 12: Optimization fence**
```sql
WITH recent_orders AS (
  SELECT * FROM orders WHERE created_at > NOW() - INTERVAL '7 days'
)
SELECT * FROM recent_orders WHERE customer_id = 123;
-- CTE is evaluated independently, then filtered
```

✅ **PostgreSQL 12+: Use NOT MATERIALIZED if needed**
```sql
WITH recent_orders AS NOT MATERIALIZED (
  SELECT * FROM orders WHERE created_at > NOW() - INTERVAL '7 days'
)
SELECT * FROM recent_orders WHERE customer_id = 123;
-- Planner can push down customer_id filter
```

✅ **Alternative: Subquery in FROM**
```sql
SELECT * FROM (
  SELECT * FROM orders WHERE created_at > NOW() - INTERVAL '7 days'
) recent_orders 
WHERE customer_id = 123;
-- Fully optimizable
```

### Pattern 11: Avoid functions on indexed columns in WHERE

❌ **Before: Function prevents index use**
```sql
SELECT * FROM events
WHERE DATE(created_at) = '2024-01-15';
-- Sequential Scan (function on indexed column)
```

✅ **After: Range query (uses index)**
```sql
SELECT * FROM events
WHERE created_at >= '2024-01-15'::timestamp
  AND created_at < '2024-01-16'::timestamp;
-- Index Scan
```

### Pattern 12: Use aggregate filters instead of WHERE after GROUP BY

❌ **Before: Subquery for filtering aggregates**
```sql
SELECT user_id, COUNT(*) as order_count
FROM orders
GROUP BY user_id
HAVING COUNT(*) > 5;
-- Works but less readable than FILTER
```

✅ **After: FILTER clause (PostgreSQL 9.4+)**
```sql
SELECT user_id, 
  COUNT(*) FILTER (WHERE status = 'completed') as completed_count,
  COUNT(*) FILTER (WHERE status = 'pending') as pending_count
FROM orders
GROUP BY user_id;
```

**Why:** Clearer intent, single table scan

### Pattern 13: Optimize LIKE queries

❌ **Before: Leading wildcard (can't use index)**
```sql
SELECT * FROM products WHERE name LIKE '%widget%';
-- Sequential Scan
```

✅ **After: Full-text search for contains queries**
```sql
CREATE INDEX idx_products_name_fts ON products 
USING gin(to_tsvector('english', name));

SELECT * FROM products 
WHERE to_tsvector('english', name) @@ to_tsquery('english', 'widget');
-- Bitmap Index Scan (much faster)
```

✅ **For prefix searches: Regular index works**
```sql
SELECT * FROM products WHERE name LIKE 'Widget%';
-- Index Scan (works with B-tree index)
```

## Index Design Patterns

### Multi-Column Index Ordering

**Rule:** Most selective column first, unless query patterns dictate otherwise

❌ **Before: Wrong order**
```sql
CREATE INDEX idx_orders_date_customer ON orders(created_at, customer_id);

-- Query often filters by customer_id alone
SELECT * FROM orders WHERE customer_id = 123;
-- Can't use index efficiently
```

✅ **After: Correct order**
```sql
CREATE INDEX idx_orders_customer_date ON orders(customer_id, created_at);

-- Both queries use index efficiently
SELECT * FROM orders WHERE customer_id = 123;
SELECT * FROM orders WHERE customer_id = 123 AND created_at > NOW() - INTERVAL '7 days';
```

### When to Add Indexes

**Add index when:**
- Column frequently in WHERE, JOIN, ORDER BY clauses
- Table has >10,000 rows
- Query scans >1-5% of table rows
- Column has high cardinality (many distinct values)

**Don't add index when:**
- Table is small (<1000 rows)
- Column has low cardinality (few distinct values like boolean)
- Table has heavy write load (indexes slow writes)
- Existing index already covers the query

### Finding Missing Indexes

```sql
-- Queries causing sequential scans
SELECT schemaname, tablename, 
       seq_scan, seq_tup_read,
       idx_scan, idx_tup_fetch,
       seq_tup_read / seq_scan as avg_seq_tup
FROM pg_stat_user_tables
WHERE seq_scan > 0
ORDER BY seq_tup_read DESC
LIMIT 20;

-- Unused indexes (candidates for removal)
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexname NOT LIKE 'pg_toast_%'
ORDER BY pg_relation_size(indexrelid) DESC;
```

## JOIN Optimization

### Join Strategies

**Nested Loop:** Best for small datasets or high selectivity
```
Nested Loop  (cost=0.29..16.35 rows=1)
  ->  Index Scan on small_table  (rows=10)
  ->  Index Scan on large_table  (rows=1)
```

**Hash Join:** Best for large datasets, equi-joins
```
Hash Join  (cost=15000.00..45000.00 rows=100000)
  Hash Cond: (a.id = b.id)
  ->  Seq Scan on table_a  (rows=100000)
  ->  Hash
        ->  Seq Scan on table_b  (rows=100000)
```

**Merge Join:** Best for pre-sorted data
```
Merge Join  (cost=0.84..892.34 rows=50000)
  Merge Cond: (a.id = b.id)
  ->  Index Scan on table_a  (rows=50000)
  ->  Index Scan on table_b  (rows=50000)
```

### Force Join Strategy (when necessary)

```sql
-- Disable nested loops
SET enable_nestloop = off;

-- Disable hash joins  
SET enable_hashjoin = off;

-- Disable merge joins
SET enable_mergejoin = off;

-- Reset
RESET enable_nestloop;
```

**Note:** Usually let planner decide; only override for testing

### JOIN Order Matters

❌ **Before: Large table first**
```sql
SELECT * FROM large_table l
JOIN small_table s ON s.id = l.small_id
WHERE s.active = true;
-- Scans entire large_table first
```

✅ **After: Filter small table first (if planner doesn't)**
```sql
SELECT * FROM small_table s
JOIN large_table l ON l.small_id = s.id
WHERE s.active = true;
-- Filter small_table first (maybe 100 rows)
-- Then join to large_table using index
```

**Note:** Modern planners usually get this right

## Statistics and ANALYZE

### When to Run ANALYZE

**Run ANALYZE after:**
- Bulk data loads
- Large UPDATE/DELETE operations
- Creating new indexes
- Significant data distribution changes

```sql
-- Analyze specific table
ANALYZE table_name;

-- Analyze specific columns (faster for large tables)
ANALYZE table_name (column1, column2);

-- Analyze all tables
ANALYZE;

-- Verbose output
ANALYZE VERBOSE table_name;
```

### Increase statistics target for complex queries

```sql
-- Default is 100
ALTER TABLE large_table ALTER COLUMN complex_column SET STATISTICS 1000;
ANALYZE large_table;
```

## Query Performance Monitoring

### Key metrics to track

```sql
-- Slow queries (requires pg_stat_statements)
SELECT 
  query,
  calls,
  total_exec_time,
  mean_exec_time,
  max_exec_time,
  rows
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Table bloat causing slow scans
SELECT 
  schemaname, tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
  n_dead_tup, n_live_tup,
  round(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 2) as dead_ratio
FROM pg_stat_user_tables
WHERE n_dead_tup > 10000
ORDER BY n_dead_tup DESC;

-- Long-running queries
SELECT pid, now() - query_start as duration, state, query
FROM pg_stat_activity
WHERE state != 'idle'
  AND now() - query_start > interval '1 minute'
ORDER BY duration DESC;
```

## Common Query Anti-Patterns

❌ **SELECT COUNT(*) on large tables**
```sql
SELECT COUNT(*) FROM large_table;
-- Always sequential scan
```

✅ **Use estimate for rough counts**
```sql
SELECT reltuples::bigint FROM pg_class WHERE relname = 'large_table';
-- Instant, approximate
```

❌ **Implicit type casting in WHERE**
```sql
CREATE TABLE events (user_id VARCHAR(50));
SELECT * FROM events WHERE user_id = 123;  -- Implicit cast prevents index use
```

✅ **Explicit casting or correct types**
```sql
SELECT * FROM events WHERE user_id = '123';
-- Or: ALTER TABLE events ALTER COLUMN user_id TYPE INTEGER;
```

❌ **NOT NULL checks on columns with few nulls**
```sql
SELECT * FROM orders WHERE customer_id IS NOT NULL;
-- Scans entire table
```

✅ **Use partial index if needed frequently**
```sql
CREATE INDEX idx_orders_customer_not_null ON orders(customer_id) 
WHERE customer_id IS NOT NULL;
```

## Optimization Workflow

1. **Identify slow query** (logs, pg_stat_statements)
2. **Run EXPLAIN ANALYZE** with BUFFERS
3. **Check statistics** are up-to-date (ANALYZE)
4. **Identify bottleneck:**
   - Sequential scans → Add index
   - High actual vs estimated → ANALYZE
   - Wrong join strategy → Check indexes, statistics
   - Subplans in loops → Rewrite as JOIN
5. **Test fix** with EXPLAIN ANALYZE
6. **Monitor in production**

## Resources for EXPLAIN Visualization

- https://explain.depesz.com/
- https://explain.dalibo.com/
- https://tatiyants.com/pev/
- pgAdmin built-in EXPLAIN visualizer

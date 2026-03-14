-- PostgreSQL Health Check Script
-- Run with: psql -U username -d database -f health_check.sql

\set QUIET on
\timing off
\pset border 2
\pset format wrapped

\echo '============================================'
\echo 'PostgreSQL Health Check Report'
\echo '============================================'
\echo ''

-- Database Version and Uptime
\echo '=== Database Information ==='
SELECT 
    version() AS postgres_version,
    pg_postmaster_start_time() AS started_at,
    now() - pg_postmaster_start_time() AS uptime;
\echo ''

-- Connection Usage
\echo '=== Connection Status ==='
SELECT 
    count(*) as current_connections,
    (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections,
    round(100.0 * count(*) / (SELECT setting::int FROM pg_settings WHERE name = 'max_connections'), 2) as pct_used
FROM pg_stat_activity;
\echo ''

-- Cache Hit Ratio (Target: >99%)
\echo '=== Cache Hit Ratio (Target: >99%) ==='
SELECT 
    round(100.0 * sum(blks_hit) / nullif(sum(blks_hit + blks_read), 0), 2) AS cache_hit_pct
FROM pg_stat_database;
\echo ''

-- Active Long-Running Queries
\echo '=== Long-Running Queries (>5 minutes) ==='
SELECT 
    pid,
    now() - query_start AS duration,
    usename,
    datname,
    state,
    left(query, 80) as query_preview
FROM pg_stat_activity
WHERE state != 'idle'
    AND now() - query_start > interval '5 minutes'
    AND pid != pg_backend_pid()
ORDER BY duration DESC
LIMIT 10;
\echo ''

-- Tables Needing Vacuum
\echo '=== Tables Needing Vacuum (>5% dead tuples) ==='
SELECT 
    schemaname,
    tablename,
    n_dead_tup,
    round(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_pct,
    last_autovacuum
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
    AND (n_dead_tup::float / NULLIF(n_live_tup, 0)) > 0.05
ORDER BY n_dead_tup DESC
LIMIT 10;
\echo ''

-- Table Bloat
\echo '=== Tables with Significant Bloat (>10k dead tuples) ==='
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    n_dead_tup,
    round(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_pct
FROM pg_stat_user_tables
WHERE n_dead_tup > 10000
ORDER BY n_dead_tup DESC
LIMIT 10;
\echo ''

-- Unused Indexes
\echo '=== Unused Indexes (0 scans, >1MB) ==='
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(schemaname||'.'||indexname)) AS index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
    AND indexname NOT LIKE '%_pkey'
    AND pg_relation_size(schemaname||'.'||indexname) > 1048576
ORDER BY pg_relation_size(schemaname||'.'||indexname) DESC
LIMIT 10;
\echo ''

-- Database Sizes
\echo '=== Database Sizes ==='
SELECT 
    datname,
    pg_size_pretty(pg_database_size(datname)) as size
FROM pg_database
WHERE datistemplate = false
ORDER BY pg_database_size(datname) DESC
LIMIT 10;
\echo ''

-- Blocking Locks
\echo '=== Blocking Locks ==='
SELECT 
    blocked_locks.pid AS blocked_pid,
    blocking_locks.pid AS blocking_pid,
    blocked_activity.usename AS blocked_user,
    left(blocked_activity.query, 60) AS blocked_query,
    left(blocking_activity.query, 60) AS blocking_query
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks 
    ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted
LIMIT 10;
\echo ''

-- Replication Status (if applicable)
\echo '=== Replication Status ==='
SELECT 
    client_addr,
    application_name,
    state,
    sync_state,
    write_lag,
    flush_lag,
    replay_lag
FROM pg_stat_replication
ORDER BY replay_lag DESC NULLS LAST;
\echo ''

\echo '=== Health Check Complete ==='

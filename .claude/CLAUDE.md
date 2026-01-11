# Project-Specific Claude Rules

<!-- 
This file customizes Claude's behavior for this specific project.
Rules here APPEND to, REINFORCE, or REPLACE your global preferences.
Place this file at `.claude/CLAUDE.md` in your project root.
-->

## Project Context

**Project Name:** [Your Project Name]

**Description:** [Brief description of what this project does]

**Tech Stack:**
- PostgreSQL [version]
- Python [version]
- [Other key technologies]

**Primary Use Case:**
[Describe the main purpose - e.g., "Multi-tenant SaaS application with PostgreSQL backend" or "Data pipeline for analytics warehouse"]

---

## Database Configuration

<!-- If this is a database-heavy project -->

### PostgreSQL Settings

**Instance Type:** [Cloud provider/self-hosted, size, etc.]
- Provider: [AWS RDS / GCP Cloud SQL / Azure / Self-hosted]
- Size: [e.g., "64GB RAM, 8 vCPU"]
- Storage: [SSD / NVMe / etc.]

**Workload Type:** [OLTP / Analytics / Mixed]

**Key Configuration Notes:**
- Max connections: [number]
- Shared buffers: [size]
- [Other important settings]

### Schema Patterns

**Multi-tenancy Model:** [Shared Schema with RLS / Separate Schemas / Separate Databases / N/A]

**Partitioning Strategy:** [If applicable]
- Tables: [list partitioned tables]
- Partition key: [column(s)]
- Partition interval: [daily/monthly/yearly]
- Retention policy: [duration]

**Replication:** [Yes/No, if yes describe setup]

---

## Development Guidelines

### Database Operations

**MUST:**
- Run all migrations in transaction blocks (where supported)
- Test migrations on staging data before production
- Include rollback scripts for all schema changes
- Run ANALYZE after data migrations

**MUST NOT:**
- Run VACUUM FULL on tables > [size threshold] without maintenance window
- Drop indexes without checking usage first (use diagnostic queries)
- Modify partition key after table creation

### Code Patterns

**Preferred Patterns:**
[Project-specific patterns - e.g., "Use Repository pattern for all database access"]

**Avoid:**
[Anti-patterns specific to this project]

---

## Testing Requirements

### Database Tests

- **Required coverage:** [percentage or specific areas]
- **Test database:** [How to set up/reset test DB]
- **Fixtures:** [Location and usage]

### Integration Tests

[Specific requirements for integration testing]

---

## Deployment & CI/CD

### Pre-deployment Checklist

- [ ] All tests passing
- [ ] Migration scripts reviewed
- [ ] Rollback plan documented
- [ ] [Other project-specific checks]

### Migration Strategy

[How database migrations are handled in this project]

---

## Common Tasks

### Adding a New Table

```sql
-- 1. Create migration file: migrations/YYYYMMDD_description.sql
-- 2. Include:
CREATE TABLE table_name (
    id BIGSERIAL PRIMARY KEY,
    -- [tenant_id if multi-tenant]
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3. Add indexes
CREATE INDEX idx_table_name_lookup ON table_name(lookup_column);

-- 4. Add RLS policies (if applicable)
-- 5. Run ANALYZE
ANALYZE table_name;
```

### Troubleshooting Slow Queries

1. Get query from `pg_stat_statements`
2. Run `EXPLAIN (ANALYZE, BUFFERS)`
3. Check for missing indexes using diagnostic queries from postgresql skill
4. [Other project-specific steps]

---

## Project-Specific Constraints

### Performance Requirements

- Query response time target: [duration]
- Max acceptable replication lag: [duration]
- [Other SLAs]

### Data Retention

- Production data: [retention policy]
- Logs: [retention policy]
- Backups: [retention policy]

---

## Team Conventions

### Naming Conventions

**Tables:** [snake_case / other]
**Columns:** [snake_case / other]
**Indexes:** `idx_{table}_{columns}` or [other pattern]
**Constraints:** `{table}_{column}_{type}` or [other pattern]

### Code Review Requirements

[What must be reviewed before merge]

---

## External Resources

### Documentation

- Internal docs: [link or location]
- API docs: [link]
- Architecture diagrams: [link or location]

### Monitoring & Alerts

- Dashboard: [link to Grafana/CloudWatch/etc.]
- Alert channels: [where alerts go]
- On-call: [rotation or contacts]

---

## Notes for Claude

<!-- Any specific instructions about how Claude should work on this project -->

**When making changes:**
- Always check if the change affects [specific areas]
- Consider impact on [specific components]
- [Other project-specific considerations]

**Testing priority:**
- Critical path: [areas that MUST be tested]
- Integration points: [external systems/APIs]

**Do not modify:**
- [Files or areas that should not be changed]

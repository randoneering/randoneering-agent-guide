# Randoneering Agent Guide

A curated collection of Claude Code skills and best practices for data engineering, database management, system configuration, and technical documentation. This repository provides deep domain expertise to enhance Claude's capabilities when working with complex technical infrastructure.

## Overview

This repository serves as a knowledge base and skill library containing battle-tested patterns, comprehensive workflows, and detailed reference materials. Each skill provides production-proven guidance for specific technical domains, from PostgreSQL optimization to Nix package development.

## Skills

### PostgreSQL Optimization

**Focus:** Database performance tuning and operational excellence

**Capabilities:**
- Configuration tuning (shared_buffers, work_mem, autovacuum)
- Query optimization and EXPLAIN analysis
- Cloud provider management (AWS RDS, GCP Cloud SQL, Azure Database)
- Database health monitoring (bloat, cache ratios, replication lag)
- Index design and covering indexes
- Vacuum management and dead tuple cleanup
- Replication slot monitoring

**Common Workflows:**
- Diagnosing slow queries with EXPLAIN plans
- Tuning postgresql.conf parameters for specific workloads
- Monitoring database health metrics
- Managing cloud-hosted PostgreSQL instances
- Optimizing indexes and query patterns

**Use when:**
- Queries are running slower than expected
- Database configuration needs optimization
- Monitoring database health and performance
- Managing RDS, Cloud SQL, or Azure PostgreSQL
- Investigating bloat or vacuum issues

[View Skill Documentation](skills/pg_optimization/SKILL.md)

### PostgreSQL Architecture

**Focus:** Database design, high availability, and large-scale deployment

**Capabilities:**
- Schema design and data modeling patterns
- Table partitioning (range, list, hash, multi-level)
- High availability with streaming replication (sync/async)
- Multi-tenancy patterns (shared schema with RLS, separate schemas, separate databases)
- Connection pooling with PgBouncer
- Failover and disaster recovery (Patroni, automatic failover)
- Backup strategies and PITR

**Common Workflows:**
- Designing normalized and denormalized schemas
- Implementing declarative partitioning
- Setting up streaming replication
- Building multi-tenant SaaS applications
- Configuring connection pooling
- Planning disaster recovery

**Use when:**
- Designing new database schemas
- Scaling to large datasets requiring partitioning
- Setting up HA/DR architectures
- Building multi-tenant applications
- Architecting enterprise PostgreSQL systems

[View Skill Documentation](skills/pg_design/SKILL.md)

### Data Engineering

**Focus:** Snowflake and DBT data warehouse engineering

**Capabilities:**
- Snowflake query caching optimization (result cache, metadata cache, warehouse cache)
- Warehouse sizing and scaling strategies (up vs out)
- DBT data quality testing (generic tests, custom tests, STAR schema validation)
- STAR schema design (fact tables, dimension tables, grain definition)
- Cost optimization strategies
- Query performance tuning

**Common Workflows:**
- Optimizing warehouse size for cost and performance
- Implementing comprehensive DBT test suites
- Designing dimensional models
- Leveraging Snowflake's caching layers
- Validating data quality

**Use when:**
- Snowflake costs are higher than expected
- Building DBT models with data quality checks
- Designing fact and dimension tables
- Optimizing query performance in Snowflake
- Right-sizing warehouses for workloads

[View Skill Documentation](skills/data_engineering/SKILL.md)

### Nix/NixOS Development

**Focus:** Package development and reproducible system configuration

**Capabilities:**
- Nix package development (derivations, builders)
- Language-specific packaging (Rust, Python, Node.js)
- Flakes and modern Nix workflows
- NixOS module configuration
- Nixpkgs contributions and testing
- Build troubleshooting and dependency resolution
- Reproducible development environments

**Common Workflows:**
- Creating new Nix packages
- Writing NixOS modules and services
- Managing flake-based projects
- Contributing to nixpkgs
- Debugging build failures
- Setting up development shells

**Use when:**
- Packaging software for Nix/NixOS
- Writing system configurations
- Contributing to nixpkgs
- Creating reproducible builds
- Managing development environments

[View Skill Documentation](skills/nix/SKILL.md)

### Documentation Writing

**Focus:** Clear, natural technical writing

**Capabilities:**
- Natural, conversational tone
- Avoiding AI-generated phrases and buzzwords
- Structured documentation (READMEs, API docs, code comments)
- Clarity principles (active voice, concrete examples, specific numbers)
- Effective error messages
- CHANGELOG formatting
- Technical accuracy with readability

**Writing Principles:**
- Use natural voice, not corporate speak
- Replace "leverage" with "use", "utilize" with "use"
- Avoid buzzwords: robust, cutting-edge, synergy, paradigm shift
- Use concrete examples instead of vague descriptions
- Write in active voice and present tense
- Provide specific numbers and metrics
- Make error messages actionable

**Use when:**
- Writing or reviewing READMEs
- Creating API documentation
- Writing code comments
- Drafting changelogs
- Crafting error messages
- Reviewing technical content for clarity

[View Skill Documentation](skills/documentation/SKILL.md)

## Repository Structure

```
randoneering-agent-guide/
├── skills/                                    # Domain-specific skill modules
│   ├── pg_optimization/                       # PostgreSQL performance
│   │   ├── SKILL.md                           # Core workflows and quick reference
│   │   └── references/                        # Deep-dive documentation
│   │       ├── postgresql_conf_tuning.md      # Configuration parameters
│   │       ├── query_optimization.md          # Query tuning patterns
│   │       ├── cloud_providers.md             # AWS, GCP, Azure guidance
│   │       └── diagnostic_queries.md          # Monitoring queries
│   ├── pg_design/                             # PostgreSQL architecture
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── schema_design.md               # Data modeling patterns
│   │       ├── partitioning.md                # Partitioning strategies
│   │       ├── ha_replication.md              # High availability
│   │       └── multi_tenancy.md               # Multi-tenant patterns
│   ├── data_engineering/                      # Snowflake and DBT
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── snowflake_caching.md           # Caching layers
│   │       ├── snowflake_warehouse_sizing.md  # Cost optimization
│   │       └── dbt_testing_patterns.md        # Data quality tests
│   ├── nix/                                   # Nix/NixOS development
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── advanced-patterns.md           # Advanced techniques
│   │       └── troubleshooting.md             # Build debugging
│   └── documentation/                         # Technical writing
│       └── SKILL.md                           # Writing guidelines
├── .claude/
│   └── CLAUDE.md                              # Project-specific configuration template
├── README.md                                  # This file
└── LICENSE                                    # GPLv3
```

## Using These Skills

### With Claude Code

These skills are designed to be referenced when working with Claude Code on relevant technical tasks. Each skill provides:

1. **Quick Reference** - Core concepts and common commands in the main SKILL.md
2. **Detailed Guides** - Comprehensive documentation in the references/ subdirectory
3. **Workflows** - Step-by-step procedures for common tasks
4. **Best Practices** - Production-tested patterns and anti-patterns
5. **Troubleshooting** - Common issues and solutions

### Reading the Skills

Each skill follows a consistent structure:

**SKILL.md** - Start here for:
- Overview of capabilities
- Quick reference tables
- Common workflows
- When to use this skill

**references/** - Dive deeper for:
- Comprehensive parameter guides
- Detailed implementation patterns
- Example configurations
- Troubleshooting guides

### Example: Optimizing a Slow PostgreSQL Query

1. **Start with the workflow** in `skills/pg_optimization/SKILL.md`
2. **Analyze the query** using patterns from `references/query_optimization.md`
3. **Run diagnostic queries** from `references/diagnostic_queries.md`
4. **Tune configuration** if needed using `references/postgresql_conf_tuning.md`
5. **Check cloud-specific settings** in `references/cloud_providers.md` if using RDS/Cloud SQL

## Skill Coverage Matrix

| Domain | Configuration | Performance | Architecture | Cloud | Monitoring | Documentation |
|--------|---------------|-------------|--------------|-------|------------|---------------|
| **PostgreSQL** | ✓ | ✓ | ✓ | ✓ | ✓ | - |
| **Snowflake** | ✓ | ✓ | ✓ | ✓ | ✓ | - |
| **DBT** | ✓ | ✓ | ✓ | - | ✓ | - |
| **Nix** | ✓ | - | ✓ | - | ✓ | - |
| **Writing** | - | - | - | - | - | ✓ |

## Key Features

- **Production-Tested Patterns**: Real-world solutions from operational experience
- **Comprehensive Workflows**: Step-by-step procedures for common tasks
- **Cloud-Ready**: Specific guidance for AWS RDS, GCP Cloud SQL, Azure Database
- **Best Practices**: Industry-standard patterns with rationale
- **Anti-Patterns**: Common mistakes to avoid with explanations
- **Quick Reference**: Fast lookup tables for parameters and commands
- **Deep Documentation**: Detailed technical content for complex topics
- **Troubleshooting Guides**: Solutions to common problems

## Project-Specific Configuration

The `.claude/CLAUDE.md` template provides a framework for customizing Claude's behavior for specific projects. Use it to:

- Define project context (tech stack, architecture, constraints)
- Document database configurations (instance type, workload, multi-tenancy model)
- Establish development guidelines (code patterns, testing requirements)
- Set deployment procedures (CI/CD, migration strategy)
- Define team conventions (naming, code review, monitoring)

Copy `.claude/CLAUDE.md` to your project root and customize for project-specific rules.

## Use Cases by Role

### Database Administrators
- Tune PostgreSQL for specific workloads (OLTP vs Analytics)
- Implement high availability with streaming replication
- Monitor database health and replication lag
- Manage vacuum and bloat
- Design backup and recovery strategies
- Optimize cloud-hosted instances (RDS, Cloud SQL, Azure)

### Data Engineers
- Design STAR schemas for data warehouses
- Optimize Snowflake warehouse costs
- Implement DBT models with comprehensive testing
- Leverage Snowflake caching layers
- Right-size warehouses for performance and cost
- Build data quality pipelines

### Backend Developers
- Design efficient database schemas
- Optimize query performance
- Implement table partitioning for large datasets
- Understand index design patterns
- Choose appropriate multi-tenancy patterns
- Write performant application queries

### DevOps Engineers
- Package software with Nix
- Configure NixOS systems declaratively
- Manage flake-based projects
- Create reproducible development environments
- Contribute to nixpkgs
- Debug build failures

### Technical Writers
- Write clear, natural documentation
- Avoid AI-generated phrases
- Structure READMEs effectively
- Create actionable error messages
- Format changelogs consistently
- Balance technical accuracy with readability

## Common Scenarios

### Scenario 1: Slow PostgreSQL Query

**Problem**: Application queries are timing out

**Approach**:
1. Use `pg_optimization` skill to analyze query with EXPLAIN
2. Check for missing indexes using diagnostic queries
3. Review query patterns in `references/query_optimization.md`
4. Consider schema changes from `pg_design` skill if needed

### Scenario 2: High Snowflake Costs

**Problem**: Snowflake warehouse costs are higher than expected

**Approach**:
1. Use `data_engineering` skill to review warehouse sizing
2. Check `references/snowflake_caching.md` for optimization opportunities
3. Analyze query patterns and optimize for result cache
4. Right-size warehouses using guidance in `references/snowflake_warehouse_sizing.md`

### Scenario 3: Multi-Tenant SaaS Design

**Problem**: Need to architect database for SaaS application

**Approach**:
1. Use `pg_design` skill to review multi-tenancy patterns
2. Read `references/multi_tenancy.md` for detailed comparison
3. Choose pattern based on requirements (isolation, scalability, cost)
4. Implement with appropriate RLS policies or schema separation

### Scenario 4: Creating Nix Package

**Problem**: Need to package custom software for NixOS

**Approach**:
1. Use `nix` skill for package development workflow
2. Follow patterns in SKILL.md for derivation creation
3. Reference `references/advanced-patterns.md` for complex cases
4. Test using guidance from skill documentation

### Scenario 5: Writing Technical Documentation

**Problem**: README needs improvement for clarity

**Approach**:
1. Use `documentation` skill to review writing principles
2. Replace buzzwords with natural language
3. Add concrete examples and specific numbers
4. Structure content using skill guidelines
5. Ensure error messages are actionable

## Technology Reference

### PostgreSQL
- **Versions**: 12, 13, 14, 15, 16 (patterns apply broadly)
- **Cloud Providers**: AWS RDS, GCP Cloud SQL, Azure Database for PostgreSQL
- **Extensions**: pg_stat_statements, pg_trgm, btree_gin
- **Tools**: psql, EXPLAIN, pg_stat_statements, Patroni, PgBouncer

### Snowflake
- **Features**: Result cache, metadata cache, warehouse cache
- **Scaling**: Warehouse sizing (XS to 6XL), multi-cluster warehouses
- **Optimization**: Query pruning, clustering, materialized views

### DBT
- **Version**: dbt-core and dbt-cloud patterns
- **Testing**: Generic tests, custom tests, schema tests
- **Models**: Incremental, snapshots, ephemeral

### Nix
- **Version**: Nix 2.x with flakes
- **Tools**: nix-build, nix-shell, nixos-rebuild, nix flake
- **Languages**: Rust, Python, Node.js, Go, Haskell

## Contributing

This repository represents knowledge accumulated from production experience with data systems and infrastructure. Suggestions for improvements are welcome via issues or pull requests.

When contributing:
- Follow the existing structure (SKILL.md + references/)
- Include practical examples and workflows
- Document both patterns and anti-patterns
- Test recommendations in real environments
- Use natural, clear language (see documentation skill)

## Maintenance

**Status**: Actively maintained

**Recent Updates**:
- Added documentation writing skill
- Enhanced Nix skill with troubleshooting guide
- Updated PostgreSQL patterns for version 16
- Expanded Snowflake caching documentation

## License

GNU General Public License v3.0 - see [LICENSE](LICENSE) file for details.

## Related Resources

### PostgreSQL
- [Official PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [PostgreSQL Wiki](https://wiki.postgresql.org/)
- [PGTune](https://pgtune.leopard.in.ua/) - Configuration calculator
- [EXPLAIN Visualizer](https://explain.depesz.com/)

### Snowflake
- [Snowflake Documentation](https://docs.snowflake.com/)
- [Snowflake Community](https://community.snowflake.com/)
- [Snowflake University](https://learn.snowflake.com/)

### DBT
- [DBT Documentation](https://docs.getdbt.com/)
- [DBT Discourse](https://discourse.getdbt.com/)
- [DBT Package Hub](https://hub.getdbt.com/)

### Nix
- [NixOS Manual](https://nixos.org/manual/nixos/stable/)
- [Nixpkgs Manual](https://nixos.org/manual/nixpkgs/stable/)
- [Nix Pills](https://nixos.org/guides/nix-pills/)
- [NixOS Wiki](https://nixos.wiki/)
- [Nix Package Search](https://search.nixos.org/)

### Technical Writing
- [Google Developer Documentation Style Guide](https://developers.google.com/style)
- [Microsoft Writing Style Guide](https://learn.microsoft.com/en-us/style-guide/welcome/)
- [GitLab Documentation Style Guide](https://docs.gitlab.com/ee/development/documentation/styleguide/)

## Contact

For questions, suggestions, or discussions about these skills:

**Owner**: justin@randoneering.tech

## Acknowledgments

These skills synthesize knowledge from:
- Years of production database operations
- Cloud provider best practices (AWS, GCP, Azure)
- Open source community contributions
- Official vendor documentation
- Hard-won operational experience

Special thanks to the PostgreSQL, Snowflake, DBT, and NixOS communities for their excellent documentation and collective wisdom.

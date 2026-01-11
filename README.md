# Randoneering Agent Guide

A comprehensive collection of Claude Code skills, configurations, and best practices focused on data engineering, PostgreSQL database management, and Nix development.

## Overview

This repository contains a curated set of skills designed to enhance Claude Code's capabilities when working with data infrastructure, databases, and system configuration. Each skill provides deep domain expertise with detailed workflows, reference materials, and battle-tested patterns.

## Skills

### Data Engineering

**Focus:** Snowflake and DBT data warehouse engineering

**Capabilities:**
- Query result caching optimization
- Warehouse sizing and cost optimization
- DBT data quality testing patterns
- STAR schema design and validation

**Use when:**
- Optimizing Snowflake query performance
- Right-sizing warehouses for cost efficiency
- Implementing DBT models with data quality checks
- Designing dimensional models

[View Skill Documentation](skills/data_engineering/SKILL.md)

### PostgreSQL Optimization

**Focus:** Database performance tuning and query optimization

**Capabilities:**
- Configuration tuning (postgresql.conf)
- Query optimization and EXPLAIN analysis
- Cloud provider management (AWS RDS, GCP Cloud SQL, Azure)
- Database health monitoring
- Index design and analysis
- Vacuum and bloat management
- Replication monitoring

**Use when:**
- Tuning PostgreSQL configuration parameters
- Analyzing and optimizing slow queries
- Managing cloud-hosted PostgreSQL instances
- Monitoring database health metrics
- Troubleshooting performance issues

[View Skill Documentation](skills/pg_optimization/SKILL.md)

### PostgreSQL Architecture

**Focus:** Database design and high availability

**Capabilities:**
- Schema design and data modeling
- Table partitioning (range, list, hash, multi-level)
- High availability architectures (streaming replication, Patroni)
- Multi-tenancy patterns (shared schema, separate schemas, separate databases)
- Connection pooling and load balancing
- Disaster recovery planning

**Use when:**
- Designing database schemas
- Implementing table partitioning strategies
- Setting up HA/DR with replication
- Building multi-tenant SaaS applications
- Architecting scalable PostgreSQL systems

[View Skill Documentation](skills/pg_design/SKILL.md)

### Nix/NixOS Development

**Focus:** Package development and system configuration

**Capabilities:**
- Nix package development
- Nixpkgs contributions
- NixOS module configuration
- Flakes management
- Derivation building
- Build troubleshooting

**Use when:**
- Developing Nix packages
- Contributing to nixpkgs
- Writing NixOS modules
- Creating flake-based projects
- Debugging Nix build failures

[View Skill Documentation](skills/nix/SKILL.md)

## Repository Structure

```
randoneering-agent-guide/
├── skills/
│   ├── data_engineering/
│   │   ├── SKILL.md                          # Skill definition
│   │   └── references/                       # Detailed documentation
│   │       ├── snowflake_caching.md
│   │       ├── snowflake_warehouse_sizing.md
│   │       └── dbt_testing_patterns.md
│   ├── pg_optimization/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── postgresql_conf_tuning.md
│   │       ├── query_optimization.md
│   │       ├── cloud_providers.md
│   │       └── diagnostic_queries.md
│   ├── pg_design/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── schema_design.md
│   │       ├── partitioning.md
│   │       ├── ha_replication.md
│   │       └── multi_tenancy.md
│   └── nix/
│       ├── SKILL.md
│       └── references/
│           ├── advanced-patterns.md
│           └── troubleshooting.md
├── .claude/
│   └── CLAUDE.md                              # Project-specific Claude rules template
└── README.md
```

## Using These Skills with Claude Code

### Installation

1. Clone this repository to your local machine:
   ```bash
   git clone https://github.com/yourusername/randoneering-agent-guide.git
   ```

2. Reference the skills directory in your Claude Code configuration.

### Workflow

Each skill follows a consistent structure:

1. **Skill Definition** - The main `SKILL.md` file contains:
   - Core capabilities overview
   - Quick reference guides
   - Common workflows
   - Best practices and patterns

2. **Reference Materials** - Detailed documentation in the `references/` directory:
   - Deep-dive technical content
   - Comprehensive parameter guides
   - Example implementations
   - Troubleshooting guides

3. **Usage Pattern**:
   - Start with the `SKILL.md` for quick reference
   - Dive into specific `references/` files for detailed information
   - Follow documented workflows for common tasks

### Example Usage

When working on a PostgreSQL performance issue:

1. Start with `skills/pg_optimization/SKILL.md` for the overall workflow
2. Reference `references/query_optimization.md` for specific optimization patterns
3. Use `references/diagnostic_queries.md` for monitoring queries
4. Apply recommendations from `references/postgresql_conf_tuning.md` for configuration

## Skill Coverage Matrix

| Domain | Configuration | Optimization | Architecture | Cloud | Monitoring |
|--------|--------------|--------------|--------------|-------|------------|
| **PostgreSQL** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Snowflake** | ✓ | ✓ | - | ✓ | ✓ |
| **DBT** | ✓ | - | ✓ | - | ✓ |
| **Nix** | ✓ | - | ✓ | - | ✓ |

## Key Features

- **Comprehensive Workflows**: Step-by-step procedures for common tasks
- **Best Practices**: Industry-standard patterns and anti-patterns
- **Cloud-Ready**: Specific guidance for AWS, GCP, and Azure
- **Production-Tested**: Real-world patterns and troubleshooting guides
- **Quick Reference**: Fast lookup for common commands and configurations
- **Deep Documentation**: Detailed reference materials for complex topics

## Contributing

This is a personal collection of skills and patterns developed through real-world experience. If you'd like to suggest improvements or report issues, please open an issue or pull request.

## Customization

The `.claude/CLAUDE.md` file provides a template for project-specific Claude configurations. Copy and customize this for your own projects to:

- Define project-specific context
- Set database configurations
- Establish development guidelines
- Document deployment procedures
- Define team conventions

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Use Cases

### Data Engineers
- Optimize Snowflake warehouse costs
- Implement robust DBT testing strategies
- Design efficient STAR schemas
- Manage query result caching

### Database Administrators
- Tune PostgreSQL configuration for workload
- Implement high availability architectures
- Monitor database health metrics
- Optimize query performance
- Design multi-tenant systems

### DevOps Engineers
- Package software with Nix
- Configure NixOS systems
- Manage flake-based projects
- Contribute to nixpkgs

### Backend Developers
- Design efficient database schemas
- Implement table partitioning
- Optimize application queries
- Understand database performance characteristics

## Related Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Snowflake Documentation](https://docs.snowflake.com/)
- [DBT Documentation](https://docs.getdbt.com/)
- [NixOS Manual](https://nixos.org/manual/nixos/stable/)
- [Nixpkgs Manual](https://nixos.org/manual/nixpkgs/stable/)

## Acknowledgments

These skills represent knowledge accumulated from years of working with production data systems, database optimization, and infrastructure management. They synthesize best practices from official documentation, community wisdom, and hard-won operational experience.

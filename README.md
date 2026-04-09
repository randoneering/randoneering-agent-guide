# Randoneering Agent Guide

Skills, agents, hooks, commands, and integration docs for Claude Code and other coding agents.

## Skills

| Category | Skills |
|----------|--------|
| **Core Workflow** | [using-superpowers](skills/using-superpowers/), [brainstorming](skills/brainstorming/), [writing-plans](skills/writing-plans/), [executing-plans](skills/executing-plans/) |
| **Development Workflow** | [test-driven-development](skills/test-driven-development/), [subagent-driven-development](skills/subagent-driven-development/), [dispatching-parallel-agents](skills/dispatching-parallel-agents/), [using-git-worktrees](skills/using-git-worktrees/), [finishing-a-development-branch](skills/finishing-a-development-branch/) |
| **Quality** | [systematic-debugging](skills/systematic-debugging/), [damage-control](skills/damage-control/), [verification-before-completion](skills/verification-before-completion/) |
| **Code Review** | [requesting-code-review](skills/requesting-code-review/), [receiving-code-review](skills/receiving-code-review/) |
| **Writing** | [documentation](skills/documentation/), [writing-skills](skills/writing-skills/), [writing-style](skills/writing-style/), [resume-tailor](skills/resume-tailor/) |
| **Data** | [dbt](skills/dbt/), [postgres](skills/postgres/), [snowflake](skills/snowflake/), [clickhouse](skills/clickhouse/), [neon](skills/neon/) |
| **Development Stacks** | [python](skills/python/), [nix](skills/nix/), [automation](skills/automation/), [flox](skills/flox/) |
| **Cloud & Infrastructure** | [cloudflare](skills/cloudflare/), [hashicorp](skills/hashicorp/) |
| **Security** | [trail_of_bits](skills/trail_of_bits/), [sentry](skills/sentry/) |

## Agents

| Category | Contents |
|----------|----------|
| **Engineering** | task-focused specialists for implementation, architecture, security, DevOps, and review |
| **Marketing** | content, campaign, paid media, SEO, and growth agents |
| **Product** | research, prioritization, feedback synthesis, and product strategy agents |
| **Project Management** | planning, tracking, workflow, and delivery-oriented agents |
| **Specialized** | domain-specific specialists across sales, finance, legal, and other functions |
| **Spatial Computing** | XR, AR/VR, and spatial interface agents |
| **Academic** | research, writing, and analysis agents for academic work |
| **Testing** | evidence, API, accessibility, performance, and validation agents |
| **Support** | reporting, compliance, infrastructure, finance, and support agents |
| **Strategy** | orchestration docs, playbooks, runbooks, and coordination guides |
| **Integrations** | converted formats and install docs for supported agent tools |

## Structure

```
agents/
├── {category}/
│   └── <domain>-<role>.md   # Agent definition
│
skills/
├── {skill}/
│   ├── SKILL.md           # Top-level skill
│   └── references/        # Supporting docs (optional)
└── {domain}/
    └── {skill}/
        ├── SKILL.md       # Domain-specific skill
        └── references/    # Supporting docs (optional)
```

## Usage

- Copy skills to your project's `.claude/skills/` directory or reference them in your `CLAUDE.md`
- Copy agents from `agents/` into the target tool's agent location, or use the docs in `agents/integrations/`

## Configuration

The `.claude/CLAUDE.md` template provides project-specific agent configuration. Copy it to your project and customize.

## License

GPLv3 - see [LICENSE](LICENSE)

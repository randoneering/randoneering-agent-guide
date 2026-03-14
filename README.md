# Randoneering Agent Guide

Skills, agents, hooks, commands, and integration docs for Claude Code and other coding agents.

## Skills

| Category | Skills |
|----------|--------|
| **Data** | [dbt](skills/dbt/), [postgres](skills/postgres/), [snowflake](skills/snowflake/) |
| **Development** | [python](skills/python/), [nix](skills/nix/), [automation](skills/automation/) |
| **Process** | [brainstorming](skills/brainstorming/), [writing-plans](skills/writing-plans/), [executing-plans](skills/executing-plans/) |
| **Quality** | [systematic-debugging](skills/systematic-debugging/), [damage-control](skills/damage-control/), [verification-before-completion](skills/verification-before-completion/) |
| **Code Review** | [requesting-code-review](skills/requesting-code-review/), [receiving-code-review](skills/receiving-code-review/) |
| **Writing** | [documentation](skills/documentation/), [writing-skills](skills/writing-skills/), [writing-style](skills/writing-style/) |

## Agents

| Category | Contents |
|----------|----------|
| **Engineering** | task-focused specialists for implementation, architecture, security, DevOps, and review |
| **Design** | UX, UI, research, brand, storytelling, and visual design agents |
| **Product** | research, prioritization, feedback synthesis, and product strategy agents |
| **Project Management** | planning, tracking, workflow, and delivery-oriented agents |
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
│   ├── SKILL.md           # Main skill definition
│   └── references/        # Supporting docs (optional)
```

## Usage

- Copy skills to your project's `.claude/skills/` directory or reference them in your `CLAUDE.md`
- Copy agents from `agents/` into the target tool's agent location, or use the docs in `agents/integrations/`

## Configuration

The `.claude/CLAUDE.md` template provides project-specific agent configuration. Copy it to your project and customize.

## License

GPLv3 - see [LICENSE](LICENSE)

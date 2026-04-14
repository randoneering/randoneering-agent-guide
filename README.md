# Randoneering Agent Guide

Skills, agents, hooks, commands, and integration docs for OpenCode, pi, and other coding agents.

## Skills

| Category | Skills |
|----------|--------|
| **Core Workflow** | [using-superpowers](skills/using-superpowers/), [brainstorming](skills/brainstorming/), [writing-plans](skills/writing-plans/), [executing-plans](skills/executing-plans/) |
| **Development Workflow** | [test-driven-development](skills/test-driven-development/), [subagent-driven-development](skills/subagent-driven-development/), [dispatching-parallel-agents](skills/dispatching-parallel-agents/), [using-git-worktrees](skills/using-git-worktrees/), [finishing-a-development-branch](skills/finishing-a-development-branch/) |
| **Quality** | [systematic-debugging](skills/systematic-debugging/), [damage-control](skills/damage-control/), [verification-before-completion](skills/verification-before-completion/) |
| **Code Review** | [requesting-code-review](skills/requesting-code-review/), [receiving-code-review](skills/receiving-code-review/) |
| **Writing** | [documentation-writing](skills/documentation-writing/), [writing-skills](skills/writing-skills/), [writing-style](skills/writing-style/), [resume-tailor](skills/resume-tailor/) |
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
└── {category}/
    ├── {skill}/
    │   ├── SKILL.md       # Skill definition
    │   └── references/    # Supporting docs (optional)
    └── README.md          # Category or package notes (optional)
```

## Usage

- OpenCode: copy skills into `.claude/skills/` or load them from a shared repo path referenced by `AGENTS.md`
- pi: copy skills into `.pi/skills/` or `.agents/skills/`, or point pi at this repo via its `skills` setting
- Agent files in `agents/` are plain Markdown prompts with portable `name` and `description` frontmatter; use them as prompt templates, imported agents, or source material for tool-specific packaging

## Configuration

- OpenCode reads project instructions from `AGENTS.md`
- pi reads `AGENTS.md` and also supports `CLAUDE.md`
- Use repo-local `AGENTS.md` for shared instructions when targeting both harnesses

## Compatibility

- Skills use the Agent Skills `SKILL.md` structure, which both OpenCode and pi can consume
- Skills may include optional frontmatter such as `allowed-tools`, `compatibility`, `metadata`, or `user-invocable`; pi ignores unknown fields and OpenCode can still use the instructions
- Agent files keep only the portable frontmatter subset: `name` and `description`
- Runtime features still vary by harness. Skills that mention subagents, todo tools, or platform-specific commands may require harness-specific adaptation during execution

## License

GPLv3 - see [LICENSE](LICENSE)

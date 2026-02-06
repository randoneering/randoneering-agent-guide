# Randoneering Agent Guide

Skills, hooks, and commands for Claude Code and other coding agents.

## Skills

| Category | Skills |
|----------|--------|
| **Data** | [dbt](skills/dbt/), [postgres](skills/postgres/), [snowflake](skills/snowflake/) |
| **Development** | [python](skills/python/), [nix](skills/nix/), [automation](skills/automation/) |
| **Process** | [brainstorming](skills/brainstorming/), [writing-plans](skills/writing-plans/), [executing-plans](skills/executing-plans/) |
| **Quality** | [systematic-debugging](skills/systematic-debugging/), [damage-control](skills/damage-control/), [verification-before-completion](skills/verification-before-completion/) |
| **Code Review** | [requesting-code-review](skills/requesting-code-review/), [receiving-code-review](skills/receiving-code-review/) |
| **Writing** | [documentation](skills/documentation/), [writing-skills](skills/writing-skills/), [writing-style](skills/writing-style/) |

## Structure

```
skills/
├── {skill}/
│   ├── SKILL.md           # Main skill definition
│   └── references/        # Supporting docs (optional)
```

## Usage

Copy skills to your project's `.claude/skills/` directory or reference them in your `CLAUDE.md`.

## Configuration

The `.claude/CLAUDE.md` template provides project-specific agent configuration. Copy it to your project and customize.

## License

GPLv3 - see [LICENSE](LICENSE)

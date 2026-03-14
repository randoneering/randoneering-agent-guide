# Project Overview

Reusable skills, agents, hooks, commands, and integration docs for Claude Code and other coding agents.

## Project Context

**Tech Stack:**
- Markdown
- Shell
- Python
- TypeScript

**Primary Use Case:**
Maintain the shared library in `skills/`, `agents/`, and `.claude/` so it can be copied, installed, or adapted into other agent-driven projects.

## Repository Structure

- `skills/`: reusable Claude-style skills and references
- `agents/`: agent definitions, strategy docs, runbooks, and tool integrations
- `.claude/skills/`: project-local skill copies and active skill development
- `.claude/commands/`: slash commands for repo workflows
- `.claude/templates/`: starter templates for project rules

## Critical Rules

- Match existing naming, tone, and folder layout
- Keep docs concise; prefer short sections and direct bullets
- Update related indexes or READMEs when adding skills, agents, or integrations
- Do not invent generated outputs; regenerate them only when the workflow requires it
- Preserve mirrored content intentionally when a change belongs in both `skills/` and `.claude/skills/`

## Common Tasks

### Adding or Updating a Skill

- Edit the canonical skill files in the appropriate `skills/` or `.claude/skills/` location
- Keep `SKILL.md` concise and action-oriented
- Update supporting references only when they add real value
- Reflect new skills in repo docs when discoverability changes

### Adding or Updating an Agent

- Place agent definitions under the correct `agents/` category
- Keep naming consistent with the existing `<domain>-<role>.md` pattern
- Update nearby strategy or integration docs when the new agent affects orchestration or installation

## Notes for Claude

- Check both `skills/` and `.claude/skills/` before assuming a skill exists in only one place
- Check `agents/` before describing the available agent catalog or integration coverage
- Prefer small, targeted doc edits over broad rewrites

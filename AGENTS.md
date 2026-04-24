# Project Overview 
Reusable skills, agents, hooks, commands, and integration docs for coding agents. 

## Project Context 

**Tech Stack:** Markdown, Shell, Python, TypeScript 

**Primary Use Case:** Maintain the shared library in `skills/` and `agents/` so it can be copied, installed, or adapted into other agent-driven projects. 

## Repository Structure 

- `skills/` — reusable skills and references (24 categories) 
- `agents/` — agent definitions, strategy docs, runbooks, and integrations (17 categories) 

## Critical Rules 

- Match existing naming, tone, and folder layout 
- Keep docs concise — short sections, direct bullets, no filler 
- Update related indexes or READMEs when adding skills, agents, or integrations 
- Do not invent generated outputs; regenerate only when the workflow requires it 
- When you need to search docs, use Context7 

## Damage Control 

Safety-first rules that apply to every session. No exceptions. 

### Blocked Commands 

Never run destructive commands without explicit user approval: 

- `rm -rf`, `rm -r`, `rm` — always ask before deleting files or directories 
- `git reset --hard`, `git clean -fd`, `git push --force` — irreversible git operations 
- `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, `DELETE` without a `WHERE` clause — destructive SQL 
- `chmod -R 777`, `chown -R` — broad permission changes 
- `> file` (redirect overwriting a file) — silent data loss 

When the user asks you to delete, remove, or clean up files, **stop and confirm** the exact paths and scope before proceeding. 

### Verification on Vague Requests 

Always ask for clarification when a request is ambiguous or could be interpreted multiple ways: 

- "Clean this up" — ask what specifically should change 
- "Fix the errors" — confirm which errors and which files 
- "Delete the old stuff" — ask which files/directories, list them first 
- "Reset everything" — confirm scope (repo state, database, config, all of the above?) 
- "Update the config" — ask which values and to what 

**Rule:** If you are unsure about scope, targets, or intent — ask first, act second. 

### Protected Paths 

Never write to or modify these without explicit approval: 

- `.env`, `credentials.json`, `*.pem`, `*.key` — secrets and credentials 
- `~/.ssh/`, `~/.gnupg/` — authentication material 
- System configs (`/etc/`, `~/.bashrc`, `~/.zshrc`) — environment-altering files 

## Documentation Standards 

Pulled from the `documentation-writing` skill: 

- Write in active voice, present tense 
- Use concrete numbers over vague claims ("reduces latency by 40ms" not "significantly faster") 
- Avoid AI buzzwords: leverage, utilize, robust, seamless, innovative, comprehensive, cutting-edge 
- Avoid AI filler phrases: moreover, furthermore, it is important to note, in today's fast-paced world 
- Comments explain **why**, not **what** 
- Error messages should be specific and actionable 
- Read-aloud test: if it doesn't sound like something you'd say, rewrite it 

## Coding Style 

### Python 

From the `python-workflow` skill: 

- **Package manager:** Use `uv` exclusively; run via `uv run python`, never manual `.venv` paths 
- **Style:** PEP 8, 88-char line length, Ruff for linting and formatting 
- **Type hints:** Required on all parameters and return values (use `list[str]`, `dict[str, Any]` for 3.9+) 
- **Naming:** PascalCase classes, snake_case functions/variables, UPPER_SNAKE_CASE constants 
- **Comments:** Single-line `#` only, no multi-line `""" """` blocks 
- **Validation:** Pydantic for data models, `pathlib.Path` for file paths 
- **Testing:** pytest with fixtures, tests in `tests/unit/` and `tests/integration/` 
- **Errors:** Specific exception types with meaningful messages; never remove public methods for lint fixes 
- **Config:** `pyproject.toml` as single source of truth; `.env` files via python-dotenv (never committed) 

### Shell 

- Quote file paths containing spaces 
- Use `set -euo pipefail` in scripts 
- Prefer long-form flags for readability (`--recursive` over `-r`) 

### Markdown 

- Use GitHub-flavored markdown 
- One sentence per line in source for clean diffs 
- Prefer tables for structured data, lists for sequences 

### TypeScript 

- Strict mode enabled 
- Explicit return types on exported functions 
- Prefer `const` over `let`; avoid `any` 

## Skill Guidelines 

From the `writing-skills` skill: 

- **Structure:** Every skill needs a `SKILL.md` — concise, action-oriented 
- **Naming:** Lowercase with hyphens, verb-first when possible (`creating-skills` not `skill-creation`) 
- **Descriptions:** Start with "Use when..." — describe triggering conditions, not the workflow 
- **Content:** One excellent example beats many mediocre ones; inline code under 50 lines, separate file for heavy reference 
- **Testing:** No skill without a failing test first (TDD for documentation) 
- **Discovery:** Put searchable terms (error messages, symptoms, tool names) early and often 

### Adding or Updating a Skill 

- Edit canonical files in the appropriate `skills/` location 
- Keep `SKILL.md` under 500 words when possible 
- Update supporting references only when they add real value 
- Reflect new skills in repo docs when discoverability changes 

### Adding or Updating an Agent 

- Place definitions under the correct `agents/` category 
- Follow the `<domain>-<role>.md` naming pattern 
- Update strategy or integration docs when the new agent affects orchestration 

## Web Search 

- Always pass `workflow: "none"` when calling `web_search` — skip the browser curator by default 
- Use `workflow: "summary-review"` only when explicitly asked to curate results 

## Tool and Skill Routing 

### dbt 

- Load dbt skills (`skills/dbt/`) before any dbt work — models, tests, semantic layer, migrations, job troubleshooting 
- Use the dbt MCP server tools for project introspection, running commands, querying metrics, and fetching docs 
- Use `dbt show` via MCP to validate SQL against the warehouse without materializing 
- Use dbt product docs tools (`search_product_docs`, `get_product_doc_pages`) for documentation lookups 

### Snowflake 

- Load Snowflake skills (`skills/snowflake/`) for Streamlit apps, Cortex agents, semantic views, ML workflows, cost management, and Postgres instances 
- Use the Snowflake MCP server (`snowflake_sql_exec`) to run SQL directly against the warehouse 
- Load sub-skills as needed: `developing-with-streamlit`, `agent-optimization`, `semantic-view-optimization`, `machine-learning`, `cost-management` 

### Orchestra 

- Use the Orchestra MCP server tools for pipeline operations — listing runs, starting pipelines, checking status, viewing logs, and managing artifacts 
- Use `orchestra-docs_search_orchestra_documentation` to look up Orchestra platform docs before guessing 

## Notes for Agents 

- Check `skills/` before assuming a skill exists in only one place 
- Check `agents/` before describing the available catalog or integration coverage 
- Prefer small, targeted doc edits over broad rewrites 
- When you need to search docs, use Context7 
- Load relevant skills before starting work — they contain tested patterns and prevent common mistakes


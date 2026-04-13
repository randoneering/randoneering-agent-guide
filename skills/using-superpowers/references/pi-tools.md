# Pi Tool Mapping

Skills in this repo often mention Claude Code or OpenCode tool names.
When you use them in pi, map them to pi's built-in behavior or the nearest equivalent.

| Skill references | Pi equivalent |
|-----------------|---------------|
| `Skill` tool | Use `/skill:name` or `read` the `SKILL.md` directly |
| `Read`, `Write`, `Edit` | Pi built-in `read`, `write`, `edit` |
| `Bash` | Pi built-in `bash` |
| `Grep` | Pi built-in `grep` |
| `Glob` or `find files` | Pi built-in `find` or `ls` |
| `TodoWrite` | Use a `TODO.md` file or your own extension |
| `Task` or subagent dispatch | No built-in equivalent. Use a pi extension, a second pi session, or execute the workflow inline |

## Important Gaps

- Pi does not ship built-in subagents.
- Pi does not ship built-in todo tracking.
- Pi loads skills via the Agent Skills standard and is lenient about unknown frontmatter fields.

## Practical Rule

If a skill depends on a harness feature pi does not provide, keep the skill content but adapt the execution method.
Preserve the workflow intent even when the exact tool name changes.

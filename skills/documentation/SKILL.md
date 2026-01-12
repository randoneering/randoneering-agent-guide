---
name: documentation-writing
description: "Documentation writing guidelines. Triggers: README, CHANGELOG, API docs, technical writing, user guides, code comments. Covers natural writing style, AI phrase avoidance, structure, clarity, and audience-appropriate tone."
---

# Documentation Writing

Guidelines for writing clear, natural, human-sounding documentation that avoids AI-typical phrases and maintains professional quality.

## Core Principles

### Natural Voice
- Write as you would explain to a colleague
- Use conversational tone without being casual
- Read aloud test: if it doesn't sound like something you'd say, rewrite it
- Prefer concrete details over vague claims
- Show don't tell: describe actual impacts rather than using adjectives

### Audience First
- Know who reads this: developers, end-users, stakeholders?
- Match technical depth to audience expertise
- Provide context without over-explaining
- Include examples relevant to the audience's work

## AI Phrase Avoidance

**CRITICAL:** These phrases signal AI-generated content. Replace automatically.

### AI Buzzwords to Replace

| Avoid | Use Instead |
|-------|-------------|
| leverage | use, apply, take advantage of |
| synergy | teamwork, working together, combined effect |
| cutting-edge | new, advanced, latest, modern |
| robust | strong, solid, reliable |
| seamlessly | works well, easy to use, smooth |
| utilize | use |
| innovative | new, creative (or describe what's actually new) |
| revolutionary | (describe the specific change) |
| transformative | (describe the actual impact) |
| game-changing | significant, major, substantial |
| scalable solution | expandable, easily adjustable |
| harnessing the power of | use, tap into, apply |

### AI Filler Phrases to Avoid

| Avoid | Replace With |
|-------|-------------|
| moreover / furthermore | also, additionally (or split into two sentences) |
| in conclusion | so, to wrap up, finally |
| it is important to note | (state the point directly) |
| in today's society / fast-paced world | (be specific about time or context) |
| this document will discuss | (start with the topic directly) |
| the impact of X on Y | (describe the effect in concrete terms) |

### Example Transformations

**Bad (AI-typical):**
> "In today's fast-paced world, leveraging cutting-edge technology is crucial. This robust solution seamlessly integrates with existing systems, providing a scalable framework that revolutionizes the industry."

**Good (natural):**
> "This tool works with your existing systems and scales as your needs grow. It reduces deployment time from hours to minutes by automating the configuration process."

## Documentation Structure

### README Files

**Essential sections:**
1. **What it does** (1-2 sentences, no buzzwords)
2. **Quick start** (minimal viable example)
3. **Installation** (step-by-step)
4. **Usage** (common scenarios with examples)
5. **Configuration** (if applicable)
6. **Troubleshooting** (common issues)

**Example opening:**
```markdown
# Project Name

Monitors PostgreSQL database health and sends alerts when metrics exceed thresholds.

## Quick Start

```bash
pip install db-monitor
db-monitor --host localhost --database mydb
```

### API Documentation

**For each endpoint/function:**
- Purpose (what it does and why you'd use it)
- Parameters (types, constraints, defaults)
- Return values (types, structure)
- Examples (real-world usage)
- Error cases (common failures)

**Pattern:**
```markdown
### `create_user(username, email, role=None)`

Creates a new user account and sends a verification email.

**Parameters:**
- `username` (str): Unique username, 3-20 characters
- `email` (str): Valid email address
- `role` (str, optional): User role. Defaults to 'user'

**Returns:**
- `User`: User object with generated ID

**Raises:**
- `ValidationError`: If username exists or email invalid
- `SMTPError`: If verification email fails to send

**Example:**
```python
user = create_user("john_doe", "john@example.com", role="admin")
print(f"Created user: {user.id}")
```

### Code Comments

**Write comments that explain WHY, not WHAT:**

**Bad:**
```python
# Increment counter by 1
counter += 1
```

**Good:**
```python
# Retry after rate limit expires (API allows 100/hour)
counter += 1
```

**When to comment:**
- Non-obvious business logic
- Performance trade-offs
- Security considerations
- Edge cases and assumptions
- Workarounds for external issues

**When not to comment:**
- Obvious operations (`x = 5  # Set x to 5`)
- Well-named functions doing expected things
- Repeated explanations (extract to function with clear name)

### CHANGELOG Format

Use semantic versioning and clear categories:

```markdown
## [1.2.0] - 2025-01-11

### Added
- PostgreSQL 17 compatibility
- Support for connection pooling via pgBouncer

### Changed
- Improved query performance for table bloat detection (10x faster)
- Updated default timeout from 30s to 60s

### Fixed
- Race condition in replication slot monitoring
- Memory leak when processing large result sets

### Deprecated
- `--legacy-mode` flag (removed in 2.0)
```

## Writing Tips

### Clarity Over Brevity
- Be concise but not cryptic
- Spell out acronyms on first use
- Link to related concepts
- Use examples for complex concepts

### Active Voice
**Prefer:** "The function returns an error"
**Over:** "An error is returned by the function"

### Present Tense
**Prefer:** "This function validates input"
**Over:** "This function will validate input"

### Specific Numbers
**Prefer:** "Reduces latency by 40ms"
**Over:** "Significantly faster"

### Concrete Examples
**Prefer:** "For a 1M row table, this query takes 2 seconds"
**Over:** "Performs well on large datasets"

## Common Patterns

### Error Messages
Be specific, actionable, and empathetic:

**Bad:** "Invalid input"
**Good:** "Username must be 3-20 characters (received: 'ab')"

**Bad:** "Connection failed"
**Good:** "Cannot connect to database at localhost:5432. Check that PostgreSQL is running and accepting connections."

### Warnings and Notes
Use sparingly and purposefully:

```markdown
> **Note:** This operation requires superuser privileges.

> **Warning:** Running VACUUM FULL locks the table. Use during maintenance windows only.

> **Tip:** For large datasets (>1M rows), consider partitioning by date.
```

### Migration Guides
When introducing breaking changes:

1. State what changed (specific API/behavior)
2. Show old approach
3. Show new approach
4. Explain reasoning (if not obvious)
5. Provide migration script (if complex)

## Tools and Validation

### Readability Checks
- Read aloud test (does it sound natural?)
- Colleague test (can someone unfamiliar understand it?)
- Beginner test (does it assume too much knowledge?)

### Structure Checks
- Can you find what you need in 30 seconds?
- Are examples copy-pasteable and runnable?
- Is the most common use case covered first?
- Are error messages actionable?

### AI Detection Checks
Scan for these patterns (all are red flags):
- 3+ buzzwords in a paragraph
- Filler phrases at start of sections
- Vague claims without specifics
- Over-formatted with excessive bold/italics
- Lists where prose would be clearer

## Documentation Types

### Technical Specifications
- Be precise and complete
- Define all terms
- Include edge cases
- Provide validation rules
- Use tables for structured data

### User Guides
- Task-oriented structure
- Step-by-step instructions
- Screenshots for UI elements
- Troubleshooting section
- FAQs for common questions

### Architecture Documents
- System overview diagram
- Component interactions
- Data flow
- Technology choices with rationale
- Trade-offs and alternatives considered

### Runbooks
- When to use this procedure
- Prerequisites and access needed
- Step-by-step commands
- Expected output at each step
- Rollback procedure
- Contact for escalation

## Anti-Patterns

### Over-Explanation
**Bad:** "In the modern software development landscape, it is important to note that..."
**Good:** "To deploy, run..."

### Marketing Speak
**Bad:** "Our innovative, game-changing solution leverages cutting-edge AI..."
**Good:** "This tool uses GPT-4 to generate SQL queries from natural language."

### Assumed Context
**Bad:** "Configure the thing as discussed."
**Good:** "Set `max_connections=100` in postgresql.conf"

### Stale Documentation
- Date-stamp complex procedures
- Note version compatibility
- Remove outdated content (don't just mark as deprecated)
- Link to source of truth for volatile info

## Quick Reference

**Before publishing, check:**
- [ ] No AI buzzwords (leverage, synergy, cutting-edge, robust, seamlessly)
- [ ] No AI fillers (moreover, in conclusion, it is important to note)
- [ ] Active voice and present tense
- [ ] Concrete examples with real numbers
- [ ] Audience-appropriate technical depth
- [ ] Examples are copy-pasteable and tested
- [ ] Error cases documented
- [ ] Links work and reference correct versions

**Key principles:**
- Natural conversational tone
- Concrete over abstract
- Examples over explanations
- Show actual impact vs. adjectives
- Read aloud test passes

---

**Note:** For project-specific documentation standards, check `.claude/CLAUDE.md` in the project directory.

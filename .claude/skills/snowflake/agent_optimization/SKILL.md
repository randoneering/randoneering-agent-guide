---
name: agent-optimization
description: "Use for **ALL** requests that mention: create, build, set up, debug, fix, troubleshoot, optimize, improve, evaluate, or analyze a (Cortex) agent. This is the **REQUIRED** entry point - even if the request seems simple. DO NOT attempt to debug (Cortex) agents manually - always invoke this skill first. This skill guides users through creating, auditing, evaluating, and debugging workflows for (Cortex) agents."
---

# Main

## When to Use

When a user wants to create, debug, evaluate, or optimize a (Cortex) agent. This is the entry point for all (Cortex) agent workflows.

## Setup

1. **Load** `agent-system-of-record/SKILL.md`: Required first step for all sessions.
2. **Load** `best-practices/SKILL.md`: Required to help maintain best practices for agent development.

⚠️ CRITICAL SAFETY INSTRUCTION: Before modifying an agent check with a user if it is a production agent and offer to create a clone. Ask user for the **fully qualified clone name** (`DATABASE.SCHEMA.CLONE_AGENT_NAME`) where they want the clone created. Follow `agent-system-of-record/SKILL.md` for clone creation. 

## Intent Detection

When user makes a request, detect their intent and load the appropriate sub-skill:

**CREATE Intent** - User wants to create/build a new agent:

- Trigger phrases: "create agent", "build agent", "set up agent", "new agent", "make an agent"
- **→ Load** `create-cortex-agent/SKILL.md`

**ADHOC_TESTING Intent** - User wants to test questions interactively:

- Trigger phrases: "test questions", "try queries", "test agent", "run some questions"
- **→ Load** `adhoc-testing-for-cortex-agent/SKILL.md`

**EVALUATE Intent** - User wants to run formal evaluation or benchmark agent:

- Trigger phrases: "evaluate agent", "run evaluation", "benchmark", "measure accuracy", "check metrics", "evaluation results"
- **→ Load** `evaluate-cortex-agent/SKILL.md`

**DATASET Intent** - User wants to create or manage evaluation datasets:

- Trigger phrases: "create dataset", "build dataset", "evaluation dataset", "add questions to dataset", "curate dataset"
- **→ Load** `dataset-curation/SKILL.md`

**DEBUG_SINGLE_QUERY Intent** - User wants to debug specific query:

- Trigger phrases: "debug query", "why did this fail", "analyze response", "investigate issue"
- **→ Load** `debug-single-query-for-cortex-agent/SKILL.md`

**OPTIMIZE Intent** - User wants to improve agent performance:

- Trigger phrases: "optimize", "improve accuracy", "production ready", "make it better"
- **→ Load** `optimize-cortex-agent/SKILL.md`

## Core Capabilities

### Primary Workflows

#### 1. Create Cortex Agent Flow

**Load** `create-cortex-agent/SKILL.md` when user chooses CREATE mode.

#### 2. Adhoc Testing Flow

**Load** `adhoc-testing-for-cortex-agent/SKILL.md` when user chooses ADHOC_TESTING mode.

Interactive testing of agent responses - explore behavior, debug issues, validate fixes.

#### 3. Evaluate Cortex Agent Flow

**Load** `evaluate-cortex-agent/SKILL.md` when user chooses EVALUATE mode.

Run formal evaluations using Snowflake's native Agent Evaluations with metrics:
- `answer_correctness` - Is the answer correct?
- `tool_selection_accuracy` - Did agent select the right tool?
- `tool_execution_accuracy` - Did agent execute tool correctly?
- `logical_consistency` - Is response logically consistent?

#### 4. Dataset Curation Flow

**Load** `dataset-curation/SKILL.md` when user chooses DATASET mode.

Create and manage evaluation datasets - from scratch, from production data, or add to existing.

#### 5. Debug Single Query Flow

**Load** `debug-single-query-for-cortex-agent/SKILL.md` when user chooses DEBUG_SINGLE_QUERY mode.

#### 6. Optimize Cortex Agent Flow

**Load** `optimize-cortex-agent/SKILL.md` when user chooses OPTIMIZE mode.

Full optimization workflow: benchmark → identify issues → improve → validate.

## Workflow Decision Tree

```
Start Session
    ↓
Run setup (Load `agent-system-of-record/SKILL.md` and `best-practices/SKILL.md`)
    ↓
Detect User Intent
    ↓
    ├─→ CREATE/BUILD → Load `create-cortex-agent/SKILL.md`
    │   (Triggers: "create agent", "build agent", "set up agent", "new agent")
    │
    ├─→ ADHOC_TESTING → Load `adhoc-testing-for-cortex-agent/SKILL.md`
    │   (Triggers: "test questions", "try queries", "test agent")
    │
    ├─→ EVALUATE → Load `evaluate-cortex-agent/SKILL.md`
    │   (Triggers: "evaluate agent", "run evaluation", "benchmark", "metrics")
    │
    ├─→ DATASET → Load `dataset-curation/SKILL.md`
    │   (Triggers: "create dataset", "build dataset", "evaluation dataset")
    │
    ├─→ DEBUG_SINGLE_QUERY → Load `debug-single-query-for-cortex-agent/SKILL.md`
    │   (Triggers: "debug query", "why did this fail", "analyze response")
    │
    └─→ OPTIMIZE → Load `optimize-cortex-agent/SKILL.md`
        (Triggers: "optimize", "improve accuracy", "production ready")
```

## Typical User Journeys

### Journey 1: New Agent Development
```
CREATE → ADHOC_TESTING → DATASET → EVALUATE → OPTIMIZE
```

### Journey 2: Production Agent Improvement
```
EVALUATE (baseline) → OPTIMIZE → EVALUATE (validate)
```

### Journey 3: Quick Testing
```
ADHOC_TESTING → DEBUG_SINGLE_QUERY (if issues found)
```

### Journey 4: Formal Benchmarking
```
DATASET → EVALUATE → compare results
```

## Rules

### Running Scripts

When running any scripts in any of the above skills, make sure to do all of the following:

1. **Check if `uv` is installed** by running `uv --version`. If it's not installed, prompt the user to install it using one of these methods:
   - `curl -LsSf https://astral.sh/uv/install.sh | sh` (recommended)
   - `brew install uv` (macOS)
   - `pip install uv`
2. When running python scripts, use `uv run --project <DIRECTORY THIS SKILL.md file is in> python <DIRECTORY THIS SKILL.md file is in>/scripts/script_name.py` to run them.
3. Do not `cd` into another directory to run them, but run them from whatever directory you're already in.
   WHY: This maintains your current working context and prevents path confusion. When using `uv run --project`, you must provide absolute paths for BOTH the --project flag AND the script itself.
4. Just run the script the way the skill says. Do not question it by running `--help` or reading the script unless the script fails when run as intended.

#### Common Mistakes When Running Scripts

1. ❌ WRONG: `uv run --project <DIRECTORY THIS SKILL.md file is in> python scripts/test_agent.py ...`
   (Relative path to script will fail)
2. ❌ WRONG: `cd <DIRECTORY THIS SKILL.md file is in> && uv run python scripts/test_agent.py ...`
   (Violates the "don't cd" rule)
3. ✅ CORRECT: `uv run --project <DIRECTORY THIS SKILL.md file is in> python <DIRECTORY THIS SKILL.md file is in>/scripts/test_agent.py ...`
   (Use the same base directory for both --project and the script path)

### System of Record

**Load** `agent-system-of-record/SKILL.md`.

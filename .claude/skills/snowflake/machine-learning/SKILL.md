---
name: machine-learning
description: "**[REQUIRED]** For **ALL** data science and machine learning tasks. Use when: analyzing data, training models, deploying models to Snowflake, registering models, working with ML workflows, running ML jobs on Snowflake compute, model registry, log model, deploy pickle file, experiment tracking, model monitoring, ML observability, tracking drift, and model performance analysis. Routes to specialized sub-skills. This skill should ALWAYS be loaded in even if only a portion of the workflow is related to machine learning."
---

# Data Science & Machine Learning Skills

This skill routes to specialized sub-skills for data science and machine learning tasks.
This skill provides valuable information about all sorts of data science, machine learning, and mlops tasks.
It MUST be loaded in if any part of the user query relates to these topics❗❗❗

## Routing Behavior

**⚠️ CRITICAL: Route AUTOMATICALLY based on the user's request. Do NOT ask the user which sub-skill to use or how they want to deploy.**

When a user asks to "train a model", "build a model" or inquires about a similar task:

- **IMMEDIATELY** load `ml-development/SKILL.md` and start working
- Do NOT ask about deployment options upfront
- Do NOT ask "Local only vs Register in Snowflake vs End-to-end"
- Training and deployment are SEPARATE tasks - handle them sequentially if needed

## Intent Detection


| User Says | Route To | Action |
|-----------|----------|--------|
| "analyze data", "train model", "build model", "feature engineering", "predict", "classify", "regression" | `ml-development/SKILL.md` | Load immediately, start training |
| "register model", "model registry", "log model", "pickle to snowflake", "save model to snowflake", "upload model", ".pkl file", ".ubj file" | `model-registry/SKILL.md` | Load immediately, start registration (Workflow A) |
| "deploy model", "deploy model for inference", "deploy for inference" | `model-registry/SKILL.md` | Load immediately, ask deployment target (Workflow B) |
| "create inference service", "SPCS inference", "inference endpoint", "serve model", "snowpark container services", "deploy to SPCS", "model endpoint", "deploy in container", "deploy model service" | `spcs-inference/SKILL.md` | Load immediately, create SPCS service |
| "ml job", "ml jobs", "run on snowflake compute", "submit job", "remote execution", "GPU training" | `ml-jobs/SKILL.md` | Load immediately, set up job |
| "model monitor", "monitor model", "add monitoring", "enable monitoring", "ML observability", "track drift", "model performance", "monitor predictions", "observability" | `model-monitor/SKILL.md` | Load immediately, set up monitoring |

**Sub-skill path aliases** (for routing resolution):

- `ml-job` → `ml-jobs/SKILL.md` (singular form routes to plural directory)
- `ml-jobs` → `ml-jobs/SKILL.md`
- `mljob` → `ml-jobs/SKILL.md`
- `mljobs` → `ml-jobs/SKILL.md`

## Workflow

```markdown
User Request → Detect Intent → Load appropriate sub-skill → Execute

Examples:
- "Train a classifier" → Load ml-development → Train locally → Done
- "Deploy my model.pkl" → Load model-registry → Register to Snowflake → Done  
- "Train AND deploy" → Load ml-development → Train → Save model → Report artifacts → Ask about deployment → If yes, load model-registry WITH CONTEXT (file path, framework, schema)
```

**Key principle**: Complete ONE task at a time. Only ask about the next step after the current step is done.

## Context Preservation Between Skills

**⚠️ CRITICAL:** When transitioning from ml-development to model-registry:

**Information to preserve and pass along:**

- Model file path (absolute path to serialized model file)
- Framework used (sklearn, xgboost, lightgbm, pytorch, tensorflow, etc.)
- Sample input schema (columns and types from training data)
- Any other relevant training context

**Why this matters:**

- Avoids asking the user to repeat information they just provided
- Prevents accidental retraining of the model
- Prevents modification of the training script
- Improves user experience with seamless workflow

**How to do it:**

1. When ml-development saves a model, it reports all details
2. When loading model-registry, explicitly mention this context
3. Model-registry checks for this context before asking questions
4. Use the preserved context instead of asking user again

**Example handoff:**

```markdown
ml-development: "Model saved to /path/to/model.pkl (sklearn). Would you like to register it?"
User: "Yes"
[Load model-registry with context: path=/path/to/model.pkl, framework=sklearn, schema=[...]]
model-registry: "I see you just trained a sklearn model. What should I call it in Snowflake?"
```

## Common Execution Patterns

Sub-skills inherit these patterns. Each sub-skill should reference this section rather than duplicating.

### Execution Mode Detection

**CRITICAL:** Check which tools you have available:

| Tool Available | Mode | Where Code Runs |
|----------------|------|-----------------|
| `code_sandbox` | **Interactive Mode** | Locally (sandbox environment) |
| `bash` + `write` only | **Write Mode** | Locally (user's machine) |

**⚠️ Neither mode runs on Snowflake compute.** For Snowflake compute, route to `ml-jobs/SKILL.md`.

### Write Mode Options

**⚠️ IMPORTANT:** All execution in Write Mode runs LOCALLY on the user's machine, NOT on Snowflake compute.

In Write Mode, you have two output formats:

1. **Local Jupyter Notebook** (`write` + `bash`) - Runs locally, structured cell-by-cell output
2. **Local Python Script** (`write` + `bash`) - Runs locally, pipelines, automation, simpler workflows

**DO NOT present "Snowflake Notebook" or "Snowflake compute" as options here.** For Snowflake compute, route to `ml-jobs/SKILL.md` instead.

Choose based on user preference or existing files. If unclear, ask the user.

### Python Environment Setup (Write Mode - Scripts)

**⚠️ CRITICAL:** Before running any Python script in Write Mode, you MUST set up the correct environment.

#### Step 1: Find Existing Environment

**ALWAYS** use the built in cortex tools first to check for existing environments:

```bash
cortex env detect
```

This will return the environment information about what kind of environment it is as well as preferences on which one to use.

#### Step 2: Required ML Packages

For ML tasks, these packages are required:

| Package | Purpose |
|---------|---------|
| `snowflake-ml-python` | Model Registry, ML Jobs, Snowflake ML |
| `snowflake-snowpark-python` | Snowflake data access |
| `scikit-learn` | ML algorithms |
| `pandas`, `numpy` | Data manipulation |
| `plotly`, `seaborn`, `matplotlib` | Data Visualization |

#### Step 3: Environment Verification

Before running scripts, verify the environment has required packages:

```bash
# Check if snowflake-ml-python is installed
<python_cmd> -c "import snowflake.ml; print(snowflake.ml.__version__)"
```

If package is missing, ask user:

```markdown
The required package `snowflake-ml-python` is not installed. Options:
1. Install it
2. Point me to a Python environment that has it installed
```

Package Installation Commands

```bash
# uv installation
uv add snowflake-ml-python

# poetry installation
poetry add snowflake-ml-python

# pip installation
pip install snowflake-ml-python
```

#### Running Scripts Pattern

```bash
# With uv project
SNOWFLAKE_CONNECTION_NAME=<connection> uv run python /abs/path/script.py

# With poetry project  
SNOWFLAKE_CONNECTION_NAME=<connection> poetry run python /abs/path/script.py

# With system python (after verifying packages)
SNOWFLAKE_CONNECTION_NAME=<connection> python3 /abs/path/script.py
```

#### Running Notebook Patterns

```bash
# With uv project (execute notebook in place)
SNOWFLAKE_CONNECTION_NAME=<connection> uv run jupyter nbconvert --to notebook --execute --inplace /abs/path/notebook.ipynb

# With poetry project (execute notebook in place)
SNOWFLAKE_CONNECTION_NAME=<connection> poetry run jupyter nbconvert --to notebook --execute --inplace /abs/path/notebook.ipynb

# With system jupyter (execute notebook in place)
SNOWFLAKE_CONNECTION_NAME=<connection> jupyter nbconvert --to notebook --execute --inplace /abs/path/notebook.ipynb
```

**⚠️ IMPORTANT:** Always use absolute paths. Never `cd` then run.

### Session Setup Patterns

**Interactive Mode (code_sandbox):**

```python
from snowflake.snowpark.context import get_active_session
session = get_active_session()
```

**Write Mode (notebooks/scripts):**

```python
import os
from snowflake.snowpark import Session
session = Session.builder.config(
    "connection_name", 
    os.getenv("SNOWFLAKE_CONNECTION_NAME") or "<connection>"
).create()
```

### Mandatory Checkpoints (Write Mode)

**⚠️ MANDATORY:** Before executing any notebook or script:

1. Present summary of what will be executed
2. Wait for user confirmation (Yes/No)
3. **NEVER** execute without explicit approval

### Output Reporting (Write Mode)

**⚠️ MANDATORY:** After writing code, always tell the user:

```markdown
Code written to: /absolute/path/to/file.py (or .ipynb)
```

After execution completes, report:

1. File location where code was saved
2. Execution results/metrics
3. Any artifacts created (models, outputs, etc.)

### Error Recovery (Write Mode)

If execution fails:

1. Read the COMPLETE error output
2. Identify root cause
3. Fix the specific issue
4. **Ask user again** before re-executing

## Sub-Skills

### ml-development

Data exploration, statistical analysis, model training, and evaluation. Covers the full ML development workflow from data loading to model evaluation.

### model-registry

Deploy serialized models to Snowflake Model Registry. Supports various model formats (`.pkl`, `.ubj`, `.json`, `.pt`, etc.) depending on framework. Routes to `spcs-inference` sub-skill for inference service creation.

### experiment-tracking

Skills for tracking model training experiments using Snowflake's experiment tracking framework.
Routes to `experiment-tracking` sub-skill for experiment tracking understanding.

### spcs-inference

Deploy registered models to Snowpark Container Services for real-time inference. Handles compute pool selection, GPU/CPU configuration, num_workers, and service creation. Part of the Model Registry workflow.

### ml-jobs

Transform local Python scripts into Snowflake ML Jobs that run on Snowflake compute pools. Supports GPU/high-memory instances, custom dependencies, and distributed multi-node training.

**Aliases:** ml-job, mljob, mljobs all route here.

### model-monitor
Set up ML Observability for models in the Snowflake Model Registry. Track drift, performance metrics, and prediction statistics over time. Supports segmentation for monitoring across data subsets and baseline comparison for drift detection.

---
name: model-registry
description: "Deploy models to Snowflake Model Registry and route to inference deployment. Use when: registering serialized models, deploying trained models, logging models. Triggers: model registry, deploy model, register model, log model, model to snowflake."
---

# Model Registry Operations

## Intent Detection

Route based on user intent:

| User Says | Route To |
|-----------|----------|
| "register model", "log model", "deploy pickle", "save model to registry" | [Workflow A: Register Model](#workflow-a-register-model) |
| "deploy model", "deploy model for inference", "deploy for inference" | [Workflow B: Deploy Model Decision Tree](#workflow-b-deploy-model-decision-tree) |
| "create inference service", "SPCS inference", "inference endpoint", "serve model", "snowpark container services" | `../spcs-inference/SKILL.md` |

---

## Workflow B: Deploy Model Decision Tree

Use this workflow when user says "deploy a model" or "deploy model for inference".

### Step 1: Choose Deployment Target

**Ask user:**
```
Where would you like to deploy your model for inference?

1. Warehouse - Run inference via SQL queries (simpler, no extra infrastructure)
2. Snowpark Container Services (SPCS) - REST endpoints, GPU support, scalable
```

**⚠️ STOP**: Wait for user response.

**If Warehouse:** Route to [Workflow A: Register Model](#workflow-a-register-model)

**If SPCS:** Load `../spcs-inference/SKILL.md` and follow its workflow.

---

## When to Use

**Register Model (Workflow A):**
- User has a serialized model file (`.pkl`, `.ubj`, `.json`, `.pt`, `.h5`, etc.)
- User wants to register/log a model to Snowflake Model Registry

**SPCS Inference Service (`../spcs-inference/SKILL.md`):**
- User has a model already registered in the registry
- User wants to deploy the model for real-time inference via SPCS
- User wants to create an HTTP endpoint for model predictions

## Execution Mode

See parent skill (`data-science-machine-learning/SKILL.md`) for **Execution Mode Detection** and **Session Setup Patterns**.

- **Interactive Mode** (`code_sandbox` available): Test model loading first, then register iteratively
- **Write Mode** (no `code_sandbox`): Write complete script, ask before executing

**⚠️ Note:** Both modes run locally on the user's machine. The model is registered TO Snowflake, but the registration code runs locally.

**⚠️ Conda Environment for WAREHOUSE Target:** When targeting WAREHOUSE, use a conda environment with `snowflake-ml-python` installed via conda (not pip). **Use the same Python version the model was trained with** to avoid pickle compatibility issues. Create with: `conda create -n snowml python=<VERSION> snowflake-ml-python -c https://repo.anaconda.com/pkgs/snowflake`

---

## Workflow A: Register Model

### Step 0: Check for Recent Model Context

**⚠️ IMPORTANT:** Before asking, check if you have context from a recent training session (model path, framework, schema). If yes, skip to Step 2 using that context. Only ask for model name in Snowflake.

**If no context:** Proceed to Step 1.

### Step 1: Gather Information

**If no recent context**, ask user for:
- Model file path (e.g., `.pkl`, `.ubj`, `.json`, `.pt`)
- Model name for Snowflake
- Database and Schema to register this model (Do not use ask_user_question tool for this one, just stop and wait for user response)
- Framework (sklearn, xgboost, lightgbm, pytorch, tensorflow, or other)
- Sample input data or schema description (if needed)
- Additional dependencies

**⚠️ STOP**: Wait for user response.

### Step 2: Check if Model Version Exists

```sql
SHOW VERSIONS IN MODEL <DATABASE>.<SCHEMA>.<MODEL_NAME>;
```

- **If version exists**: Ask user to choose new version (v2, v3...) or new model name
- **If "does not exist" error**: Proceed with "v1"

**⚠️ STOP**: Wait for user choice if model exists.

### Step 3: Determine Model Type

Based on the framework:

| Framework | Model Type | Approach |
|-----------|------------|----------|
| sklearn, xgboost, lightgbm, pytorch, tensorflow | Built-in | Direct `log_model()` |
| Other (pycaret, custom, etc.) | Custom | Requires `CustomModel` wrapper |

### Step 4: Generate Deployment Code

**For Built-in Model Types (sklearn, xgboost, lightgbm, pytorch, tensorflow):**

```python
import pandas as pd
from snowflake.ml.registry import Registry
from snowflake.snowpark import Session

session = Session.builder.config("connection_name", "<CONNECTION_NAME>").create()

# setup database and schema
session.use_database("<DATABASE>")
session.use_schema("<SCHEMA>")

reg = Registry(session=session, database_name="<DATABASE>", schema_name="<SCHEMA>")

# Load model using framework-appropriate method
# sklearn/lightgbm (pickle): pickle.load() or joblib.load()
# xgboost (.ubj/.json): xgb.Booster(); booster.load_model()
# pytorch (.pt): torch.load()
# tensorflow (.h5): tf.keras.models.load_model()
model = <LOAD_MODEL_CODE>

sample_input = pd.DataFrame(<SAMPLE_DATA>)

mv = reg.log_model(
    model,
    model_name="<MODEL_NAME>",
    version_name="<VERSION_NAME>",  # e.g., "v1", "v2" - determined in Step 2
    sample_input_data=sample_input,
    conda_dependencies=["<FRAMEWORK>", "<OTHER_DEPS>"],  # Snowflake conda channel (warehouse) or conda-forge (SPCS)
    target_platforms=["WAREHOUSE", "SNOWPARK_CONTAINER_SERVICES"],
    comment="<DESCRIPTION>"
)

print(f"Model registered: {mv.model_name} version {mv.version_name}")
```

**For Custom/Unsupported Model Types:**

```python
import pandas as pd
from snowflake.ml.registry import Registry
from snowflake.ml.model import custom_model
from snowflake.snowpark import Session

session = Session.builder.config("connection_name", "<CONNECTION_NAME>").create()

model_context = custom_model.ModelContext(
    model_file="<MODEL_FILE_PATH>"
)

class MyCustomModel(custom_model.CustomModel):
    def __init__(self, context: custom_model.ModelContext) -> None:
        super().__init__(context)
        # Load model using framework-appropriate method
        self.model = <LOAD_MODEL_CODE>

    @custom_model.inference_api
    def predict(self, input_df: pd.DataFrame) -> pd.DataFrame:
        predictions = self.model.predict(input_df)
        return pd.DataFrame({"prediction": predictions})

my_model = MyCustomModel(model_context)

sample_input = pd.DataFrame(<SAMPLE_DATA>)
output = my_model.predict(sample_input)

reg = Registry(session=session, database_name="<DATABASE>", schema_name="<SCHEMA>")

mv = reg.log_model(
    my_model,
    model_name="<MODEL_NAME>",
    version_name="<VERSION_NAME>",  # e.g., "v1", "v2" - determined in Step 2
    sample_input_data=sample_input,
    conda_dependencies=["<DEPS>"],  # Snowflake conda channel (warehouse) or conda-forge (SPCS)
    target_platforms=["WAREHOUSE", "SNOWPARK_CONTAINER_SERVICES"],
    comment="<DESCRIPTION>"
)

print(f"Model registered: {mv.model_name} version {mv.version_name}")
```

### Step 5: Execute and Verify

**Interactive Mode**: Test model loading → test prediction → run registration → verify with `reg.show_models()`

**Write Mode**: Write complete script, then ask user confirmation before executing.

**⚠️ MANDATORY:** Present summary and wait for user approval before executing.

Follow **Python Environment Setup** from parent skill. If execution fails, read complete error, fix, and ask user again before re-executing.

## log_model() Parameters

| Parameter | Description | Required |
|-----------|-------------|----------|
| `model` | Python model object | Yes |
| `model_name` | Name in registry | Yes |
| `version_name` | Version identifier | Recommended |
| `sample_input_data` | DataFrame for schema inference | Yes* |
| `conda_dependencies` | List of conda packages (for warehouse) | See below |
| `pip_requirements` | List of pip packages (requires artifact_repository_map for warehouse) | See below |
| `target_platforms` | Target deployment platforms | See below |
| `artifact_repository_map` | Map of package indexes for non-conda packages | See below |

*Or provide `signatures` instead.

## Dependencies for Warehouse vs SPCS

**For WAREHOUSE target:**
- Use `conda_dependencies` for packages in Snowflake conda channel
- OR use `pip_requirements` + `artifact_repository_map` for PyPI packages

**For SPCS only:**
- Can use `pip_requirements` directly without `artifact_repository_map`
- `conda_dependencies` are loaded from conda-forge (not Snowflake conda channel)

## target_platforms Strategy

**Default approach:** Try `["WAREHOUSE", "SNOWPARK_CONTAINER_SERVICES"]` first to enable both warehouse inference and SPCS deployment.

**Fallback:** If `log_model()` fails with warehouse target (e.g., due to unsupported dependencies or model size), retry with `["SNOWPARK_CONTAINER_SERVICES"]` only.

```python
# First attempt: try both platforms (use conda_dependencies for warehouse compatibility)
try:
    mv = reg.log_model(
        model,
        model_name="<MODEL_NAME>",
        version_name="<VERSION>",
        sample_input_data=sample_input,
        conda_dependencies=["<DEPS>"],  # Snowflake conda channel (warehouse) or conda-forge (SPCS)
        target_platforms=["WAREHOUSE", "SNOWPARK_CONTAINER_SERVICES"],
    )
except Exception as e:
    # Fallback: SPCS only (can use pip_requirements directly)
    mv = reg.log_model(
        model,
        model_name="<MODEL_NAME>",
        version_name="<VERSION>",
        sample_input_data=sample_input,
        pip_requirements=["<DEPS>"],
        target_platforms=["SNOWPARK_CONTAINER_SERVICES"],
    )
```

## Using artifact_repository_map for Non-Conda Packages

When your model depends on packages **not available in the Snowflake conda channel**, use `artifact_repository_map` to specify PyPI as the package source.

Use the shared `pypi_shared_repository` for public PyPI packages:

```python
mv = reg.log_model(
    model,
    model_name="<MODEL_NAME>",
    version_name="<VERSION>",
    sample_input_data=sample_input,
    pip_requirements=["scikit-learn", "shap>=0.42.0"],
    target_platforms=["WAREHOUSE", "SNOWPARK_CONTAINER_SERVICES"],
    artifact_repository_map={
        "shap": "pypi_shared_repository"  # Map non-conda packages to PyPI
    },
)
```

- **Keys**: Package names (must also be listed in `pip_requirements`)
- **Values**: Use `pypi_shared_repository` for public PyPI packages

## Common Issues (Workflow A)

- **Version exists**: Use `SHOW VERSIONS IN MODEL` to check, increment version or rename
- **Not serializable**: Ensure saved with `pickle.dump()` or `joblib.dump()`
- **Schema inference fails**: Provide explicit `signatures`
- **Package not found in Snowflake channel**: Use `artifact_repository_map` to specify PyPI or custom repository (see [Using artifact_repository_map](#using-artifact_repository_map-for-non-conda-packages))

### Step 6: Post-Registration Verification

**⚠️ MANDATORY:** After registration completes, verify the model was registered correctly before proceeding.

**Run verification checks:**

```sql
-- 1. Verify model exists in registry
SHOW MODELS IN SCHEMA <DATABASE>.<SCHEMA>;

-- 2. Verify version was created
SHOW VERSIONS IN MODEL <DATABASE>.<SCHEMA>.<MODEL_NAME>;

-- 3. Check available functions/methods
SHOW FUNCTIONS IN MODEL <DATABASE>.<SCHEMA>.<MODEL_NAME>;
```

**Verification checklist:**

| Check | Expected Result |
|-------|-----------------|
| `SHOW MODELS` includes model | Model name listed in results |
| `SHOW VERSIONS IN MODEL` returns version | Version name listed (e.g., "v1") |
| `SHOW FUNCTIONS IN MODEL` returns methods | At least one method (e.g., `PREDICT`, `PREDICT_PROBA`) |

**If verification fails:**
- Model not found: Check database/schema context, re-run registration
- Version not found: Registration may have failed silently, check for errors
- No functions: Sample input may have been invalid, re-register with correct schema

**⚠️ STOP**: Only proceed to next steps after all verification checks pass.

---

### Step 7: Next Steps

**If target_platforms includes WAREHOUSE:**

Ask user what they'd like to do:
1. **Test warehouse inference** - Run a sample prediction query
2. **Deploy to SPCS** - Create an inference service (Workflow B)
3. **Set up model monitoring** - Track drift and performance (load `../model-monitor/SKILL.md`)
4. **Done** - Finish here

**If target_platforms is SPCS only:**

Warehouse inference is not available. Ask user:
1. **Deploy to SPCS** - Create an inference service (Workflow B)
2. **Set up model monitoring** - Track drift and performance (load `../model-monitor/SKILL.md`)
3. **Done** - Finish here

**⚠️ STOP**: Wait for user response.

**If user chooses to test warehouse inference:**

**⚠️ Always specify the version explicitly.** Use the version from Step 2 (e.g., `V1`, `V2`)—do not rely on the default version.

Run a sample prediction using SQL or Python. Use the method name from the model (e.g., `PREDICT`, `PREDICT_PROBA`, `TRANSFORM`).

**SQL Syntax:**

Use `MODEL(model_name, version)!METHOD(...)` syntax. Version names are **unquoted identifiers**.

```sql
SELECT MODEL(<DATABASE>.<SCHEMA>.<MODEL_NAME>, <VERSION>)!<METHOD_NAME>(col1, col2, col3) AS result
FROM <INPUT_TABLE>
LIMIT 10;

-- Extract specific output field
SELECT MODEL(<DATABASE>.<SCHEMA>.<MODEL_NAME>, <VERSION>)!<METHOD_NAME>(col1, col2, col3):output_feature_0 AS result
FROM <INPUT_TABLE>;
```

**⚠️ Important:** Do NOT quote version names. Use `V2` not `'V2'`.

**Python:**
```python
mv = reg.get_model("<MODEL_NAME>").version("<VERSION>")
# Check available methods
print(mv.show_functions())
# Run inference
result = mv.run(test_data, function_name="<method_name>")
print(result)
```

**If user chooses SPCS deployment:** Proceed to Workflow B.

**When to use Warehouse vs SPCS Inference:**

| Use Case | Recommendation |
|----------|----------------|
| Ad-hoc queries, testing | Warehouse inference |
| Batch predictions | Warehouse inference |
| Real-time API endpoint | SPCS inference (Workflow B) |
| High-throughput, low-latency | SPCS inference (Workflow B) |

## Output

- Model registered in Snowflake Model Registry
- Model name and version for reference
- Ready for warehouse inference (SQL) or SPCS deployment (load `../spcs-inference/SKILL.md`)

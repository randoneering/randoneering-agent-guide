---
name: spcs-inference
description: "Deploy models from Snowflake Model Registry to Snowpark Container Services for real-time inference. Use when: creating inference services, SPCS deployment, REST endpoints for models, GPU inference. Triggers: create inference service, SPCS inference, inference endpoint, serve model, deploy to SPCS, model endpoint."
parent_skill: model-registry
---

# SPCS Inference Service Deployment

Deploy a registered model to Snowpark Container Services for real-time inference.

## Prerequisites

- Model already registered in Snowflake Model Registry (see `../model-registry/SKILL.md`)
- Access to a compute pool (GPU or CPU)
- `BIND SERVICE ENDPOINT` privilege for HTTP endpoints

---

## Workflow: Create Inference Service

### Step 1: Identify the Model

If coming from model registration, use that model reference. Otherwise ask for:
- Model name and version
- Database/Schema where the model is registered

**⚠️ STOP**: Wait for response if not already known.

### Step 2: Choose Service Database and Schema

**Ask user:**
```
Which database and schema would you like to deploy the inference service in?

Note: This can be different from where the model is registered.
```

**⚠️ STOP**: Wait for user response.

### Step 3: Select Compute Pool

```sql
SHOW COMPUTE POOLS;
```

Present available compute pools to the user, indicating GPU vs CPU, nodes, and services running:

**Ask user:**
```
Available compute pools:

| Pool Name | Instance Family | GPUs/Node | Min/Max Nodes | Active Nodes | State | Services |
|-----------|-----------------|-----------|---------------|--------------|-------|----------|
| POOL_A    | GPU_NV_M        | 4 x A10G  | 1 / 4         | 2            | ACTIVE | 2        |
| POOL_B    | CPU_X64_M       | None      | 1 / 2         | 0            | SUSPENDED | 0      |
| ...       | ...             | ...       | ...           | ...          | ... | ...      |

Which compute pool would you like to use?

💡 Recommendation: Use a GPU compute pool for models that require GPU inference 
(e.g., deep learning, transformers, large embeddings).
```

**⚠️ STOP**: Wait for user response.

**GPU Reference:**

| Instance Family | GPUs per Node | GPU Type |
|-----------------|---------------|----------|
| GPU_NV_S        | 1             | A10G     |
| GPU_NV_M        | 4             | A10G     |
| GPU_NV_L        | 8             | A100     |

If no suitable pool exists, offer to create one:

```sql
CREATE COMPUTE POOL IF NOT EXISTS <POOL_NAME>
    MIN_NODES = 1 MAX_NODES = <N>
    INSTANCE_FAMILY = '<INSTANCE_FAMILY>'
    AUTO_RESUME = TRUE;
```

### Step 4: Configure Max Instances

**Ask user:**
```
How many max instances would you like for the service?

- 1 instance: Suitable for development/testing or low traffic
- 2+ instances: Recommended for production workloads expecting higher load

💡 The service will scale between 1 and max_instances based on demand.

Enter max_instances (default: 1):
```

**⚠️ STOP**: Wait for user response.

### Step 5: Configure num_workers

**⚠️ MANDATORY - ALWAYS ASK THIS QUESTION**

This step must be executed for every deployment regardless of compute pool type.

---

**For GPU compute pool:**

**Ask user:**
```
Now let's configure num_workers.

GPUs are spread equally among workers. Each worker needs its own copy of the model 
in GPU memory.

If your model fits into a single GPU, you can start by setting num_workers to the 
number of GPUs available.

Example: If your model needs 2 A10 GPUs and you have 4 available (GPU_NV_M), 
then num_workers must be 2.

💡 If you see backpressure and GPU utilization is not very high, consider 
tuning up the number of workers.

Based on your compute pool (<POOL_NAME> with <N> GPUs):
- gpu_requests will be set to <N> (max available for this node)

How many workers would you like? (Enter num_workers):
```

**⚠️ STOP**: Wait for user to provide num_workers value. Do NOT proceed without it.

---

**For CPU compute pool:**

**Ask user:**
```
Now let's configure num_workers.

For CPU inference, we recommend leaving num_workers unset - our system will auto-pick 
an appropriate value based on your workload.

Would you like to:
1. Use auto-picker (recommended)
2. Specify num_workers manually
```

**⚠️ STOP**: Wait for user response.

### Step 6: Check Existing Service

```sql
SHOW SERVICES LIKE '<SERVICE_NAME>' IN SCHEMA <DATABASE>.<SCHEMA>;
```

If exists, ask user: rename, delete & recreate, or keep existing.

### Step 7: Create Service

**For GPU compute pool:**

```python
import os
from snowflake.ml.registry import Registry
from snowflake.snowpark import Session

session = Session.builder.config(
    "connection_name", 
    os.getenv("SNOWFLAKE_CONNECTION_NAME") or "<CONNECTION>"
).create()
session.use_database("<SERVICE_DATABASE>")
session.use_schema("<SERVICE_SCHEMA>")

reg = Registry(session=session, database_name="<MODEL_DATABASE>", schema_name="<MODEL_SCHEMA>")
mv = reg.get_model("<MODEL_NAME>").version("<VERSION>")

mv.create_service(
    service_name="<SERVICE_NAME>",
    service_compute_pool="<COMPUTE_POOL>",
    ingress_enabled=True,
    gpu_requests="<MAX_GPUS_FOR_NODE>",
    num_workers=<NUM_WORKERS>,
    max_instances=<MAX_INSTANCES>,
)

print(mv.list_services())
```

**For CPU compute pool (with auto-picker):**

```python
import os
from snowflake.ml.registry import Registry
from snowflake.snowpark import Session

session = Session.builder.config(
    "connection_name", 
    os.getenv("SNOWFLAKE_CONNECTION_NAME") or "<CONNECTION>"
).create()
session.use_database("<SERVICE_DATABASE>")
session.use_schema("<SERVICE_SCHEMA>")

reg = Registry(session=session, database_name="<MODEL_DATABASE>", schema_name="<MODEL_SCHEMA>")
mv = reg.get_model("<MODEL_NAME>").version("<VERSION>")

mv.create_service(
    service_name="<SERVICE_NAME>",
    service_compute_pool="<COMPUTE_POOL>",
    ingress_enabled=True,
    max_instances=<MAX_INSTANCES>,
    # num_workers not set - using auto-picker
)

print(mv.list_services())
```

### Step 8: Execute and Verify

**⚠️ MANDATORY:** Present summary and get user confirmation before executing:

```
Summary:
- Model: <MODEL_DATABASE>.<MODEL_SCHEMA>.<MODEL_NAME> (version <VERSION>)
- Service: <SERVICE_DATABASE>.<SERVICE_SCHEMA>.<SERVICE_NAME>
- Compute Pool: <COMPUTE_POOL> (GPU/CPU)
- Max Instances: <MAX_INSTANCES>
- GPU Requests: <VALUE or N/A>
- Num Workers: <VALUE or auto>

Proceed? (Yes/No)
```

Service creation takes 5-15 minutes. Tell the user and offer to check status:

```
Service creation initiated. This typically takes 5-15 minutes.
Would you like me to check the status for you?
```

To check status:
```sql
SHOW SERVICES LIKE '<SERVICE_NAME>' IN SCHEMA <SERVICE_DATABASE>.<SERVICE_SCHEMA>;
```

### Step 9: Usage Examples

**SQL:**
```sql
SELECT <SERVICE_NAME>!PREDICT(col1, col2) FROM input_table;
```

**Python (mv.run):**
```python
result = mv.run(test_data, function_name="predict", service_name="<SERVICE_NAME>")
```

**REST API:**

Requires: network policy allowing client IP, PAT token, service role grant.

```python
import requests

url = "https://<endpoint-url>/<function>"  # SHOW ENDPOINTS IN SERVICE <SERVICE_NAME>
headers = {"Authorization": "Snowflake Token=\"<PAT>\""}
response = requests.post(url, json={"data": [[0, val1, val2]]}, headers=headers)
```

See [REST API Access Setup](#rest-api-access-setup) for details.

### Step 10: Setup REST API Access

**Ask user:**
```
Would you like to set up REST API access to call this service from outside Snowflake?

This is needed if you want to call the inference endpoint from external apps, 
scripts, or services (not via SQL or Python SDK).
```

**⚠️ STOP**: Wait for user response.

**If yes:** Continue with the REST API Access Setup flow below.

**If no:** Deployment complete.

### Next Steps

Ask user:
```
Your inference service is running! What would you like to do next?

1. Set up model monitoring - Track drift and performance
2. Done - Finish here
```

**If monitoring:** Load `../model-monitor/SKILL.md`

**If done:** Skip to Service Management Reference.

---

## REST API Access Setup

To access the inference endpoint from outside Snowflake (e.g., external apps, services, or local scripts), you need proper authentication and network access configured.

### Network Policy (Required)

**Ask user:**
```
Do you have a network policy that allows your client IP to access Snowflake?
```

**⚠️ STOP**: Wait for user response.

**If yes:** Skip to [Service Role Grant](#service-role-grant).

**If no or unsure:** Users calling the endpoint need a network policy allowing their client IP. If user has ACCOUNTADMIN/SECURITYADMIN, help them create one:

```sql
-- Create network rule for client IP
CREATE NETWORK RULE <RULE_NAME> MODE = INGRESS TYPE = IPV4 VALUE_LIST = ('<CLIENT_IP>/32');

-- Create and apply policy
CREATE NETWORK POLICY <POLICY_NAME> ALLOWED_NETWORK_RULE_LIST = ('<RULE_NAME>');
ALTER USER <USERNAME> SET NETWORK_POLICY = <POLICY_NAME>;
```

### Service Role Grant

```sql
GRANT SERVICE ROLE <SERVICE_NAME>!ALL_ENDPOINTS_USAGE TO ROLE <ROLE_NAME>;
```

### Authentication

**Development:** Use Programmatic Access Token (PAT) - create in Snowsight under User Menu > Preferences.

**Production:** Use keypair JWT authentication for automated systems. See: [Programmatic Access to SPCS](https://medium.com/snowflake/programmatic-access-to-snowpark-container-services-b49ef65a7694)

### Test with PAT

**Ask user:**
```
Would you like to test the REST endpoint? 

Do you have a PAT (Programmatic Access Token)? 
If not, you can create one in Snowsight under User Menu > Preferences > Programmatic Access Tokens.
```

**If user has PAT, get the endpoint URL:**
```sql
SHOW ENDPOINTS IN SERVICE <SERVICE_NAME>;
```

Then ask for:
- PAT token
- Sample input data

**Generate test script:**

```python
import requests

url = "<ENDPOINT_URL>/<FUNCTION_NAME>"
pat = "<PAT_TOKEN>"

headers = {"Authorization": f"Snowflake Token=\"{pat}\""}
payload = {"data": [[0, <SAMPLE_INPUT>]]}

response = requests.post(url, json=payload, headers=headers)
print(response.status_code)
print(response.json())
```

**⚠️ STOP**: Wait for user response before proceeding.

---

## Common Issues

- **Compute pool not ready**: Resuming a suspended pool can take a few minutes. Tell the user and offer to check status with `SHOW COMPUTE POOLS`
- **Service fails**: Check logs with `CALL SYSTEM$GET_SERVICE_LOGS('<SERVICE_NAME>', 0, 'model-inference')`
- **Missing privileges**: Need `USAGE` on compute pool, `BIND SERVICE ENDPOINT` for HTTP
- **GPU memory issues**: Reduce num_workers if model doesn't fit in GPU memory

---

## Debugging Service Issues

When service is failing or experiencing issues (OOM, crashes, errors), use platform metrics and logs.

### Step 1: Check Platform Metrics

```sql
-- Memory and CPU usage (look for OOM patterns)
SELECT timestamp, metric_name, value, unit, container_name
FROM TABLE(<SERVICE_NAME>!SPCS_GET_METRICS())
WHERE metric_name IN ('container.memory.usage', 'container.cpu.usage', 'container.memory.max_usage')
ORDER BY timestamp DESC
LIMIT 50;

-- GPU metrics (if applicable)
SELECT timestamp, metric_name, value, container_name
FROM TABLE(<SERVICE_NAME>!SPCS_GET_METRICS())
WHERE metric_name LIKE '%gpu%'
ORDER BY timestamp DESC;
```

### Step 2: Check Container Logs

**Model inference container:**
```sql
SELECT * FROM TABLE(<SERVICE_NAME>!SPCS_GET_LOGS())
WHERE container_name = 'model-inference'
ORDER BY timestamp DESC
LIMIT 100;
```

**Proxy container:**
```sql
SELECT * FROM TABLE(<SERVICE_NAME>!SPCS_GET_LOGS())
WHERE container_name = 'proxy'
ORDER BY timestamp DESC
LIMIT 100;
```

**Live logs (current container):**
```sql
CALL SYSTEM$GET_SERVICE_LOGS('<SERVICE_NAME>', 0, 'model-inference');
CALL SYSTEM$GET_SERVICE_LOGS('<SERVICE_NAME>', 0, 'proxy');
```

### Common OOM Fixes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `container.memory.max_usage` near limit | Model too large | Use larger instance or reduce num_workers |
| Repeated container restarts | OOM kills | Check logs for "OOMKilled", reduce batch size |
| GPU memory errors in logs | Model doesn't fit | Reduce num_workers or use instance with more GPU memory |

### Step 3: Event Table (if service is dead)

If service is terminated, use event table directly:

```sql
-- Find your event table
SHOW PARAMETERS LIKE 'event_table' IN ACCOUNT;

-- Logs from event table
SELECT timestamp, value, resource_attributes
FROM <EVENT_TABLE>
WHERE resource_attributes:"snow.service.name" = '<SERVICE_NAME>'
  AND record_type = 'LOG'
ORDER BY timestamp DESC
LIMIT 100;

-- Metrics from event table
SELECT timestamp, record:metric_name::string as metric, record:value as value
FROM <EVENT_TABLE>
WHERE resource_attributes:"snow.service.name" = '<SERVICE_NAME>'
  AND record_type = 'METRIC'
ORDER BY timestamp DESC
LIMIT 100;
```

---

## Service Management Reference

**Suspend/Resume:**
```sql
ALTER SERVICE <SERVICE_NAME> SUSPEND;
ALTER SERVICE <SERVICE_NAME> RESUME;
```

**Auto-suspend (default 30 min):**
```sql
ALTER SERVICE <SERVICE_NAME> SET AUTO_SUSPEND_SECS = <seconds>;
```

**Delete service:**
```sql
DROP SERVICE <SERVICE_NAME>;
```

**Scale service:**
```sql
ALTER SERVICE <SERVICE_NAME> SET MIN_INSTANCES = <n> MAX_INSTANCES = <n>;
```

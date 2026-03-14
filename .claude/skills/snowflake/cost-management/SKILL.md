---
name: cost-management
description: "Snowflake billing and credit analysis - generates SQL queries against ACCOUNT_USAGE billing/metering views to analyze Snowflake account charges and credit consumption (compute, storage, data transfer costs). Use for: virtual warehouse costs, credit consumption, storage costs, query compute costs, serverless compute costs, cost attribution by team/department, budget tracking, cost anomaly detection, spend optimization. Triggers: costs, spending, credits, bills, billing, charges, expensive, budget, warehouse costs, storage costs, how much did it cost, cost breakdown, top spenders, cost allocation."
location: system
---

# Cost Management Instructions

Generate SQL queries against Snowflake ACCOUNT_USAGE cost and metering data using the embedded semantic model.

## When to Use

**Warehouse & Compute:** Warehouse costs, compute pools, Snowpark containers, resize events, utilization  
**Storage:** Database/stage storage usage, growth trends, optimization opportunities  
**Query Costs:** Expensive queries, parameterized patterns, query acceleration, user attribution  
**Attribution:** Team/department cost breakdown via tags, untagged resources, budget tracking  
**Anomalies:** Automated detection, variance analysis, week/month-over-week comparisons  
**Services:** Serverless tasks, Cortex AI (Analyst/Functions), clustering, data transfer

## Workflow

### Step 1: Parse Question → Identify Domain

- Warehouse costs → WAREHOUSE_METERING, METERING
- Query costs → QUERY_ATTRIBUTION, QUERY_HISTORY
- Storage → DATABASE_STORAGE, STAGE_STORAGE
- Team attribution → TAG_REFERENCES + cost tables
- Anomalies → ANOMALIES_DAILY
- Service-specific → CORTEX_*, SERVERLESS_TASK_HISTORY, SNOWPARK_CONTAINER_SERVICES

### Step 2: Check Verified Queries FIRST

Search the embedded semantic model's `verified_queries` section (90+ queries) for matching patterns:
- Spending/costs → "Where is my money going", "Top warehouses/users"
- Time comparisons → "Week-over-week", "Month-over-month", "Why has my cost increased"
- Anomalies → "Cost anomaly analysis", "Anomaly trends"
- Teams/attribution → "Team cost breakdown", "Team attribution"
- Services → Cortex, serverless tasks, clustering, data transfer queries

**If match found:** Adapt the verified query SQL (adjust time filters, object names, limits). Replace `__table_name` with `SNOWFLAKE.ACCOUNT_USAGE.TABLE_NAME` from base_table definition.

**If no match:** Generate SQL using semantic model table definitions and similar verified queries as structural reference.

### Step 3: SQL Construction Guidelines

- All tables in `SNOWFLAKE.ACCOUNT_USAGE` schema
- Use ROUND() for credit amounts (2 decimal places)
- For anomaly queries, ALWAYS filter on `IS_ANOMALY = TRUE` (not actual > forecasted)
- JOIN TAG_REFERENCES for cost attribution
- Apply time filters (common: last 7/30 days, month-to-date)
- Order by cost/credits DESC, use LIMIT for top-N queries

### Step 4: Execute Query

Return generated SQL and results.

## Key Notes

- Round credits to 2 decimals
- Anomaly detection requires `IS_ANOMALY = TRUE`
- TAG_REFERENCES enables team/department attribution
- METERING = cross-service view; specific tables = detail
- Apply time filters to avoid excessive data scanning
- 90+ verified queries embedded below with proven patterns

---

## Semantic Model

Semantic model embedded below:

name: cost_management
description: Semantic view covering account level cost related views
tables:
  - name: ANOMALIES_DAILY
    synonyms:
      - cost anomalies
      - spending anomalies
      - usage anomalies
      - anomaly detection
    description: Daily cost anomaly detection results with consumption patterns and anomaly indicators
    base_table:
      database: SNOWFLAKE
      schema: ACCOUNT_USAGE
      table: ANOMALIES_DAILY
    primary_key:
      columns:
        - DATE
        - ANOMALY_ID
    dimensions:
      - name: ANOMALY_ID
        synonyms:
          - anomaly identifier
        description: System-generated identifier for the anomaly detection record
        expr: anomaly_id
        data_type: VARCHAR(16777216)
      - name: DATE
        synonyms:
          - anomaly date
          - detection date
        description: Day in UTC when the consumption occurred
        expr: date
        data_type: DATE
      - name: IS_ANOMALY
        synonyms:
          - anomaly flag
          - is cost anomaly
          - anomaly detected
          - true anomaly
          - actual anomaly
        description: "CRITICAL: This boolean field is the authoritative indicator of anomalies. Only rows where is_anomaly = TRUE represent actual cost anomalies. Do not assume actual_value > forecasted_value means anomaly - use this field instead."
        expr: is_anomaly
        data_type: BOOLEAN
    facts:
      - name: ACTUAL_VALUE
        description: Amount of consumption measured in credits
        expr: actual_value
        data_type: NUMBER(38,2)
      - name: FORECASTED_VALUE
        description: Predicted consumption based on the anomaly-detecting algorithm, measured in credits
        expr: forecasted_value
        data_type: NUMBER(38,2)
      - name: LOWER_BOUND
        description: Predicted lowest level of consumption based on the anomaly-detecting algorithm, measured in credits
        expr: lower_bound
        data_type: NUMBER(38,2)
      - name: UPPER_BOUND
        description: Predicted highest level of consumption based on the anomaly-detecting algorithm, measured in credits
        expr: upper_bound
        data_type: NUMBER(38,2)
    metrics:
      - name: ANOMALY_PERCENTAGE
        description: Percentage of days that were identified as cost anomalies
        expr: (SUM(CASE WHEN anomalies_daily.is_anomaly THEN 1 ELSE 0 END) * 100.0 / COUNT(anomalies_daily.date))
      - name: AVERAGE_VARIANCE_FROM_FORECAST
        description: Average absolute variance between actual and forecasted consumption in credits
        expr: AVG(ABS(anomalies_daily.actual_value - anomalies_daily.forecasted_value))
      - name: TOTAL_ANOMALOUS_CONSUMPTION
        description: Total consumption in credits during anomalous periods
        expr: SUM(CASE WHEN anomalies_daily.is_anomaly THEN anomalies_daily.actual_value ELSE 0 END)
  - name: AUTOMATIC_CLUSTERING_HISTORY
    synonyms:
      - clustering history
      - automatic clustering
      - clustering usage
      - clustering costs
      - table clustering
    description: Historical record of automatic clustering operations including credits consumed, bytes and rows reclustered for each table clustering event
    base_table:
      database: SNOWFLAKE
      schema: ACCOUNT_USAGE
      table: AUTOMATIC_CLUSTERING_HISTORY
    primary_key:
      columns:
        - START_TIME
        - TABLE_ID
    dimensions:
      - name: DATABASE_ID
        synonyms:
          - clustering database id
        description: Internal identifier for the database containing the clustered table
        expr: database_id
        data_type: NUMBER(38,0)
      - name: DATABASE_NAME
        synonyms:
          - clustering database
        description: Name of the database containing the clustered table
        expr: database_name
        data_type: VARCHAR(134217728)
      - name: END_TIME
        synonyms:
          - clustering end time
          - clustering end
        description: End of the automatic clustering time range
        expr: end_time
        data_type: TIMESTAMP_LTZ(9)
      - name: INSTANCE_ID
        synonyms:
          - clustering instance id
        description: Internal identifier for the instance that the table belongs to
        expr: instance_id
        data_type: NUMBER(38,0)
      - name: SCHEMA_ID
        synonyms:
          - clustering schema id
        description: Internal identifier for the schema containing the clustered table
        expr: schema_id
        data_type: NUMBER(38,0)
      - name: SCHEMA_NAME
        synonyms:
          - clustering schema
        description: Name of the schema containing the clustered table
        expr: schema_name
        data_type: VARCHAR(134217728)
      - name: START_TIME
        synonyms:
          - clustering start time
          - clustering start
        description: Start of the automatic clustering time range
        expr: start_time
        data_type: TIMESTAMP_LTZ(9)
      - name: TABLE_ID
        synonyms:
          - clustering table id
        description: Internal identifier for the table that was clustered
        expr: table_id
        data_type: NUMBER(38,0)
      - name: TABLE_NAME
        synonyms:
          - clustering table
          - clustered table
        description: Name of the table that was clustered
        expr: table_name
        data_type: VARCHAR(134217728)
    facts:
      - name: CREDITS_USED
        synonyms:
          - clustering cost
          - clustering spend
          - clustering charges
          - clustering money
          - clustering billing
        description: Credits billed for automatic clustering during the time window
        expr: credits_used
        data_type: NUMBER(38,9)
      - name: NUM_BYTES_RECLUSTERED
        synonyms:
          - bytes clustered
          - clustering bytes
          - reclustered bytes
        description: Number of bytes reclustered during the clustering operation
        expr: num_bytes_reclustered
        data_type: NUMBER(38,0)
      - name: NUM_ROWS_RECLUSTERED
        synonyms:
          - rows clustered
          - clustering rows
          - reclustered rows
        description: Number of rows reclustered during the clustering operation
        expr: num_rows_reclustered
        data_type: NUMBER(38,0)
    metrics:
      - name: AVERAGE_CLUSTERING_CREDITS
        synonyms:
          - average clustering cost
          - avg clustering spend
          - clustering cost per operation
        description: Average credits consumed per automatic clustering operation
        expr: AVG(automatic_clustering_history.credits_used)
      - name: TOTAL_BYTES_RECLUSTERED
        synonyms:
          - total clustering bytes
          - total bytes clustered
          - clustering data volume
        description: Total bytes reclustered across all automatic clustering operations
        expr: SUM(automatic_clustering_history.num_bytes_reclustered)
      - name: TOTAL_CLUSTERING_CREDITS
        synonyms:
          - total clustering cost
          - total clustering spend
          - clustering spending
          - clustering billing
        description: Total credits consumed by automatic clustering across all tables and time periods
        expr: SUM(automatic_clustering_history.credits_used)
      - name: TOTAL_ROWS_RECLUSTERED
        synonyms:
          - total clustering rows
          - total rows clustered
          - clustering row count
        description: Total rows reclustered across all automatic clustering operations
        expr: SUM(automatic_clustering_history.num_rows_reclustered)
  - name: CORTEX_ANALYST_USAGE_HISTORY
    synonyms:
      - cortex analyst
      - analyst usage
      - data assistant
      - conversational AI
      - AI analyst assistant
      - analyst requests
    description: Historical usage and credits consumed by Cortex Analyst (conversational data analysis assistant) requests, aggregated hourly by user
    base_table:
      database: SNOWFLAKE
      schema: ACCOUNT_USAGE
      table: CORTEX_ANALYST_USAGE_HISTORY
    primary_key:
      columns:
        - START_TIME
        - USERNAME
    dimensions:
      - name: END_TIME
        synonyms:
          - analyst end time
          - cortex end time
        description: End of the time range when Cortex Analyst message responses were sent
        expr: end_time
        data_type: TIMESTAMP_LTZ(9)
      - name: START_TIME
        synonyms:
          - analyst start time
          - cortex start time
        description: Start of the time range when Cortex Analyst message requests were received
        expr: start_time
        data_type: TIMESTAMP_LTZ(9)
      - name: USERNAME
        synonyms:
          - analyst user
          - data assistant user
          - conversational AI user
          - analyst requesting user
        description: Username of the user who sent Cortex Analyst message requests
        expr: username
        data_type: VARCHAR(16777216)
    facts:
      - name: CREDITS
        synonyms:
          - analyst cost
          - analyst spend
          - analyst money
          - analyst charges
          - conversational AI cost
          - data assistant cost
          - analyst billing
        description: Credits consumed by Cortex Analyst (conversational data analysis assistant) requests during the time window
        expr: credits
        data_type: NUMBER(38,9)
      - name: REQUEST_COUNT
        synonyms:
          - analyst requests
          - analyst messages
          - conversational requests
          - data assistant requests
        description: Number of messages sent to Cortex Analyst during the time window
        expr: request_count
        data_type: NUMBER(18,0)
    metrics:
      - name: AVERAGE_CREDITS_PER_REQUEST
        synonyms:
          - analyst cost per request
          - cost per analyst request
          - analyst cost efficiency
          - conversational AI cost efficiency
        description: Average credits consumed per Cortex Analyst message request
        expr: SUM(cortex_analyst_usage_history.credits) / SUM(cortex_analyst_usage_history.request_count)
      - name: TOTAL_CORTEX_ANALYST_CREDITS
        synonyms:
          - total analyst cost
          - total analyst spend
          - total analyst money
          - analyst spending
          - conversational AI spending
          - data assistant billing
        description: Total credits consumed by Cortex Analyst (conversational data analysis assistant) across all users and time periods
        expr: SUM(cortex_analyst_usage_history.credits)
      - name: TOTAL_CORTEX_ANALYST_REQUESTS
        synonyms:
          - total analyst requests
          - total analyst messages
          - total conversational requests
          - analyst request count
        description: Total number of messages sent to Cortex Analyst across all users and time periods
        expr: SUM(cortex_analyst_usage_history.request_count)
      - name: UNIQUE_CORTEX_USERS
        synonyms:
          - unique analyst users
          - analyst user count
          - conversational AI users
          - data assistant users
        description: Number of unique users who have sent requests to Cortex Analyst
        expr: COUNT(DISTINCT cortex_analyst_usage_history.username)
  - name: CORTEX_FUNCTIONS_USAGE_HISTORY
    synonyms:
      - cortex functions
      - function usage
      - AI functions
      - cortex function usage
      - function usage history
      - AI function costs
    description: Hourly aggregated usage history of Cortex Functions (AI_COMPLETE, AI_TRANSLATE, etc.) including tokens and credits consumed by function and model with time dimensions for trend analysis
    base_table:
      database: SNOWFLAKE
      schema: ACCOUNT_USAGE
      table: CORTEX_FUNCTIONS_USAGE_HISTORY
    primary_key:
      columns:
        - START_TIME
        - FUNCTION_NAME
        - MODEL_NAME
        - WAREHOUSE_ID
    dimensions:
      - name: END_TIME
        synonyms:
          - function end time
          - AI function end
          - cortex function end
          - function end
        description: End of the hour-long time window in which the Cortex function usage took place
        expr: end_time
        data_type: TIMESTAMP_LTZ(9)
      - name: FUNCTION_NAME
        synonyms:
          - function name
          - AI function name
          - cortex function
          - function type
        description: Name of the Cortex function (e.g., COMPLETE, TRANSLATE) used during the time window
        expr: function_name
        data_type: VARCHAR(134217728)
      - name: MODEL_NAME
        synonyms:
          - model name
          - AI model name
          - function model
          - model type
        description: Name of the AI model used during the time window (empty for functions where model is not specified)
        expr: model_name
        data_type: VARCHAR(134217728)
      - name: START_TIME
        synonyms:
          - function start time
          - AI function start
          - cortex function start
          - function start
        description: Start of the hour-long time window in which the Cortex function usage took place
        expr: start_time
        data_type: TIMESTAMP_LTZ(9)
      - name: WAREHOUSE_ID
        synonyms:
          - function warehouse
          - AI function warehouse
          - cortex warehouse
          - function warehouse id
        description: ID of the warehouse that executed the Cortex functions during the time window
        expr: warehouse_id
        data_type: NUMBER(38,0)
    facts:
      - name: TOKENS
        synonyms:
          - function tokens
          - AI function tokens
          - cortex tokens
          - function token usage
        description: Number of tokens consumed by Cortex functions during the hour-long time window for the function, model, and warehouse combination
        expr: tokens
        data_type: NUMBER(38,0)
      - name: TOKEN_CREDITS
        synonyms:
          - function cost
          - AI function cost
          - function spend
          - function charges
          - function billing
        description: Credits consumed by Cortex functions during the hour-long time window for the function, model, and warehouse combination
        expr: token_credits
        data_type: NUMBER(38,9)
    metrics:
      - name: AVERAGE_FUNCTION_CREDITS
        synonyms:
          - average function cost
          - cost per hour
          - function cost efficiency
          - function cost average
        description: Average credits consumed per hour by Cortex functions
        expr: AVG(cortex_functions_usage_history.token_credits)
      - name: AVERAGE_FUNCTION_TOKENS
        synonyms:
          - average function tokens
          - tokens per hour
          - function token efficiency
          - function token average
        description: Average tokens consumed per hour by Cortex functions
        expr: AVG(cortex_functions_usage_history.tokens)
      - name: TOTAL_FUNCTION_CREDITS
        synonyms:
          - total function cost
          - total AI function cost
          - total function spend
          - function spending
          - function billing
        description: Total credits consumed by Cortex functions across all time windows, functions, and models
        expr: SUM(cortex_functions_usage_history.token_credits)
      - name: TOTAL_FUNCTION_TOKENS
        synonyms:
          - total function tokens
          - total AI function tokens
          - total cortex tokens
          - function token usage
        description: Total tokens consumed by Cortex functions across all time windows, functions, and models
        expr: SUM(cortex_functions_usage_history.tokens)
      - name: TOTAL_FUNCTION_WINDOWS
        synonyms:
          - total function windows
          - function time window count
          - function time periods
        description: Total number of hourly time windows with Cortex function usage recorded
        expr: COUNT(cortex_functions_usage_history.start_time)
  - name: DATABASE_STORAGE
    synonyms:
      - database storage
      - storage usage
      - historical database storage
    description: Average daily storage usage per database, including table, Time Travel, Fail-safe, and hybrid table storage
    base_table:
      database: SNOWFLAKE
      schema: ACCOUNT_USAGE
      table: DATABASE_STORAGE_USAGE_HISTORY
    primary_key:
      columns:
        - USAGE_DATE
        - DATABASE_ID
    dimensions:
      - name: DATABASE_ID
        synonyms:
          - db id
        description: Internal database ID
        expr: database_id
        data_type: NUMBER(38,0)
      - name: DATABASE_NAME
        synonyms:
          - db name
        description: Name of the database
        expr: database_name
        data_type: VARCHAR(134217728)
      - name: USAGE_DATE
        synonyms:
          - storage date
        description: Date of the storage usage record
        expr: usage_date
        data_type: DATE
    facts:
      - name: AVERAGE_DATABASE_BYTES
        description: Average daily bytes used in database tables and Time Travel
        expr: average_database_bytes
        data_type: FLOAT
      - name: AVERAGE_FAILSAFE_BYTES
        description: Average daily bytes stored in Fail-safe
        expr: average_failsafe_bytes
        data_type: FLOAT
      - name: AVERAGE_HYBRID_TABLE_STORAGE_BYTES
        description: Average daily bytes used by hybrid table storage
        expr: average_hybrid_table_storage_bytes
        data_type: FLOAT
    metrics:
      - name: TOTAL_AVERAGE_DATABASE_BYTES
        description: Sum of average daily database storage usage (table + Time Travel)
        expr: SUM(database_storage.average_database_bytes)
      - name: TOTAL_AVERAGE_FAILSAFE_BYTES
        description: Sum of average daily Fail-safe storage
        expr: SUM(database_storage.average_failsafe_bytes)
      - name: TOTAL_AVERAGE_HYBRID_TABLE_STORAGE_BYTES
        description: Sum of average daily hybrid table storage
        expr: SUM(database_storage.average_hybrid_table_storage_bytes)
  - name: DATA_TRANSFER
    synonyms:
      - data movement
      - cross-region transfer
      - cloud egress
      - network transfer
    description: Cross-region, cross-cloud, or external data transfer history
    base_table:
      database: SNOWFLAKE
      schema: ACCOUNT_USAGE
      table: DATA_TRANSFER_HISTORY
    primary_key:
      columns:
        - START_TIME
        - TARGET_REGION
    dimensions:
      - name: END_TIME
        synonyms:
          - transfer end time
        description: End of the data transfer window
        expr: end_time
        data_type: TIMESTAMP_LTZ(9)
      - name: SOURCE_CLOUD
        synonyms:
          - origin cloud
          - source cloud provider
        description: Cloud provider of the source region
        expr: source_cloud
        data_type: VARCHAR(134217728)
      - name: SOURCE_REGION
        synonyms:
          - origin region
        description: Region where the data originated
        expr: source_region
        data_type: VARCHAR(134217728)
      - name: START_TIME
        synonyms:
          - transfer start time
        description: Start of the data transfer window
        expr: start_time
        data_type: TIMESTAMP_LTZ(9)
      - name: TARGET_CLOUD
        synonyms:
          - destination cloud
          - target cloud provider
        description: Cloud provider of the target region
        expr: target_cloud
        data_type: VARCHAR(134217728)
      - name: TARGET_REGION
        synonyms:
          - destination region
        description: Destination region of the data transfer
        expr: target_region
        data_type: VARCHAR(134217728)
      - name: TRANSFER_TYPE
        synonyms:
          - type of transfer
          - transfer classification
        description: "Classification of transfer: cross-region, cross-cloud, or external"
        expr: transfer_type
        data_type: VARCHAR(134217728)
    facts:
      - name: BYTES_TRANSFERRED
        description: Total bytes transferred during the interval
        expr: bytes_transferred
        data_type: FLOAT
    metrics:
      - name: TOTAL_BYTES_TRANSFERRED
        description: Total bytes transferred between regions, clouds, or externally
        expr: SUM(data_transfer.bytes_transferred)
      - name: TOTAL_GB_TRANSFERRED
        description: Total data transferred in gigabytes
        expr: SUM(data_transfer.bytes_transferred) / POW(1024, 3)
      - name: TOTAL_TB_TRANSFERRED
        description: Total data transferred in terabytes
        expr: SUM(data_transfer.bytes_transferred) / POW(1024, 4)
  - name: METERING
    synonyms:
      - credit usage
      - object metering
      - resource usage
      - spend history
      - daily usage summary
      - summary usage
    description: Hourly credit usage per object (e.g., warehouse, task)
    base_table:
      database: SNOWFLAKE
      schema: ACCOUNT_USAGE
      table: METERING_HISTORY
    primary_key:
      columns:
        - START_TIME
        - ENTITY_ID
    dimensions:
      - name: ENTITY_ID
        synonyms:
          - object id
          - resource id
        description: ID of the Snowflake object consuming credits
        expr: entity_id
        data_type: NUMBER(38,0)
      - name: NAME
        synonyms:
          - object name
          - resource name
        description: Name of the Snowflake object consuming credits
        expr: name
        data_type: VARCHAR(16777216)
      - name: SERVICE_TYPE
        synonyms:
          - service
          - usage type
        description: Type of Snowflake service (e.g., WAREHOUSE, CLOUD_SERVICES)
        expr: service_type
        data_type: VARCHAR(134217728)
      - name: START_TIME
        synonyms:
          - usage start time
          - start timestamp
        description: Timestamp when usage period begins
        expr: start_time
        data_type: TIMESTAMP_LTZ(0)
    facts:
      - name: CREDITS_USED
        synonyms:
          - total credits
          - credit consumption
          - usage cost
          - credit usage
        description: Total credits consumed during the recorded hour
        expr: credits_used
        data_type: NUMBER(38,9)
      - name: CREDITS_USED_CLOUD_SERVICES
        synonyms:
          - cloud services cost
          - overhead cost
          - cloud spend
          - cloud charges
          - services billing
        description: Credits used by cloud service overhead
        expr: credits_used_cloud_services
        data_type: NUMBER(38,9)
      - name: CREDITS_USED_COMPUTE
        synonyms:
          - compute credits
          - compute cost
          - warehouse credits
        description: Credits attributed to compute operations
        expr: credits_used_compute
        data_type: NUMBER(38,9)
    metrics:
      - name: TOTAL_CLOUD_SERVICES_CREDITS
        synonyms:
          - total cloud cost
          - total overhead cost
          - cloud services spending
          - overhead spending
        description: Total cloud services credits used
        expr: SUM(metering.credits_used_cloud_services)
      - name: TOTAL_COMPUTE_CREDITS
        synonyms:
          - total compute cost
          - total compute spend
          - total compute money
          - compute spending
          - warehouse spending
        description: Total compute credits used
        expr: SUM(metering.credits_used_compute)
      - name: TOTAL_CREDITS_USED
        synonyms:
          - total money
          - total cost
          - total spend
          - total spending
          - total charges
          - total bill
          - total billing
          - where is my money going
          - what am I spending on
          - cost breakdown
          - spending breakdown
        description: Total Snowflake credits used
        expr: SUM(metering.credits_used)
  - name: QUERY_ACCELERATION_HISTORY
    synonyms:
      - query acceleration
      - QAS history
      - query acceleration service
      - accelerated queries
    description: Historical usage and credits consumed by the Query Acceleration Service for warehouse-level acceleration
    base_table:
      database: SNOWFLAKE
      schema: ACCOUNT_USAGE
      table: QUERY_ACCELERATION_HISTORY
    primary_key:
      columns:
        - START_TIME
        - WAREHOUSE_ID
    dimensions:
      - name: END_TIME
        synonyms:
          - acceleration end time
          - QAS end time
        description: End of the time range when Query Acceleration Service was active
        expr: end_time
        data_type: TIMESTAMP_LTZ(9)
      - name: START_TIME
        synonyms:
          - acceleration start time
          - QAS start time
        description: Start of the time range when Query Acceleration Service was active
        expr: start_time
        data_type: TIMESTAMP_LTZ(9)
      - name: WAREHOUSE_ID
        synonyms:
          - acceleration warehouse id
          - QAS warehouse id
        description: Internal identifier of the warehouse that used Query Acceleration Service
        expr: warehouse_id
        data_type: NUMBER(38,0)
      - name: WAREHOUSE_NAME
        synonyms:
          - acceleration warehouse
          - QAS warehouse name
        description: Name of the warehouse that consumed Query Acceleration Service credits
        expr: warehouse_name
        data_type: VARCHAR(134217728)
    facts:
      - name: CREDITS_USED
        synonyms:
          - acceleration cost
          - acceleration spend
          - QAS money
          - acceleration charges
          - query acceleration billing
        description: Credits consumed by the Query Acceleration Service during the time window (Enterprise Edition feature)
        expr: credits_used
        data_type: NUMBER(38,9)
    metrics:
      - name: AVERAGE_CREDITS_PER_WINDOW
        synonyms:
          - average acceleration cost
          - average QAS spend
          - QAS cost per window
        description: Average Query Acceleration Service credits consumed per time window
        expr: AVG(query_acceleration_history.credits_used)
      - name: TOTAL_ACCELERATION_CREDITS
        description: Total credits consumed by Query Acceleration Service across all warehouses and time periods
        expr: SUM(query_acceleration_history.credits_used)
  - name: QUERY_ATTRIBUTION
    synonyms:
      - query cost
      - query attribution
      - query credits
      - expensive queries
      - top queries
      - costliest queries
    description: Compute credits attributed to each query execution over the past 365 days
    base_table:
      database: SNOWFLAKE
      schema: ACCOUNT_USAGE
      table: QUERY_ATTRIBUTION_HISTORY
    primary_key:
      columns:
        - QUERY_ID
    dimensions:
      - name: END_TIME
        synonyms:
          - query end time
        description: Timestamp when query execution ended
        expr: end_time
        data_type: TIMESTAMP_LTZ(3)
      - name: PARENT_QUERY_ID
        synonyms:
          - parent query
        description: ID of the parent query if part of a multi-statement execution
        expr: parent_query_id
        data_type: VARCHAR(16777216)
      - name: QUERY_HASH
        synonyms:
          - query signature
        description: Hash representing the query structure (normalized)
        expr: query_hash
        data_type: VARCHAR(16777216)
      - name: QUERY_ID
        synonyms:
          - query
        description: Unique identifier for the query
        expr: query_id
        data_type: VARCHAR(16777216)
      - name: QUERY_PARAMETERIZED_HASH
        synonyms:
          - parameterized query hash
          - query family
        description: Hash of the query with parameters abstracted
        expr: query_parameterized_hash
        data_type: VARCHAR(16777216)
      - name: QUERY_TAG
        synonyms:
          - query tag
        description: Custom tag associated with the query (for attribution)
        expr: query_tag
        data_type: VARCHAR(16777216)
      - name: ROOT_QUERY_ID
        synonyms:
          - root query
        description: ID of the root query in a query call chain
        expr: root_query_id
        data_type: VARCHAR(16777216)
      - name: START_TIME
        synonyms:
          - query start time
        description: Timestamp when query execution started
        expr: start_time
        data_type: TIMESTAMP_LTZ(3)
      - name: USER_NAME
        synonyms:
          - user
        description: Username that executed the query
        expr: user_name
        data_type: VARCHAR(16777216)
      - name: WAREHOUSE_ID
        synonyms:
          - query warehouse id
        description: ID of the warehouse used for the query
        expr: warehouse_id
        data_type: NUMBER(38,0)
      - name: WAREHOUSE_NAME
        synonyms:
          - query warehouse
        description: Name of the warehouse used for the query
        expr: warehouse_name
        data_type: VARCHAR(134217728)
    facts:
      - name: CREDITS_ATTRIBUTED_COMPUTE
        synonyms:
          - query cost
          - query spend
          - query charges
          - query money
          - individual query cost
        description: Compute credits attributed to this query execution
        expr: credits_attributed_compute
        data_type: FLOAT
      - name: CREDITS_USED_QUERY_ACCELERATION
        synonyms:
          - query acceleration cost
          - QAS cost
          - query acceleration spend
          - query acceleration money
        description: Credits used by Query Acceleration Service for this query (if applicable)
        expr: credits_used_query_acceleration
        data_type: FLOAT
    metrics:
      - name: TOTAL_QUERY_ACCELERATION_CREDITS
        synonyms:
          - total QAS cost
          - total acceleration spend
          - total acceleration money
          - acceleration spending
        description: Total credits used by Query Acceleration Service for queries
        expr: SUM(query_attribution.credits_used_query_acceleration)
      - name: TOTAL_QUERY_COMPUTE_CREDITS
        synonyms:
          - total query cost
          - total query spend
          - total query money
          - query spending
          - query cost breakdown
        description: Total compute credits attributed to query execution
        expr: SUM(query_attribution.credits_attributed_compute)
      - name: TOTAL_QUERY_CREDITS
        synonyms:
          - total query cost breakdown
          - complete query spend
          - all query costs
          - query cost analysis
        description: "Total query cost: compute + query acceleration credits"
        expr: SUM(COALESCE(query_attribution.credits_attributed_compute, 0) + COALESCE(query_attribution.credits_used_query_acceleration, 0))
  - name: QUERY_HISTORY
    synonyms:
      - query logs
      - query history
      - query execution
    description: Detailed history of executed queries, including text, execution time, and performance metadata
    base_table:
      database: SNOWFLAKE
      schema: ACCOUNT_USAGE
      table: QUERY_HISTORY
    primary_key:
      columns:
        - QUERY_ID
    dimensions:
      - name: DATABASE_NAME
        synonyms:
          - execution db
        description: Name of the database in use when query was executed
        expr: database_name
        data_type: VARCHAR(134217728)
      - name: END_TIME
        synonyms:
          - query end
        description: Timestamp when the query finished execution
        expr: end_time
        data_type: TIMESTAMP_LTZ(6)
      - name: QUERY_ID
        synonyms:
          - query
        description: Unique identifier for the query
        expr: query_id
        data_type: VARCHAR(134217728)
      - name: QUERY_TEXT
        synonyms:
          - sql text
          - query body
        description: Text of the executed query
        expr: query_text
        data_type: VARCHAR(134217728)
      - name: QUERY_TYPE
        synonyms:
          - sql type
          - query kind
        description: Type of query (e.g., SELECT, INSERT)
        expr: query_type
        data_type: VARCHAR(134217728)
      - name: ROLE_NAME
        synonyms:
          - active role
        description: Role active during query execution
        expr: role_name
        data_type: VARCHAR(134217728)
      - name: SCHEMA_NAME
        synonyms:
          - execution schema
        description: Name of the schema in use when query was executed
        expr: schema_name
        data_type: VARCHAR(134217728)
      - name: START_TIME
        synonyms:
          - query start
        description: Timestamp when the query started execution
        expr: start_time
        data_type: TIMESTAMP_LTZ(6)
      - name: USER_NAME
        synonyms:
          - query user
        description: Username of the user who ran the query
        expr: user_name
        data_type: VARCHAR(134217728)
      - name: WAREHOUSE_ID
        synonyms:
          - execution warehouse id
        description: ID of the warehouse used to run the query
        expr: warehouse_id
        data_type: NUMBER(38,0)
      - name: WAREHOUSE_NAME
        synonyms:
          - execution warehouse
        description: Name of the warehouse used to run the query
        expr: warehouse_name
        data_type: VARCHAR(134217728)
    facts:
      - name: BYTES_SCANNED
        description: Number of bytes scanned by the query
        expr: bytes_scanned
        data_type: NUMBER(38,0)
      - name: BYTES_WRITTEN
        description: Number of bytes written by the query
        expr: bytes_written
        data_type: NUMBER(38,0)
      - name: ERROR_CODE
        description: Error code if the query failed, NULL if successful
        expr: error_code
        data_type: VARCHAR(134217728)
      - name: EXECUTION_TIME
        description: Actual time in milliseconds spent executing the query
        expr: execution_time
        data_type: NUMBER(38,0)
      - name: QUERY_PARAMETERIZED_HASH
        description: Hash value of the parameterized query
        expr: query_parameterized_hash
        data_type: VARCHAR(134217728)
      - name: ROWS_DELETED
        description: Number of rows deleted by the query (if applicable)
        expr: rows_deleted
        data_type: NUMBER(38,0)
      - name: ROWS_INSERTED
        description: Number of rows inserted by the query (if applicable)
        expr: rows_inserted
        data_type: NUMBER(38,0)
      - name: ROWS_PRODUCED
        description: Number of rows returned by the query
        expr: rows_produced
        data_type: NUMBER(38,0)
      - name: ROWS_UPDATED
        description: Number of rows updated by the query (if applicable)
        expr: rows_updated
        data_type: NUMBER(38,0)
      - name: TOTAL_ELAPSED_TIME
        description: Total time in milliseconds the query spent executing, including compilation, queueing, and execution
        expr: total_elapsed_time
        data_type: NUMBER(38,0)
    metrics:
      - name: TOTAL_BYTES_SCANNED
        description: Total bytes scanned by queries
        expr: SUM(query_history.bytes_scanned)
      - name: TOTAL_BYTES_WRITTEN
        description: Total bytes written by queries
        expr: SUM(query_history.bytes_written)
      - name: TOTAL_ELAPSED_TIME_MS
        description: Total elapsed time including compilation, queueing, and execution (milliseconds)
        expr: SUM(query_history.total_elapsed_time)
      - name: TOTAL_EXECUTION_TIME_MS
        description: Total execution time across all queries (milliseconds)
        expr: SUM(query_history.execution_time)
      - name: TOTAL_FAILED_QUERIES
        description: Total number of failed queries
        expr: SUM(CASE WHEN query_history.error_code IS NOT NULL THEN 1 ELSE 0 END)
      - name: TOTAL_QUERIES
        description: Total number of queries executed
        expr: COUNT(query_history.query_id)
      - name: TOTAL_ROWS_PRODUCED
        description: Total rows produced by queries
        expr: SUM(query_history.rows_produced)
  - name: SERVERLESS_TASK_HISTORY
    synonyms:
      - serverless tasks
      - task usage
      - serverless task usage
      - task history
    description: Historical usage and credits consumed by serverless tasks with task-level and schema/database attribution
    base_table:
      database: SNOWFLAKE
      schema: ACCOUNT_USAGE
      table: SERVERLESS_TASK_HISTORY
    primary_key:
      columns:
        - START_TIME
        - TASK_ID
    dimensions:
      - name: DATABASE_ID
        synonyms:
          - task database id
        description: Internal identifier for the database containing the serverless task
        expr: database_id
        data_type: NUMBER(38,0)
      - name: DATABASE_NAME
        synonyms:
          - task database
        description: Name of the database containing the serverless task
        expr: database_name
        data_type: VARCHAR(134217728)
      - name: END_TIME
        synonyms:
          - task end time
          - serverless task end
        description: End of the time range when serverless task usage occurred
        expr: end_time
        data_type: TIMESTAMP_LTZ(9)
      - name: INSTANCE_ID
        synonyms:
          - task instance id
        description: Internal identifier for the instance which the serverless task belongs to
        expr: instance_id
        data_type: NUMBER(38,0)
      - name: SCHEMA_ID
        synonyms:
          - task schema id
        description: Internal identifier for the schema containing the serverless task
        expr: schema_id
        data_type: NUMBER(38,0)
      - name: SCHEMA_NAME
        synonyms:
          - task schema
        description: Name of the schema containing the serverless task
        expr: schema_name
        data_type: VARCHAR(134217728)
      - name: START_TIME
        synonyms:
          - task start time
          - serverless task start
        description: Start of the time range when serverless task usage occurred
        expr: start_time
        data_type: TIMESTAMP_LTZ(9)
      - name: TASK_ID
        synonyms:
          - serverless task id
        description: Internal identifier for the serverless task
        expr: task_id
        data_type: NUMBER(38,0)
      - name: TASK_NAME
        synonyms:
          - task
          - serverless task name
        description: Name of the serverless task
        expr: task_name
        data_type: VARCHAR(134217728)
    facts:
      - name: CREDITS_USED
        synonyms:
          - task cost
          - task spend
          - task money
          - task charges
          - serverless cost
          - serverless spend
        description: Credits consumed by serverless tasks during the time window
        expr: credits_used
        data_type: NUMBER(38,9)
    metrics:
      - name: AVERAGE_CREDITS_PER_TASK_WINDOW
        synonyms:
          - average task cost
          - average task spend
          - task cost per execution
        description: Average serverless task credits consumed per task execution window
        expr: AVG(serverless_task_history.credits_used)
      - name: TOTAL_SERVERLESS_TASK_CREDITS
        synonyms:
          - total task cost
          - total task spend
          - total task money
          - serverless spending
          - task billing
        description: Total credits consumed by serverless tasks across all tasks and time periods
        expr: SUM(serverless_task_history.credits_used)
      - name: TOTAL_TASK_EXECUTIONS
        description: Total number of serverless task execution windows recorded
        expr: COUNT(serverless_task_history.task_id)
  - name: SNOWPARK_CONTAINER_SERVICES
    synonyms:
      - container services
      - snowpark usage
      - container usage
      - spcs
    description: Snowpark Container Services resource usage per compute pool and time window
    base_table:
      database: SNOWFLAKE
      schema: ACCOUNT_USAGE
      table: SNOWPARK_CONTAINER_SERVICES_HISTORY
    primary_key:
      columns:
        - START_TIME
        - COMPUTE_POOL_NAME
    dimensions:
      - name: APPLICATION_ID
        synonyms:
          - app id
        description: ID of the application that owns the compute pool (if any)
        expr: application_id
        data_type: NUMBER(38,0)
      - name: APPLICATION_NAME
        synonyms:
          - app name
        description: Name of the application associated with the compute pool (if any)
        expr: application_name
        data_type: VARCHAR(134217728)
      - name: COMPUTE_POOL_NAME
        synonyms:
          - pool
          - container pool
          - spcs pool
        description: Name of the compute pool that incurred the credit usage
        expr: compute_pool_name
        data_type: VARCHAR(16777216)
      - name: END_TIME
        synonyms:
          - spcs end time
        description: End time of the usage interval
        expr: end_time
        data_type: TIMESTAMP_LTZ(0)
      - name: IS_EXCLUSIVE
        synonyms:
          - exclusive usage
        description: TRUE if the compute pool was created exclusively for an application
        expr: is_exclusive
        data_type: BOOLEAN
      - name: START_TIME
        synonyms:
          - spcs start time
        description: Start time of the usage interval
        expr: start_time
        data_type: TIMESTAMP_LTZ(0)
    facts:
      - name: CREDITS_USED
        synonyms:
          - container cost
          - container spend
          - container charges
          - SPCS cost
          - container service money
        description: Total credits consumed by the container service during the hour
        expr: credits_used
        data_type: NUMBER(38,9)
    metrics:
      - name: TOTAL_CREDITS_USED
        synonyms:
          - total container cost
          - total container spend
          - total SPCS money
          - container service spending
          - container billing
        description: Total Snowflake credits consumed by Snowpark Container Services
        expr: SUM(snowpark_container_services.credits_used)
  - name: STAGE_STORAGE
    synonyms:
      - stage storage
      - internal stage usage
      - file stage usage
    description: Average daily internal stage storage usage (named and default stages)
    base_table:
      database: SNOWFLAKE
      schema: ACCOUNT_USAGE
      table: STAGE_STORAGE_USAGE_HISTORY
    primary_key:
      columns:
        - USAGE_DATE
    dimensions:
      - name: USAGE_DATE
        synonyms:
          - stage usage date
        description: Date of the stage storage usage record
        expr: usage_date
        data_type: DATE
    facts:
      - name: AVERAGE_STAGE_BYTES
        description: Average daily bytes used by internal stages (named and default)
        expr: average_stage_bytes
        data_type: NUMBER(38,6)
    metrics:
      - name: TOTAL_AVERAGE_STAGE_BYTES
        description: Sum of average daily internal stage storage
        expr: SUM(stage_storage.average_stage_bytes)
  - name: TAG_REFERENCES
    synonyms:
      - tags
      - object tags
      - tag mapping
    description: "Tag associations for Snowflake objects used for attributing cost or grouping usage. Contains apply_method field to distinguish between MANUAL (direct), INHERITED (from parent objects), PROPAGATED (automatic), and CLASSIFIED (auto-applied) tags. Note: Inheritance behavior may vary - test with your specific tagging setup."
    base_table:
      database: SNOWFLAKE
      schema: ACCOUNT_USAGE
      table: TAG_REFERENCES
    primary_key:
      columns:
        - OBJECT_NAME
        - TAG_NAME
        - TAG_SCHEMA
        - TAG_DATABASE
    dimensions:
      - name: APPLY_METHOD
        synonyms:
          - tag application method
          - tag source
          - how tag applied
        description: "How the tag was applied: MANUAL (directly set), INHERITED (from parent object), PROPAGATED (automatic propagation), CLASSIFIED (auto-applied for sensitive data)"
        expr: apply_method
        data_type: VARCHAR(16777216)
      - name: DOMAIN
        synonyms:
          - tag domain
          - object type
          - resource type
        description: Object type to which the tag is applied (e.g., WAREHOUSE)
        expr: domain
        data_type: VARCHAR(16777216)
      - name: OBJECT_NAME
        synonyms:
          - tagged object
          - tagged resource
          - resource name
        description: Name of the tagged object (e.g., warehouse name)
        expr: object_name
        data_type: VARCHAR(16777216)
      - name: TAG_DATABASE
        synonyms:
          - tag db
          - tag database
        description: Database where the tag is defined
        expr: tag_database
        data_type: VARCHAR(16777216)
      - name: TAG_NAME
        synonyms:
          - tag
          - team
          - team name
          - cost center
          - department
          - owner
          - group
          - classification
          - category
        description: Name of the tag applied to the object. Tags are schema-level objects used for data governance, cost attribution, compliance, and resource monitoring. Common examples include team, cost_center, data_classification, environment, or project.
        expr: tag_name
        data_type: VARCHAR(16777216)
      - name: TAG_SCHEMA
        synonyms:
          - tag namespace
          - tag schema
        description: Schema where the tag is defined
        expr: tag_schema
        data_type: VARCHAR(16777216)
      - name: TAG_VALUE
        synonyms:
          - tag value
          - team value
          - cost center value
          - department value
          - team name value
          - classification value
        description: String value associated with the tag name, forming a key-value pair. Values can be duplicated across objects (e.g., multiple tables tagged with team=engineering) or unique. Used for data governance, cost allocation, sensitive data classification, and policy enforcement.
        expr: tag_value
        data_type: VARCHAR(16777216)
  - name: WAREHOUSE_EVENTS_HISTORY
    synonyms:
      - warehouse events
      - warehouse lifecycle
      - warehouse operations
      - warehouse status changes
    description: Historical events for warehouse operations including resume, suspend, resize, and cluster management activities
    base_table:
      database: SNOWFLAKE
      schema: ACCOUNT_USAGE
      table: WAREHOUSE_EVENTS_HISTORY
    primary_key:
      columns:
        - TIMESTAMP
        - WAREHOUSE_ID
        - CLUSTER_NUMBER
        - EVENT_NAME
    dimensions:
      - name: EVENT_NAME
        synonyms:
          - event type
          - warehouse operation
          - operation type
        description: Type of warehouse event (e.g., RESUME_WAREHOUSE, SUSPEND_WAREHOUSE, ALTER_WAREHOUSE)
        expr: event_name
        data_type: VARCHAR(134217728)
      - name: EVENT_REASON
        synonyms:
          - event trigger
          - operation reason
          - why event occurred
        description: Reason for the event (e.g., WAREHOUSE_AUTORESUME, WAREHOUSE_AUTOSUSPEND, WAREHOUSE_RESIZE)
        expr: event_reason
        data_type: VARCHAR(134217728)
      - name: EVENT_STATE
        synonyms:
          - event status
          - operation status
        description: "State of the event: STARTED or COMPLETED"
        expr: event_state
        data_type: VARCHAR(134217728)
      - name: QUERY_ID
        synonyms:
          - triggering query
          - event query
        description: ID of the query that triggered the event (NULL for manual or system-initiated events)
        expr: query_id
        data_type: VARCHAR(134217728)
      - name: ROLE_NAME
        synonyms:
          - event role
          - user role
        description: Role used when the event was initiated (NULL for system-initiated events)
        expr: role_name
        data_type: VARCHAR(134217728)
      - name: SIZE
        synonyms:
          - warehouse size
          - compute size
          - instance size
        description: Warehouse size at the time of the event (e.g., X-SMALL, SMALL, MEDIUM, LARGE, X-LARGE, 2X-LARGE, etc.)
        expr: size
        data_type: VARCHAR(134217728)
      - name: TIMESTAMP
        synonyms:
          - event time
          - event timestamp
          - warehouse event time
        description: Date and time when the warehouse event occurred
        expr: timestamp
        data_type: TIMESTAMP_LTZ(6)
      - name: USER_NAME
        synonyms:
          - event user
          - triggering user
        description: Name of the user who initiated the event (NULL for system-initiated events)
        expr: user_name
        data_type: VARCHAR(134217728)
      - name: WAREHOUSE_ID
        synonyms:
          - event warehouse id
        description: Unique identifier of the warehouse involved in the event
        expr: warehouse_id
        data_type: NUMBER(38,0)
      - name: WAREHOUSE_NAME
        synonyms:
          - event warehouse
          - warehouse
        description: Name of the warehouse involved in the event
        expr: warehouse_name
        data_type: VARCHAR(134217728)
    facts:
      - name: CLUSTER_COUNT
        description: Total number of clusters in the warehouse at the time of the event (useful for tracking scaling patterns)
        expr: cluster_count
        data_type: VARCHAR(134217728)
      - name: CLUSTER_NUMBER
        description: Numeric identifier of the specific cluster involved in the event (always 1 for single-cluster warehouses)
        expr: cluster_number
        data_type: NUMBER(38,0)
    metrics:
      - name: AVERAGE_CLUSTER_COUNT
        description: Average number of clusters across all warehouse events (multi-cluster scaling indicator)
        expr: AVG(warehouse_events_history.cluster_count)
      - name: TOTAL_RESIZE_EVENTS
        description: Total number of resize initiation events (for actual size changes, use WAREHOUSE_CONSISTENT events with LAG analysis)
        expr: SUM(CASE WHEN warehouse_events_history.event_name = 'RESIZE_WAREHOUSE' THEN 1 ELSE 0 END)
      - name: TOTAL_WAREHOUSE_EVENTS
        description: Total number of warehouse events recorded
        expr: COUNT(warehouse_events_history.timestamp)
  - name: WAREHOUSE_METERING
    synonyms:
      - warehouse usage
      - warehouse metering
      - warehouse spend
    description: Hourly credit usage per warehouse
    base_table:
      database: SNOWFLAKE
      schema: ACCOUNT_USAGE
      table: WAREHOUSE_METERING_HISTORY
    primary_key:
      columns:
        - START_TIME
        - WAREHOUSE_ID
    dimensions:
      - name: START_TIME
        synonyms:
          - warehouse usage start time
          - warehouse start timestamp
        description: Timestamp when warehouse usage period begins
        expr: start_time
        data_type: TIMESTAMP_LTZ(0)
      - name: WAREHOUSE_ID
        synonyms:
          - warehouse id
        description: Unique identifier for the warehouse
        expr: warehouse_id
        data_type: NUMBER(38,0)
      - name: WAREHOUSE_NAME
        synonyms:
          - warehouse
          - warehouse name
        description: Warehouse name
        expr: warehouse_name
        data_type: VARCHAR(16777216)
    facts:
      - name: CREDITS_ATTRIBUTED_COMPUTE_QUERIES
        description: Warehouse compute credits attributed to queries
        expr: credits_attributed_compute_queries
        data_type: NUMBER(38,9)
      - name: CREDITS_USED
        synonyms:
          - warehouse money
          - warehouse cost
          - warehouse spend
          - warehouse charges
          - warehouse billing
        description: Credits used by each warehouse
        expr: credits_used
        data_type: NUMBER(38,9)
      - name: CREDITS_USED_CLOUD_SERVICES
        synonyms:
          - warehouse cloud cost
          - warehouse overhead cost
          - warehouse cloud spend
        description: Warehouse-specific cloud services overhead
        expr: credits_used_cloud_services
        data_type: NUMBER(38,9)
      - name: CREDITS_USED_COMPUTE
        synonyms:
          - warehouse compute cost
          - warehouse compute spend
          - warehouse compute money
        description: Warehouse-specific compute credits
        expr: credits_used_compute
        data_type: NUMBER(38,9)
    metrics:
      - name: TOTAL_WAREHOUSE_CLOUD_SERVICES_CREDITS
        synonyms:
          - total warehouse cloud cost
          - warehouse overhead spending
          - warehouse cloud money
        description: Total cloud services credits for all warehouses
        expr: SUM(warehouse_metering.credits_used_cloud_services)
      - name: TOTAL_WAREHOUSE_COMPUTE_CREDITS
        synonyms:
          - total warehouse compute cost
          - warehouse compute spending
          - warehouse compute money
        description: Total compute credits for all warehouses
        expr: SUM(warehouse_metering.credits_used_compute)
      - name: TOTAL_WAREHOUSE_CREDITS_USED
        synonyms:
          - total warehouse cost
          - total warehouse spend
          - total warehouse money
          - warehouse spending breakdown
        description: Total warehouse credits used
        expr: SUM(warehouse_metering.credits_used)
  - name: BUDGET_DETAILS
    synonyms:
      - budgets
      - budget details
      - spending budgets
    description: Budget definitions and current month spending by database and schema
    base_table:
      database: SNOWFLAKE
      schema: ACCOUNT_USAGE
      table: BUDGET_DETAILS
    primary_key:
      columns:
        - BUDGET_NAME
        - DATABASE_NAME
        - SCHEMA_NAME
        - CREATED_ON
    dimensions:
      - name: BUDGET_NAME
        synonyms:
          - budget
          - budget identifier
        description: Name of the budget
        expr: budget_name
        data_type: VARCHAR(16777216)
      - name: DATABASE_NAME
        synonyms:
          - database
        description: Database scope for the budget (if applicable)
        expr: database_name
        data_type: VARCHAR(16777216)
      - name: SCHEMA_NAME
        synonyms:
          - schema
        description: Schema scope for the budget (if applicable)
        expr: schema_name
        data_type: VARCHAR(16777216)
      - name: CREATED_ON
        synonyms:
          - created at
          - creation time
        description: Timestamp when the budget was created
        expr: created_on
        data_type: TIMESTAMP_LTZ(6)
    facts:
      - name: CREDIT_LIMIT
        synonyms:
          - budget credit limit
          - budget cap
        description: Credit limit defined for the budget
        expr: credit_limit
        data_type: NUMBER(38,0)
      - name: CURRENT_MONTH_SPENDING
        synonyms:
          - current month spend
          - month-to-date spending
        description: Credits spent in the current month under the budget
        expr: current_month_spending
        data_type: NUMBER(38,2)
relationships:
  - name: STORAGE_USAGE_DATE
    left_table: DATABASE_STORAGE
    right_table: STAGE_STORAGE
    relationship_columns:
      - left_column: USAGE_DATE
        right_column: USAGE_DATE
  - name: WAREHOUSE_MAPPING
    left_table: METERING
    right_table: WAREHOUSE_METERING
    relationship_columns:
      - left_column: ENTITY_ID
        right_column: WAREHOUSE_ID
      - left_column: START_TIME
        right_column: START_TIME
  - name: QUERY_HISTORY_TO_ATTRIBUTION
    left_table: QUERY_HISTORY
    right_table: QUERY_ATTRIBUTION
    relationship_columns:
      - left_column: QUERY_ID
        right_column: QUERY_ID
  - name: WAREHOUSE_EVENTS_TO_QUERIES
    left_table: WAREHOUSE_EVENTS_HISTORY
    right_table: QUERY_HISTORY
    relationship_columns:
      - left_column: QUERY_ID
        right_column: QUERY_ID
verified_queries:
  - name: Where is my money going - service breakdown
    question: Where is my money going? Show me a complete breakdown of my Snowflake spending by service type.
    sql: SELECT service_type, ROUND(SUM(credits_used), 2) AS total_credits, ROUND(SUM(credits_used) / SUM(SUM(credits_used)) OVER () * 100, 1) AS percentage_of_total FROM __metering WHERE start_time >= DATEADD(DAY, -7, CURRENT_DATE()) AND start_time < CURRENT_DATE() GROUP BY service_type ORDER BY total_credits DESC
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Total credits used (UI internal)
    question: How many credits were used last week?
    sql: SELECT 'current_period' AS time, ROUND(IFNULL(SUM(credits_used), 0), 2) AS credits_used FROM __metering WHERE start_time >= DATEADD(DAY, -7, CURRENT_DATE()) AND start_time < CURRENT_DATE()
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Credits used by service type (UI internal)
    question: How much did I spend by service type last week?
    sql: SELECT service_type, ROUND(SUM(credits_used), 2) AS credits_used FROM __metering WHERE start_time >= DATEADD(DAY, -7, CURRENT_DATE()) AND start_time < CURRENT_DATE() GROUP BY service_type ORDER BY credits_used DESC
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Week-over-week credit usage comparison
    question: How did my Snowflake spend change compared to the previous week?
    sql: SELECT 'current_week' AS period, ROUND(IFNULL(SUM(credits_used), 0), 2) AS credits_used FROM __metering WHERE start_time >= DATEADD(DAY, -7, CURRENT_DATE())  AND start_time < CURRENT_DATE() UNION ALL SELECT 'previous_week' AS period, ROUND(IFNULL(SUM(credits_used), 0), 2) AS credits_used FROM __metering WHERE start_time >= DATEADD(DAY, -14, CURRENT_DATE()) AND start_time < DATEADD(DAY, -7, CURRENT_DATE())
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Month-over-month credit usage comparison
    question: How did my Snowflake spend change compared to last month?
    sql: SELECT 'current_month' AS period, ROUND(IFNULL(SUM(credits_used), 0), 2) AS credits_used FROM __metering WHERE start_time >= DATE_TRUNC('MONTH', CURRENT_DATE()) AND start_time < DATE_TRUNC('MONTH', DATEADD(MONTH, 1, CURRENT_DATE())) UNION ALL SELECT 'previous_month' AS period, ROUND(IFNULL(SUM(credits_used), 0), 2) AS credits_used FROM __metering WHERE start_time >= DATE_TRUNC('MONTH', DATEADD(MONTH, -1, CURRENT_DATE())) AND start_time < DATE_TRUNC('MONTH', CURRENT_DATE())
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Cost anomaly analysis
    question: Which days had cost anomalies and how much did consumption exceed forecasts? Were there any spend anomalies? Were there any spend anomalies in the past month? Any cost anomalies recently?
    sql: SELECT date, COUNT(*) AS anomaly_count, ROUND(SUM(actual_value), 2) AS total_consumption, ROUND(SUM(forecasted_value), 2) AS total_forecast, ROUND(SUM(actual_value - forecasted_value), 2) AS variance_amount, ROUND((SUM(actual_value) - SUM(forecasted_value)) / SUM(forecasted_value) * 100, 2) AS variance_percent FROM __anomalies_daily WHERE is_anomaly = TRUE AND date >= CURRENT_DATE - 30 GROUP BY date ORDER BY variance_percent DESC LIMIT 10
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Anomaly trends over time
    question: What is the trend of cost anomalies by week over the past 3 months?
    sql: SELECT DATE_TRUNC('WEEK', date) AS week_start, COUNT(DISTINCT date) AS days_with_anomalies, COUNT(*) AS total_anomalies, ROUND(AVG(actual_value - forecasted_value), 2) AS avg_variance_credits, ROUND(AVG((actual_value - forecasted_value) / forecasted_value * 100), 2) AS avg_variance_percent FROM __anomalies_daily WHERE is_anomaly = TRUE AND date >= CURRENT_DATE - 90 GROUP BY week_start ORDER BY week_start DESC
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Correct anomaly detection vs incorrect filtering
    question: What is the difference between actual anomalies (is_anomaly=TRUE) and just high consumption days (actual > forecast)?
    sql: WITH actual_anomalies AS (SELECT COUNT(*) AS true_anomaly_days FROM __anomalies_daily WHERE is_anomaly = TRUE AND date >= CURRENT_DATE - 30), high_consumption AS (SELECT COUNT(*) AS high_consumption_days FROM __anomalies_daily WHERE actual_value > forecasted_value AND date >= CURRENT_DATE - 30) SELECT aa.true_anomaly_days, hc.high_consumption_days, (hc.high_consumption_days - aa.true_anomaly_days) AS difference_in_counts, 'Always use is_anomaly = TRUE for anomaly detection' AS important_note FROM actual_anomalies aa CROSS JOIN high_consumption hc
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Team cost breakdown across all services
    question: What did each team spend in total? Show me detailed team costs by service type. What is the cost breakdown by team for the past month? How much did each team spend across all Snowflake services?
    sql: SELECT tr.tag_name, tr.tag_value AS team, m.service_type, COUNT(DISTINCT m.name) AS resource_count, ROUND(SUM(m.credits_used), 2) AS total_credits, ROUND(SUM(m.credits_used_compute), 2) AS compute_credits, ROUND(SUM(m.credits_used_cloud_services), 2) AS cloud_services_credits, ROUND(AVG(m.credits_used), 2) AS avg_credits_per_resource FROM __metering m JOIN __tag_references tr ON m.name = tr.object_name WHERE m.start_time >= DATEADD(MONTH, -1, CURRENT_DATE()) AND m.start_time < CURRENT_DATE() AND tr.tag_value IS NOT NULL AND tr.tag_value != '' GROUP BY tr.tag_name, tr.tag_value, m.service_type ORDER BY total_credits DESC
    verified_at: 1753987877
    verified_by: Spencer Moritz
  - name: Team cost breakdown by warehouse
    question: What is the total cost breakdown by team across all warehouses?
    sql: SELECT tr.tag_name, tr.tag_value AS team, COUNT(DISTINCT wm.warehouse_name) AS warehouse_count, ROUND(SUM(wm.credits_used), 2) AS total_credits, ROUND(AVG(wm.credits_used), 2) AS avg_credits_per_warehouse FROM __warehouse_metering wm JOIN __tag_references tr ON wm.warehouse_name = tr.object_name WHERE tr.domain = 'WAREHOUSE' AND tr.tag_value IS NOT NULL AND tr.tag_value != '' AND wm.start_time >= DATEADD(DAY, -7, CURRENT_DATE()) AND wm.start_time < CURRENT_DATE() GROUP BY tr.tag_name, tr.tag_value ORDER BY total_credits DESC
    verified_at: 1753987877
    verified_by: Spencer Moritz
  - name: Department resource utilization
    question: How many resources does each department own and what do they cost?
    sql: SELECT tag_name AS department, domain AS resource_type, COUNT(DISTINCT object_name) AS resource_count, CASE WHEN domain = 'WAREHOUSE' THEN 'See warehouse costs in other queries' ELSE 'Storage/Other resources' END AS cost_note FROM __tag_references GROUP BY tag_name, domain ORDER BY tag_name, resource_count DESC
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Top teams by warehouse spend
    question: Which teams or cost centers have the highest warehouse costs?
    sql: SELECT tr.tag_name, tr.tag_value AS team, wm.warehouse_name, ROUND(SUM(wm.credits_used), 2) AS credits FROM __warehouse_metering wm JOIN __tag_references tr ON wm.warehouse_name = tr.object_name WHERE tr.domain = 'WAREHOUSE' AND tr.tag_value IS NOT NULL AND tr.tag_value != '' AND wm.start_time >= DATEADD(DAY, -7, CURRENT_DATE()) AND wm.start_time < CURRENT_DATE() GROUP BY tr.tag_name, tr.tag_value, wm.warehouse_name ORDER BY credits DESC LIMIT 100
    verified_at: 1753987877
    verified_by: Spencer Moritz
  - name: Top users by query costs
    question: What users are spending the most? Which users are spending the most? Who is spending the most?
    sql: SELECT user_name, COUNT(DISTINCT query_id) AS query_count, ROUND(SUM(credits_attributed_compute + COALESCE(credits_used_query_acceleration, 0)), 2) AS total_credits FROM __query_attribution WHERE start_time >= DATEADD(DAY, -7, CURRENT_DATE()) AND start_time < CURRENT_DATE() GROUP BY user_name ORDER BY total_credits DESC LIMIT 20
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Credits by service type and entity
    question: How much compute and cloud services credit has each entity used by service type?
    sql: SELECT DATE_TRUNC('DAY', CONVERT_TIMEZONE('UTC', start_time)) AS start_time, entity_id, name, service_type, ROUND(SUM(credits_used), 2) AS credits_used, ROUND(SUM(credits_used_compute), 2) AS credits_compute, ROUND(SUM(credits_used_cloud_services), 2) AS credits_cloud FROM __metering WHERE start_time >= DATEADD(DAY, -7, CURRENT_DATE()) AND start_time < CURRENT_DATE() AND service_type = 'WAREHOUSE_METERING' GROUP BY 1, 2, 3, 4
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Top warehouses by credit usage
    question: Which warehouses consumed the most credits last week?
    sql: SELECT warehouse_name, warehouse_id, ROUND(SUM(credits_used), 2) AS credits FROM __warehouse_metering WHERE start_time >= DATEADD(DAY, -7, CURRENT_DATE()) AND start_time < CURRENT_DATE() GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 100
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Top databases by storage usage
    question: Which databases used the most storage on average?
    sql: WITH daily AS (SELECT database_name, usage_date, MAX(database_id) AS object_id, MAX(average_database_bytes + average_failsafe_bytes + average_hybrid_table_storage_bytes) AS database_storage_bytes FROM __database_storage WHERE usage_date >= DATEADD(DAY, -7, CURRENT_DATE()) AND usage_date < CURRENT_DATE() GROUP BY ALL) SELECT database_name, AVG(database_storage_bytes) AS database_storage_bytes FROM daily GROUP BY 1 ORDER BY 2 DESC LIMIT 100
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Storage usage by object type
    question: What is the database and stage storage usage for each day?
    sql: SELECT usage_date, database_name AS object_name, 'DATABASE' AS object_type, MAX(average_database_bytes) AS database_bytes, MAX(average_failsafe_bytes) AS failsafe_bytes, 0 AS stage_bytes, MAX(database_id) AS object_id, 0 AS hybrid_bytes FROM __database_storage WHERE usage_date >= DATEADD(DAY, -7, CURRENT_DATE()) AND usage_date < CURRENT_DATE() GROUP BY 1, 2, 3 UNION ALL SELECT usage_date, 'Stages' AS object_name, 'STAGE' AS object_type, 0, 0, MAX(average_stage_bytes), 0, 0 FROM __stage_storage WHERE usage_date >= DATEADD(DAY, -7, CURRENT_DATE()) AND usage_date < CURRENT_DATE() GROUP BY 1, 2, 3
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Storage growth trend analysis
    question: How is storage usage trending across databases over time?
    sql: SELECT database_name, usage_date, ROUND(average_database_bytes / POW(1024, 4), 3) AS database_tb, ROUND(average_failsafe_bytes / POW(1024, 4), 3) AS failsafe_tb, ROUND(average_hybrid_table_storage_bytes / POW(1024, 4), 3) AS hybrid_tb, ROUND((average_database_bytes + average_failsafe_bytes + average_hybrid_table_storage_bytes) / POW(1024, 4), 3) AS total_tb, LAG(ROUND((average_database_bytes + average_failsafe_bytes + average_hybrid_table_storage_bytes) / POW(1024, 4), 3)) OVER (PARTITION BY database_name ORDER BY usage_date) AS prev_day_tb FROM __database_storage WHERE usage_date >= CURRENT_DATE - 30 AND database_name IN (SELECT database_name FROM __database_storage WHERE usage_date = CURRENT_DATE - 1 ORDER BY (average_database_bytes + average_failsafe_bytes + average_hybrid_table_storage_bytes) DESC LIMIT 10) ORDER BY database_name, usage_date DESC
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Most expensive individual queries
    question: Which individual queries consumed the most compute credits last week?
    sql: SELECT qh.query_id, qh.warehouse_name, qh.user_name, ROUND(qa.credits_attributed_compute, 2) AS credits_attributed_compute, ROUND(qa.credits_used_query_acceleration, 2) AS credits_used_query_acceleration, ROUND((qh.total_elapsed_time / 1000), 2) AS duration_seconds, LEFT(qh.query_text, 100) AS query_preview FROM __query_history qh JOIN __query_attribution qa ON qh.query_id = qa.query_id WHERE qh.start_time >= CURRENT_DATE - 7 AND qa.credits_attributed_compute > 0 ORDER BY qa.credits_attributed_compute DESC LIMIT 20
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Top parameterized queries with text
    question: Which parameterized queries were the most expensive last week, and what did they do?
    sql: WITH expensive_queries AS (SELECT query_parameterized_hash, COUNT(query_id) AS num_queries FROM __query_attribution WHERE start_time >= DATEADD(DAY, -7, CURRENT_DATE()) AND start_time < CURRENT_DATE() GROUP BY query_parameterized_hash) SELECT eq.query_parameterized_hash, eq.num_queries, qh.query_id, qh.query_text FROM expensive_queries AS eq JOIN __query_history AS qh ON eq.query_parameterized_hash = qh.query_parameterized_hash QUALIFY ROW_NUMBER() OVER (PARTITION BY eq.query_parameterized_hash ORDER BY qh.end_time DESC) = 1 ORDER BY eq.num_queries DESC LIMIT 5
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Data transfer by region and cloud
    question: How much data was transferred by region, cloud, and transfer type?
    sql: SELECT DATE_TRUNC('DAY', CONVERT_TIMEZONE('UTC', start_time)) AS start_time, target_cloud, target_region, transfer_type, SUM(bytes_transferred) AS bytes_transferred FROM __data_transfer WHERE start_time >= DATEADD(DAY, -7, CURRENT_DATE()) AND start_time < CURRENT_DATE() GROUP BY 1, 2, 3, 4
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Data transfer cost analysis
    question: What are the top data transfer costs by region and cloud provider?
    sql: SELECT target_cloud, target_region, source_cloud, source_region, transfer_type, COUNT(*) AS transfer_count, ROUND(SUM(bytes_transferred) / POW(1024, 4), 3) AS total_tb_transferred, DATE_TRUNC('DAY', start_time) AS transfer_date FROM __data_transfer WHERE start_time >= CURRENT_DATE - 30 GROUP BY target_cloud, target_region, source_cloud, source_region, transfer_type, transfer_date HAVING total_tb_transferred > 0.1 ORDER BY total_tb_transferred DESC LIMIT 25
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Top compute pools by spend
    question: Which compute pools used the most credits over the past week?
    sql: SELECT compute_pool_name, ROUND(SUM(credits_used), 2) AS total_credits FROM __snowpark_container_services WHERE start_time >= DATEADD(DAY, -7, CURRENT_DATE()) AND start_time < CURRENT_DATE() GROUP BY compute_pool_name ORDER BY total_credits DESC LIMIT 10
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Total Snowpark container services credits
    question: How many total credits were used by Snowpark container services last week?
    sql: SELECT ROUND(SUM(credits_used), 2) AS total_credits FROM __snowpark_container_services WHERE start_time >= DATEADD(DAY, -7, CURRENT_DATE()) AND start_time < CURRENT_DATE()
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Top applications by Snowpark container spend
    question: Which applications used the most Snowpark container credits last week?
    sql: SELECT application_name, application_id, ROUND(SUM(credits_used), 2) AS total_credits FROM __snowpark_container_services WHERE start_time >= DATEADD(DAY, -7, CURRENT_DATE()) AND start_time < CURRENT_DATE() AND application_id IS NOT NULL AND application_id <> '' GROUP BY application_name, application_id ORDER BY total_credits DESC LIMIT 10
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Warehouse resize events
    question: Have any warehouses been resized recently?
    sql: WITH warehouse_states AS (SELECT warehouse_name, timestamp, size, LAG(size) OVER (PARTITION BY warehouse_name ORDER BY timestamp) as previous_size FROM __warehouse_events_history WHERE event_name = 'WAREHOUSE_CONSISTENT' AND timestamp >= CURRENT_DATE - 7) SELECT warehouse_name, timestamp, previous_size, size as new_size FROM warehouse_states WHERE previous_size IS NOT NULL AND previous_size != size ORDER BY timestamp DESC
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Query acceleration credits by warehouse (month-to-date)
    question: Which warehouses used the most query acceleration service credits this month?
    sql: SELECT warehouse_name, ROUND(SUM(credits_used), 2) AS total_credits_used FROM __query_acceleration_history WHERE start_time >= DATE_TRUNC('month', CURRENT_DATE) GROUP BY warehouse_name ORDER BY total_credits_used DESC
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Serverless task credits last week
    question: How many credits did serverless tasks consume last week?
    sql: SELECT task_name, database_name, schema_name, ROUND(SUM(credits_used), 2) AS total_credits FROM __serverless_task_history WHERE start_time >= DATEADD('D', -7, CURRENT_DATE) AND start_time < CURRENT_DATE GROUP BY task_name, database_name, schema_name ORDER BY total_credits DESC
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Top serverless tasks by database
    question: Which databases have the highest serverless task credit usage?
    sql: SELECT database_name, COUNT(DISTINCT task_name) AS task_count, ROUND(SUM(credits_used), 2) AS total_credits FROM __serverless_task_history WHERE start_time >= DATEADD('D', -30, CURRENT_DATE) GROUP BY database_name ORDER BY total_credits DESC LIMIT 10
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Serverless task usage last 12 hours
    question: What serverless task activity happened in the last 12 hours?
    sql: SELECT task_name, database_name, schema_name, start_time, end_time, ROUND(credits_used, 2) AS credits_used FROM __serverless_task_history WHERE start_time >= DATEADD('H', -12, CURRENT_TIMESTAMP) ORDER BY start_time DESC
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Top Cortex Analyst users by credits
    question: Which users consumed the most Cortex Analyst credits this month?
    sql: SELECT username, ROUND(SUM(credits), 2) AS total_credits, SUM(request_count) AS total_requests, ROUND(SUM(credits) / NULLIF(SUM(request_count), 0), 4) AS avg_credits_per_request FROM __cortex_analyst_usage_history WHERE start_time >= DATE_TRUNC('month', CURRENT_DATE) GROUP BY username ORDER BY total_credits DESC LIMIT 10
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Cortex Analyst usage trend last 30 days
    question: How has Cortex Analyst usage trended over the past month?
    sql: SELECT DATE_TRUNC('DAY', start_time) AS usage_date, ROUND(SUM(credits), 2) AS daily_credits, SUM(request_count) AS daily_requests, COUNT(DISTINCT username) AS unique_users FROM __cortex_analyst_usage_history WHERE start_time >= DATEADD('D', -30, CURRENT_DATE) GROUP BY usage_date ORDER BY usage_date DESC
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Cortex function usage trends
    question: Show me the daily trend of Cortex function usage and costs over the past week
    sql: SELECT DATE(start_time) AS usage_date, function_name, SUM(tokens) AS total_tokens, ROUND(SUM(token_credits), 2) AS total_credits FROM __cortex_functions_usage_history WHERE start_time >= DATEADD('D', -7, CURRENT_DATE) GROUP BY DATE(start_time), function_name ORDER BY usage_date DESC, total_credits DESC
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Top Cortex functions by cost
    question: Which Cortex functions are the most expensive? What are my top AI function costs? Which AI models consumed the most credits?
    sql: SELECT function_name, model_name, SUM(tokens) AS total_tokens, ROUND(SUM(token_credits), 2) AS total_credits, COUNT(*) AS time_windows FROM __cortex_functions_usage_history GROUP BY function_name, model_name ORDER BY total_credits DESC LIMIT 10
    verified_at: 1742476800
    verified_by: Nathan Scharfe
  - name: Top 5 most expensive databases by storage
    question: Which 5 databases are contributing the most to storage costs?
    sql: SELECT database_name, database_id, COUNT(*) as days_tracked, AVG((average_database_bytes + average_failsafe_bytes + COALESCE(average_hybrid_table_storage_bytes, 0))) / (1024*1024*1024) AS avg_total_storage_gb, AVG(average_database_bytes) / (1024*1024*1024) AS avg_database_storage_gb, AVG(average_failsafe_bytes) / (1024*1024*1024) AS avg_failsafe_storage_gb, AVG(COALESCE(average_hybrid_table_storage_bytes, 0)) / (1024*1024*1024) AS avg_hybrid_storage_gb, MIN(usage_date) as first_date, MAX(usage_date) as last_date FROM __database_storage WHERE usage_date >= DATEADD(days, -30, CURRENT_DATE()) GROUP BY database_name, database_id ORDER BY avg_total_storage_gb DESC LIMIT 5
    verified_at: 1752164792
    verified_by: Spencer Moritz
  - name: Most expensive warehouses on date of anomalies
    question: Over the past 6 months what were the most expensive warehouses on the date that had anomalies?
    sql: SELECT a.anomaly_date, a.spend, w.warehouse_name as top_warehouse_name, w.daily_credits_used AS warehouse_credits_used FROM (SELECT DISTINCT date as anomaly_date, actual_value as spend FROM __anomalies_daily WHERE date >= DATEADD(month, -6, CURRENT_DATE()) AND is_anomaly = TRUE) a JOIN (SELECT DATE(CONVERT_TIMEZONE('UTC', start_time)) as usage_date, warehouse_name, SUM(credits_used) as daily_credits_used, ROW_NUMBER() OVER (PARTITION BY DATE(CONVERT_TIMEZONE('UTC', start_time)) ORDER BY SUM(credits_used) DESC) as warehouse_cost_rank FROM __warehouse_metering GROUP BY DATE(CONVERT_TIMEZONE('UTC', start_time)), warehouse_name QUALIFY warehouse_cost_rank = 1) w ON a.anomaly_date = w.usage_date ORDER BY a.anomaly_date DESC, a.spend DESC
    verified_at: 1752179859
    verified_by: Spencer Moritz
  - name: Most expensive queries on date of anomalies
    question: Over the past 6 months what were the most expensive queries on the date that had anomalies?
    sql: SELECT a.anomaly_date, q.query_id as query_id, q.warehouse_id as warehouse_id, q.credits_used AS credits_used FROM (SELECT DISTINCT date as anomaly_date, actual_value as spend FROM __anomalies_daily WHERE date >= DATEADD(month, -6, CURRENT_DATE()) AND is_anomaly = TRUE) a JOIN (SELECT DATE(CONVERT_TIMEZONE('UTC', start_time)) as usage_date, query_id, warehouse_id, credits_attributed_compute as credits_used, ROW_NUMBER() OVER (PARTITION BY DATE(CONVERT_TIMEZONE('UTC', start_time)) ORDER BY credits_attributed_compute DESC) as query_cost_rank FROM __query_attribution WHERE start_time >= DATEADD(month, -6, CURRENT_DATE()) QUALIFY query_cost_rank = 1) q ON a.anomaly_date = q.usage_date ORDER BY a.anomaly_date DESC
    verified_at: 1752181289
    verified_by: Spencer Moritz
  - name: Which teams are taking up the most storage over the past month, and what are their storage usage patterns?
    question: Which teams are taking up the most storage over the past month, and what are their storage usage patterns?
    sql: SELECT tr.tag_value AS team_name, tr.tag_name AS tag_key, SUM(ds.average_database_bytes + ds.average_failsafe_bytes + COALESCE(ds.average_hybrid_table_storage_bytes, 0)) / (1024 * 1024 * 1024 * 1024) AS total_storage_tb, COUNT(DISTINCT ds.database_name) AS databases_owned, COUNT(*) AS storage_records, AVG(ds.average_database_bytes + ds.average_failsafe_bytes + COALESCE(ds.average_hybrid_table_storage_bytes, 0)) / (1024 * 1024 * 1024 * 1024) AS avg_daily_storage_tb FROM __tag_references tr JOIN __database_storage ds ON tr.object_name = ds.database_name WHERE tr.domain = 'DATABASE' AND tr.tag_value IS NOT NULL AND ds.usage_date >= DATEADD(month, -1, CURRENT_DATE()) GROUP BY tr.tag_value, tr.tag_name ORDER BY total_storage_tb DESC LIMIT 10
    verified_at: 1752623375
    verified_by: Spencer Moritz
  - name: Which warehouses saw the largest change in month cost?
    question: Which warehouses saw the largest change in month cost?
    sql: WITH monthly_warehouse_spend AS (SELECT warehouse_name, warehouse_id, DATE_TRUNC('month', start_time) AS spend_month, SUM(credits_used) AS total_credits FROM __warehouse_metering WHERE start_time >= DATE_TRUNC('month', DATEADD('month', -1, CURRENT_DATE())) AND start_time < DATE_TRUNC('month', DATEADD('month', 1, CURRENT_DATE())) GROUP BY warehouse_name, warehouse_id, DATE_TRUNC('month', start_time)), warehouse_comparison AS (SELECT warehouse_name, warehouse_id, SUM(CASE WHEN spend_month = DATE_TRUNC('month', CURRENT_DATE()) THEN total_credits ELSE 0 END) AS current_month_credits, SUM(CASE WHEN spend_month = DATE_TRUNC('month', DATEADD('month', -1, CURRENT_DATE())) THEN total_credits ELSE 0 END) AS previous_month_credits FROM monthly_warehouse_spend GROUP BY warehouse_name, warehouse_id) SELECT warehouse_name, ROUND(current_month_credits, 2) AS current_month_credits, ROUND(previous_month_credits, 2) AS previous_month_credits, ROUND(current_month_credits - previous_month_credits, 2) AS credit_difference, CASE WHEN previous_month_credits > 0 THEN ROUND(((current_month_credits - previous_month_credits) / previous_month_credits) * 100, 2) ELSE NULL END AS percentage_change, CASE WHEN current_month_credits > previous_month_credits THEN 'INCREASED' WHEN current_month_credits < previous_month_credits THEN 'DECREASED' WHEN current_month_credits = previous_month_credits THEN 'UNCHANGED' ELSE 'NEW_WAREHOUSE' END AS trend_direction FROM warehouse_comparison WHERE current_month_credits > 0 OR previous_month_credits > 0 ORDER BY ABS(current_month_credits - previous_month_credits) DESC
    verified_at: 1752548299
    verified_by: Spencer Moritz
  - name: Who are the top-5 users with the greatest increase in query cost?
    question: Who are the top-5 users with the greatest increase in query cost?
    sql: WITH monthly_user_spend AS (SELECT user_name, DATE_TRUNC('month', start_time) AS spend_month, SUM(credits_attributed_compute) AS total_credits FROM __query_attribution WHERE start_time >= DATE_TRUNC('month', DATEADD('month', -2, CURRENT_DATE())) AND start_time < DATE_TRUNC('month', DATEADD('month', 1, CURRENT_DATE())) GROUP BY user_name, DATE_TRUNC('month', start_time)), user_comparison AS (SELECT user_name, SUM(CASE WHEN spend_month = DATE_TRUNC('month', CURRENT_DATE()) THEN total_credits ELSE 0 END) AS current_month_credits, SUM(CASE WHEN spend_month = DATE_TRUNC('month', DATEADD('month', -1, CURRENT_DATE())) THEN total_credits ELSE 0 END) AS previous_month_credits FROM monthly_user_spend GROUP BY user_name) SELECT user_name, ROUND(current_month_credits, 2) AS current_month_credits, ROUND(previous_month_credits, 2) AS previous_month_credits, ROUND(current_month_credits - previous_month_credits, 2) AS credit_increase, CASE WHEN previous_month_credits > 0 THEN ROUND(((current_month_credits - previous_month_credits) / previous_month_credits) * 100, 2) ELSE NULL END AS percentage_increase, CASE WHEN previous_month_credits = 0 THEN 'NEW_USER' ELSE 'INCREASED' END AS user_status FROM user_comparison WHERE current_month_credits > previous_month_credits ORDER BY (current_month_credits - previous_month_credits) DESC LIMIT 5
    verified_at: 1752549972
    verified_by: Spencer Moritz
  - name: Why has my cost increased?
    question: Why has my cost increased?
    sql: WITH monthly_service_costs AS (SELECT DATE_TRUNC('month', start_time) AS cost_month, service_type, SUM(credits_used) AS total_credits FROM __metering WHERE start_time >= DATE_TRUNC('month', DATEADD('month', -2, CURRENT_DATE())) GROUP BY DATE_TRUNC('month', start_time), service_type), service_comparison AS (SELECT service_type, SUM(CASE WHEN cost_month = DATE_TRUNC('month', CURRENT_DATE()) THEN total_credits ELSE 0 END) AS current_month_credits, SUM(CASE WHEN cost_month = DATE_TRUNC('month', DATEADD('month', -1, CURRENT_DATE())) THEN total_credits ELSE 0 END) AS previous_month_credits FROM monthly_service_costs GROUP BY service_type), service_increases AS (SELECT service_type, current_month_credits, previous_month_credits, current_month_credits - previous_month_credits AS credit_increase, CASE WHEN previous_month_credits > 0 THEN ROUND(((current_month_credits - previous_month_credits) / previous_month_credits) * 100, 2) ELSE NULL END AS percentage_increase FROM service_comparison WHERE current_month_credits > previous_month_credits), top_warehouse_increases AS (SELECT 'WAREHOUSE' AS resource_type, warehouse_name AS resource_name, SUM(CASE WHEN DATE_TRUNC('month', start_time) = DATE_TRUNC('month', CURRENT_DATE()) THEN credits_used ELSE 0 END) AS current_month_credits, SUM(CASE WHEN DATE_TRUNC('month', start_time) = DATE_TRUNC('month', DATEADD('month', -1, CURRENT_DATE())) THEN credits_used ELSE 0 END) AS previous_month_credits FROM __warehouse_metering WHERE start_time >= DATE_TRUNC('month', DATEADD('month', -2, CURRENT_DATE())) GROUP BY warehouse_name HAVING SUM(CASE WHEN DATE_TRUNC('month', start_time) = DATE_TRUNC('month', CURRENT_DATE()) THEN credits_used ELSE 0 END) > SUM(CASE WHEN DATE_TRUNC('month', start_time) = DATE_TRUNC('month', DATEADD('month', -1, CURRENT_DATE())) THEN credits_used ELSE 0 END)), top_user_increases AS (SELECT 'USER' AS resource_type, user_name AS resource_name, SUM(CASE WHEN DATE_TRUNC('month', start_time) = DATE_TRUNC('month', CURRENT_DATE()) THEN credits_attributed_compute ELSE 0 END) AS current_month_credits, SUM(CASE WHEN DATE_TRUNC('month', start_time) = DATE_TRUNC('month', DATEADD('month', -1, CURRENT_DATE())) THEN credits_attributed_compute ELSE 0 END) AS previous_month_credits FROM __query_attribution WHERE start_time >= DATE_TRUNC('month', DATEADD('month', -2, CURRENT_DATE())) GROUP BY user_name HAVING SUM(CASE WHEN DATE_TRUNC('month', start_time) = DATE_TRUNC('month', CURRENT_DATE()) THEN credits_attributed_compute ELSE 0 END) > SUM(CASE WHEN DATE_TRUNC('month', start_time) = DATE_TRUNC('month', DATEADD('month', -1, CURRENT_DATE())) THEN credits_attributed_compute ELSE 0 END)), recent_anomalies AS (SELECT date, actual_value, forecasted_value, actual_value - forecasted_value AS anomaly_impact FROM __anomalies_daily WHERE is_anomaly = TRUE AND date >= DATEADD('month', -1, CURRENT_DATE()) ORDER BY date DESC LIMIT 3) SELECT 'SERVICE_TYPE_ANALYSIS' AS analysis_type, service_type AS category, NULL AS subcategory, ROUND(current_month_credits, 2) AS current_month_credits, ROUND(previous_month_credits, 2) AS previous_month_credits, ROUND(credit_increase, 2) AS credit_increase, percentage_increase, ROW_NUMBER() OVER (ORDER BY credit_increase DESC) AS rank_by_increase FROM service_increases UNION ALL SELECT 'TOP_WAREHOUSE_INCREASES' AS analysis_type, resource_name AS category, NULL AS subcategory, ROUND(current_month_credits, 2) AS current_month_credits, ROUND(previous_month_credits, 2) AS previous_month_credits, ROUND(current_month_credits - previous_month_credits, 2) AS credit_increase, CASE WHEN previous_month_credits > 0 THEN ROUND(((current_month_credits - previous_month_credits) / previous_month_credits) * 100, 2) ELSE NULL END AS percentage_increase, ROW_NUMBER() OVER (ORDER BY (current_month_credits - previous_month_credits) DESC) AS rank_by_increase FROM top_warehouse_increases UNION ALL SELECT 'TOP_USER_INCREASES' AS analysis_type, resource_name AS category, NULL AS subcategory, ROUND(current_month_credits, 2) AS current_month_credits, ROUND(previous_month_credits, 2) AS previous_month_credits, ROUND(current_month_credits - previous_month_credits, 2) AS credit_increase, CASE WHEN previous_month_credits > 0 THEN ROUND(((current_month_credits - previous_month_credits) / previous_month_credits) * 100, 2) ELSE NULL END AS percentage_increase, ROW_NUMBER() OVER (ORDER BY (current_month_credits - previous_month_credits) DESC) AS rank_by_increase FROM top_user_increases UNION ALL SELECT 'RECENT_ANOMALIES' AS analysis_type, TO_VARCHAR(date) AS category, 'Anomaly Impact' AS subcategory, ROUND(actual_value, 2) AS current_month_credits, ROUND(forecasted_value, 2) AS previous_month_credits, ROUND(anomaly_impact, 2) AS credit_increase, NULL AS percentage_increase, ROW_NUMBER() OVER (ORDER BY date DESC) AS rank_by_increase FROM recent_anomalies ORDER BY analysis_type, rank_by_increase
    verified_at: 1752549502
    verified_by: Spencer Moritz
  - name: Which team consumed the most Cortex AI functions over the past month, and what was their usage pattern?
    question: Which team consumed the most Cortex AI functions over the past month, and what was their usage pattern?
    sql: WITH warehouse_tags AS (SELECT DISTINCT wm.warehouse_id, wm.warehouse_name, tr.tag_name, tr.tag_value FROM __warehouse_metering wm JOIN __tag_references tr ON wm.warehouse_name = tr.object_name WHERE tr.domain = 'WAREHOUSE' AND tr.tag_value IS NOT NULL), cortex_functions_by_team AS (SELECT wt.tag_name AS tag_key, wt.tag_value AS tag_value, 'CORTEX_FUNCTIONS' AS service_type, SUM(cf.token_credits) AS total_credits, COUNT(*) AS usage_records, COUNT(DISTINCT cf.function_name) AS unique_functions, COUNT(DISTINCT cf.model_name) AS unique_models FROM __cortex_functions_usage_history cf JOIN warehouse_tags wt ON cf.warehouse_id = wt.warehouse_id WHERE cf.start_time >= DATEADD(month, -1, CURRENT_DATE()) GROUP BY wt.tag_name, wt.tag_value) SELECT tag_key, tag_value, total_credits AS total_cortex_credits, usage_records AS total_usage_records, unique_functions, unique_models, ROUND(total_credits / usage_records, 4) AS avg_credits_per_usage FROM cortex_functions_by_team ORDER BY total_credits DESC LIMIT 10
    verified_at: 1752613587
    verified_by: Spencer Moritz
  - name: How much have I spent so far this calendar year on database storage?
    question: How much have I spent so far this calendar year on database storage?
    sql: SELECT SUM(m.credits_used) AS total_storage_credits, COUNT(*) AS total_records, AVG(m.credits_used) AS avg_hourly_storage_credits, MIN(m.start_time) AS first_date, MAX(m.start_time) AS last_date FROM __metering m WHERE m.service_type = 'STORAGE' AND m.start_time >= DATE_TRUNC('YEAR', CURRENT_DATE()) AND m.start_time <= CURRENT_DATE()
    verified_at: 1752556030
    verified_by: Spencer Moritz
  - name: Which tables are driving up our clustering expenses?
    question: Which tables are driving up our clustering expenses?
    sql: SELECT database_name, schema_name, table_name, ROUND(SUM(credits_used), 2) AS total_clustering_credits, COUNT(*) AS clustering_events, ROUND(AVG(credits_used), 4) AS avg_credits_per_event, MIN(start_time) AS first_clustering, MAX(start_time) AS last_clustering FROM __automatic_clustering_history WHERE start_time >= DATEADD('month', -1, CURRENT_DATE()) GROUP BY database_name, schema_name, table_name ORDER BY total_clustering_credits DESC LIMIT 20
    verified_at: 1752556689
    verified_by: Spencer Moritz
  - name: Which service is consuming the most money?
    question: Which service is consuming the most money?
    sql: SELECT service_type, ROUND(SUM(credits_used), 2) AS total_credits, COUNT(*) AS usage_records, ROUND(AVG(credits_used), 4) AS avg_credits_per_hour, MIN(start_time) AS first_usage, MAX(start_time) AS last_usage FROM __metering WHERE start_time >= DATEADD('month', -1, CURRENT_DATE()) GROUP BY service_type ORDER BY total_credits DESC LIMIT 10
    verified_at: 1752612861
    verified_by: Spencer Moritz
  - name: Simple tag combination cost overview
    question: Show me a quick overview of all tag combinations and their spending over the past month. What are the basic cost totals by tag name and value?
    sql: SELECT tr.tag_name, tr.tag_value, CONCAT(tr.tag_name, '=', tr.tag_value) AS tag_combination, tr.domain AS resource_type, COUNT(DISTINCT tr.object_name) AS tagged_resources, COUNT(DISTINCT m.service_type) AS service_types_used, ROUND(SUM(m.credits_used), 2) AS total_credits, ROUND(SUM(m.credits_used_compute), 2) AS compute_credits, ROUND(SUM(m.credits_used_cloud_services), 2) AS cloud_services_credits, ROUND(AVG(m.credits_used), 4) AS avg_credits_per_hour, MIN(m.start_time) AS first_usage, MAX(m.start_time) AS last_usage FROM __tag_references tr JOIN __metering m ON tr.object_name = m.name WHERE m.start_time >= DATEADD('month', -1, CURRENT_DATE()) AND tr.tag_name IS NOT NULL AND tr.tag_value IS NOT NULL AND tr.tag_value != '' GROUP BY tr.tag_name, tr.tag_value, tr.domain HAVING SUM(m.credits_used) > 0 ORDER BY total_credits DESC LIMIT 20
    verified_at: 1752557428
    verified_by: Spencer Moritz
  - name: For each cost anomaly over the past 4 months, what were the top 5 resources that contributed most to the excessive spending so I can identify patterns and prevent future incidents?
    question: For each cost anomaly over the past 4 months, what were the top 5 resources that contributed most to the excessive spending so I can identify patterns and prevent future incidents?
    sql: WITH anomaly_dates AS (SELECT DISTINCT date as anomaly_date, actual_value, forecasted_value, (actual_value - forecasted_value) as anomaly_impact FROM __anomalies_daily WHERE is_anomaly = TRUE AND date >= DATEADD('month', -4, CURRENT_DATE())), anomaly_day_spending AS (SELECT DATE(m.start_time) as usage_date, m.service_type, m.name as resource_name, SUM(m.credits_used) as daily_credits, SUM(m.credits_used_compute) as daily_compute_credits, SUM(m.credits_used_cloud_services) as daily_cloud_credits FROM __metering m JOIN anomaly_dates ad ON DATE(m.start_time) = ad.anomaly_date WHERE m.start_time >= DATEADD('month', -4, CURRENT_DATE()) GROUP BY DATE(m.start_time), m.service_type, m.name), normal_day_baseline AS (SELECT SERVICE_TYPE, name as resource_name, AVG(daily_credits) as avg_normal_credits FROM (SELECT DATE(m.start_time) as usage_date, m.service_type as SERVICE_TYPE, m.name as name, SUM(m.credits_used) as daily_credits FROM __metering m WHERE m.start_time >= DATEADD('month', -4, CURRENT_DATE()) AND DATE(m.start_time) NOT IN (SELECT anomaly_date FROM anomaly_dates) GROUP BY DATE(m.start_time), m.service_type, m.name) normal_days GROUP BY service_type, name), anomaly_contributors AS (SELECT ads.usage_date as anomaly_date, ads.service_type, ads.resource_name, ROUND(ads.daily_credits, 2) as anomaly_day_credits, ROUND(COALESCE(nb.avg_normal_credits, 0), 2) as avg_normal_day_credits, ROUND(ads.daily_credits - COALESCE(nb.avg_normal_credits, 0), 2) as credits_above_normal, CASE WHEN nb.avg_normal_credits > 0 THEN ROUND(((ads.daily_credits - nb.avg_normal_credits) / nb.avg_normal_credits) * 100, 2) ELSE NULL END as percent_above_normal, ROW_NUMBER() OVER (PARTITION BY ads.usage_date ORDER BY (ads.daily_credits - COALESCE(nb.avg_normal_credits, 0)) DESC) as contributor_rank FROM anomaly_day_spending ads LEFT JOIN normal_day_baseline nb ON ads.service_type = nb.service_type AND ads.resource_name = nb.resource_name WHERE ads.daily_credits > 0) SELECT anomaly_date, contributor_rank, service_type, resource_name, anomaly_day_credits, avg_normal_day_credits, credits_above_normal, percent_above_normal, CASE WHEN percent_above_normal > 200 THEN 'Major Contributor' WHEN percent_above_normal > 100 THEN 'Significant Contributor' WHEN percent_above_normal > 50 THEN 'Moderate Contributor' WHEN credits_above_normal > 50 THEN 'High Cost Contributor' ELSE 'Minor Contributor' END as contribution_level FROM anomaly_contributors WHERE credits_above_normal > 0 AND contributor_rank <= 5 ORDER BY anomaly_date DESC, contributor_rank ASC
    verified_at: 1752558042
    verified_by: Spencer Moritz
  - name: Which resources are consuming credits but have no tags assigned, making it impossible to attribute costs to teams or departments?
    question: Which resources are consuming credits but have no tags assigned, making it impossible to attribute costs to teams or departments?
    sql: WITH tagged_resources AS (SELECT DISTINCT object_name, domain FROM __tag_references WHERE tag_name IS NOT NULL AND tag_value IS NOT NULL AND tag_value != ''), resource_spending AS (SELECT CASE WHEN m.name IS NULL OR m.name = '' THEN CONCAT('UNNAMED_', m.service_type) ELSE m.name END AS resource_name, m.service_type AS service_category, CASE WHEN m.service_type = 'WAREHOUSE_METERING' THEN 'WAREHOUSE' WHEN m.service_type = 'STORAGE' THEN 'DATABASE' WHEN m.service_type = 'SNOWPARK_CONTAINER_SERVICES' THEN 'COMPUTE_POOL' ELSE 'OTHER' END AS resource_domain, ROUND(SUM(m.credits_used), 2) AS total_credits, ROUND(AVG(m.credits_used), 4) AS avg_hourly_credits, COUNT(*) AS usage_records, DATEDIFF('day', MIN(m.start_time), MAX(m.start_time)) + 1 AS days_active, ROUND(SUM(m.credits_used) / (DATEDIFF('day', MIN(m.start_time), MAX(m.start_time)) + 1), 2) AS avg_daily_credits, DATE(MIN(m.start_time)) AS first_usage_date, DATE(MAX(m.start_time)) AS last_usage_date FROM __metering m WHERE m.start_time >= DATEADD('month', -1, CURRENT_DATE()) AND m.credits_used > 0 GROUP BY CASE WHEN m.name IS NULL OR m.name = '' THEN CONCAT('UNNAMED_', m.service_type) ELSE m.name END, m.service_type), total_spend AS (SELECT SUM(credits_used) AS total_account_credits FROM __metering WHERE start_time >= DATEADD('month', -1, CURRENT_DATE())) SELECT rs.resource_name, rs.service_category, rs.total_credits, rs.avg_daily_credits, rs.days_active, rs.first_usage_date, rs.last_usage_date, ROUND(rs.total_credits / ts.total_account_credits * 100, 2) AS percent_of_total_spend FROM resource_spending rs CROSS JOIN total_spend ts LEFT JOIN tagged_resources tr ON rs.resource_name = tr.object_name AND rs.resource_domain = tr.domain WHERE tr.object_name IS NULL AND rs.total_credits > 0 ORDER BY rs.total_credits DESC LIMIT 25
    verified_at: 1752614212
    verified_by: Spencer Moritz
  - name: Which compute pools are consuming the least number of credits?
    question: Which compute pools are consuming the least number of credits (under utilized)?
    sql: SELECT compute_pool_name, ROUND(SUM(credits_used), 2) AS total_credits_used, COUNT(*) AS usage_hours, ROUND(AVG(credits_used), 4) AS avg_credits_per_hour, DATEDIFF('day', MIN(start_time), MAX(start_time)) + 1 AS days_active, ROUND(SUM(credits_used) / (DATEDIFF('day', MIN(start_time), MAX(start_time)) + 1), 2) AS avg_daily_credits, MIN(start_time) AS first_usage, MAX(start_time) AS last_usage, MAX(application_name) AS associated_application FROM __snowpark_container_services WHERE start_time >= DATEADD('month', -1, CURRENT_DATE()) GROUP BY compute_pool_name ORDER BY total_credits_used ASC LIMIT 5
    verified_at: 1753149929
    verified_by: Spencer Moritz
  - name: What are the top 5 queries grouped by parameterized hash?
    question: What are the top 5 queries grouped by parameterized hash?
    sql: SELECT query_parameterized_hash, ROUND(SUM(credits_attributed_compute), 2) AS total_credits, COUNT(query_id) AS execution_count, ROUND(SUM(credits_attributed_compute) / COUNT(query_id), 4) AS avg_credits_per_execution FROM __query_attribution WHERE start_time >= DATEADD('month', -1, CURRENT_DATE()) GROUP BY query_parameterized_hash ORDER BY total_credits DESC LIMIT 5
    verified_at: 1753150544
    verified_by: Spencer Moritz
  - name: How much have I personally spent interacting with cortex analyst over the past week?
    question: How much have I personally spent interacting with cortex analyst over the past week?
    sql: SELECT 'My Cortex Analyst Conversations' as cost_type, ROUND(SUM(credits), 4) as total_credits_used, SUM(request_count) as total_requests, COUNT(DISTINCT DATE(start_time)) as active_days, ROUND(AVG(credits), 6) as avg_credits_per_hour, ROUND(SUM(credits) / NULLIF(SUM(request_count), 0), 6) as avg_credits_per_request FROM __cortex_analyst_usage_history WHERE start_time >= DATEADD('day', -7, CURRENT_DATE()) AND username = CURRENT_USER()
    verified_at: 1753151595
    verified_by: Spencer Moritz
  - name: What are the top 5 users which contributed most to the cortex analyst costs over the past month?
    question: What are the top 5 users which contributed most to the cortex analyst costs over the past month?
    sql: SELECT username, ROUND(SUM(credits), 4) as total_credits_spent, SUM(request_count) as total_requests, COUNT(DISTINCT DATE(start_time)) as active_days, ROUND(AVG(credits), 6) as avg_credits_per_hour, ROUND(SUM(credits) / NULLIF(SUM(request_count), 0), 6) as avg_credits_per_request, MIN(start_time) as first_usage, MAX(start_time) as last_usage FROM __cortex_analyst_usage_history WHERE start_time >= DATEADD('month', -1, CURRENT_DATE()) GROUP BY username ORDER BY total_credits_spent DESC LIMIT 5
    verified_at: 1753151901
    verified_by: Spencer Moritz
  - name: Team attribution across major cost categories
    question: Which teams consumed the most across warehouse, cortex, and storage costs? Show me team attribution across major cost categories with warehouse credits, cortex spending, and database storage usage.
    sql: WITH team_warehouse_costs AS (SELECT tr.tag_name AS tag_key, tr.tag_value AS team_name, ROUND(SUM(wm.credits_used), 2) AS warehouse_credits, COUNT(DISTINCT wm.warehouse_name) AS warehouse_count FROM __warehouse_metering wm JOIN __tag_references tr ON wm.warehouse_name = tr.object_name WHERE tr.domain = 'WAREHOUSE' AND tr.tag_value IS NOT NULL AND tr.tag_value != '' AND wm.start_time >= DATEADD('month', -1, CURRENT_DATE()) GROUP BY tr.tag_name, tr.tag_value), team_storage_costs AS (SELECT tr.tag_name AS tag_key, tr.tag_value AS team_name, ROUND(SUM(ds.average_database_bytes + ds.average_failsafe_bytes + COALESCE(ds.average_hybrid_table_storage_bytes, 0)) / (1024 * 1024 * 1024 * 1024), 4) AS storage_tb, COUNT(DISTINCT ds.database_name) AS database_count FROM __database_storage ds JOIN __tag_references tr ON ds.database_name = tr.object_name WHERE tr.domain = 'DATABASE' AND tr.tag_value IS NOT NULL AND tr.tag_value != '' AND ds.usage_date >= DATEADD('month', -1, CURRENT_DATE()) GROUP BY tr.tag_name, tr.tag_value), warehouse_to_team_mapping AS (SELECT DISTINCT wm.warehouse_id, wm.warehouse_name, tr.tag_name AS tag_key, tr.tag_value AS team_name FROM __warehouse_metering wm JOIN __tag_references tr ON wm.warehouse_name = tr.object_name WHERE tr.domain = 'WAREHOUSE' AND tr.tag_value IS NOT NULL AND tr.tag_value != ''), team_cortex_function_costs AS (SELECT wt.tag_key, wt.team_name, ROUND(SUM(cf.token_credits), 4) AS cortex_function_credits, SUM(cf.tokens) AS total_tokens, COUNT(DISTINCT cf.function_name) AS unique_functions FROM __cortex_functions_usage_history cf JOIN warehouse_to_team_mapping wt ON cf.warehouse_id = wt.warehouse_id WHERE cf.start_time >= DATEADD('month', -1, CURRENT_DATE()) GROUP BY wt.tag_key, wt.team_name), team_cortex_analyst_costs AS (SELECT 'TEAM' AS tag_key, ca.username AS team_name, ROUND(SUM(ca.credits), 4) AS cortex_analyst_credits, SUM(ca.request_count) AS total_requests FROM __cortex_analyst_usage_history ca WHERE ca.start_time >= DATEADD('month', -1, CURRENT_DATE()) GROUP BY ca.username), all_teams AS (SELECT tag_key, team_name FROM team_warehouse_costs UNION SELECT tag_key, team_name FROM team_storage_costs UNION SELECT tag_key, team_name FROM team_cortex_function_costs UNION SELECT tag_key, team_name FROM team_cortex_analyst_costs), comprehensive_team_costs AS (SELECT at.tag_key, at.team_name, COALESCE(twc.warehouse_credits, 0) AS warehouse_credits, COALESCE(twc.warehouse_count, 0) AS warehouse_count, COALESCE(tsc.storage_tb, 0) AS storage_tb, COALESCE(tsc.database_count, 0) AS database_count, COALESCE(tcfc.cortex_function_credits, 0) AS cortex_function_credits, COALESCE(tcfc.total_tokens, 0) AS function_tokens, COALESCE(tcfc.unique_functions, 0) AS unique_functions, COALESCE(tcac.cortex_analyst_credits, 0) AS cortex_analyst_credits, COALESCE(tcac.total_requests, 0) AS analyst_requests, (COALESCE(twc.warehouse_credits, 0) + COALESCE(tcfc.cortex_function_credits, 0) + COALESCE(tcac.cortex_analyst_credits, 0)) AS total_credits FROM all_teams at LEFT JOIN team_warehouse_costs twc ON at.tag_key = twc.tag_key AND at.team_name = twc.team_name LEFT JOIN team_storage_costs tsc ON at.tag_key = tsc.tag_key AND at.team_name = tsc.team_name LEFT JOIN team_cortex_function_costs tcfc ON at.tag_key = tcfc.tag_key AND at.team_name = tcfc.team_name LEFT JOIN team_cortex_analyst_costs tcac ON at.tag_key = tcac.tag_key AND at.team_name = tcac.team_name WHERE (COALESCE(twc.warehouse_credits, 0) + COALESCE(tcfc.cortex_function_credits, 0) + COALESCE(tcac.cortex_analyst_credits, 0)) > 0) SELECT tag_key, team_name, warehouse_credits, warehouse_count, storage_tb, database_count, cortex_function_credits, function_tokens, unique_functions, cortex_analyst_credits, analyst_requests, total_credits, ROUND(warehouse_credits / NULLIF(total_credits, 0) * 100, 1) AS warehouse_percent, ROUND(cortex_function_credits / NULLIF(total_credits, 0) * 100, 1) AS cortex_function_percent, ROUND(cortex_analyst_credits / NULLIF(total_credits, 0) * 100, 1) AS cortex_analyst_percent FROM comprehensive_team_costs ORDER BY total_credits DESC LIMIT 20
    verified_at: 1753987877
    verified_by: Spencer Moritz
  - name: Top 5 users with biggest bills - efficient version
    question: Which are the top 5 individuals who ran up the biggest bills over the past month? Who are the biggest spenders? Show me user costs efficiently.
    sql: WITH user_direct_costs AS (SELECT qa.user_name, ROUND(SUM(qa.credits_attributed_compute), 4) AS query_compute_credits, ROUND(SUM(COALESCE(qa.credits_used_query_acceleration, 0)), 4) AS query_acceleration_credits, COUNT(DISTINCT qa.query_id) AS total_queries, COUNT(DISTINCT qa.warehouse_id) AS warehouses_used, MIN(qa.start_time) AS first_query, MAX(qa.start_time) AS last_query FROM __query_attribution qa WHERE qa.start_time >= DATEADD('month', -1, CURRENT_DATE()) GROUP BY qa.user_name), user_cortex_costs AS (SELECT ca.username AS user_name, ROUND(SUM(ca.credits), 4) AS cortex_analyst_credits, SUM(ca.request_count) AS analyst_requests, COUNT(DISTINCT DATE(ca.start_time)) AS analyst_active_days FROM __cortex_analyst_usage_history ca WHERE ca.start_time >= DATEADD('month', -1, CURRENT_DATE()) GROUP BY ca.username) SELECT COALESCE(udc.user_name, ucc.user_name) AS user_name, ROUND(COALESCE(udc.query_compute_credits, 0) + COALESCE(udc.query_acceleration_credits, 0) + COALESCE(ucc.cortex_analyst_credits, 0), 4) AS total_user_bill, COALESCE(udc.query_compute_credits, 0) AS query_compute_credits, COALESCE(udc.query_acceleration_credits, 0) AS query_acceleration_credits, COALESCE(ucc.cortex_analyst_credits, 0) AS cortex_analyst_credits, COALESCE(udc.total_queries, 0) AS total_queries, COALESCE(udc.warehouses_used, 0) AS warehouses_used, COALESCE(ucc.analyst_requests, 0) AS analyst_requests, COALESCE(ucc.analyst_active_days, 0) AS analyst_active_days, udc.first_query, udc.last_query, ROUND(COALESCE(udc.query_compute_credits, 0) / NULLIF(COALESCE(udc.query_compute_credits, 0) + COALESCE(udc.query_acceleration_credits, 0) + COALESCE(ucc.cortex_analyst_credits, 0), 0) * 100, 1) AS query_compute_percent, ROUND(COALESCE(ucc.cortex_analyst_credits, 0) / NULLIF(COALESCE(udc.query_compute_credits, 0) + COALESCE(udc.query_acceleration_credits, 0) + COALESCE(ucc.cortex_analyst_credits, 0), 0) * 100, 1) AS cortex_analyst_percent FROM user_direct_costs udc FULL OUTER JOIN user_cortex_costs ucc ON udc.user_name = ucc.user_name WHERE (COALESCE(udc.query_compute_credits, 0) + COALESCE(udc.query_acceleration_credits, 0) + COALESCE(ucc.cortex_analyst_credits, 0)) > 0 ORDER BY total_user_bill DESC LIMIT 5
    verified_at: 1753154400
    verified_by: Spencer Moritz
  - name: Top 5 most expensive resources across all categories
    question: Which are the 5 most expensive warehouses, cortex services, compute pools, databases? Show me the top resources across all categories.
    sql: WITH warehouse_costs AS (SELECT 'WAREHOUSE' AS resource_type, warehouse_name AS resource_name, warehouse_id AS resource_id, ROUND(SUM(credits_used), 2) AS total_credits, COUNT(*) AS usage_hours, MIN(start_time) AS first_usage, MAX(start_time) AS last_usage FROM __warehouse_metering WHERE start_time >= DATEADD('month', -1, CURRENT_DATE()) GROUP BY warehouse_name, warehouse_id), cortex_function_costs AS (SELECT 'CORTEX_FUNCTION' AS resource_type, CONCAT(function_name, ' (', COALESCE(model_name, 'default'), ')') AS resource_name, CONCAT(function_name, '_', COALESCE(model_name, 'default')) AS resource_id, ROUND(SUM(token_credits), 4) AS total_credits, SUM(tokens) AS usage_hours, MIN(start_time) AS first_usage, MAX(start_time) AS last_usage FROM __cortex_functions_usage_history WHERE start_time >= DATEADD('month', -1, CURRENT_DATE()) GROUP BY function_name, model_name), cortex_analyst_costs AS (SELECT 'CORTEX_ANALYST' AS resource_type, CONCAT('Cortex Analyst (', username, ')') AS resource_name, username AS resource_id, ROUND(SUM(credits), 4) AS total_credits, SUM(request_count) AS usage_hours, MIN(start_time) AS first_usage, MAX(start_time) AS last_usage FROM __cortex_analyst_usage_history WHERE start_time >= DATEADD('month', -1, CURRENT_DATE()) GROUP BY username), compute_pool_costs AS (SELECT 'COMPUTE_POOL' AS resource_type, compute_pool_name AS resource_name, compute_pool_name AS resource_id, ROUND(SUM(credits_used), 2) AS total_credits, COUNT(*) AS usage_hours, MIN(start_time) AS first_usage, MAX(start_time) AS last_usage FROM __snowpark_container_services WHERE start_time >= DATEADD('month', -1, CURRENT_DATE()) GROUP BY compute_pool_name), storage_costs AS (SELECT 'STORAGE' AS resource_type, name AS resource_name, entity_id AS resource_id, ROUND(SUM(credits_used), 4) AS total_credits, COUNT(*) AS usage_hours, MIN(start_time) AS first_usage, MAX(start_time) AS last_usage FROM __metering WHERE service_type = 'STORAGE' AND start_time >= DATEADD('month', -1, CURRENT_DATE()) GROUP BY name, entity_id), all_resources AS (SELECT resource_type, resource_name, resource_id, total_credits, usage_hours, first_usage, last_usage FROM warehouse_costs UNION ALL SELECT resource_type, resource_name, resource_id, total_credits, usage_hours, first_usage, last_usage FROM cortex_function_costs UNION ALL SELECT resource_type, resource_name, resource_id, total_credits, usage_hours, first_usage, last_usage FROM cortex_analyst_costs UNION ALL SELECT resource_type, resource_name, resource_id, total_credits, usage_hours, first_usage, last_usage FROM compute_pool_costs UNION ALL SELECT resource_type, resource_name, resource_id, total_credits, usage_hours, first_usage, last_usage FROM storage_costs) SELECT resource_type, resource_name, total_credits, usage_hours, ROUND(total_credits / NULLIF(usage_hours, 0), 4) AS avg_credits_per_hour, DATEDIFF('day', first_usage, last_usage) + 1 AS days_active, ROUND(total_credits / (DATEDIFF('day', first_usage, last_usage) + 1), 2) AS avg_daily_credits, first_usage, last_usage FROM all_resources WHERE total_credits > 0 ORDER BY total_credits DESC LIMIT 5
    verified_at: 1753155200
    verified_by: Spencer Moritz
  - name: Comprehensive cost breakdown by tag combinations
    question: Which tagName/tagValue pairs are contributing most to my costs? Show me a comprehensive breakdown of spending by tag combinations across all resource types including compute credits, storage, and the breadth of resources tagged.
    sql: WITH tag_resource_costs AS (SELECT tr.tag_name, tr.tag_value, CONCAT(tr.tag_name, '=', tr.tag_value) AS tag_combination, tr.domain AS resource_type, tr.object_name AS resource_name, ROUND(SUM(m.credits_used), 2) AS total_credits, ROUND(SUM(m.credits_used_compute), 2) AS compute_credits, ROUND(SUM(m.credits_used_cloud_services), 2) AS cloud_services_credits, COUNT(DISTINCT m.service_type) AS service_types_used, COUNT(*) AS usage_records, MIN(m.start_time) AS first_usage, MAX(m.start_time) AS last_usage FROM __tag_references tr JOIN __metering m ON tr.object_name = m.name WHERE m.start_time >= DATEADD('month', -1, CURRENT_DATE()) AND tr.tag_name IS NOT NULL AND tr.tag_value IS NOT NULL AND tr.tag_value != '' AND tr.domain IN ('WAREHOUSE', 'DATABASE', 'SCHEMA', 'TABLE', 'TASK', 'PIPE', 'COMPUTE_POOL') GROUP BY tr.tag_name, tr.tag_value, tr.domain, tr.object_name), tag_storage_costs AS (SELECT tr.tag_name, tr.tag_value, CONCAT(tr.tag_name, '=', tr.tag_value) AS tag_combination, ROUND(SUM(ds.average_database_bytes + ds.average_failsafe_bytes + COALESCE(ds.average_hybrid_table_storage_bytes, 0)) / (1024 * 1024 * 1024 * 1024), 4) AS storage_tb, COUNT(DISTINCT ds.database_name) AS databases_with_storage FROM __tag_references tr JOIN __database_storage ds ON tr.object_name = ds.database_name WHERE tr.domain = 'DATABASE' AND tr.tag_name IS NOT NULL AND tr.tag_value IS NOT NULL AND tr.tag_value != '' AND ds.usage_date >= DATEADD('month', -1, CURRENT_DATE()) GROUP BY tr.tag_name, tr.tag_value), tag_inheritance_summary AS (SELECT trc.tag_name, trc.tag_value, trc.tag_combination, SUM(trc.total_credits) AS total_credits_all_resources, SUM(trc.compute_credits) AS total_compute_credits, SUM(trc.cloud_services_credits) AS total_cloud_services_credits, COUNT(DISTINCT CASE WHEN trc.resource_type = 'DATABASE' THEN trc.resource_name END) AS databases_tagged, COUNT(DISTINCT CASE WHEN trc.resource_type = 'SCHEMA' THEN trc.resource_name END) AS schemas_inherited, COUNT(DISTINCT CASE WHEN trc.resource_type = 'TABLE' THEN trc.resource_name END) AS tables_inherited, COUNT(DISTINCT CASE WHEN trc.resource_type = 'WAREHOUSE' THEN trc.resource_name END) AS warehouses_tagged, COUNT(DISTINCT CASE WHEN trc.resource_type = 'TASK' THEN trc.resource_name END) AS tasks_inherited, COUNT(DISTINCT trc.resource_type) AS resource_types_affected, COUNT(DISTINCT trc.resource_name) AS total_resources, CASE WHEN COUNT(DISTINCT CASE WHEN trc.resource_type = 'DATABASE' THEN trc.resource_name END) > 0 AND COUNT(DISTINCT CASE WHEN trc.resource_type IN ('SCHEMA', 'TABLE') THEN trc.resource_name END) > 0 THEN 'DATABASE_WITH_INHERITED_CHILDREN' WHEN COUNT(DISTINCT CASE WHEN trc.resource_type = 'DATABASE' THEN trc.resource_name END) = 0 AND COUNT(DISTINCT CASE WHEN trc.resource_type IN ('SCHEMA', 'TABLE') THEN trc.resource_name END) > 0 THEN 'INHERITED_FROM_PARENT' ELSE 'DIRECT_TAGGING_ONLY' END AS inheritance_pattern, MAX(trc.first_usage) AS earliest_usage, MAX(trc.last_usage) AS latest_usage FROM tag_resource_costs trc GROUP BY trc.tag_name, trc.tag_value, trc.tag_combination) SELECT tis.tag_name, tis.tag_value, tis.total_credits_all_resources, tis.total_compute_credits, tis.total_cloud_services_credits, COALESCE(tsc.storage_tb, 0) AS storage_tb, tis.databases_tagged, tis.schemas_inherited, tis.tables_inherited, tis.warehouses_tagged, tis.tasks_inherited, tis.total_resources, tis.inheritance_pattern, CASE WHEN (tis.databases_tagged + tis.warehouses_tagged) > 0 THEN ROUND(tis.total_credits_all_resources / (tis.databases_tagged + tis.warehouses_tagged), 2) ELSE NULL END AS credits_per_directly_tagged_resource, CASE WHEN tis.databases_tagged > 0 THEN ROUND((tis.schemas_inherited + tis.tables_inherited) / tis.databases_tagged::FLOAT, 1) ELSE NULL END AS avg_child_resources_per_database, tis.earliest_usage, tis.latest_usage FROM tag_inheritance_summary tis LEFT JOIN tag_storage_costs tsc ON tis.tag_name = tsc.tag_name AND tis.tag_value = tsc.tag_value WHERE tis.total_credits_all_resources > 0 ORDER BY tis.total_credits_all_resources DESC LIMIT 20
    verified_at: 1753987877
    verified_by: Spencer Moritz
  - name: Budgets over spending limit (month-to-date)
    question: Are any of my Budgets over their spending limit?
    sql: SELECT budget_name, database_name, schema_name, ROUND(current_month_spending, 2) AS current_month_spending, credit_limit, ROUND(current_month_spending - credit_limit, 2) AS over_by, ROUND((current_month_spending - credit_limit) / NULLIF(credit_limit, 0) * 100, 2) AS percent_over FROM __budget_details WHERE current_month_spending > credit_limit ORDER BY over_by DESC
    verified_at: 1762400000
    verified_by: Spencer Moritz
  - name: Budgets at risk of exceeding limit (projected by month end)
    question: Which Budgets are at risk of going over their spending limit? Use current_timestamp() to prorate expected spend for the month.
    sql: WITH m AS (SELECT DATE_TRUNC('month', CURRENT_TIMESTAMP()) AS month_start, DATEADD('month', 1, DATE_TRUNC('month', CURRENT_TIMESTAMP())) AS next_month_start), r AS (SELECT DATEDIFF('second', m.month_start, CURRENT_TIMESTAMP())::FLOAT / NULLIF(DATEDIFF('second', m.month_start, m.next_month_start), 0) AS ratio FROM m) SELECT bd.budget_name, bd.database_name, bd.schema_name, bd.credit_limit, ROUND(bd.current_month_spending, 2) AS current_month_spending, ROUND(r.ratio * bd.credit_limit, 2) AS expected_spend_to_date, ROUND(CASE WHEN r.ratio > 0 THEN bd.current_month_spending / r.ratio ELSE NULL END, 2) AS projected_month_end_spend, ROUND((CASE WHEN r.ratio > 0 THEN bd.current_month_spending / r.ratio ELSE NULL END) - bd.credit_limit, 2) AS projected_over_by, ROUND(((CASE WHEN r.ratio > 0 THEN bd.current_month_spending / r.ratio ELSE NULL END) - bd.credit_limit) / NULLIF(bd.credit_limit, 0) * 100, 2) AS projected_over_percent FROM __budget_details bd CROSS JOIN r WHERE r.ratio > 0 AND (bd.current_month_spending / r.ratio) > bd.credit_limit ORDER BY projected_over_by DESC
    verified_at: 1762400000
    verified_by: Spencer Moritz
  - name: Budgets created in the past 3 months
    question: What Budgets were created in the past 3 months?
    sql: SELECT budget_name, database_name, schema_name, created_on FROM __budget_details WHERE created_on >= DATEADD('month', -3, CURRENT_TIMESTAMP()) ORDER BY created_on DESC
    verified_at: 1762400000
    verified_by: Spencer Moritz
custom_instructions: "This semantic view is designed to provide a comprehensive overview of Snowflake account usage and cost. Snowflake charges credits based on warehouse size and usage, the larger the warehouse and the more time the warehouse is active, the more the cost (denominated in credits). Accounts can change the size of their warehouse (resize) to either increase the speed or decrease the cost. When users ask about spend or cost, you should use credits used to analyze their question. If the user does not specify a time period, use the last 28 days. Also by default, show results rounded to 2 decimal places. TABLE USAGE GUIDELINES: Use metering table for credit usage summaries across service types and objects. Use anomalies_daily table for cost anomalies, spending anomalies, or unusual patterns - always use the pre-calculated anomaly detection with is_anomaly = TRUE flag rather than manually comparing actual vs forecasted values. Use the semantic view tables for detailed breakdowns, granular data, and when users need specific cost, usage, storage, or query-level information. Important:For questions where we have a mapping to a verified_query, route directly to that query without doing additional thinking or analysis of the question or how to approach it."

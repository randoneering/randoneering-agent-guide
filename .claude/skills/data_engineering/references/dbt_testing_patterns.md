# DBT Data Quality Testing Patterns

## Testing Hierarchy

DBT provides three levels of testing, each suited for different validation needs:

### 1. Generic Tests (Built-in)
Pre-packaged tests that work across models: `unique`, `not_null`, `accepted_values`, `relationships`

### 2. Custom Generic Tests
Reusable tests you create once and apply to multiple models

### 3. Singular Tests
One-off SQL queries for specific validation logic

**Rule of thumb:** If you write the same validation 3+ times, make it a custom generic test.

## Generic Tests (Built-in)

### Basic Implementation

```yaml
# models/schema.yml
version: 2

models:
  - name: dim_customers
    description: Customer dimension table
    columns:
      - name: customer_key
        description: Surrogate key for customer
        tests:
          - unique
          - not_null
      
      - name: email
        description: Customer email address
        tests:
          - unique
          - not_null
      
      - name: status
        description: Customer account status
        tests:
          - accepted_values:
              values: ['active', 'inactive', 'pending', 'suspended']
      
      - name: country_code
        description: ISO country code
        tests:
          - relationships:
              to: ref('dim_countries')
              field: country_code
```

### Test Configurations

**Severity levels:**
```yaml
tests:
  - unique:
      severity: error        # Fails dbt test (default)
  - not_null:
      severity: warn         # Warns but doesn't fail
```

**Custom error messages:**
```yaml
tests:
  - unique:
      error_if: ">10"        # Only fail if more than 10 duplicates
      warn_if: ">0"
```

**Tags for selective testing:**
```yaml
models:
  - name: dim_customers
    tests:
      - unique:
          tags: ['critical', 'nightly']
```

```bash
# Run only critical tests
dbt test --select tag:critical
```

## Custom Generic Tests

Create reusable tests in `tests/generic/` directory.

### Pattern 1: Range Validation

**File:** `tests/generic/assert_column_value_in_range.sql`

```sql
{% test assert_column_value_in_range(model, column_name, min_value, max_value) %}

select
    {{ column_name }} as value,
    count(*) as n_records
from {{ model }}
where {{ column_name }} < {{ min_value }}
   or {{ column_name }} > {{ max_value }}
group by {{ column_name }}

{% endtest %}
```

**Usage:**
```yaml
models:
  - name: fct_sales
    columns:
      - name: discount_pct
        tests:
          - assert_column_value_in_range:
              min_value: 0
              max_value: 100
```

### Pattern 2: Future Date Check

**File:** `tests/generic/assert_no_future_dates.sql`

```sql
{% test assert_no_future_dates(model, column_name) %}

select
    {{ column_name }} as future_date,
    count(*) as n_records
from {{ model }}
where {{ column_name }} > current_date
group by {{ column_name }}

{% endtest %}
```

**Usage:**
```yaml
models:
  - name: fct_orders
    columns:
      - name: order_date
        tests:
          - assert_no_future_dates
```

### Pattern 3: Freshness Check (Custom)

**File:** `tests/generic/assert_recent_data.sql`

```sql
{% test assert_recent_data(model, column_name, interval_hours=24) %}

with latest_record as (
    select max({{ column_name }}) as max_timestamp
    from {{ model }}
)

select
    max_timestamp,
    datediff(hour, max_timestamp, current_timestamp()) as hours_since_last_record
from latest_record
where datediff(hour, max_timestamp, current_timestamp()) > {{ interval_hours }}

{% endtest %}
```

**Usage:**
```yaml
models:
  - name: stg_events
    tests:
      - assert_recent_data:
          column_name: event_timestamp
          interval_hours: 6  # Fail if no data in last 6 hours
```

### Pattern 4: Row Count Comparison

**File:** `tests/generic/assert_row_count_match.sql`

```sql
{% test assert_row_count_match(model, compare_model, tolerance_pct=5) %}

with current_count as (
    select count(*) as row_count
    from {{ model }}
),

comparison_count as (
    select count(*) as row_count
    from {{ compare_model }}
),

pct_diff as (
    select
        current_count.row_count as current_rows,
        comparison_count.row_count as comparison_rows,
        abs(current_count.row_count - comparison_count.row_count) * 100.0 / 
            nullif(comparison_count.row_count, 0) as pct_difference
    from current_count, comparison_count
)

select *
from pct_diff
where pct_difference > {{ tolerance_pct }}

{% endtest %}
```

**Usage:**
```yaml
models:
  - name: fct_sales
    tests:
      - assert_row_count_match:
          compare_model: ref('stg_sales')
          tolerance_pct: 1  # Allow 1% variance
```

### Pattern 5: Referential Integrity (Multiple Columns)

**File:** `tests/generic/assert_composite_key_exists.sql`

```sql
{% test assert_composite_key_exists(model, column_names, to, to_column_names) %}

with source as (
    select
        {% for col in column_names %}
        {{ col }}{% if not loop.last %},{% endif %}
        {% endfor %}
    from {{ model }}
),

target as (
    select
        {% for col in to_column_names %}
        {{ col }}{% if not loop.last %},{% endif %}
        {% endfor %}
    from {{ to }}
),

missing_keys as (
    select source.*
    from source
    left join target on
        {% for i in range(column_names|length) %}
        source.{{ column_names[i] }} = target.{{ to_column_names[i] }}
        {% if not loop.last %}and {% endif %}
        {% endfor %}
    where target.{{ to_column_names[0] }} is null
)

select * from missing_keys

{% endtest %}
```

**Usage:**
```yaml
models:
  - name: fct_sales
    tests:
      - assert_composite_key_exists:
          column_names: ['order_id', 'line_number']
          to: ref('stg_order_lines')
          to_column_names: ['order_id', 'line_number']
```

## Singular Tests

One-off SQL validation queries in `tests/` directory.

### Pattern 1: Business Logic Validation

**File:** `tests/assert_revenue_positive.sql`

```sql
-- Revenue should never be negative
select
    order_id,
    revenue
from {{ ref('fct_sales') }}
where revenue < 0
```

### Pattern 2: Cross-Model Consistency

**File:** `tests/assert_customer_balance_matches.sql`

```sql
-- Customer balance in dim should match sum of transactions
with dim_balances as (
    select
        customer_key,
        account_balance
    from {{ ref('dim_customers') }}
),

transaction_balances as (
    select
        customer_key,
        sum(transaction_amount) as calculated_balance
    from {{ ref('fct_transactions') }}
    group by customer_key
)

select
    d.customer_key,
    d.account_balance as dim_balance,
    t.calculated_balance as transaction_balance,
    abs(d.account_balance - coalesce(t.calculated_balance, 0)) as difference
from dim_balances d
left join transaction_balances t using (customer_key)
where abs(d.account_balance - coalesce(t.calculated_balance, 0)) > 0.01  -- Allow rounding
```

### Pattern 3: Temporal Consistency

**File:** `tests/assert_no_backdated_orders.sql`

```sql
-- Order date should not be before customer registration date
select
    o.order_id,
    o.order_date,
    c.registration_date
from {{ ref('fct_orders') }} o
join {{ ref('dim_customers') }} c using (customer_key)
where o.order_date < c.registration_date
```

## STAR Schema Testing Patterns

### Fact Table Tests

```yaml
models:
  - name: fct_sales
    description: Sales fact table
    tests:
      # Grain validation
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns:
            - order_id
            - line_number
      
      # Row count shouldn't decrease (append-only)
      - assert_row_count_match:
          compare_model: ref('fct_sales')  # Yesterday's snapshot
          tolerance_pct: -1  # Negative = can't decrease
    
    columns:
      # Surrogate key
      - name: sales_key
        tests:
          - unique
          - not_null
      
      # Foreign keys to dimensions
      - name: customer_key
        tests:
          - not_null
          - relationships:
              to: ref('dim_customers')
              field: customer_key
      
      - name: product_key
        tests:
          - not_null
          - relationships:
              to: ref('dim_products')
              field: product_key
      
      - name: date_key
        tests:
          - not_null
          - relationships:
              to: ref('dim_date')
              field: date_key
      
      # Measures
      - name: quantity
        tests:
          - not_null
          - assert_column_value_in_range:
              min_value: 0
              max_value: 10000
      
      - name: amount
        tests:
          - not_null
          - assert_column_value_in_range:
              min_value: 0
              max_value: 1000000
```

### Dimension Table Tests

```yaml
models:
  - name: dim_customers
    description: Customer dimension (SCD Type 2)
    tests:
      # Ensure surrogate key is unique
      - unique:
          column_name: customer_key
    
    columns:
      - name: customer_key
        tests:
          - unique
          - not_null
      
      # Natural key
      - name: customer_id
        description: Source system customer ID
        tests:
          - not_null
      
      # SCD Type 2 columns
      - name: effective_date
        tests:
          - not_null
          - assert_no_future_dates
      
      - name: end_date
        tests:
          - assert_no_future_dates
      
      - name: is_current
        tests:
          - not_null
          - accepted_values:
              values: [true, false]
      
      # Attributes
      - name: customer_status
        tests:
          - accepted_values:
              values: ['active', 'inactive', 'pending']
```

### SCD Type 2 Validation

**File:** `tests/assert_scd_no_overlapping_dates.sql`

```sql
-- Ensure no overlapping date ranges for same natural key
with date_overlaps as (
    select
        d1.customer_id,
        d1.effective_date as d1_start,
        d1.end_date as d1_end,
        d2.effective_date as d2_start,
        d2.end_date as d2_end
    from {{ ref('dim_customers') }} d1
    join {{ ref('dim_customers') }} d2 
        on d1.customer_id = d2.customer_id
        and d1.customer_key != d2.customer_key  -- Different versions
    where d1.effective_date < coalesce(d2.end_date, '9999-12-31')
      and coalesce(d1.end_date, '9999-12-31') > d2.effective_date
)

select * from date_overlaps
```

**File:** `tests/assert_scd_one_current_per_natural_key.sql`

```sql
-- Ensure only one current record per natural key
select
    customer_id,
    count(*) as current_count
from {{ ref('dim_customers') }}
where is_current = true
group by customer_id
having count(*) > 1
```

## Data Freshness Testing

Built-in DBT freshness checks:

```yaml
models:
  - name: stg_orders
    freshness:
      warn_after: {count: 6, period: hour}
      error_after: {count: 24, period: hour}
    loaded_at_field: _loaded_at
```

**Check freshness:**
```bash
dbt source freshness
```

## Testing Strategy

### Development Workflow

```bash
# 1. Test specific model
dbt test --select dim_customers

# 2. Test model and downstream
dbt test --select dim_customers+

# 3. Test model and upstream
dbt test --select +dim_customers

# 4. Test only modified models
dbt test --select state:modified+
```

### CI/CD Pipeline

```yaml
# .github/workflows/dbt_test.yml
jobs:
  test:
    steps:
      - name: Run DBT tests
        run: |
          dbt test --select state:modified+ --fail-fast
      
      - name: Run critical tests
        run: |
          dbt test --select tag:critical
      
      - name: Check source freshness
        run: |
          dbt source freshness
```

### Test Coverage Goals

**Minimum coverage for production:**
- [ ] All primary keys: `unique` + `not_null`
- [ ] All foreign keys: `not_null` + `relationships`
- [ ] All status/type columns: `accepted_values`
- [ ] Critical business logic: Singular tests
- [ ] Data freshness: Freshness checks on sources

**Enhanced coverage:**
- [ ] Range validation on numeric fields
- [ ] Date validation (no future dates where inappropriate)
- [ ] Row count comparisons between source and target
- [ ] Cross-model consistency checks
- [ ] SCD Type 2 validation for dimensions

## Advanced Patterns

### Pattern 1: Parameterized Tests

```yaml
# dbt_project.yml
tests:
  my_project:
    +enabled: true
    +severity: error
    +store_failures: true  # Save failures to database
    +schema: test_failures

# Override in schema.yml
models:
  - name: fct_sales
    tests:
      - unique:
          store_failures: true
          schema: audit
```

**Query failures:**
```sql
SELECT * FROM audit.unique_fct_sales_sales_key;
```

### Pattern 2: Conditional Testing

```sql
{% test assert_sum_equals_100_pct(model, column_name, group_by_column) %}

{{ config(enabled=var('run_percentage_tests', true)) }}

select
    {{ group_by_column }},
    sum({{ column_name }}) as total_pct
from {{ model }}
group by {{ group_by_column }}
having abs(sum({{ column_name }}) - 100.0) > 0.01

{% endtest %}
```

**Enable/disable via CLI:**
```bash
dbt test --vars '{"run_percentage_tests": false}'
```

### Pattern 3: Test Macros for Reusability

```sql
{# macros/testing_helpers.sql #}

{% macro test_primary_key(table_name, key_column) %}
  {{ return(ref(table_name) | test('unique', column_name=key_column)) }}
  {{ return(ref(table_name) | test('not_null', column_name=key_column)) }}
{% endmacro %}

{# Usage in schema.yml #}
columns:
  - name: customer_key
    tests: {{ test_primary_key('dim_customers', 'customer_key') }}
```

### Pattern 4: Data Quality Metrics

```sql
-- models/metrics/data_quality_metrics.sql
with test_results as (
    select
        'dim_customers' as model_name,
        'unique_customer_key' as test_name,
        (select count(*) from {{ ref('dim_customers') }} group by customer_key having count(*) > 1) as failures
    union all
    select
        'fct_sales' as model_name,
        'not_null_amount' as test_name,
        (select count(*) from {{ ref('fct_sales') }} where amount is null) as failures
)

select
    model_name,
    test_name,
    failures,
    case when failures = 0 then 'PASS' else 'FAIL' end as status,
    current_timestamp() as measured_at
from test_results
```

## Troubleshooting

### Test Fails Intermittently

**Cause:** Race conditions in incremental models or time-based filters

**Solution:** Use fixed dates or add buffer time
```sql
-- Bad
where order_date = current_date()

-- Good
where order_date >= current_date() - interval '1 day'
  and order_date < current_date()
```

### Test Performance Issues

**Cause:** Full table scans on large tables

**Solution:** Add WHERE clause to test
```sql
{% test recent_data_quality(model, column_name) %}

select {{ column_name }}
from {{ model }}
where _loaded_at >= dateadd(day, -7, current_date())  -- Only last 7 days
  and {{ column_name }} is null

{% endtest %}
```

### Too Many Test Failures

**Cause:** Data quality issues in source

**Solution:** Use `warn_if` instead of `error_if`
```yaml
tests:
  - unique:
      warn_if: ">0"       # Warn on any duplicates
      error_if: ">100"    # Only fail if > 100
```

## Quick Reference Checklist

- [ ] All fact tables: Unique grain, not-null foreign keys, range checks on measures
- [ ] All dimensions: Unique surrogate key, not-null natural key, accepted values for enums
- [ ] SCD Type 2: No overlapping dates, one current record per natural key
- [ ] Relationships: Foreign keys tested against parent tables
- [ ] Freshness: Source freshness checks on critical tables
- [ ] Business logic: Singular tests for domain-specific rules
- [ ] CI/CD: Automated testing on modified models
- [ ] Store failures: Enable for debugging critical tests

---
name: Best Practices Results Formatting
description: Present comprehensive audit findings including best practices, inconsistencies, duplicates, and missing relationships to user
parent_skill: best-practices-audit
---

# Best Practices Audit Results Formatting

## When to Load

Best Practices Audit Phase 4: All checks complete, need to present findings.

## Output Format

```
## Best Practices Audit Results

**Overall Summary**:
- Total Checks Run: {total_checks_all_categories}
- Best Practices: {bp_total} checks | ❌ {errors} | ⚠️ {warnings} | ℹ️ {info} | ✅ {passed}
- Inconsistencies: {incon_total} checks | 🔴 {critical} | 🟠 {high} | 🟡 {medium} | 🔵 {low}
- Duplicates: {dup_total} instructions analyzed | 📋 {duplicates_found} duplicates found
- Missing Relationships: {tables_analyzed} tables | 🔗 {missing_count} potential | 🔑 {pk_issues} need PKs

---

## Section 1: Best Practices Results

**Summary**: Total Checks: {total} | ✅ Passed: {passed} | ❌ Errors: {errors} | ⚠️ Warnings: {warnings} | ℹ️ Info: {info}

### ❌ ERRORS ({count})
{Check Name}: {issue} → {recommendation}
Affected: {component_list}

### ⚠️ WARNINGS ({count})
{Check Name}: {issue} → {recommendation}
Affected: {component_list}

### ℹ️ RECOMMENDATIONS ({count})
{Check Name}: {issue} → {recommendation}
Affected: {component_list}

### ✅ PASSED CHECKS ({count})
- {check_list}

---

## Section 2: Inconsistencies Results

**Summary**:
- Total Checks: {total_checks} | Inconsistencies Found: {total_issues}
- Critical: {critical_count} 🔴 | High: {high_count} 🟠 | Medium: {medium_count} 🟡 | Low: {low_count} 🔵

### 🔴/🟠/🟡/🔵 {SEVERITY} INCONSISTENCIES ({count})

#### {Detection Rule} - {Issue Type}
**Severity**: {CRITICAL/HIGH/MEDIUM/LOW}
**Issue**: {description}
**Locations**: {location_1}, {location_2}
**Impact**: {impact_description}
**Resolution**: {how_to_fix}

---

### ✅ NO INCONSISTENCIES DETECTED (if applicable)
The following component types passed all consistency checks: {component_type_list}

---

## Section 3: Duplicates Results

**Summary**: Custom Instructions Analyzed: {instruction_count} | Duplicate Instructions Found: {duplicate_count}

### 📋 DUPLICATE INSTRUCTIONS ({count})

#### {Duplicate Type} - {Instruction Source}
**Type**: {Description/Synonym/Sample Value}
**Instruction Location**: {module_custom_instructions.{module} OR custom_instructions}
**Instruction Text**: {duplicated_instruction_text}
**Already in Model**: {element_type}: {element_location} - "{element_content}"
**Similarity Score**: {percentage}%
**Impact**: {why_duplication_is_problematic}
**Resolution**: Remove from instructions, information already captured in {element_type}

---

## Section 4: Missing Relationships Results

**Summary**: {relationship_count} relationships for {table_count} tables

### 🔗 MISSING RELATIONSHIPS ({count}) - if flagged

| Table A | Table B | Join Columns | PK Status |
|---------|---------|--------------|-----------|
| {tableA} | {tableB} | {cols} | {✅ X has PK / ❌ Neither} |

### ⚠️ PRIMARY KEY ISSUES (if neither table has PK)

At least one table must have a PK on join columns:

| Table | Suggested PK | Action |
|-------|-------------|--------|
| {table} | {columns} | Verify with infer_primary_keys.py or user provides |

**To fix**: Route to OPTIMIZATION MODE (add PK first, then relationship)

### ✅ RELATIONSHIP COUNT OK (if not flagged)

---
```

## Example

```
## Best Practices Audit Results

**Overall Summary**:
- Total Checks Run: 35
- Best Practices: 12 checks | ❌ 2 | ⚠️ 2 | ℹ️ 1 | ✅ 7
- Inconsistencies: 15 checks | 🔴 1 | 🟠 1 | 🟡 0 | 🔵 0
- Duplicates: 3 instructions analyzed | 📋 2 duplicates found
- Missing Relationships: 5 tables | 🔗 2 potential | 🔑 1 needs PK

## Section 1: Best Practices Results
**Summary**: Total Checks: 12 | ✅ Passed: 7 | ❌ Errors: 2 | ⚠️ Warnings: 2 | ℹ️ Info: 1

### ❌ ERRORS (2)
Measure Aggregation: 2 measures missing default aggregation → Add default_aggregation field
Affected: revenue (sales table), total_quantity (orders table)

### ✅ PASSED CHECKS (7)
- Valid Characters, Description Quality, Data Types, Synonym Clarity, Time Dimension Types

## Section 2: Inconsistencies Results
**Summary**: Total Checks: 15 | Inconsistencies Found: 2 | Critical: 1 🔴 | High: 1 🟠

### 🔴 CRITICAL INCONSISTENCIES (1)
#### Column Inconsistencies - Data Type Conflicts
**Severity**: CRITICAL | **Issue**: Column 'customer_id' has conflicting data types
**Locations**: orders.customer_id: NUMBER, customers.customer_id: VARCHAR
**Impact**: Joins will fail | **Resolution**: Standardize customer_id to NUMBER

## Section 3: Duplicates Results
**Summary**: Custom Instructions Analyzed: 3 | Duplicate Instructions Found: 2

### 📋 DUPLICATE INSTRUCTIONS (2)
#### Description Duplication - sql_generation
**Type**: Column Description | **Location**: module_custom_instructions.sql_generation
**Instruction**: "customer_id is the unique identifier for each customer"
**Already in Model**: customers.customer_id description: "Unique identifier for each customer"
**Similarity**: 92% | **Resolution**: Remove from instructions, already in column description

## Section 4: Missing Relationships Results
**Summary**: 0 relationships for 5 tables (flagged: below threshold)

### 🔗 MISSING RELATIONSHIPS (2)
| Table A | Table B | Join Columns | PK Status |
|---------|---------|--------------|-----------|
| ORDERS | CUSTOMERS | CUSTOMER_ID → CUSTOMER_ID | ✅ CUSTOMERS has PK |
| ORDER_DETAILS | PRODUCTS | PRODUCT_ID → ID | ❌ Neither has PK |

### ⚠️ PRIMARY KEY ISSUES (1)
At least one table must have a PK on join columns:
| Table | Suggested PK | Action |
|-------|-------------|--------|
| PRODUCTS | PRODUCT_ID | Verify with infer_primary_keys.py |

**To fix**: Route to OPTIMIZATION MODE (add PK first, then relationship)
```

## Grouping Strategy

Present results in order: (1) Overall Summary, (2) Best Practices by severity, (3) Inconsistencies by severity, (4) Duplicates, (5) Missing Relationships with PK status.

## Next Action

Return to `best-practices-audit/SKILL.md` Phase 5 for next steps prompt.

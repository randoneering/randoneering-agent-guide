#!/usr/bin/env python3
"""
Generate DBT schema.yml test configurations from existing models.

Usage:
    python generate_dbt_tests.py <path_to_dbt_model.sql>
    python generate_dbt_tests.py models/marts/fct_sales.sql

Output:
    YAML configuration for schema.yml with recommended tests based on column names
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple


def extract_columns_from_sql(sql_content: str) -> List[Tuple[str, str]]:
    """
    Extract column names and types from final SELECT in DBT model.
    
    Returns list of (column_name, inferred_type) tuples.
    """
    # Find the final SELECT statement (usually in the 'final' CTE or main query)
    final_select_pattern = r'final\s+AS\s*\((.*?)\)\s*SELECT\s+(.*?)\s+FROM\s+final'
    match = re.search(final_select_pattern, sql_content, re.DOTALL | re.IGNORECASE)
    
    if not match:
        # Try to find standalone SELECT at end
        final_select_pattern = r'SELECT\s+(.*?)\s+FROM'
        match = re.search(final_select_pattern, sql_content, re.DOTALL | re.IGNORECASE)
    
    if not match:
        return []
    
    select_clause = match.group(1) if len(match.groups()) == 1 else match.group(2)
    
    columns = []
    # Split by comma, handling nested functions
    for line in select_clause.split('\n'):
        line = line.strip()
        if not line or line.startswith('--'):
            continue
        
        # Remove trailing comma
        line = line.rstrip(',')
        
        # Extract column alias
        alias_match = re.search(r'\s+AS\s+(\w+)$', line, re.IGNORECASE)
        if alias_match:
            col_name = alias_match.group(1)
        else:
            # No alias, use column name directly
            col_match = re.search(r'(\w+)$', line)
            if col_match:
                col_name = col_match.group(1)
            else:
                continue
        
        # Infer type from column name
        col_lower = col_name.lower()
        if '_key' in col_lower or '_id' in col_lower:
            col_type = 'key'
        elif '_date' in col_lower or col_lower.startswith('date_'):
            col_type = 'date'
        elif '_timestamp' in col_lower or '_at' in col_lower:
            col_type = 'timestamp'
        elif 'status' in col_lower or 'type' in col_lower or 'category' in col_lower:
            col_type = 'enum'
        elif 'amount' in col_lower or 'price' in col_lower or 'revenue' in col_lower:
            col_type = 'numeric'
        elif 'quantity' in col_lower or 'count' in col_lower:
            col_type = 'integer'
        elif 'pct' in col_lower or 'percent' in col_lower or 'rate' in col_lower:
            col_type = 'percentage'
        elif 'is_' in col_lower or 'has_' in col_lower:
            col_type = 'boolean'
        else:
            col_type = 'string'
        
        columns.append((col_name, col_type))
    
    return columns


def generate_test_config(columns: List[Tuple[str, str]], model_name: str) -> str:
    """Generate YAML test configuration for schema.yml."""
    
    yaml_lines = [
        "models:",
        f"  - name: {model_name}",
        "    description: TODO - Add model description",
        "    columns:"
    ]
    
    for col_name, col_type in columns:
        yaml_lines.append(f"      - name: {col_name}")
        yaml_lines.append(f"        description: TODO - Add column description")
        yaml_lines.append("        tests:")
        
        # Add tests based on column type
        if col_type == 'key':
            yaml_lines.extend([
                "          - unique",
                "          - not_null",
                "          # - relationships:",
                "          #     to: ref('parent_table')",
                "          #     field: parent_key"
            ])
        elif col_type == 'date':
            yaml_lines.extend([
                "          - not_null",
                "          # - assert_no_future_dates  # Uncomment if applicable"
            ])
        elif col_type == 'timestamp':
            yaml_lines.extend([
                "          - not_null"
            ])
        elif col_type == 'enum':
            yaml_lines.extend([
                "          - not_null",
                "          - accepted_values:",
                "              values: ['TODO', 'add', 'valid', 'values']"
            ])
        elif col_type == 'numeric':
            yaml_lines.extend([
                "          - not_null",
                "          - assert_column_value_in_range:",
                "              min_value: 0",
                "              max_value: 1000000  # TODO - Adjust"
            ])
        elif col_type == 'integer':
            yaml_lines.extend([
                "          - not_null",
                "          - assert_column_value_in_range:",
                "              min_value: 0",
                "              max_value: 10000  # TODO - Adjust"
            ])
        elif col_type == 'percentage':
            yaml_lines.extend([
                "          - not_null",
                "          - assert_column_value_in_range:",
                "              min_value: 0",
                "              max_value: 100"
            ])
        elif col_type == 'boolean':
            yaml_lines.extend([
                "          - not_null",
                "          - accepted_values:",
                "              values: [true, false]"
            ])
        else:
            yaml_lines.append("          - not_null")
        
        yaml_lines.append("")  # Blank line between columns
    
    return '\n'.join(yaml_lines)


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    
    model_path = Path(sys.argv[1])
    
    if not model_path.exists():
        print(f"Error: File not found: {model_path}")
        sys.exit(1)
    
    # Read model SQL
    sql_content = model_path.read_text()
    
    # Extract columns
    columns = extract_columns_from_sql(sql_content)
    
    if not columns:
        print("Warning: Could not extract columns from SQL. Using simple extraction...")
        # Fallback: just find all column-like words
        columns = [(word, 'string') for word in re.findall(r'\b([a-z_]+_(?:key|id|date|at))\b', sql_content, re.IGNORECASE)]
    
    if not columns:
        print("Error: No columns found in model")
        sys.exit(1)
    
    # Generate YAML
    model_name = model_path.stem
    yaml_config = generate_test_config(columns, model_name)
    
    # Output
    print("\n" + "="*60)
    print(f"Generated test configuration for: {model_name}")
    print("="*60 + "\n")
    print(yaml_config)
    print("\n" + "="*60)
    print("Copy this configuration to your schema.yml file")
    print("Remember to:")
    print("  1. Add descriptions for model and columns")
    print("  2. Review and adjust test parameters (ranges, values)")
    print("  3. Uncomment and configure relationship tests")
    print("  4. Remove tests that don't apply to your use case")
    print("="*60)


if __name__ == '__main__':
    main()

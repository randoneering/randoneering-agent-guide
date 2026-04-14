#!/usr/bin/env python3
"""
Script to retrieve agent configuration from Snowflake.
Fetches the complete agent specification including instructions and tools.
"""

import argparse
import json
import os
import sys

import requests
import snowflake.connector


def get_agent_config(agent_name: str, database: str, schema: str, connection_name: str) -> dict:
    """
    Retrieve agent configuration via REST API.
    
    Args:
        agent_name: Name of the agent
        database: Database name
        schema: Schema name
        connection_name: Snowflake connection name
        
    Returns:
        Agent configuration as dictionary
    """
    conn = snowflake.connector.connect(connection_name=connection_name)
    
    url = f"https://{conn.host}/api/v2/databases/{database}/schemas/{schema}/agents/{agent_name}"
    
    headers = {
        "Authorization": f'Snowflake Token="{conn.rest.token}"',
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers, verify=False)
    
    if response.status_code != 200:
        raise Exception(f"Failed to retrieve agent config: {response.status_code} - {response.text}")
    
    return response.json()


def main():
    parser = argparse.ArgumentParser(
        description="Retrieve agent configuration from Snowflake",
        epilog="""
Examples:
  %(prog)s --agent-name MY_AGENT
  %(prog)s --agent-name MY_AGENT --output config.json
  %(prog)s --agent-name MY_AGENT --database TEMP --schema MY_SCHEMA --output ./config.json
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--agent-name", required=True, help="Name of the agent")
    parser.add_argument("--database", default="SNOWFLAKE_INTELLIGENCE", help="Database name (default: SNOWFLAKE_INTELLIGENCE)")
    parser.add_argument("--schema", default="AGENTS", help="Schema name (default: AGENTS)")
    parser.add_argument("--connection", default=os.getenv("SNOWFLAKE_CONNECTION_NAME", "snowhouse"), 
                        help="Snowflake connection name")
    parser.add_argument("--output", help="Output file path where agent config will be saved (default: stdout)")
    
    args = parser.parse_args()
    
    try:
        config = get_agent_config(args.agent_name, args.database, args.schema, args.connection)
        
        output = json.dumps(config, indent=2)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"Agent configuration saved to {args.output}", file=sys.stderr)
        else:
            print(output)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test agent with a question and save the response.

This script sends a request to a Snowflake agent and saves the response
to the appropriate location in the agent's workspace.
"""

import argparse
import os
import json
import requests
import snowflake.connector
import urllib3
from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def test_agent(agent_name, question, output_file, 
               database="SNOWFLAKE_INTELLIGENCE", 
               schema="AGENTS",
               connection_name=None,
               enable_research_mode=False,
               current_date_override=None):
    """
    Send a request to an agent and save the response.
    
    Args:
        agent_name: Name of the agent
        question: Question to ask the agent
        output_file: Path to save the response
        database: Database name (default: SNOWFLAKE_INTELLIGENCE)
        schema: Schema name (default: AGENTS)
        connection_name: Snowflake connection name (default: from env or 'snowhouse')
        enable_research_mode: Enable experimental staged reasoning agent flow type (default: False)
        current_date_override: Optional date string timestamp (e.g., "2024-01-01") for CurrentDateOverride experimental flag (default: None)
    """
    if connection_name is None:
        connection_name = os.getenv("SNOWFLAKE_CONNECTION_NAME", "snowhouse")
    
    conn = snowflake.connector.connect(connection_name=connection_name)
    
    try:
        cursor = conn.cursor()
        
        token = conn.rest.token
        host = conn.host
        
        url = f"https://{host}/api/v2/databases/{database}/schemas/{schema}/agents/{agent_name}:run"
        
        headers = {
            "Authorization": f"Snowflake Token=\"{token}\"",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": question
                        }
                    ]
                }
            ]
        }

        # Add experimental flags if any are enabled
        experimental_flags = {}

        if enable_research_mode:
            experimental_flags["ReasoningAgentFlowType"] = "staged"
            print("Research mode enabled: staged reasoning agent flow type")

        if current_date_override:
            experimental_flags["CurrentDateOverride"] = current_date_override
            print(f"Current date override enabled: {current_date_override}")

        if experimental_flags:
            payload["experimental"] = experimental_flags
        
        print(f"Sending request to agent {database}.{schema}.{agent_name}")
        print(f"Question: '{question}'")
        print(f"Streaming response...\n")
        
        response = requests.post(url, headers=headers, json=payload, stream=True, verify=False)
        
        if response.status_code != 200:
            print(f"✗ Error: Status Code {response.status_code}")
            print(f"Response: {response.text}")
            return None
        else:
            final_response = None
            event_type = None
            
            for line in response.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    if decoded.startswith('event: '):
                        event_type = decoded[7:].strip()
                    elif decoded.startswith('data: '):
                        try:
                            data = json.loads(decoded[6:])
                            if event_type == 'response':
                                final_response = data
                        except:
                            pass
            
            if final_response:
                print("\n" + "="*60)
                print("✓ Request completed successfully!")
                print(f"Saving response to: {output_file}")
                
                # Ensure directory exists
                Path(output_file).parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_file, 'w') as f:
                    f.write(json.dumps(final_response, indent=2))
                
                print(f"✓ Response saved to {output_file}")
                print("="*60)
                
                # Extract and display the final text answer
                if 'content' in final_response:
                    for item in final_response['content']:
                        if item.get('type') == 'text':
                            print(f"\nAgent Response:\n{item['text']}\n")
                
                return final_response
            else:
                print("✗ No final response received")
                return None
            
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test agent with a question and save the response",
        epilog="""
Examples:
  %(prog)s --agent-name MY_AGENT --question "What is the weather today?" --output-file ./response.json
  %(prog)s --agent-name MY_AGENT --question "Price for AAPL" --output-file ./results/test1.json --database TEMP --schema MY_SCHEMA
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--agent-name", required=True, help="Name of the agent")
    parser.add_argument("--question", required=True, help="Question to ask the agent")
    parser.add_argument("--output-file", required=True, help="Path to save the response")
    parser.add_argument("--database", default="SNOWFLAKE_INTELLIGENCE", help="Database name (default: SNOWFLAKE_INTELLIGENCE)")
    parser.add_argument("--schema", default="AGENTS", help="Schema name (default: AGENTS)")
    parser.add_argument("--connection", help="Snowflake connection name")
    parser.add_argument("--current-date-override", default=None, help="Override current date (e.g., '2024-01-15') for testing time-sensitive queries (default: None)")
    parser.add_argument("--enable-research-mode", default=False, help="Enable research mode (default: False)")
    
    args = parser.parse_args()
    
    test_agent(args.agent_name, args.question, args.output_file, args.database, args.schema, args.connection, current_date_override=args.current_date_override, enable_research_mode=args.enable_research_mode)

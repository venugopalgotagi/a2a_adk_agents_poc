import glob
import json
import os

import asyncpg
import mcp.types
from mcp.server import FastMCP

from a2a_client.a2a_client import delegate_to_agent

# Initialize FastMCP
mcp = FastMCP("Currency MCP Server 💵",host="localhost",port=8181)

@mcp.tool(description="Scan specialized_agents folder and register agents to DB", name="scan_and_register_agents")
async def scan_and_register_agents() -> str:
    """Scans for agent.json files and registers them in the database."""
    DB_DSN = "postgresql://postgres:postgres@localhost:5432/postgres"
    
    try:
        conn = await asyncpg.connect(DB_DSN)
        try:
            # Drop table to ensure schema change (switching PK to agent_name)
            await conn.execute('DROP TABLE IF EXISTS agents')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS agents (
                    agent_name TEXT PRIMARY KEY,
                    agent_uri TEXT
                )
            ''')

            # Get absolute path to the project root (parent of mcp_server directory)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            specialized_agents_dir = os.path.join(project_root, "specialized_agents")
            print(f"DEBUG: specialized_agents_dir: {specialized_agents_dir}")
            
            agent_files = glob.glob(os.path.join(specialized_agents_dir, "**/agent.json"), recursive=True)
            print(f"DEBUG: Found agent files: {agent_files}")
            registered_count = 0
            
            for agent_file in agent_files:
                try:
                    with open(agent_file, 'r') as f:
                        data = json.load(f)
                        name = data.get('name')
                        url = data.get('url')
                        
                        if name and url:
                            await conn.execute('''
                                INSERT INTO agents (agent_name, agent_uri) 
                                VALUES ($1, $2)
                                ON CONFLICT (agent_name) 
                                DO UPDATE SET agent_uri = $2
                            ''', name, url)
                            registered_count += 1
                except Exception as e:
                    print(f"Error processing {agent_file}: {e}")
                    continue

            return f"Successfully registered {registered_count} agents."
        finally:
            await conn.close()
    except Exception as e:
        return f"Database error: {str(e)}"

@mcp.tool(description="List all registered agents from DB", name="list_registered_agents")
async def list_registered_agents() -> dict:
    """Lists all agents currently registered in the database."""
    DB_DSN = "postgresql://postgres:postgres@localhost:5432/postgres"

    try:
        conn = await asyncpg.connect(DB_DSN)
        try:
            rows = await conn.fetch('SELECT agent_name, agent_uri FROM agents')
            agents = []
            for row in rows:
                agents.append({
                    "name": row['agent_name'],
                    "uri": row['agent_uri']
                })
            return json.dumps(agents)
        finally:
            await conn.close()
    except Exception as e:
        return f"Database error: {str(e)}"


@mcp.tool(description="Delegate Request To Agent", name="agent_executor")
async def agent_executor(content: bytes, agent_url:str, mime_type:str):
    return await delegate_to_agent(content, agent_url, mime_type)

if __name__ == "__main__":
    # Run the server
    mcp.run(transport="sse")
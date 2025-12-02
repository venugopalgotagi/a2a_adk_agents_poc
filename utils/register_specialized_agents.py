from google.adk.tools.mcp_tool.mcp_toolset import McpToolset,SseConnectionParams,McpToolsetConfig

async def tool_call():
    # Define the SSE connection parameters
    sse_params = SseConnectionParams(
        url="http://localhost:8181/sse",  # URL of the MCP server supporting SSE
        timeout=30  # Connection timeout in seconds
    )

    # Define the MCP configuration including the SSE connection parameters
    mcp_config = McpToolsetConfig(
        sse_connection_params=sse_params
    )

    # Create the MCPToolset from the configuration
    mcp_tool_set:McpToolset = McpToolset.from_config(config=mcp_config, config_abs_path="")
    tools = await mcp_tool_set.get_tools()

    tool = [tool for tool in tools if tool.name == 'scan_and_register_agents'][0]
    try:
        agents = await tool.run_async(args={}, tool_context=None)
        print(agents)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(tool_call())

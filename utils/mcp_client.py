from google.adk.tools.mcp_tool import MCPToolset
from mcp.client.stdio import StdioServerParameters


async def setup_mcp_client():
    connection_params = StdioServerParameters(
        command="python", args=["-m", "mcp.server.stdio"]
    )
    tools, exit_stack = await MCPToolset.from_server(
        connection_params=connection_params
    )
    return tools, exit_stack

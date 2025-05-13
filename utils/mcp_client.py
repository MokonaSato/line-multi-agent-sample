from google.adk.tools.mcp_tool import MCPToolset
from mcp.client.stdio import StdioServerParameters


async def setup_mcp_client():
    try:
        connection_params = StdioServerParameters(
            command="python", args=["-m", "mcp.server.stdio"]
        )
        tools, exit_stack = await MCPToolset.from_server(
            connection_params=connection_params
        )
        return tools, exit_stack
    except Exception as e:
        import logging

        logging.getLogger("main").error(
            f"MCPクライアント初期化エラー: {str(e)}"
        )

        # エラー時に代替のスタブを返す
        class DummyExitStack:
            def close(self):
                pass

        return None, DummyExitStack()

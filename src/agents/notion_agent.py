# ./adk_agent_samples/mcp_agent/agent.py
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    StdioServerParameters,
)


async def create_agent():
    """Gets tools from MCP Server."""
    tools, exit_stack = await MCPToolset.from_server(
        connection_params=StdioServerParameters(
            command="npx",
            args=["-y", "@notionhq/notion-mcp-server"],
            env={
                "OPENAPI_MCP_HEADERS": (
                    '{"Authorization": "Bearer '
                    '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", '
                    '"Notion-Version": "2022-06-28" }'
                )
            },
        )
    )

    notion_agent = LlmAgent(
        model="gemini-2.0-flash",
        name="notion_agent",
        instruction=(
            "Notionのページやデータベースにアクセスして情報を取得したり、"
            "書き込んだり、削除したりすることができるエージェントです。"
        ),
        tools=tools,
    )
    return notion_agent, exit_stack


notion_agent = create_agent()

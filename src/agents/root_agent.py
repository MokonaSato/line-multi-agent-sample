# ./adk_agent_samples/mcp_agent/agent.py
import os

from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools import agent_tool
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    StdioServerParameters,
)

from src.agents.calc_agent import calculator_agent
from src.agents.google_search_agent import google_search_agent
from src.utils.file_utils import read_prompt_file

# プロンプトファイルのパスを指定
prompt_file_path = os.path.join(
    os.path.dirname(__file__), "prompts", "root.txt"
)
root_prompt = read_prompt_file(prompt_file_path)


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

    tools.append(agent_tool.AgentTool(agent=google_search_agent))

    notion_agent = LlmAgent(
        model="gemini-2.0-flash",
        name="notion_agent",
        instruction=root_prompt,
        tools=tools,
        sub_agents=[
            calculator_agent,
        ],
    )
    return notion_agent, exit_stack


notion_agent = create_agent()

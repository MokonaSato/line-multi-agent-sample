# ./adk_agent_samples/mcp_agent/agent.py
import os
from contextlib import AsyncExitStack

from google.adk.agents import Agent
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools import agent_tool
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    StdioServerParameters,
)

# from config import NOTION_TOKEN
from src.agents.calc_agent import (
    add_numbers,
    divide_numbers,
    multiply_numbers,
    subtract_numbers,
)
from src.agents.google_search_agent import google_search_agent
from src.utils.file_utils import read_prompt_file

# プロンプトファイルのパスを指定
prompt_file_path = os.path.join(
    os.path.dirname(__file__), "prompts", "root.txt"
)
root_prompt = read_prompt_file(prompt_file_path)

# グローバル変数
_root_agent = None
_exit_stack = AsyncExitStack()


async def create_agent():
    """Gets tools from MCP Server."""
    global _root_agent, _exit_stack

    # すでに作成済みの場合はそれを返す
    if _root_agent is not None:
        return _root_agent, _exit_stack

    tools, exit_stack = await MCPToolset.from_server(
        connection_params=StdioServerParameters(
            command="npx",
            args=[
                "-y",
                "@notionhq/notion-mcp-server",
                "--mode",
                "mcp",
                "--stdio",
            ],
            env={
                "NOTION_TOKEN": "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",
                "Notion-Version": "2022-06-28",
            },
        )
    )

    # exit_stackをグローバルなものにマージする
    await _exit_stack.enter_async_context(exit_stack)

    tools.append(agent_tool.AgentTool(agent=google_search_agent))

    # 毎回新しいcalculator_agentを作成
    calc_agent = Agent(
        name="calculator_agent",
        model="gemini-2.0-flash",
        description="2つの数字を使って四則演算（足し算、引き算、掛け算、割り算）ができる計算エージェント",
        instruction="計算をサポートする",
        tools=[
            add_numbers,
            subtract_numbers,
            multiply_numbers,
            divide_numbers,
        ],
    )

    _root_agent = LlmAgent(
        model="gemini-2.0-flash",
        name="root_agent",
        instruction=root_prompt,
        tools=tools,
        sub_agents=[
            calc_agent,
        ],
    )
    return _root_agent, _exit_stack


root_agent = create_agent()

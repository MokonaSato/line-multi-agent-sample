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

from config import NOTION_TOKEN

# from config import NOTION_TOKEN
from src.agents.calc_agent import (
    add_numbers,
    divide_numbers,
    multiply_numbers,
    subtract_numbers,
)
from src.agents.google_search_agent import google_search_agent
from src.utils.file_utils import read_prompt_file
from src.utils.logger import setup_logger

# ロガーを設定
logger = setup_logger("root_agent")

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
        logger.info("Returning existing root agent")
        return _root_agent, _exit_stack

    logger.info("Creating new root agent with local Notion MCP Server")

    try:
        # ローカルのNotion MCP Serverに接続
        tools, exit_stack = await MCPToolset.from_server(
            connection_params=StdioServerParameters(
                command="npx",
                args=["-y", "@notionhq/notion-mcp-server"],
                env={
                    "OPENAPI_MCP_HEADERS": (
                        f'{{"Authorization": "Bearer {NOTION_TOKEN}", '
                        f'"Notion-Version": "2022-06-28" }}'
                    )
                },
            )
        )

        # exit_stackをグローバルなものにマージする
        await _exit_stack.enter_async_context(exit_stack)
        logger.info("Successfully connected to local Notion MCP Server")

    except Exception as e:
        logger.error(f"Failed to connect to Notion MCP Server: {e}")
        # MCPサーバーへの接続に失敗した場合は空のツールリストで続行
        tools = []

    # Google検索エージェントを追加
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

    logger.info("Root agent created successfully")
    return _root_agent, _exit_stack

# ./adk_agent_samples/mcp_agent/agent.py
import os
from contextlib import AsyncExitStack

from google.adk.agents import Agent
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools import agent_tool

# from config import NOTION_TOKEN
from src.agents.google_search_agent import google_search_agent
from src.agents.tools.calculator_tools import calculator_tools_list
from src.agents.tools.notion_tools import notion_tools_list
from src.agents.tools.web_tools import fetch_web_content
from src.utils.file_utils import read_prompt_file
from src.utils.logger import setup_logger

# ロガーを設定
logger = setup_logger("root_agent")

# プロンプトファイルのパスを指定
root_prompt_file_path = os.path.join(
    os.path.dirname(__file__), "prompts", "root.txt"
)
root_prompt = read_prompt_file(root_prompt_file_path)

calc_prompt_file_path = os.path.join(
    os.path.dirname(__file__), "prompts", "calculator.txt"
)
calc_prompt = read_prompt_file(calc_prompt_file_path)

notion_prompt_file_path = os.path.join(
    os.path.dirname(__file__), "prompts", "notion.txt"
)
notion_prompt = read_prompt_file(notion_prompt_file_path)

extraction_prompt_file_path = os.path.join(
    os.path.dirname(__file__), "prompts", "content_extraction.txt"
)
extraction_prompt = read_prompt_file(extraction_prompt_file_path)

vision_prompt_file_path = os.path.join(
    os.path.dirname(__file__), "prompts", "vision.txt"
)
vision_prompt = read_prompt_file(vision_prompt_file_path)


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

    # 毎回新しいcalculator_agentを作成
    calc_agent = Agent(
        name="calculator_agent",
        model="gemini-2.5-flash-preview-05-20",
        description="2つの数字を使って四則演算（足し算、引き算、掛け算、割り算）ができる計算エージェント",
        instruction=calc_prompt,
        tools=calculator_tools_list,
    )

    notion_agent = Agent(
        name="notion_agent",
        model="gemini-2.5-flash-preview-05-20",
        description=(
            "NotionワークスペースのデータとやりとりするエージェントFです。"
            "ページやデータベースの検索、作成、更新、およびコンテンツの管理を行います。"
            "Notion関連のリクエストに対応します。"
        ),
        instruction=notion_prompt,
        tools=notion_tools_list,
    )

    content_extraction_agent = Agent(
        name="content_extraction_agent",
        model="gemini-2.5-flash-preview-05-20",
        description=(
            "Webページのコンテンツを構造化して抽出するエージェント。"
            "レシピ、記事、製品情報など様々な種類のコンテンツを分析できます。"
        ),
        instruction=extraction_prompt,
        tools=[],
    )

    vision_agent = Agent(
        name="vision_agent",
        model="gemini-2.5-flash-preview-05-20",
        description="画像を分析して詳細な情報を抽出するエージェント。料理、製品、シーン、テキスト、図表などを認識できます。",
        instruction=vision_prompt,
        tools=[],
    )

    _root_agent = LlmAgent(
        model="gemini-2.5-flash-preview-05-20",
        name="root_agent",
        instruction=root_prompt,
        tools=[
            agent_tool.AgentTool(agent=google_search_agent),
            fetch_web_content,
        ],
        sub_agents=[
            calc_agent,
            notion_agent,
            content_extraction_agent,
            vision_agent,
        ],
    )

    logger.info("Root agent created successfully")
    return _root_agent, _exit_stack

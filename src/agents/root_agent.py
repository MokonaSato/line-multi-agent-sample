# src/agents/sequential_recipe_agent.py
import os
from contextlib import AsyncExitStack

from google.adk.agents import Agent, SequentialAgent
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools import agent_tool

from src.agents import google_search_agent
from src.agents.tools.calculator_tools import calculator_tools_list
from src.agents.tools.notion_tools import notion_tools_list
from src.agents.tools.web_tools import fetch_web_content
from src.utils.file_utils import read_prompt_file
from src.utils.logger import setup_logger

# ロガーを設定
logger = setup_logger("sequential_recipe_agent")

extraction_prompt_file_path = os.path.join(
    os.path.dirname(__file__), "prompts", "content_extraction.txt"
)
extraction_prompt = read_prompt_file(extraction_prompt_file_path)

data_transformation_prompt_file_path = os.path.join(
    os.path.dirname(__file__), "prompts", "data_transformation.txt"
)
data_transformation_prompt = read_prompt_file(
    data_transformation_prompt_file_path
)

notion_prompt_file_path = os.path.join(
    os.path.dirname(__file__), "prompts", "notion.txt"
)
notion_prompt = read_prompt_file(notion_prompt_file_path)

calc_prompt_file_path = os.path.join(
    os.path.dirname(__file__), "prompts", "calculator.txt"
)
calc_prompt = read_prompt_file(calc_prompt_file_path)

root_prompt_file_path = os.path.join(
    os.path.dirname(__file__), "prompts", "root.txt"
)
root_prompt = read_prompt_file(root_prompt_file_path)


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

    # --- 1. Define Sub-Agents for Each Pipeline Stage ---
    # Content Extraction Agent
    # URLからレシピ情報を抽出する
    content_extraction_agent = LlmAgent(
        name="ContentExtractionAgent",
        model="gemini-2.5-flash-preview-05-20",
        instruction=extraction_prompt,
        description="URLからレシピ情報を抽出します。",
        tools=[fetch_web_content],
        output_key="extracted_recipe_data",
    )

    # Data Transformation Agent
    # 抽出されたデータをNotion DB形式に変換する
    data_transformation_agent = LlmAgent(
        name="DataTransformationAgent",
        model="gemini-2.5-flash-preview-05-20",
        instruction=data_transformation_prompt,
        description="抽出されたレシピデータをNotion DB形式に変換します。",
        output_key="notion_formatted_data",
    )

    # Notion Registration Agent
    # 変換されたデータをNotion DBに登録する
    notion_registration_agent = LlmAgent(
        name="NotionRegistrationAgent",
        model="gemini-2.5-flash-preview-05-20",
        instruction=notion_prompt,
        description="変換されたデータをNotion データベースに登録します。",
        tools=notion_tools_list,
        output_key="registration_result",
    )

    # --- 2. Create the SequentialAgent ---
    # レシピ抽出からNotion登録までのパイプラインを実行する
    recipe_extraction_pipeline = SequentialAgent(
        name="RecipeExtractionPipeline",
        sub_agents=[
            content_extraction_agent,
            data_transformation_agent,
            notion_registration_agent,
        ],
        description="URLからレシピを抽出し、Notion データベースに登録するパイプラインを実行します。",
        # エージェントは提供された順序で実行される
    )

    # --- 3. Root Agent Wrapper ---
    # ユーザーからのリクエストを受け取り、パイプラインを実行する
    recipe_workflow_agent = LlmAgent(
        name="RecipeWorkflowAgent",
        model="gemini-2.5-flash-preview-05-20",
        instruction="""""",
        description="レシピ抽出・登録ワークフローの全体を管理します。",
        sub_agents=[recipe_extraction_pipeline],
    )
    # --- 既存のエージェント ---
    # 計算エージェント
    calc_agent = Agent(
        name="calculator_agent",
        model="gemini-2.5-flash-preview-05-20",
        description="2つの数字を使って四則演算（足し算、引き算、掛け算、割り算）ができる計算エージェント",
        instruction=calc_prompt,
        tools=calculator_tools_list,
    )

    _root_agent = LlmAgent(
        model="gemini-2.5-flash-preview-05-20",
        name="root_agent",
        instruction=root_prompt,
        tools=[
            agent_tool.AgentTool(agent=google_search_agent),
        ],
        sub_agents=[
            calc_agent,
            recipe_workflow_agent,
        ],
    )

    logger.info("Root agent created successfully")
    return _root_agent, _exit_stack

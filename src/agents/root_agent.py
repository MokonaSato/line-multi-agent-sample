"""マルチエージェントシステムのルートエージェント定義モジュール

このモジュールは、以下のコンポーネントを含む階層的なエージェントシステムを定義します：
- ルートエージェント: すべてのサブエージェントを管理・調整する
- 専用サブエージェント: 計算、レシピワークフロー、Notion操作など特定の機能を担当する
- 順次実行エージェント: 複数のステップからなるワークフローを管理する
"""

import os
from contextlib import AsyncExitStack
from typing import Dict, List, Tuple

from google.adk.agents import Agent, SequentialAgent
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools import agent_tool, google_search

from src.agents.tools.calculator_tools import calculator_tools_list
from src.agents.tools.notion_tools import notion_tools_list
from src.agents.tools.web_tools import fetch_web_content
from src.utils.file_utils import read_prompt_file
from src.utils.logger import setup_logger

# ロガーを設定
logger = setup_logger("root_agent")

# グローバル変数
_root_agent = None
_exit_stack = AsyncExitStack()


def _load_all_prompts() -> Dict[str, str]:
    """すべてのプロンプトファイルを一括で読み込む"""
    prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
    prompt_files = {
        "recipe_extraction": "content_extraction_for_recipe.txt",
        "data_transformation": "data_transformation.txt",
        "recipe_notion": "notion_for_recipe.txt",
        "recipe_workflow": "recipe_workflow.txt",
        "calculator": "calculator.txt",
        "notion": "notion.txt",
        "root": "root.txt",
    }

    prompts = {}
    for key, filename in prompt_files.items():
        file_path = os.path.join(prompts_dir, filename)
        try:
            prompts[key] = read_prompt_file(file_path)
        except Exception as e:
            logger.error(
                f"プロンプトファイル '{filename}' の読み込みに失敗: {e}"
            )
            prompts[key] = f"Error loading prompt: {str(e)}"

    return prompts


def _create_recipe_pipeline(prompts: Dict[str, str]) -> SequentialAgent:
    """レシピ抽出パイプラインを作成する"""
    # Content Extraction Agent - URLからレシピ情報を抽出
    content_extraction_agent = LlmAgent(
        name="ContentExtractionAgent",
        model="gemini-2.5-flash-preview-05-20",
        instruction=prompts["recipe_extraction"],
        description="URLからレシピ情報を抽出します。",
        tools=[fetch_web_content],
        output_key="extracted_recipe_data",
    )

    # Data Transformation Agent - 抽出データをNotion DB形式に変換
    data_transformation_agent = LlmAgent(
        name="DataTransformationAgent",
        model="gemini-2.5-flash-preview-05-20",
        instruction=prompts["data_transformation"],
        description="抽出されたレシピデータをNotion DB形式に変換します。",
        tools=[],
        output_key="notion_formatted_data",
    )

    # Notion Registration Agent - 変換データをNotion DBに登録
    notion_registration_agent = LlmAgent(
        name="NotionRegistrationAgent",
        model="gemini-2.5-flash-preview-05-20",
        instruction=prompts["recipe_notion"],
        description="変換されたデータをNotion データベースに登録します。",
        tools=notion_tools_list,
        output_key="registration_result",
    )

    # レシピ処理の全工程を順番に実行するSequentialAgent
    return SequentialAgent(
        name="RecipeExtractionPipeline",
        sub_agents=[
            content_extraction_agent,
            data_transformation_agent,
            notion_registration_agent,
        ],
        description="URLからレシピを抽出し、Notion データベースに登録するパイプラインを実行します。",
    )


def _create_standard_agents(prompts: Dict[str, str]) -> List[Agent]:
    """標準的なサブエージェントを作成する"""
    # 計算エージェント
    calc_agent = Agent(
        name="calculator_agent",
        model="gemini-2.5-flash-preview-05-20",
        description="2つの数字を使って四則演算（足し算、引き算、掛け算、割り算）ができる計算エージェント",
        instruction=prompts["calculator"],
        tools=calculator_tools_list,
    )

    # レシピワークフローエージェント - レシピパイプラインのラッパー
    recipe_pipeline = _create_recipe_pipeline(prompts)
    recipe_workflow_agent = LlmAgent(
        name="RecipeWorkflowAgent",
        model="gemini-2.5-flash-preview-05-20",
        instruction=prompts["recipe_workflow"],
        description="レシピ抽出・登録ワークフローの全体を管理します。",
        sub_agents=[recipe_pipeline],
    )

    # Google検索エージェント
    google_search_agent = Agent(
        name="google_search_agent",
        model="gemini-2.0-flash",
        description="Google検索を使って質問に答えるエージェントです。",
        instruction="インターネット検索であなたの質問に答えます。何でも聞いてください！",
        tools=[google_search],
    )

    # Notionエージェント
    notion_agent = LlmAgent(
        name="NotionRegistrationAgent",
        model="gemini-2.5-flash-preview-05-20",
        instruction=prompts["notion"],
        description=(
            "Notionワークスペースの汎用的な操作を行うエージェントです。"
            "ページやデータベースの検索、作成、更新、およびコンテンツの管理を行います。"
            "レシピ登録以外のNotion関連のリクエストに対応します。"
        ),
        tools=notion_tools_list,
        output_key="registration_result",
    )

    return {
        "calc_agent": calc_agent,
        "recipe_workflow_agent": recipe_workflow_agent,
        "google_search_agent": google_search_agent,
        "notion_agent": notion_agent,
    }


async def create_agent() -> Tuple[LlmAgent, AsyncExitStack]:
    """ルートエージェントとすべてのサブエージェントを作成する

    Returns:
        Tuple[LlmAgent, AsyncExitStack]: ルートエージェントとリソース管理用のexitスタック
    """
    global _root_agent, _exit_stack

    # すでに作成済みの場合はそれを返す
    if _root_agent is not None:
        logger.info("既存のルートエージェントを返します")
        return _root_agent, _exit_stack

    try:
        logger.info("新しいルートエージェントを作成します")

        # 全プロンプトを読み込む
        prompts = _load_all_prompts()

        # 標準エージェントを作成
        agents = _create_standard_agents(prompts)

        # ルートエージェントを作成
        _root_agent = LlmAgent(
            model="gemini-2.5-flash-preview-05-20",
            name="root_agent",
            instruction=prompts["root"],
            tools=[
                agent_tool.AgentTool(agent=agents["google_search_agent"]),
            ],
            sub_agents=[
                agents["calc_agent"],
                agents["recipe_workflow_agent"],
                agents["notion_agent"],
            ],
        )

        logger.info("ルートエージェントの作成に成功しました")

    except Exception as e:
        logger.error(f"ルートエージェント作成中にエラーが発生: {e}")
        raise

    return _root_agent, _exit_stack

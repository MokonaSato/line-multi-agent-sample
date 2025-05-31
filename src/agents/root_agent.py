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
from src.agents.tools.notion import notion_tools_list
from src.agents.tools.web_tools import fetch_web_content
from src.utils.file_utils import read_prompt_file
from src.utils.logger import setup_logger

# ロガーを設定
logger = setup_logger("root_agent")

# グローバル変数
_root_agent = None
_exit_stack = AsyncExitStack()


def _load_all_prompts() -> Dict[str, str]:
    """すべてのプロンプトファイルを一括で読み込む

    既存のプロンプト構造との互換性を保ちながら、新しいプロンプト管理システムも使用できるようにする
    """
    from src.utils.prompt_manager import PromptManager

    # 新しいプロンプト管理システムを初期化
    try:
        manager = PromptManager()

        # 既存のキーと新しいパスのマッピング
        prompt_mapping = {
            "recipe_extraction": "workflows.recipe.url_extraction.extraction",
            "data_transformation": "workflows.recipe.url_extraction.transformation",
            "recipe_notion": "workflows.recipe.url_extraction.notion",
            "recipe_workflow": "workflows.recipe.url_extraction.workflow",
            "image_analysis": "workflows.recipe.image_extraction.analysis",
            "image_data_enhancement": "workflows.recipe.image_extraction.enhancement",
            "image_notion": "workflows.recipe.image_extraction.notion",
            "image_workflow": "workflows.recipe.image_extraction.workflow",
            "calculator": "agents.calculator.main",
            "notion": "agents.notion.main",
            "root": "agents.root.main",
            "vision": "agents.vision.main",
        }

        # 一旦従来の方法をフォールバックとして残す
        prompts = {}

        # 新しいシステムからプロンプトを取得
        for key, prompt_path in prompt_mapping.items():
            try:
                prompts[key] = manager.get_prompt(prompt_path)
                logger.info(
                    f"新しい管理システムから '{key}' プロンプトを読み込みました"
                )
            except Exception as e:
                logger.warning(
                    f"新システムからの '{key}' プロンプト読み込みに失敗: {e}"
                )
                # 従来の方法で読み込む
                old_style_load(prompts, key)

        return prompts

    except Exception as e:
        logger.error(f"新しいプロンプト管理システムの初期化に失敗: {e}")
        logger.info("従来のプロンプト読み込み方法にフォールバック")
        return _load_prompts_legacy()


def old_style_load(prompts_dict: Dict[str, str], key: str) -> None:
    """従来の方法でプロンプトを読み込む（フォールバック用）"""
    prompt_files = {
        "recipe_extraction": "url_recipe_workflow/content_extraction.txt",
        "data_transformation": "url_recipe_workflow/data_transformation.txt",
        "recipe_notion": "url_recipe_workflow/notion.txt",
        "recipe_workflow": "url_recipe_workflow/recipe_workflow.txt",
        "image_analysis": "image_recipe_workflow/image_analysis.txt",
        "image_data_enhancement": "image_recipe_workflow/image_data_enhancement.txt",
        "image_notion": "image_recipe_workflow/notion.txt",
        "image_workflow": "image_recipe_workflow/image_workflow.txt",
        "calculator": "calculator.txt",
        "notion": "notion.txt",
        "root": "root.txt",
        "vision": "vision.txt",
    }

    if key in prompt_files:
        prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
        file_path = os.path.join(prompts_dir, prompt_files[key])
        try:
            prompts_dict[key] = read_prompt_file(file_path)
            logger.info(f"従来の方法で '{key}' プロンプトを読み込みました")
        except Exception as e:
            logger.error(
                f"プロンプトファイル '{prompt_files[key]}' の読み込みに失敗: {e}"
            )
            if key == "vision":
                prompts_dict[
                    key
                ] = """あなたは画像を分析する専門家です。
提供された画像の内容を詳細に説明し、関連情報を抽出してください。
画像のタイプ（料理、製品、文書など）を特定し、適切な情報を抽出してください。"""
            else:
                prompts_dict[key] = f"Error loading prompt: {str(e)}"


def _load_prompts_legacy() -> Dict[str, str]:
    """従来の方法ですべてのプロンプトファイルを一括で読み込む（フォールバック用）"""
    prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
    prompt_files = {
        "recipe_extraction": "url_recipe_workflow/content_extraction.txt",
        "data_transformation": "url_recipe_workflow/data_transformation.txt",
        "recipe_notion": "url_recipe_workflow/notion.txt",
        "recipe_workflow": "url_recipe_workflow/recipe_workflow.txt",
        "image_analysis": "image_recipe_workflow/image_analysis.txt",
        "image_data_enhancement": "image_recipe_workflow/image_data_enhancement.txt",
        "image_notion": "image_recipe_workflow/notion.txt",
        "image_workflow": "image_recipe_workflow/image_workflow.txt",
        "calculator": "calculator.txt",
        "notion": "notion.txt",
        "root": "root.txt",
        "vision": "vision.txt",
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
            if key == "vision":
                prompts[
                    key
                ] = """あなたは画像を分析する専門家です。
提供された画像の内容を詳細に説明し、関連情報を抽出してください。
画像のタイプ（料理、製品、文書など）を特定し、適切な情報を抽出してください。"""
            else:
                prompts[key] = f"Error loading prompt: {str(e)}"

    return prompts


def _create_url_recipe_pipeline(prompts: Dict[str, str]) -> SequentialAgent:
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


def _create_image_recipe_pipeline(prompts: Dict[str, str]) -> SequentialAgent:
    """画像レシピ抽出エージェントを作成"""

    logger.info("Creating image recipe extraction agents")

    # --- 1. Image Analysis Agent ---
    image_analysis_agent = LlmAgent(
        name="ImageAnalysisAgent",
        model="gemini-2.5-flash-preview-05-20",
        instruction=prompts["image_analysis"],
        description="画像を分析してレシピ情報を抽出します。",
        tools=[],  # Geminiの視覚認識機能を使用
        output_key="extracted_image_data",
    )

    # --- 2. Image Data Enhancement Agent ---
    # プロンプトを動的に生成してコンテキスト変数を正しく設定
    enhancement_instruction = prompts["image_data_enhancement"].replace(
        "{extracted_recipe_data}", "{extracted_image_data}"
    )

    image_data_enhancement_agent = LlmAgent(
        name="ImageDataEnhancementAgent",
        model="gemini-2.5-flash-preview-05-20",
        instruction=enhancement_instruction,
        description="抽出された画像データを実用的なレシピに強化します。",
        tools=[],  # データ処理のみ
        output_key="enhanced_recipe_data",
    )

    # --- 3. Recipe Notion Agent (既存のものを再利用) ---
    recipe_notion_agent = LlmAgent(
        name="RecipeNotionAgent",
        model="gemini-2.5-flash-preview-05-20",
        instruction=prompts["image_notion"],  # 既存のレシピ登録専用プロンプト
        description="強化されたレシピデータを料理レシピデータベースに登録します。",
        tools=notion_tools_list,
        output_key="registration_result",
    )

    # --- 4. Sequential Pipeline ---
    return SequentialAgent(
        name="ImageRecipeExtractionPipeline",
        sub_agents=[
            image_analysis_agent,
            image_data_enhancement_agent,
            recipe_notion_agent,
        ],
        description="画像からレシピを抽出し、Notion レシピデータベースに登録するパイプラインを実行します。",
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
    url_recipe_pipeline = _create_url_recipe_pipeline(prompts)
    url_recipe_workflow_agent = LlmAgent(
        name="RecipeWorkflowAgent",
        model="gemini-2.5-flash-preview-05-20",
        instruction=prompts["recipe_workflow"],
        description="URLからのレシピ抽出・登録ワークフローの全体を管理します。",
        sub_agents=[url_recipe_pipeline],
    )

    image_recipe_pipeline = _create_image_recipe_pipeline(prompts)
    image_recipe_workflow_agent = LlmAgent(
        name="ImageRecipeWorkflowAgent",
        model="gemini-2.5-flash-preview-05-20",
        instruction=prompts["image_workflow"],
        description="画像レシピ抽出・登録ワークフローの全体を管理します。",
        sub_agents=[image_recipe_pipeline],
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

    # 汎用画像認識エージェント（レシピ以外の画像分析用）
    vision_agent = LlmAgent(
        name="vision_agent",
        model="gemini-2.5-flash-preview-05-20",
        instruction=prompts["vision"],
        description=(
            "画像を分析して詳細な情報を抽出します。料理写真、製品画像、"
            "スクリーンショット、図表などから視覚的要素を認識し、"
            "詳細な説明と関連データを提供します。"
        ),
        tools=[],  # 画像分析のみ
    )

    return {
        "calc_agent": calc_agent,
        "url_recipe_workflow_agent": url_recipe_workflow_agent,
        "image_recipe_workflow_agent": image_recipe_workflow_agent,
        "google_search_agent": google_search_agent,
        "notion_agent": notion_agent,
        "vision_agent": vision_agent,
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
                agents["url_recipe_workflow_agent"],
                agents["image_recipe_workflow_agent"],
                agents["notion_agent"],
                agents["vision_agent"],
            ],
        )

        logger.info("ルートエージェントの作成に成功しました")

    except Exception as e:
        logger.error(f"ルートエージェント作成中にエラーが発生: {e}")
        raise

    return _root_agent, _exit_stack

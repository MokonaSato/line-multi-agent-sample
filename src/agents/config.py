# src/agents/config.py
"""エージェントシステムの設定モジュール

このモジュールは、エージェントの設定（モデル、ツール、説明文など）を定義します。
設定値を一元管理することで、コードの重複を減らし保守性を向上させます。
"""

# デフォルトのLLMモデル
DEFAULT_MODEL = "gemini-2.5-flash-preview-05-20"
SEARCH_MODEL = "gemini-2.0-flash"  # 検索用の軽量モデル

# 共通の設定値
RECIPE_DATABASE_ID = "recipe-database-id"
REQUIRED_TOOLS = "notion_create_recipe_page"
ERROR_PREVENTION = (
    "missing required parametersエラーを防ぐため、内部で専用ツールを使用"
)

# エージェント設定
AGENT_CONFIG = {
    # ルートエージェント設定
    "root": {
        "name": "root_agent",
        "model": DEFAULT_MODEL,
        "prompt_key": "root",
        "description": "複数のサブエージェントを管理・調整するルートエージェント",
        # 変数を明示的に追加
        "variables": {
            "recipe_database_id": RECIPE_DATABASE_ID,
            "required_tools": REQUIRED_TOOLS,
            "error_prevention": ERROR_PREVENTION,
        },
    },
    # 計算エージェント設定
    "calculator": {
        "name": "calculator_agent",
        "model": DEFAULT_MODEL,
        "prompt_key": "calculator",
        "description": "2つの数字を使って四則演算（足し算、引き算、掛け算、割り算）ができる計算エージェント",
    },
    # URLレシピ関連エージェント
    "url_recipe": {
        "extraction_agent": {
            "name": "ContentExtractionAgent",
            "model": DEFAULT_MODEL,
            "prompt_key": "recipe_extraction",
            "description": "URLからレシピ情報を抽出します。",
            "output_key": "extracted_recipe_data",
            "variables": {
                "recipe_database_id": RECIPE_DATABASE_ID,
            },
        },
        "transformation_agent": {
            "name": "DataTransformationAgent",
            "model": DEFAULT_MODEL,
            "prompt_key": "data_transformation",
            "description": "抽出されたレシピデータをNotion DB形式に変換します。",
            "output_key": "notion_formatted_data",
            "variables": {
                "recipe_database_id": RECIPE_DATABASE_ID,
            },
        },
        "registration_agent": {
            "name": "NotionRegistrationAgent",
            "model": DEFAULT_MODEL,
            "prompt_key": "recipe_notion",
            "description": (
                "変換されたデータをNotion データベースに登録します。"
                f"必ず{REQUIRED_TOOLS}ツールを使用し、"
                "missing required parametersエラーを防ぎます。"
            ),
            "output_key": "registration_result",
            "variables": {
                "recipe_database_id": RECIPE_DATABASE_ID,
                "required_tools": REQUIRED_TOOLS,
            },
        },
        "workflow_agent": {
            "name": "RecipeWorkflowAgent",
            "model": DEFAULT_MODEL,
            "prompt_key": "recipe_workflow",
            "description": "URLからのレシピ抽出・登録ワークフローの全体を管理します。",
            "variables": {
                "recipe_database_id": RECIPE_DATABASE_ID,
                "required_tools": REQUIRED_TOOLS,
            },
        },
        "pipeline": {
            "name": "RecipeExtractionPipeline",
            "description": "URLからレシピを抽出し、Notion データベースに登録するパイプラインを実行します。",
            "required_tools": REQUIRED_TOOLS,
            "error_prevention": ERROR_PREVENTION,
            "variables": {
                "recipe_database_id": RECIPE_DATABASE_ID,
            },
        },
    },
    # 画像レシピ関連エージェント
    "image_recipe": {
        "analysis_agent": {
            "name": "ImageAnalysisAgent",
            "model": DEFAULT_MODEL,
            "prompt_key": "image_analysis",
            "description": "画像を分析してレシピ情報を抽出します。",
            "output_key": "extracted_image_data",
        },
        "enhancement_agent": {
            "name": "ImageDataEnhancementAgent",
            "model": DEFAULT_MODEL,
            "prompt_key": "image_data_enhancement",
            "description": "抽出された画像データを実用的なレシピに強化します。",
            "output_key": "enhanced_recipe_data",
        },
        "registration_agent": {
            "name": "RecipeNotionAgent",
            "model": DEFAULT_MODEL,
            "prompt_key": "image_notion",
            "description": (
                "強化されたレシピデータを料理レシピデータベースに登録します。"
                f"必ず{REQUIRED_TOOLS}ツールを使用し、"
                "missing required parametersエラーを防ぎます。"
            ),
            "output_key": "registration_result",
            "variables": {
                "recipe_database_id": RECIPE_DATABASE_ID,
                "required_tools": REQUIRED_TOOLS,
            },
        },
        "workflow_agent": {
            "name": "ImageRecipeWorkflowAgent",
            "model": DEFAULT_MODEL,
            "prompt_key": "image_workflow",
            "description": "画像レシピ抽出・登録ワークフローの全体を管理します。",
            "variables": {
                "recipe_database_id": RECIPE_DATABASE_ID,
                "required_tools": REQUIRED_TOOLS,
            },
        },
        "pipeline": {
            "name": "ImageRecipeExtractionPipeline",
            "description": "画像からレシピを抽出し、Notion レシピデータベースに登録するパイプラインを実行します。",
            "required_tools": REQUIRED_TOOLS,
            "error_prevention": ERROR_PREVENTION,
            "variables": {
                "recipe_database_id": RECIPE_DATABASE_ID,
            },
        },
    },
    # Google検索エージェント
    "google_search": {
        "name": "google_search_agent",
        "model": SEARCH_MODEL,
        "description": "Google検索を使って質問に答えるエージェントです。",
        "instruction": "インターネット検索であなたの質問に答えます。何でも聞いてください！",
    },
    # Notionエージェント
    "notion": {
        "name": "NotionRegistrationAgent",
        "model": DEFAULT_MODEL,
        "prompt_key": "notion",
        "description": (
            "Notionワークスペースの包括的な操作を行うエージェントです。"
            "レシピの登録、検索、閲覧、管理を含む全般的なNotion関連タスクに対応します。"
            "レシピデータベースの操作（登録・検索・一覧表示）、"
            "ページやデータベースの検索・作成・更新、およびコンテンツの管理を行います。"
            f"レシピ登録の場合は必ず{REQUIRED_TOOLS}ツールを使用し、"
            "レシピ検索の場合は適切な検索ツールを使用します。"
        ),
        "output_key": "registration_result",
        "variables": {
            "recipe_database_id": RECIPE_DATABASE_ID,
            "required_tools": REQUIRED_TOOLS,
        },
    },
    # 汎用画像認識エージェント
    "vision": {
        "name": "vision_agent",
        "model": DEFAULT_MODEL,
        "prompt_key": "vision",
        "description": (
            "画像を分析して詳細な情報を抽出します。料理写真、製品画像、"
            "スクリーンショット、図表などから視覚的要素を認識し、"
            "詳細な説明と関連データを提供します。"
        ),
    },
}

# プロンプトパスのマッピング
PROMPT_MAPPING = {
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

# 従来のプロンプトファイルパス（フォールバック用）
LEGACY_PROMPT_FILES = {
    "recipe_extraction": "url_recipe_workflow/content_extraction.txt",
    "data_transformation": "url_recipe_workflow/data_transformation.txt",
    "recipe_notion": "url_recipe_workflow/notion.txt",
    "recipe_workflow": "url_recipe_workflow/recipe_workflow.txt",
    "image_analysis": "image_recipe_workflow/image_analysis.txt",
    "image_data_enhancement": (
        "image_recipe_workflow/image_data_enhancement.txt"
    ),
    "image_notion": "image_recipe_workflow/notion.txt",
    "image_workflow": "image_recipe_workflow/image_workflow.txt",
    "calculator": "calculator.txt",
    "notion": "notion.txt",
    "root": "root.txt",
    "vision": "vision.txt",
}

# デフォルトの画像分析プロンプト（フォールバック用）
DEFAULT_VISION_PROMPT = """あなたは画像を分析する専門家です。
提供された画像の内容を詳細に説明し、関連情報を抽出してください。
画像のタイプ（料理、製品、文書など）を特定し、適切な情報を抽出してください。"""

# src/agents/config.py
"""エージェントシステムの設定モジュール

このモジュールは、エージェントの設定（モデル、ツール、説明文など）を定義します。
設定値を一元管理することで、コードの重複を減らし保守性を向上させます。
"""

# デフォルトのLLMモデル
DEFAULT_MODEL = "gemini-2.5-flash-preview-05-20"
SEARCH_MODEL = "gemini-2.0-flash"  # 検索用の軽量モデル

# 共通の設定値
RECIPE_DATABASE_ID = "1f79a940-1325-80d9-93c6-c33da454f18f"
REQUIRED_TOOLS = "notion_create_page_mcp"  # MCP Serverツールに変更
ERROR_PREVENTION = (
    "MCP Server接続エラーを防ぐため、内部でMCPサーバー連携ツールを使用"
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
            "agent_name": "root_agent",
            "basic_principles": "ユーザーの質問に正確かつ丁寧に答えます。",
            "available_tools": "利用可能なツールを活用して最適な支援を提供します。",
            "recipe_database_id": RECIPE_DATABASE_ID,
            "required_tools": REQUIRED_TOOLS,
            "error_prevention": ERROR_PREVENTION,
            "workflow_descriptions": {
                "recipe_extraction": "URLからレシピを抽出してNotionデータベースに登録します。",
                "image_recipe_extraction": "画像からレシピを抽出してNotionデータベースに登録します。",
            },
        },
    },
    # 計算エージェント設定
    "calculator": {
        "name": "calculator_agent",
        "model": DEFAULT_MODEL,
        "prompt_key": "calculator",
        "description": "2つの数字を使って四則演算（足し算、引き算、掛け算、割り算）ができる計算エージェント",
        "variables": {
            "agent_name": "計算エージェント",
            "available_functions": "add, subtract, multiply, divide",
        },
    },
    # ファイルシステムエージェント
    "filesystem": {
        "name": "filesystem_agent",
        "model": DEFAULT_MODEL,
        "prompt_key": "filesystem",
        "description": (
            "ファイルシステムの操作を行います。ファイルの作成、読み込み、"
            "削除、ディレクトリの管理などを安全に実行します。"
            "作業ディレクトリ内でのみ操作可能です。"
        ),
        "variables": {
            "agent_name": "ファイルシステムエージェント",
            "agent_description": "安全なファイルシステム操作を実行する専門エージェント",
        },
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
            "name": "NotionMCPRegistrationAgent",
            "model": DEFAULT_MODEL,
            "prompt_key": "recipe_notion",
            "description": (
                "変換されたデータをNotion MCP Server経由でNotion データベースに登録します。"
                f"優先的に{REQUIRED_TOOLS}ツール（MCP Server）を使用し、"
                "MCP Server接続エラーを防ぎます。"
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
                "error_prevention": ERROR_PREVENTION,
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
            "variables": {
                "analysis_principle": "画像から実際に確認できる情報のみ",
                "image_analysis_principle": "画像から料理の詳細を正確に抽出する",
                "extraction_type": "画像レシピ",
                "source_type": "画像",
                "confidence_levels": "高/中/低",
                "image_types": "完成料理/調理過程/材料/レシピカード",
            },
        },
        "enhancement_agent": {
            "name": "ImageDataEnhancementAgent",
            "model": DEFAULT_MODEL,
            "prompt_key": "image_data_enhancement",
            "description": "抽出された画像データを実用的なレシピに強化します。",
            "output_key": "enhanced_recipe_data",
            "variables": {
                "analysis_principle": "画像から実際に確認できる情報のみ",
                "image_analysis_principle": "画像から料理の詳細を正確に抽出する",
                "input_data_key": "extracted_image_data",
                "output_format_key": "enhanced_recipe_data",
                "fidelity_principle": "画像から確認できた情報のみをもとに整理",
                "image_fidelity_principle": "画像から確認できた情報のみを忠実に登録",
            },
        },
        "registration_agent": {
            "name": "RecipeNotionMCPAgent",
            "model": DEFAULT_MODEL,
            "prompt_key": "image_notion",
            "description": (
                "強化されたレシピデータをNotion MCP Server経由で料理レシピデータベースに登録します。"
                f"優先的に{REQUIRED_TOOLS}ツール（MCP Server）を使用し、"
                "MCP Server接続エラーを防ぎます。"
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
                "error_prevention": ERROR_PREVENTION,
                "image_analysis_principle": "画像から料理の詳細を正確に抽出する",
                "analysis_principle": "画像から実際に確認できる情報のみ",
                "pipeline_name": "ImageRecipeExtractionPipeline",
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
        "name": "NotionMCPAgent",
        "model": DEFAULT_MODEL,
        "prompt_key": "notion",
        "description": (
            "Notion MCP Serverを通じてNotionワークスペースの包括的な操作を行うエージェントです。"
            "レシピの登録、検索、閲覧、管理を含む全般的なNotion関連タスクに対応します。"
            "レシピデータベースの操作（登録・検索・一覧表示）、"
            "ページやデータベースの検索・作成・更新、およびコンテンツの管理を行います。"
            f"レシピ登録の場合は優先的に{REQUIRED_TOOLS}ツール（MCP Server経由）を使用し、"
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
        "variables": {
            "agent_name": "画像認識エージェント",
            "agent_description": "画像を分析して詳細な情報を抽出する視覚認識の専門家",
            "analysis_confidence_levels": "高/中/低",
            "output_format_type": "JSON",
            "image_categories": {
                "food": "料理/食品",
                "product": "製品画像",
                "text": "テキスト含有画像/スクリーンショット",
                "chart": "図表/グラフ",
            },
            "extraction_rules": {
                "certainty_principle": "確実に確認できる情報のみを抽出",
                "uncertainty_handling": "不確かな情報は推定であることを明記",
                "confidence_reporting": "信頼度の低い推測には「推定」であることを明記",
            },
        },
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
    "filesystem": "agents.filesystem.main",
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
    "filesystem": "filesystem.txt",
    "main": "agents/root/main.txt",
    "system": "core/system.txt",
}

# デフォルトの画像分析プロンプト（フォールバック用）
DEFAULT_VISION_PROMPT = """あなたは画像を分析する専門家です。
提供された画像の内容を詳細に説明し、関連情報を抽出してください。
画像のタイプ（料理、製品、文書など）を特定し、適切な情報を抽出してください。"""

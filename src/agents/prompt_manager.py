"""シンプルなプロンプト管理モジュール

直接的なファイル読み込みと基本的な変数置換機能を提供する
シンプルなプロンプト管理システムです。
"""

import os
import re
from typing import Dict

from src.utils.file_utils import read_prompt_file
from src.utils.logger import setup_logger

logger = setup_logger("prompt_manager")

# プロンプトファイルの直接マッピング（実際のファイルパス）
PROMPT_FILE_MAPPING = {
    # エージェント用プロンプト
    "root": "agents/root/main.txt",
    "calculator": "agents/calculator/main.txt",
    "filesystem": "agents/filesystem/main.txt",
    "notion": "agents/notion/main.txt",
    "vision": "agents/vision/main.txt",
    # URLレシピワークフロー
    "recipe_extraction": "workflows/recipe/url_extraction/extraction.txt",
    "data_transformation": (
        "workflows/recipe/url_extraction/transformation.txt"
    ),
    "recipe_notion": "workflows/recipe/url_extraction/notion.txt",
    "recipe_workflow": "workflows/recipe/url_extraction/workflow.txt",
    # 画像レシピワークフロー
    "image_analysis": "workflows/recipe/image_extraction/analysis.txt",
    "image_data_enhancement": (
        "workflows/recipe/image_extraction/enhancement.txt"
    ),
    "image_notion": "workflows/recipe/image_extraction/notion.txt",
    "image_workflow": "workflows/recipe/image_extraction/workflow.txt",
    # システム・共通プロンプト
    "main": "agents/root/main.txt",  # メインとルートは同じ
    "system": "core/system.txt",
}

# 基本的な変数置換用のデフォルト値
DEFAULT_VARIABLES = {
    "agent_name": "root_agent",
    "basic_principles": "ユーザーの質問に正確かつ丁寧に答えます。",
    "available_tools": "利用可能なツールを活用して最適な支援を提供します。",
    "available_functions": "add, subtract, multiply, divide",
    "this": "計算関数",
    "recipe_database_id": "1f79a940-1325-80d9-93c6-c33da454f18f",
    "required_tools": "notion_create_page_mcp",
    "required_fields": "名前、材料、手順",
    "target_format": "Notion データベース形式",
    "primary_tool": "notion_create_page_mcp",
    "forbidden_tools": "notion_create_page, create",
    "error_prevention_rule": (
        "汎用ツールを使用すると「missing required parameters」エラーが発生します"
    ),
    "agent_description": "Notionデータベースに対する操作を行う専門エージェント",
    "optional_fields": "人数、調理時間、保存期間、URL",
    "validation_rules": "必須パラメータの存在チェック、データ型の検証、文字列の長さチェック",
    "notion_token_env": "NOTION_TOKEN",
    "required_params": "名前、材料、手順",
    "recipe_tool": "notion_create_page_mcp",
    "generic_tools": "notion_create_page, create",
    "error_prevention": (
        "missing required parametersエラーを防ぐため、内部で専用ツールを使用"
    ),
    "recipe_extraction_desc": (
        "URLからレシピを抽出してNotionデータベースに登録します。"
    ),
    "image_recipe_extraction_desc": (
        "画像からレシピを抽出してNotionデータベースに登録します。"
    ),
    # テンプレート変数を追加
    "extraction_type": "レシピ情報",
    "extraction_description": "レシピ抽出の専門家",
    "source_type": "Webページ",
    "extraction_targets": "レシピの名前、材料、手順",
    "extraction_process": "Webページを解析してレシピ情報を抽出します",
    "output_format": "JSON形式での構造化データ",
    "special_processing_rules": "料理に関する専門知識を活用します",
    # パイプライン変数を追加
    "pipeline_name": "ImageRecipePipeline",
    "image_analysis_principle": "画像から料理の詳細を正確に抽出する",
    # デフォルト値を追加
    "default_values": {
        "name": "不明なレシピ",
        "ingredients": "材料情報なし",
        "instructions": "調理手順なし",
    },
    # Notion制限値を追加
    "notion_limits": {
        "rich_text_max": "2000",
    },
    # システムプロンプト変数を追加
    "ai_role": "高性能AIアシスタント",
    "system_purpose": "様々なタスクを実行する様々な専門エージェントの基盤",
    "supported_languages": "日本語、英語",
    "primary_language": "日本語",
    # ワークフロー専用変数を追加
    "input_context": "extracted_recipe_data",
    "input_data_key": "extracted_image_data",
    "output_format_key": "enhanced_recipe_data",
    "fidelity_principle": "画像から確認できた情報のみをもとに整理",
    "image_fidelity_principle": "画像から確認できた情報のみを忠実に登録",
    "forbidden_actions": [
        "見えない材料の推測による追加",
        "一般的な知識による手順の補完",
        "数値項目の推測値設定",
        "創作的な料理名の付与",
    ],
    # テンプレートシステム変数
    "workflow_name": "レシピ処理ワークフロー",
    "workflow_description": "レシピ情報を処理するワークフローを管理するエージェント",
    "workflow_type_description": "URLから抽出されたレシピデータ",
    "pipeline_steps": "1. データ抽出 → 2. データ変換 → 3. Notion登録",
    "error_prevention_strategy": "各ステップでデータ検証を実行し、エラーを未然に防ぐ",
    "success_criteria": "Notionデータベースにレシピが正常に登録されること",
    "failure_handling": "エラー発生時は詳細なエラーメッセージをユーザーに提供",
    "workflow_descriptions": {
        "recipe_extraction": (
            "URLからレシピを抽出してNotionデータベースに登録します。"
        ),
        "image_recipe_extraction": (
            "画像からレシピを抽出してNotionデータベースに登録します。"
        ),
    },
}

# デフォルトのビジョンプロンプト
DEFAULT_VISION_PROMPT = """
あなたは画像認識の専門家です。画像を分析して詳細な情報を抽出します。

## 基本動作
- 画像の内容を正確に説明してください
- 見えるもののみを報告し、推測は避けてください
- 必要に応じて詳細な分析を提供してください

## 対応する画像タイプ
- 料理写真
- 製品画像
- スクリーンショット
- 図表
- 文書画像

画像の内容について何でもお聞きください。
"""


class PromptManager:
    """シンプルなプロンプト管理クラス

    テンプレート継承なしの直接的なファイル読み込みのみを行います。
    基本的な変数置換機能も提供します。
    """

    def __init__(self):
        """初期化"""
        self.prompts_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "prompts"
        )
        self._cache = {}

    def _replace_variables(self, prompt: str) -> str:
        """プロンプト内の変数を置換

        Args:
            prompt: 変数を含むプロンプトテキスト

        Returns:
            str: 変数置換済みのプロンプトテキスト
        """
        # 基本的な{{variable}}形式の変数を置換
        for var_name, var_value in DEFAULT_VARIABLES.items():
            if isinstance(var_value, dict):
                # ネストされた辞書の場合
                for nested_key, nested_value in var_value.items():
                    pattern = f"{{{{{var_name}.{nested_key}}}}}"
                    prompt = prompt.replace(pattern, str(nested_value))
            else:
                pattern = f"{{{{{var_name}}}}}"
                prompt = prompt.replace(pattern, str(var_value))

        # {{override: ...}} と {{/override}} の間のブロックを削除（簡易実装）
        prompt = re.sub(
            r"\{\{override:.*?\}\}.*?\{\{/override\}\}",
            "",
            prompt,
            flags=re.DOTALL,
        )

        # {{block: ...}} と {{/block}} の間のブロックを削除（簡易実装）
        prompt = re.sub(
            r"\{\{block:.*?\}\}(.*?)\{\{/block\}\}",
            r"\1",
            prompt,
            flags=re.DOTALL,
        )

        # メタデータセクション（---で囲まれた部分）を削除
        prompt = re.sub(r"^---.*?---\n", "", prompt, flags=re.DOTALL)

        return prompt.strip()

    def get_prompt(self, key: str) -> str:
        """指定されたキーのプロンプトを取得

        Args:
            key: プロンプトのキー

        Returns:
            str: プロンプトテキスト（変数置換済み）

        Raises:
            ValueError: 指定されたキーが存在しない場合
        """
        # キャッシュに存在すればそれを返す
        if key in self._cache:
            return self._cache[key]

        # マッピングから実際のファイルパスを取得
        if key not in PROMPT_FILE_MAPPING:
            raise ValueError(f"未知のプロンプトキー: {key}")

        file_path = os.path.join(self.prompts_dir, PROMPT_FILE_MAPPING[key])

        try:
            prompt = read_prompt_file(file_path)
            # 基本的な変数置換を実行
            prompt = self._replace_variables(prompt)
            self._cache[key] = prompt
            logger.info(f"プロンプト '{key}' を正常に読み込みました")
            return prompt
        except FileNotFoundError:
            logger.error(f"プロンプトファイルが見つかりません: {file_path}")
            # ビジョンプロンプトには特別なデフォルト値を設定
            if key == "vision":
                self._cache[key] = DEFAULT_VISION_PROMPT
                return DEFAULT_VISION_PROMPT
            else:
                error_msg = (
                    f"Error: プロンプトファイル '{key}' が見つかりません"
                )
                self._cache[key] = error_msg
                return error_msg
        except Exception as e:
            logger.error(f"プロンプト '{key}' の読み込みに失敗: {e}")
            error_msg = f"Error loading prompt: {str(e)}"
            self._cache[key] = error_msg
            return error_msg

    def get_all_prompts(self) -> Dict[str, str]:
        """すべてのプロンプトを一括で読み込む

        Returns:
            Dict[str, str]: キーとプロンプトテキストのディクショナリ
        """
        prompts = {}
        for key in PROMPT_FILE_MAPPING.keys():
            try:
                prompts[key] = self.get_prompt(key)
            except Exception as e:
                logger.error(f"プロンプト '{key}' の読み込みに失敗: {e}")
                prompts[key] = f"Error loading {key}: {str(e)}"

        return prompts

    def reload_cache(self):
        """キャッシュをクリアして再読み込み"""
        self._cache.clear()
        logger.info("プロンプトキャッシュをクリアしました")

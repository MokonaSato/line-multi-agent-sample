"""シンプルなプロンプト管理モジュール

直接的なファイル読み込みと基本的な変数置換機能を提供する
シンプルなプロンプト管理システムです。
"""

import os
import re
from typing import Dict, Optional

import yaml

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
    "validation_rules": (
        "必須パラメータの存在チェック、データ型の検証、文字列の長さチェック"
    ),
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
    "analysis_principle": "画像から実際に確認できる情報のみ",
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
    "error_prevention_strategy": (
        "各ステップでデータ検証を実行し、エラーを未然に防ぐ"
    ),
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

    def _extract_file_variables(self, content: str) -> Dict[str, str]:
        """ファイル内のYAMLメタデータから変数を抽出

        Args:
            content: ファイルの内容

        Returns:
            Dict[str, str]: 変数名と値のディクショナリ
        """
        variables = {}

        # YAMLメタデータセクションを抽出
        yaml_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if yaml_match:
            try:
                yaml_content = yaml_match.group(1)
                yaml_data = yaml.safe_load(yaml_content)

                if isinstance(yaml_data, dict) and "variables" in yaml_data:
                    file_variables = yaml_data["variables"]
                    if isinstance(file_variables, dict):
                        for key, value in file_variables.items():
                            variables[key] = str(value)

            except (yaml.YAMLError, AttributeError) as e:
                logger.warning(f"YAML解析中にエラー: {e}")

        return variables

    def _replace_variables_with_dict(
        self, prompt: str, variables: Dict[str, str]
    ) -> str:
        """辞書を使用して変数を置換

        Args:
            prompt: 変数を含むプロンプトテキスト
            variables: 変数辞書

        Returns:
            str: 変数置換済みのプロンプトテキスト
        """
        # 基本的な{{variable}}形式の変数を置換
        for var_name, var_value in variables.items():
            if isinstance(var_value, dict):
                # ネストされた辞書の場合（複数レベル対応）
                prompt = self._replace_nested_dict_variables(
                    prompt, var_name, var_value
                )
            elif isinstance(var_value, list):
                # リストの場合（配列アクセス処理はスキップ）
                continue
            else:
                pattern = f"{{{{{var_name}}}}}"
                prompt = prompt.replace(pattern, str(var_value))

        # テンプレートブロックを処理
        prompt = self._process_template_blocks(prompt)

        # 未置換の変数パターンがないか確認してログ出力
        remaining_vars = re.findall(r"\{\{([^}]+)\}\}", prompt)
        if remaining_vars:
            logger.warning(f"未置換の変数が残っています: {remaining_vars}")

        return prompt

    def _replace_nested_dict_variables(
        self, prompt: str, prefix: str, value_dict: dict
    ) -> str:
        """ネストされた辞書変数を再帰的に置換

        Args:
            prompt: プロンプトテキスト
            prefix: 変数のプレフィックス
            value_dict: 辞書値

        Returns:
            str: 置換後のプロンプトテキスト
        """
        for nested_key, nested_value in value_dict.items():
            if isinstance(nested_value, dict):
                # さらにネストされている場合は再帰的に処理
                prompt = self._replace_nested_dict_variables(
                    prompt, f"{prefix}.{nested_key}", nested_value
                )
            else:
                pattern = f"{{{{{prefix}.{nested_key}}}}}"
                prompt = prompt.replace(pattern, str(nested_value))

        return prompt

    def _process_template_blocks(self, prompt: str) -> str:
        """テンプレートブロックを処理

        Args:
            prompt: プロンプトテキスト

        Returns:
            str: ブロック処理済みのプロンプトテキスト
        """
        # {{override: ...}} と {{/override}} の間のブロックの内容を展開
        prompt = re.sub(
            r"\{\{override:.*?\}\}(.*?)\{\{/override\}\}",
            r"\1",
            prompt,
            flags=re.DOTALL,
        )

        # {{block: ...}} と {{/block}} の間のブロックの内容を展開
        prompt = re.sub(
            r"\{\{block:.*?\}\}(.*?)\{\{/block\}\}",
            r"\1",
            prompt,
            flags=re.DOTALL,
        )

        # YAMLメタデータセクション（先頭の---で囲まれた部分）を削除
        if prompt.startswith("---\n"):
            # 最初の --- から次の --- までを削除
            parts = prompt.split("---\n", 2)
            if len(parts) >= 3:
                prompt = parts[2]  # メタデータ後の本文のみを保持

        return prompt.strip()

    def _replace_variables(self, prompt: str) -> str:
        """プロンプト内の変数を置換（後方互換性のため）

        Args:
            prompt: 変数を含むプロンプトテキスト

        Returns:
            str: 変数置換済みのプロンプトテキスト
        """
        return self._replace_variables_with_dict(prompt, DEFAULT_VARIABLES)

    def get_prompt(
        self, key: str, custom_variables: Optional[Dict[str, str]] = None
    ) -> str:
        """指定されたキーのプロンプトを取得

        Args:
            key: プロンプトのキー
            custom_variables: エージェント固有の変数（オプション）

        Returns:
            str: プロンプトテキスト（変数置換済み）

        Raises:
            ValueError: 指定されたキーが存在しない場合
        """
        # カスタム変数がある場合はキャッシュを無効化
        if custom_variables:
            # ユニークなキャッシュキーを生成
            import json

            try:
                custom_str = json.dumps(
                    custom_variables, sort_keys=True, default=str
                )
                cache_key = f"{key}_{hash(custom_str)}"
            except (TypeError, ValueError):
                # JSONシリアライズできない場合は文字列化
                cache_key = f"{key}_{hash(str(custom_variables))}"
        else:
            cache_key = key

        if cache_key in self._cache:
            return self._cache[cache_key]

        # マッピングから実際のファイルパスを取得
        if key not in PROMPT_FILE_MAPPING:
            raise ValueError(f"未知のプロンプトキー: {key}")

        file_path = os.path.join(self.prompts_dir, PROMPT_FILE_MAPPING[key])

        try:
            prompt = read_prompt_file(file_path)

            # ファイル内の変数を抽出
            file_variables = self._extract_file_variables(prompt)

            # 変数置換の優先順位: カスタム変数 > デフォルト変数 > ファイル変数
            all_variables = {**file_variables, **DEFAULT_VARIABLES}
            if custom_variables:
                all_variables.update(custom_variables)

            # 最初の変数置換（{{variable}}形式の単純な置換）
            prompt = self._replace_variables_with_dict(prompt, all_variables)

            # 二重参照の解決（{{{{variable}}}}形式）
            for var_name, var_value in all_variables.items():
                value_str = str(var_value)
                if value_str.startswith("{{") and value_str.endswith("}}"):
                    # {{variable}}形式の値を持つ変数を再度置換
                    nested_var = value_str[2:-2]  # {{}}を除去
                    if nested_var in all_variables:
                        all_variables[var_name] = str(
                            all_variables[nested_var]
                        )

            # 二度目の変数置換（二重参照を解決）
            prompt = self._replace_variables_with_dict(prompt, all_variables)

            self._cache[cache_key] = prompt
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
                prompts[key] = f"Error: {str(e)}"
        return prompts

    def clear_cache(self):
        """プロンプトキャッシュをクリア"""
        self._cache.clear()
        logger.info("プロンプトキャッシュをクリアしました")

"""シンプルなプロンプト管理モジュール

基本的なファイル読み込みと簡単な変数置換機能のみを提供する
軽量なプロンプト管理システムです。
"""

import os
import re
from typing import Dict, Optional

import yaml

from src.utils.file_utils import read_prompt_file
from src.utils.logger import setup_logger

logger = setup_logger("prompt_manager")

# 実際に使用されているプロンプトファイルのマッピング
PROMPT_FILE_MAPPING = {
    # エージェント用プロンプト
    "root": "agents/root/main.txt",
    "calculator": "agents/calculator/main.txt",
    "filesystem": "agents/filesystem/main.txt",
    "notion": "agents/notion/main.txt",
    "vision": "agents/vision/main.txt",
    # URLレシピワークフロー
    "recipe_extraction": "workflows/recipe/url_extraction/extraction.txt",
    "data_transformation": "workflows/recipe/url_extraction/transformation.txt",
    "recipe_notion": "workflows/recipe/url_extraction/notion.txt",
    "recipe_workflow": "workflows/recipe/url_extraction/workflow.txt",
    # 画像レシピワークフロー
    "image_analysis": "workflows/recipe/image_extraction/analysis.txt",
    "image_data_enhancement": "workflows/recipe/image_extraction/enhancement.txt",
    "image_notion": "workflows/recipe/image_extraction/notion.txt",
    "image_workflow": "workflows/recipe/image_extraction/workflow.txt",
    # システム・共通プロンプト
    "main": "agents/root/main.txt",  # メインとルートは同じ
    "system": "core/system.txt",
}

# 実際に使用されている変数のみ
DEFAULT_VARIABLES = {
    # エージェント基本情報
    "agent_name": "root_agent",
    "basic_principles": "ユーザーの質問に正確かつ丁寧に答えます。",
    "available_tools": "利用可能なツールを活用して最適な支援を提供します。",
    "available_functions": "add, subtract, multiply, divide",
    
    # Notion関連
    "recipe_database_id": "1f79a940-1325-80d9-93c6-c33da454f18f",
    "required_tools": "notion_create_page_mcp",
    "primary_tool": "notion_create_page_mcp",
    "forbidden_tools": "notion_create_page, create",
    "error_prevention_rule": "汎用ツールを使用すると「missing required parameters」エラーが発生します",
    
    # ワークフロー説明
    "workflow_descriptions": {
        "recipe_extraction": "URLからレシピを抽出してNotionデータベースに登録します。",
        "image_recipe_extraction": "画像からレシピを抽出してNotionデータベースに登録します。",
    },
    
    # システム情報
    "ai_role": "高性能AIアシスタント",
    "system_purpose": "様々なタスクを実行する様々な専門エージェントの基盤",
    "supported_languages": "日本語、英語",
    "primary_language": "日本語",
    
    # 画像分析関連
    "analysis_principle": "画像から実際に確認できる情報のみ",
    "image_fidelity_principle": "画像から確認できた情報のみを忠実に登録",
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
    
    基本的なファイル読み込みと簡単な変数置換機能のみを提供します。
    """

    def __init__(self):
        """初期化"""
        self.prompts_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "prompts"
        )
        self._cache = {}

    def _extract_yaml_variables(self, content: str) -> Dict[str, str]:
        """YAMLメタデータから変数を抽出
        
        Args:
            content: ファイルの内容
            
        Returns:
            Dict[str, str]: 抽出された変数
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
                        variables.update(file_variables)
            except (yaml.YAMLError, AttributeError) as e:
                logger.warning(f"YAML解析中にエラー: {e}")
        
        return variables

    def _replace_simple_variables(self, content: str, variables: Dict[str, str]) -> str:
        """基本的な変数置換を実行
        
        Args:
            content: プロンプトテキスト
            variables: 変数辞書
            
        Returns:
            str: 変数置換済みテキスト
        """
        # {{variable}}形式の基本変数を置換
        for var_name, var_value in variables.items():
            if isinstance(var_value, dict):
                # 1階層のネスト変数のみ対応
                for nested_key, nested_value in var_value.items():
                    pattern = f"{{{{{var_name}.{nested_key}}}}}"
                    content = content.replace(pattern, str(nested_value))
            else:
                pattern = f"{{{{{var_name}}}}}"
                content = content.replace(pattern, str(var_value))
        
        return content

    def _clean_content(self, content: str) -> str:
        """コンテンツのクリーンアップ
        
        Args:
            content: プロンプトテキスト
            
        Returns:
            str: クリーンアップ済みテキスト
        """
        # YAMLメタデータセクションを削除
        if content.startswith("---\n"):
            parts = content.split("---\n", 2)
            if len(parts) >= 3:
                content = parts[2]
        
        # シンプルなテンプレートブロック処理
        # {{override: ...}} と {{/override}} の間の内容を展開
        content = re.sub(
            r"\{\{override:.*?\}\}(.*?)\{\{/override\}\}",
            r"\1",
            content,
            flags=re.DOTALL,
        )
        
        # {{block: ...}} と {{/block}} の間の内容を展開
        content = re.sub(
            r"\{\{block:.*?\}\}(.*?)\{\{/block\}\}",
            r"\1",
            content,
            flags=re.DOTALL,
        )
        
        return content.strip()

    def get_prompt(
        self, key: str, custom_variables: Optional[Dict[str, str]] = None
    ) -> str:
        """指定されたキーのプロンプトを取得
        
        Args:
            key: プロンプトのキー
            custom_variables: カスタム変数（オプション）
            
        Returns:
            str: プロンプトテキスト（変数置換済み）
            
        Raises:
            ValueError: 指定されたキーが存在しない場合
        """
        if key not in PROMPT_FILE_MAPPING:
            raise ValueError(f"未知のプロンプトキー: {key}")
        
        # キャッシュキー生成
        cache_key = key
        if custom_variables:
            cache_key = f"{key}_{hash(str(sorted(custom_variables.items())))}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        file_path = os.path.join(self.prompts_dir, PROMPT_FILE_MAPPING[key])
        
        try:
            # ファイル読み込み
            content = read_prompt_file(file_path)
            
            # YAMLメタデータから変数を抽出
            file_variables = self._extract_yaml_variables(content)
            
            # 変数を統合（優先順位: カスタム > ファイル > デフォルト）
            all_variables = {**DEFAULT_VARIABLES, **file_variables}
            if custom_variables:
                all_variables.update(custom_variables)
            
            # 変数置換
            content = self._replace_simple_variables(content, all_variables)
            
            # コンテンツクリーンアップ
            content = self._clean_content(content)
            
            # 未置換変数の警告
            remaining_vars = re.findall(r"\{\{([^}]+)\}\}", content)
            if remaining_vars:
                logger.warning(f"未置換の変数が残っています: {remaining_vars}")
            
            self._cache[cache_key] = content
            logger.info(f"プロンプト '{key}' を正常に読み込みました")
            return content
            
        except FileNotFoundError:
            logger.error(f"プロンプトファイルが見つかりません: {file_path}")
            if key == "vision":
                self._cache[key] = DEFAULT_VISION_PROMPT
                return DEFAULT_VISION_PROMPT
            else:
                error_msg = f"Error: プロンプトファイル '{key}' が見つかりません"
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
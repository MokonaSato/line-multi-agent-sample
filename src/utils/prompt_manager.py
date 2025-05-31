"""プロンプト管理システムモジュール

このモジュールは、エージェントやワークフロー用のプロンプトを効率的に管理するための
機能を提供します。テンプレート継承、変数置換、メタデータ処理などの高度な機能を含みます。
"""

import logging
import os
import re
from typing import Dict

import yaml

logger = logging.getLogger(__name__)


class PromptManager:
    """プロンプト管理クラス"""

    def __init__(self, root_dir: str = None):
        """
        プロンプトマネージャーを初期化

        Args:
            root_dir: プロンプトルートディレクトリ。省略時はデフォルト
        """
        self.root_dir = root_dir or os.path.join(
            os.path.dirname(__file__), "../prompts"
        )
        self.loaded_prompts = {}
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """全体設定ファイルを読み込む"""
        config_path = os.path.join(self.root_dir, "config.yaml")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as file:
                    return yaml.safe_load(file)
            except Exception as e:
                logger.error(f"設定ファイルの読み込みに失敗: {e}")
                return {}
        return {}

    def get_prompt(self, prompt_id: str) -> str:
        """
        プロンプトIDからプロンプト内容を取得

        Args:
            prompt_id: プロンプトID (例: "agents.vision.main")

        Returns:
            プロンプト文字列
        """
        if prompt_id in self.loaded_prompts:
            return self.loaded_prompts[prompt_id]

        # プロンプトIDから末尾の.txtを取り除く（もし存在すれば）
        if prompt_id.endswith(".txt"):
            prompt_id = prompt_id[:-4]

        # まず、そのままのパスで試す
        path_parts = prompt_id.split(".")
        file_path = os.path.join(self.root_dir, *path_parts) + ".txt"

        # ファイルが存在しない場合、階層構造を持つパスとして試す
        if not os.path.exists(file_path) and len(path_parts) > 1:
            # 例: agents.root.main を agents/root/main.txt に変換
            file_path = os.path.join(
                self.root_dir, path_parts[0], "/".join(path_parts[1:]) + ".txt"
            )

        # それでもファイルが見つからない場合、ディレクトリ以下に同名のファイルを探す
        if not os.path.exists(file_path) and len(path_parts) > 1:
            # 例: agents.root を agents/root/root.txt に変換
            last_part = path_parts[-1]
            file_path = os.path.join(
                self.root_dir,
                "/".join(path_parts[:-1]),
                last_part,
                last_part + ".txt",
            )

        # 設定ファイルを確認
        config_dir = os.path.dirname(file_path)
        config_path = os.path.join(config_dir, "config.yaml")
        variables = {}

        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as config_file:
                    config = yaml.safe_load(config_file)
                    if "variables" in config:
                        variables = config["variables"]
            except Exception as e:
                logger.error(
                    f"設定ファイル '{config_path}' の読み込みに失敗: {e}"
                )

        # プロンプトファイル読み込み
        try:
            if not os.path.exists(file_path):
                logger.error(
                    f"プロンプトファイル '{file_path}' が存在しません"
                )
                return f"Error: prompt file '{prompt_id}' not found"

            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

            # メタデータの処理
            content = self._process_metadata(content)

            # 継承関係の処理
            content = self._process_inheritance(content)

            # テンプレート処理（変数置換）
            if variables:
                content = self._apply_variables(content, variables)

            # グローバル変数の適用
            if self.config and "global_variables" in self.config:
                content = self._apply_variables(
                    content, self.config["global_variables"]
                )

            self.loaded_prompts[prompt_id] = content
            return content
        except Exception as e:
            logger.error(f"プロンプト '{prompt_id}' の読み込みに失敗: {e}")
            return f"Error loading prompt {prompt_id}: {str(e)}"

    def _process_metadata(self, content: str) -> str:
        """
        YAMLメタデータセクションを処理

        Args:
            content: プロンプト内容

        Returns:
            メタデータを除去したプロンプト内容
        """
        # YAMLメタデータセクションを検出
        metadata_pattern = r"^---\s*$(.*?)^---\s*$"
        match = re.search(metadata_pattern, content, re.MULTILINE | re.DOTALL)

        if match:
            # メタデータセクションを除去
            yaml_section = match.group(0)
            content = content.replace(yaml_section, "", 1).lstrip()

            # メタデータを解析（現在は使用していないが将来的に役立つ可能性あり）
            try:
                metadata_content = match.group(1)
                # メタデータは現在使用していないがログに記録
                yaml.safe_load(metadata_content)
            except Exception as e:
                logger.warning(f"メタデータの解析に失敗: {e}")

        return content

    def _apply_variables(self, content: str, variables: dict) -> str:
        """
        変数を適用

        Args:
            content: プロンプト内容
            variables: 置換する変数の辞書

        Returns:
            変数を置換したプロンプト内容
        """
        for key, value in variables.items():
            pattern = r"\{\{\s*" + re.escape(key) + r"\s*\}\}"
            content = re.sub(pattern, str(value), content)
        return content

    def _process_inheritance(self, content: str) -> str:
        """
        継承関係を処理

        Args:
            content: プロンプト内容

        Returns:
            継承を処理したプロンプト内容
        """
        # {{extend: templates.agent_base}} のようなパターンを検出
        extend_pattern = r"\{\{extend:\s*([a-zA-Z0-9_.]+)\s*\}\}"
        match = re.search(extend_pattern, content)

        if match:
            base_id = match.group(1)
            base_content = self.get_prompt(base_id)
            # 拡張マーカーを削除
            content = re.sub(extend_pattern, "", content)
            # ベースにカスタム内容を適用
            return self._merge_contents(base_content, content)

        return content

    def _merge_contents(self, base: str, custom: str) -> str:
        """
        ベースと拡張コンテンツをマージ

        Args:
            base: ベースプロンプト内容
            custom: カスタムプロンプト内容

        Returns:
            マージされたプロンプト内容
        """
        # {{block: name}}...{{/block}} パターンを処理
        block_pattern = (
            r"\{\{block:\s*([a-zA-Z0-9_]+)\s*\}\}(.*?)\{\{/block\}\}"
        )
        blocks = re.finditer(block_pattern, base, re.DOTALL)

        for match in blocks:
            block_name = match.group(1)
            # 使用していないが、将来の拡張のために変数を保持
            _ = match.group(2)  # default_content

            # カスタム内容にオーバーライドがあるか確認
            override_pattern = (
                r"\{\{override:\s*"
                + re.escape(block_name)
                + r"\s*\}\}(.*?)\{\{/override\}\}"
            )
            override_match = re.search(override_pattern, custom, re.DOTALL)

            if override_match:
                # オーバーライドで置換
                override_content = override_match.group(1)
                base = base.replace(match.group(0), override_content)
                # 使用したオーバーライドセクションを削除
                custom = re.sub(override_pattern, "", custom)

        # ベースにないカスタム内容を追加
        return base + "\n\n" + custom

    def get_agent_prompts(self, agent_name: str) -> Dict[str, str]:
        """
        エージェント用のすべてのプロンプトを辞書で取得

        Args:
            agent_name: エージェント名（例: "root", "calculator"）

        Returns:
            プロンプト名とその内容のマッピング辞書
        """
        config_path = os.path.join(
            self.root_dir, "agents", agent_name, "config.yaml"
        )
        prompts = {}

        if not os.path.exists(config_path):
            logger.error(
                f"エージェント '{agent_name}' の設定ファイルが見つかりません"
            )
            return prompts

        try:
            with open(config_path, "r", encoding="utf-8") as file:
                config = yaml.safe_load(file)

            if "prompts" in config:
                for prompt_item in config["prompts"]:
                    for key, path in prompt_item.items():
                        prompts[key] = self.get_prompt(path.replace("/", "."))

            return prompts
        except Exception as e:
            logger.error(
                f"エージェント '{agent_name}' のプロンプト読み込みに失敗: {e}"
            )
            return {}

    def get_workflow_prompts(self, workflow_path: str) -> Dict[str, str]:
        """
        ワークフロー用のすべてのプロンプトを辞書で取得

        Args:
            workflow_path: ワークフローパス（例: "recipe.url_extraction"）

        Returns:
            プロンプト名とその内容のマッピング辞書
        """
        path_parts = workflow_path.split(".")
        config_path = os.path.join(
            self.root_dir, "workflows", *path_parts, "config.yaml"
        )
        prompts = {}

        if not os.path.exists(config_path):
            logger.error(
                f"ワークフロー '{workflow_path}' の設定ファイルが見つかりません"
            )
            return prompts

        try:
            with open(config_path, "r", encoding="utf-8") as file:
                config = yaml.safe_load(file)

            if "prompts" in config:
                for prompt_item in config["prompts"]:
                    for key, path in prompt_item.items():
                        full_path = path.replace("/", ".")
                        prompts[key] = self.get_prompt(full_path)

            return prompts
        except Exception as e:
            logger.error(
                f"ワークフロー '{workflow_path}' のプロンプト読み込みに失敗: {e}"
            )
            return {}

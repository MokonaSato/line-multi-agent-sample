"""プロンプト管理モジュール

このモジュールはPromptManagerクラスを提供し、プロンプトの読み込みと管理を行います。
従来のファイルベースのプロンプト読み込みと新しいフォーマットの両方をサポートします。
"""

import os
from typing import Dict

from src.agents.config import (
    DEFAULT_VISION_PROMPT,
    LEGACY_PROMPT_FILES,
    PROMPT_MAPPING,
)
from src.utils.file_utils import read_prompt_file
from src.utils.logger import setup_logger

logger = setup_logger("prompt_manager")


class PromptManagerSingleton:
    """プロンプト管理用のシングルトンクラス

    プロンプトの読み込みと管理を一元的に行い、キャッシングによるパフォーマンス向上も図ります。
    """

    _instance = None

    def __new__(cls):
        """シングルトンパターン実装"""
        if cls._instance is None:
            cls._instance = super(PromptManagerSingleton, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初期化（シングルトンではインスタンス時に一度だけ実行）"""
        if not self._initialized:
            self._prompts_cache = {}
            self._initialized = True

    def get_all_prompts(self) -> Dict[str, str]:
        """すべてのプロンプトを一括で読み込む

        新しい管理システムからプロンプトの読み込みを試み、失敗した場合は
        従来の方法にフォールバックします。

        Returns:
            Dict[str, str]: キーとプロンプトテキストのディクショナリ
        """
        # キャッシュをクリア（確実に最新を読み込むため）
        self._prompts_cache = {}

        # すべてのプロンプトを読み込む
        prompts = {}
        for key, prompt_path in PROMPT_MAPPING.items():
            prompts[key] = self.get_prompt(key)

        return prompts

    def get_prompt(self, key: str) -> str:
        """指定されたキーのプロンプトを取得

        Args:
            key (str): プロンプトのキー

        Returns:
            str: プロンプトテキスト

        Raises:
            ValueError: 指定されたキーが存在しない場合
        """
        # キャッシュに存在すればそれを返す
        if key in self._prompts_cache:
            return self._prompts_cache[key]

        # 新しいプロンプト管理システムから読み込み
        if key in PROMPT_MAPPING:
            try:
                from src.utils.prompt_manager import PromptManager

                manager = PromptManager()
                prompt = manager.get_prompt(PROMPT_MAPPING[key])
                self._prompts_cache[key] = prompt
                logger.info(
                    f"新しい管理システムから '{key}' プロンプトを読み込みました"
                )
                return prompt
            except Exception as e:
                logger.warning(
                    f"新システムからの '{key}' プロンプト読み込みに失敗: {e}"
                )
                # 従来の方法で読み込みを試みる

        # 従来の方法で読み込む
        if key in LEGACY_PROMPT_FILES:
            prompts_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "prompts"
            )
            file_path = os.path.join(prompts_dir, LEGACY_PROMPT_FILES[key])
            try:
                prompt = read_prompt_file(file_path)
                self._prompts_cache[key] = prompt
                logger.info(f"従来の方法で '{key}' プロンプトを読み込みました")
                return prompt
            except Exception as e:
                logger.error(
                    f"プロンプトファイル '{LEGACY_PROMPT_FILES[key]}' の読み込みに失敗: {e}"
                )
                # 特定のプロンプトにデフォルト値を設定
                if key == "vision":
                    self._prompts_cache[key] = DEFAULT_VISION_PROMPT
                    return DEFAULT_VISION_PROMPT
                else:
                    error_msg = f"Error loading prompt: {str(e)}"
                    self._prompts_cache[key] = error_msg
                    return error_msg

        # キーが見つからない場合
        raise ValueError(f"未知のプロンプトキー: {key}")


# シングルトンインスタンスを公開
PromptManager = PromptManagerSingleton

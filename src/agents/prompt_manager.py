"""プロンプト管理モジュール（簡素化版）

このモジュールはPromptManagerクラスを提供し、プロンプトの読み込みと管理を行います。
"""

import os
from typing import Dict

from src.agents.config import DEFAULT_VISION_PROMPT, LEGACY_PROMPT_FILES
from src.utils.file_utils import read_prompt_file
from src.utils.logger import setup_logger

logger = setup_logger("prompt_manager")


class PromptManager:
    """プロンプト管理クラス

    プロンプトの読み込みと管理を一元的に行います。
    """

    def __init__(self):
        """初期化"""
        self._prompts_cache = {}

    def get_all_prompts(self) -> Dict[str, str]:
        """すべてのプロンプトを一括で読み込む

        Returns:
            Dict[str, str]: キーとプロンプトテキストのディクショナリ
        """
        # キャッシュをクリア（確実に最新を読み込むため）
        self._prompts_cache = {}

        # すべてのプロンプトを読み込む
        prompts = {}
        for key in LEGACY_PROMPT_FILES.keys():
            try:
                prompts[key] = self.get_prompt(key)
            except Exception as e:
                logger.error(f"プロンプト '{key}' の読み込みに失敗: {e}")
                prompts[key] = f"Error loading {key}: {str(e)}"

        return prompts

    def get_prompt(self, key: str) -> str:
        """指定されたキーのプロンプトを取得

        Args:
            key: プロンプトのキー

        Returns:
            str: プロンプトテキスト

        Raises:
            ValueError: 指定されたキーが存在しない場合
        """
        # キャッシュに存在すればそれを返す
        if key in self._prompts_cache:
            return self._prompts_cache[key]

        # PROMPT_MAPPINGは廃止されました - 直接従来の方法で読み込みます

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

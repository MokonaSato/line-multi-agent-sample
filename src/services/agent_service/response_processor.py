"""エージェント応答の処理モジュール

このモジュールは、エージェントからの応答を処理するためのユーティリティを提供します。
中間応答の検出や最終応答の判定など、応答処理に関連する機能を集約しています。
"""

from google.adk.events import Event

from src.services.agent_service.constants import (
    AGENT_CONFIG,
    COMPLETION_INDICATORS,
    ERROR_INDICATORS,
    INTERMEDIATE_PATTERNS,
)
from src.utils.logger import setup_logger

logger = setup_logger("agent_response_processor")


class ResponseProcessor:
    """エージェント応答の処理を行うクラス

    エージェントからの応答を解析し、中間応答と最終応答を判別します。
    """

    @staticmethod
    def is_intermediate_response(author: str, response: str) -> bool:
        """Sequential Agentの中間応答かどうかを判定

        Args:
            author: 応答者（エージェント）名
            response: 応答テキスト

        Returns:
            中間応答であればTrue、そうでなければFalse
        """
        # JSON形式のみの応答は中間結果の可能性が高い
        if response.strip().startswith(
            "```json"
        ) and response.strip().endswith("```"):
            return True

        # 特定のエージェント名パターンで中間応答を検出
        for pattern in INTERMEDIATE_PATTERNS:
            if pattern in response:
                return True

        # 短すぎる応答（JSON断片など）
        if len(response.strip()) < 50 and "```" in response:
            return True

        return False

    @staticmethod
    def is_final_response(author: str, response: str, step_count: int) -> bool:
        """真の最終応答かどうかを判定

        Args:
            author: 応答者（エージェント）名
            response: 応答テキスト
            step_count: SequentialAgentの実行ステップ数

        Returns:
            最終応答であればTrue、そうでなければFalse
        """
        # 明確な完了メッセージが含まれている場合
        for indicator in COMPLETION_INDICATORS:
            if indicator in response:
                return True

        # エラーメッセージの場合も最終応答として扱う
        for indicator in ERROR_INDICATORS:
            if indicator in response:
                return True

        # Sequential Agentで複数ステップが実行された後の応答
        min_steps = AGENT_CONFIG["min_steps_for_sequential"]
        min_length = AGENT_CONFIG["min_final_response_length"]

        if step_count >= min_steps and len(response) > min_length:
            return True

        # root_agentからの応答で、十分な長さがある場合
        if author == "root_agent" and len(response) > min_length:
            return True

        return False

    @staticmethod
    def log_function_calls(event: Event) -> None:
        """関数呼び出しイベントのログを出力

        Args:
            event: 処理するイベントオブジェクト
        """
        if not event.content or not event.content.parts:
            return

        parts = event.content.parts
        if parts and parts[0].function_call:
            logger.info(
                f"[{event.author}]→ call {parts[0].function_call.name}"
            )
        elif parts and parts[0].function_response:
            logger.info(
                f"[{event.author}]← response {parts[0].function_response.name}"
            )

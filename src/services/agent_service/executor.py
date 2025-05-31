"""エージェント実行モジュール

このモジュールは、エージェントの実行と応答の取得を担当します。
ランナーを使ってエージェントを実行し、応答を処理する機能を提供します。
"""

from typing import List, Optional, Tuple

from google.adk.runners import Runner
from google.genai import types

from src.services.agent_service.response_processor import ResponseProcessor
from src.utils.logger import setup_logger

logger = setup_logger("executor")


class AgentExecutor:
    """エージェント実行クラス

    ランナーを使用してエージェントを実行し、応答を処理します。
    """

    def __init__(self, runner: Runner):
        """初期化

        Args:
            runner: エージェント実行用のランナー
        """
        self.runner = runner
        self.response_processor = ResponseProcessor()

    async def execute_and_get_response(
        self,
        message: str,
        user_id: str,
        session_id: str,
        content: types.Content,
        image_data: Optional[bytes] = None,
    ) -> str:
        """エージェントを実行し応答を取得

        Args:
            message: オリジナルのメッセージ（ログ用）
            user_id: ユーザーID
            session_id: セッションID
            content: Content型のメッセージ
            image_data: 画像データ（ログ用）

        Returns:
            エージェントからの最終応答
        """
        # 初期値設定
        final_response = ""
        all_responses = []
        sequential_step_count = 0

        try:
            # ログ出力
            self._log_execution_start(message, image_data)

            # エージェント実行
            events_async = self.runner.run_async(
                session_id=session_id, user_id=user_id, new_message=content
            )

            # 応答イベントを処理
            async for event in events_async:
                # 関数呼び出しのログ
                if event.author != "user" and event.content:
                    ResponseProcessor.log_function_calls(event)

                # 最終応答を処理
                result = await self._process_final_response(
                    event, all_responses, sequential_step_count
                )

                if result:
                    final_response, all_responses, sequential_step_count = (
                        result
                    )

                    # 真の最終応答が見つかった場合はループを抜ける
                    if final_response:
                        logger.info("Received true final response from agent")
                        break

        except Exception as e:
            logger.error(f"Error during agent execution: {e}")
            final_response = f"エラーが発生しました: {str(e)}"

        # 最終応答がない場合のフォールバック処理
        if not final_response:
            final_response = self._handle_fallback_response(all_responses)

        return final_response

    def _log_execution_start(
        self, message: str, image_data: Optional[bytes]
    ) -> None:
        """エージェント実行開始時のログ出力

        Args:
            message: ユーザーメッセージ
            image_data: 画像データ（オプション）
        """
        log_message = (
            f"Running agent for message: '{message[:50]}...' (truncated)"
        )
        if image_data:
            log_message += f" with image ({len(image_data)} bytes)"
        logger.info(log_message)

    async def _process_final_response(
        self, event, all_responses: List[str], step_count: int
    ) -> Optional[Tuple[str, List[str], int]]:
        """最終応答候補を処理

        Args:
            event: イベントオブジェクト
            all_responses: これまでの応答リスト
            step_count: 現在のステップカウント

        Returns:
            処理結果のタプル (最終応答, 応答リスト, ステップカウント)
            または None（最終応答候補ではない場合）
        """
        if not (
            event.is_final_response() and event.content and event.content.parts
        ):
            return None

        current_response = event.content.parts[0].text

        # Sequential Agentの中間応答を検出
        if ResponseProcessor.is_intermediate_response(
            event.author, current_response
        ):
            logger.info(
                f"Sequential intermediate response from {event.author}"
            )
            all_responses.append(current_response)
            step_count += 1
            return ("", all_responses, step_count)

        # 真の最終応答かどうかを判定
        if ResponseProcessor.is_final_response(
            event.author, current_response, step_count
        ):
            return (current_response, all_responses, step_count)
        else:
            logger.info(
                f"Received response from {event.author}, continuing..."
            )
            all_responses.append(current_response)
            return ("", all_responses, step_count)

    def _handle_fallback_response(self, all_responses: List[str]) -> str:
        """フォールバック応答を取得

        最終応答がない場合に、代替の応答を返します。

        Args:
            all_responses: 収集されたすべての応答

        Returns:
            フォールバック応答
        """
        if all_responses:
            final_response = all_responses[-1]
            logger.info("Using last collected response as final response")
            return final_response
        else:
            logger.warning("No responses collected from agent")
            return "応答を取得できませんでした。"

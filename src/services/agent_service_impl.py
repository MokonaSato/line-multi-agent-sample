"""統合されたエージェントサービスモジュール

このモジュールは、エージェントシステムへのメインインターフェースを提供します。
以前の細分化されたモジュール（executor, message_handler, response_processor, session_manager）
の機能をすべて統合し、シンプルで保守しやすい単一モジュールとして実装します。

主な機能：
- セッション管理（ユーザーごとのコンテキスト保持）
- メッセージ送信（テキストのみ/画像付き）
- 応答処理（中間応答の処理、最終応答の判定）
- リソース管理（初期化とクリーンアップ）
"""

import asyncio
import base64
from typing import List, Optional, Tuple

from google.adk.artifacts.in_memory_artifact_service import (
    InMemoryArtifactService,
)
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, Session
from google.genai import types

from src.agents.root_agent import create_agent
from src.utils.logger import setup_logger

# ロガーを設定
logger = setup_logger("agent_service")

# アプリケーション名
APP_NAME = "line_multi_agent"

# レスポンス判定用パターン
COMPLETION_INDICATORS = [
    "レシピ登録成功",
    "✅",
    "登録されたページID",
    "ページURL:",
    "Step 4完了",
    "最終結果",
    "registration_result",
    "画像からのレシピ抽出・登録が完了しました",
    "処理が完了しました",
    "レシピ登録エラー",
    "❌ レシピ登録エラー",
    "❌ 画像レシピ登録に失敗しました",
    "📋 **エラー詳細**",
    "Notion API トークンが設定されていません",
]

ERROR_INDICATORS = [
    "エラーが発生しました",
    "❌",
    "失敗しました",
    "機能はございません",
    "Notion API トークンが設定されていません",
    "NOTION_TOKEN が設定されていません",
    "Notion API Error",
    "登録処理に失敗しました",
    "レシピ登録エラー",
    "環境変数を確認してください",
    "APIエラー",
    "トークンが未設定",
    "トークンが無効",
    "必須パラメータが不足しています",
    "missing required parameters",
    "missing_parameter",
]

INTERMEDIATE_PATTERNS = [
    "ContentExtractionAgent",
    "DataTransformationAgent",
    "ImageAnalysisAgent",
    "ImageDataEnhancementAgent",
    "extracted_recipe_data",
    "extracted_image_data",
    "enhanced_recipe_data",
    "notion_formatted_data",
]

# エージェント設定
MIN_FINAL_RESPONSE_LENGTH = 50
MIN_STEPS_FOR_SEQUENTIAL = 2
MAX_SESSION_HISTORY_SIZE = 3  # セッション履歴の最大保持数

# Gemini API エラー対処設定
MAX_RETRY_ATTEMPTS = 3  # リトライ最大回数
RETRY_DELAY_SECONDS = 2  # リトライ間隔（秒）
TOKEN_LIMIT_REDUCTION_RATIO = 0.8  # トークン制限エラー時の削減比率


class AgentService:
    """統合されたエージェントサービスクラス

    エージェントとのやり取りを管理し、アプリケーションに一貫したインターフェースを提供します。
    以前の複数クラスの機能をすべて統合した単一クラスです。
    """

    def __init__(self):
        """初期化"""
        # サービス
        self.session_service = InMemorySessionService()
        self.artifacts_service = InMemoryArtifactService()

        # エージェント関連
        self.root_agent = None
        self.exit_stack = None
        self.runner = None

    async def init_agent(self) -> None:
        """エージェントを初期化（必要時のみ実行）"""
        if self.root_agent is None:
            try:
                # エージェントとリソース管理スタックを生成
                self.root_agent, self.exit_stack = await create_agent()

                # ランナーを初期化
                self.runner = Runner(
                    app_name=APP_NAME,
                    agent=self.root_agent,
                    artifact_service=self.artifacts_service,
                    session_service=self.session_service,
                )

                logger.info("Agent initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize agent: {e}")
                raise

    async def get_or_create_session(
        self, user_id: str, session_id: Optional[str] = None
    ) -> str:
        """セッションを取得または作成

        Args:
            user_id: ユーザーID
            session_id: セッションID（未指定時は生成）

        Returns:
            有効なセッションID
        """
        if session_id is None:
            session_id = f"session_{user_id}"

        # 既存セッションを取得
        session = self._get_session(user_id, session_id)

        if session is None:
            # 新規セッション作成
            logger.info(
                f"Creating new session: {session_id} for user: {user_id}"
            )
            self.session_service.create_session(
                app_name=APP_NAME, user_id=user_id, session_id=session_id
            )
        else:
            # セッション履歴のサイズをチェックして制限
            self._limit_session_history(session)
            logger.debug(f"Using existing session: {session_id}")

        return session_id

    def _limit_session_history(self, session: Session) -> None:
        """セッション履歴のサイズを制限

        Args:
            session: セッションオブジェクト
        """
        if session.history and len(session.history) > MAX_SESSION_HISTORY_SIZE:
            # 古い履歴を削除（最新のものを保持）
            session.history = session.history[-MAX_SESSION_HISTORY_SIZE:]
            logger.info(
                f"Session history limited to {MAX_SESSION_HISTORY_SIZE} items"
            )

    def _get_session(self, user_id: str, session_id: str) -> Optional[Session]:
        """セッションを取得（内部メソッド）"""
        try:
            session = self.session_service.get_session(session_id)
            if session and session.user_id == user_id:
                return session
        except Exception:
            pass
        return None

    def create_message_content(
        self,
        message: str,
        image_data: Optional[bytes] = None,
        image_mime_type: Optional[str] = None,
    ) -> types.Content:
        """メッセージをContent型に変換

        Args:
            message: ユーザーのメッセージ文字列
            image_data: 画像バイナリデータ（オプション）
            image_mime_type: 画像MIMEタイプ（オプション）

        Returns:
            Content型のメッセージ
        """
        parts = [types.Part(text=message)]

        if image_data and image_mime_type:
            logger.info(
                f"Adding image data to message "
                f"(MIME type: {image_mime_type})"
            )
            image_base64 = base64.b64encode(image_data).decode("utf-8")
            image_part = types.Part(
                inline_data=types.Blob(
                    mime_type=image_mime_type, data=image_base64
                )
            )
            parts.append(image_part)

        return types.Content(role="user", parts=parts)

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
    def is_completion_response(response: str) -> bool:
        """最終応答かどうかを判定

        Args:
            response: 応答テキスト

        Returns:
            最終応答であればTrue、そうでなければFalse
        """
        for indicator in COMPLETION_INDICATORS:
            if indicator in response:
                return True
        return False

    @staticmethod
    def log_function_calls(event: Event) -> None:
        """関数呼び出しをログに記録

        Args:
            event: イベントオブジェクト
        """
        if hasattr(event, "function_call") and event.function_call:
            func_name = event.function_call.name
            logger.info(f"Function called: {func_name}")

    @staticmethod
    def is_gemini_500_error(error: Exception) -> bool:
        """Gemini 500エラーかどうかを判定

        Args:
            error: 例外オブジェクト

        Returns:
            Gemini 500エラーであればTrue
        """
        error_str = str(error).lower()
        return (
            "500" in error_str
            and ("internal" in error_str or "gemini" in error_str)
        ) or (hasattr(error, "code") and error.code == 500)

    @staticmethod
    def is_token_limit_error(error: Exception) -> bool:
        """トークン制限エラーかどうかを判定

        Args:
            error: 例外オブジェクト

        Returns:
            トークン制限エラーであればTrue
        """
        error_str = str(error).lower()
        return (
            "token" in error_str
            and (
                "limit" in error_str
                or "length" in error_str
                or "too long" in error_str
            )
        ) or ("input_token" in error_str)

    def _truncate_message_for_retry(
        self,
        message: str,
        reduction_ratio: float = TOKEN_LIMIT_REDUCTION_RATIO,
    ) -> str:
        """メッセージを短縮してリトライ用に調整

        Args:
            message: 元のメッセージ
            reduction_ratio: 削減比率（0.0-1.0）

        Returns:
            短縮されたメッセージ
        """
        if len(message) <= 100:
            return message

        target_length = int(len(message) * reduction_ratio)
        truncated = message[:target_length]

        # 文の途中で切れないように調整
        last_period = truncated.rfind("。")
        last_exclamation = truncated.rfind("！")
        last_question = truncated.rfind("？")

        cut_point = max(last_period, last_exclamation, last_question)
        if cut_point > target_length * 0.7:  # 70%以上の位置で見つかった場合
            truncated = truncated[: cut_point + 1]

        logger.info(
            f"Message truncated from {len(message)} to "
            f"{len(truncated)} characters"
        )
        return truncated + "（メッセージが長すぎるため一部省略しました）"

    def _reduce_session_history_for_retry(self, session: Session) -> None:
        """セッション履歴を大幅に削減してリトライ用に調整

        Args:
            session: セッションオブジェクト
        """
        if session.history and len(session.history) > 3:
            # 最新の3つのみ保持
            session.history = session.history[-3:]
            logger.info("Session history reduced to 3 items for retry")

    async def execute_and_get_response(
        self,
        message: str,
        user_id: str,
        session_id: str,
        content: types.Content,
        image_data: Optional[bytes] = None,
    ) -> str:
        """エージェントを実行し応答を取得（リトライ機能付き）

        Args:
            message: オリジナルのメッセージ（ログ用）
            user_id: ユーザーID
            session_id: セッションID
            content: Content型のメッセージ
            image_data: 画像データ（ログ用）

        Returns:
            エージェントからの最終応答
        """
        last_error = None
        current_message = message
        current_content = content

        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                return await self._execute_single_attempt(
                    current_message,
                    user_id,
                    session_id,
                    current_content,
                    image_data,
                )

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Attempt {attempt + 1}/{MAX_RETRY_ATTEMPTS} failed: {e}"
                )

                # Gemini 500エラーまたはトークン制限エラーの場合のみリトライ
                if not (
                    self.is_gemini_500_error(e) or self.is_token_limit_error(e)
                ):
                    logger.error(f"Non-retryable error: {e}")
                    break

                # 最後の試行でない場合はリトライ準備
                if attempt < MAX_RETRY_ATTEMPTS - 1:
                    # トークン制限エラーの場合はメッセージを短縮
                    if self.is_token_limit_error(e):
                        logger.info(
                            "Token limit error detected, "
                            "truncating message for retry"
                        )
                        current_message = self._truncate_message_for_retry(
                            current_message
                        )
                        current_content = self.create_message_content(
                            current_message,
                            image_data,
                            image_data and "image/jpeg" or None,
                        )

                        # セッション履歴も削減
                        session = self._get_session(user_id, session_id)
                        if session:
                            self._reduce_session_history_for_retry(session)

                    # リトライ前に待機
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
                    logger.info(
                        f"Retrying attempt {attempt + 2}/{MAX_RETRY_ATTEMPTS}"
                    )

        # すべてのリトライが失敗した場合
        logger.error(
            f"All {MAX_RETRY_ATTEMPTS} attempts failed. "
            f"Last error: {last_error}"
        )
        return f"エラーが発生しました: {str(last_error)}"

    async def _execute_single_attempt(
        self,
        message: str,
        user_id: str,
        session_id: str,
        content: types.Content,
        image_data: Optional[bytes] = None,
    ) -> str:
        """単一の実行試行（内部メソッド）

        Args:
            message: オリジナルのメッセージ（ログ用）
            user_id: ユーザーID
            session_id: セッションID
            content: Content型のメッセージ
            image_data: 画像データ（ログ用）

        Returns:
            エージェントからの最終応答
        """
        final_response = ""
        all_responses = []
        sequential_step_count = 0

        # ログ出力
        image_info = (
            f" (with {len(image_data)} bytes image)" if image_data else ""
        )
        logger.info(
            f"Processing message from user {user_id}: "
            f"{message[:100]}...{image_info}"
        )

        # エージェント実行
        events_async = self.runner.run_async(
            session_id=session_id, user_id=user_id, new_message=content
        )

        # 応答イベントを処理
        async for event in events_async:
            # 関数呼び出しのログ
            if event.author != "user" and event.content:
                self.log_function_calls(event)

            # 最終応答を処理
            result = await self._process_final_response(
                event, all_responses, sequential_step_count
            )

            if result:
                (final_response, all_responses, sequential_step_count) = result

                # 真の最終応答が見つかった場合はループを抜ける
                if final_response:
                    logger.info("Received true final response from agent")
                    break

        # 最終応答がない場合のフォールバック処理
        if not final_response:
            final_response = self._handle_fallback_response(all_responses)

        return final_response

    async def _process_final_response(
        self,
        event: Event,
        all_responses: List[str],
        sequential_step_count: int,
    ) -> Optional[Tuple[str, List[str], int]]:
        """最終応答を処理

        Args:
            event: イベントオブジェクト
            all_responses: すべての応答のリスト
            sequential_step_count: Sequential Agentのステップ数

        Returns:
            (最終応答, 全応答リスト, ステップ数) または None
        """
        if event.author == "user" or not event.content:
            return None

        # event.contentの構造を安全に処理
        content_text = ""
        if hasattr(event.content, "parts") and event.content.parts:
            # event.contentがContentオブジェクトの場合
            if event.content.parts[0].text:
                content_text = event.content.parts[0].text
            else:
                content_text = ""
        elif isinstance(event.content, list) and len(event.content) > 0:
            # event.contentがリストの場合
            if hasattr(event.content[0], "text"):
                content_text = event.content[0].text
            elif hasattr(event.content[0], "parts") and event.content[0].parts:
                if event.content[0].parts[0].text:
                    content_text = event.content[0].parts[0].text
                else:
                    content_text = ""
        elif hasattr(event.content, "text"):
            # event.contentが直接テキストを持つ場合
            content_text = event.content.text
        else:
            # その他の場合はログに記録してスキップ
            logger.debug(
                f"Unknown event.content structure: {type(event.content)}"
            )
            return None

        author = event.author

        # 中間応答の場合はスキップ
        if self.is_intermediate_response(author, content_text):
            logger.debug(f"Skipping intermediate response from {author}")
            return None, all_responses, sequential_step_count

        # Sequential Agentのステップカウント
        if "SequentialAgent" in author:
            sequential_step_count += 1

        # すべての応答を記録
        all_responses.append(content_text)

        # 最終応答の判定
        if self.is_completion_response(content_text):
            return content_text, all_responses, sequential_step_count

        # Sequential Agentの場合は追加条件をチェック
        if (
            "SequentialAgent" in author
            and sequential_step_count >= MIN_STEPS_FOR_SEQUENTIAL
            and len(content_text) >= MIN_FINAL_RESPONSE_LENGTH
        ):
            return content_text, all_responses, sequential_step_count

        return None, all_responses, sequential_step_count

    def _handle_fallback_response(self, all_responses: List[str]) -> str:
        """フォールバック応答を処理

        Args:
            all_responses: すべての応答のリスト

        Returns:
            フォールバック応答
        """
        if all_responses:
            last_response = all_responses[-1]
            logger.warning(
                f"No true final response found, using last response: "
                f"{last_response[:100]}..."
            )
            return last_response
        else:
            logger.warning("No responses received from agent")
            return "申し訳ございませんが、応答を取得できませんでした。"

    async def call_agent_text(
        self, message: str, user_id: str, session_id: Optional[str] = None
    ) -> str:
        """テキストメッセージを送信して応答を取得

        Args:
            message: ユーザーからのメッセージ
            user_id: ユーザーID
            session_id: セッションID（未指定時は新規作成）

        Returns:
            エージェントからの応答文字列
        """
        return await self._call_agent_internal(
            message=message,
            user_id=user_id,
            session_id=session_id,
            image_data=None,
            image_mime_type=None,
        )

    async def call_agent_with_image(
        self,
        message: str,
        image_data: bytes,
        image_mime_type: str,
        user_id: str,
        session_id: Optional[str] = None,
    ) -> str:
        """画像付きメッセージを送信して応答を取得

        Args:
            message: ユーザーからのメッセージ
            image_data: 画像のバイナリデータ
            image_mime_type: 画像のMIMEタイプ（例: "image/jpeg"）
            user_id: ユーザーID
            session_id: セッションID（未指定時は新規作成）

        Returns:
            エージェントからの応答文字列
        """
        return await self._call_agent_internal(
            message=message,
            user_id=user_id,
            session_id=session_id,
            image_data=image_data,
            image_mime_type=image_mime_type,
        )

    async def _call_agent_internal(
        self,
        message: str,
        user_id: str,
        session_id: Optional[str] = None,
        image_data: Optional[bytes] = None,
        image_mime_type: Optional[str] = None,
    ) -> str:
        """エージェントへの内部呼び出し（テキスト・画像両対応）

        Args:
            message: ユーザーからのメッセージ
            user_id: ユーザーID
            session_id: セッションID（未指定時は新規作成）
            image_data: 画像のバイナリデータ（オプション）
            image_mime_type: 画像のMIMEタイプ（オプション）

        Returns:
            エージェントからの応答文字列
        """
        # エージェントを初期化
        await self.init_agent()

        # セッションを管理
        session_id = await self.get_or_create_session(user_id, session_id)

        # メッセージをContent型に変換
        content = self.create_message_content(
            message, image_data, image_mime_type
        )

        # エージェントを実行して応答を取得
        return await self.execute_and_get_response(
            message, user_id, session_id, content, image_data
        )

    async def cleanup_resources(self) -> None:
        """リソースをクリーンアップ（アプリケーション終了時に呼び出す）"""
        if self.exit_stack:
            try:
                await self.exit_stack.aclose()
                logger.info("Successfully cleaned up resources")
            except Exception as e:
                logger.error(f"Error during resource cleanup: {e}")


# グローバルサービスインスタンス
_agent_service = AgentService()


# 公開インターフェース関数
async def init_agent():
    """エージェントを初期化する（一度だけ実行）"""
    await _agent_service.init_agent()
    return _agent_service.root_agent


async def call_agent_async(
    message: str, user_id: str, session_id: Optional[str] = None
) -> str:
    """テキストメッセージをエージェントに送信し、応答を返す"""
    return await _agent_service.call_agent_text(message, user_id, session_id)


async def call_agent_with_image_async(
    message: str,
    image_data: bytes,
    image_mime_type: str,
    user_id: str,
    session_id: Optional[str] = None,
) -> str:
    """画像付きメッセージをエージェントに送信し、応答を返す"""
    return await _agent_service.call_agent_with_image(
        message, image_data, image_mime_type, user_id, session_id
    )


async def cleanup_resources():
    """リソースをクリーンアップ"""
    await _agent_service.cleanup_resources()

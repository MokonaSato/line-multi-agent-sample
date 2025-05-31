"""エージェントサービスモジュール

このモジュールは、エージェントシステムへのメインインターフェースを提供します。
テキストや画像を含むメッセージをエージェントに送信し、応答を取得する機能を提供します。

主な機能：
- セッション管理（ユーザーごとのコンテキスト保持）
- メッセージ送信（テキストのみ/画像付き）
- 応答処理（中間応答の処理、最終応答の判定）
- リソース管理（初期化とクリーンアップ）
"""

from typing import Optional

from google.adk.artifacts.in_memory_artifact_service import (
    InMemoryArtifactService,
)
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from src.agents.root_agent import create_agent
from src.services.agent_service.constants import APP_NAME
from src.services.agent_service.executor import AgentExecutor
from src.services.agent_service.message_handler import MessageHandler
from src.services.agent_service.session_manager import SessionManager
from src.utils.logger import setup_logger

# ロガーを設定
logger = setup_logger("agent_service")


class AgentService:
    """エージェントサービスクラス

    エージェントとのやり取りを管理し、アプリケーションに一貫したインターフェースを提供します。
    シングルトンパターンで実装されており、アプリケーション全体で同じインスタンスが使用されます。
    """

    _instance = None

    def __new__(cls):
        """シングルトンインスタンスを作成または返却"""
        if cls._instance is None:
            cls._instance = super(AgentService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初期化（一度だけ実行）"""
        if not self._initialized:
            # サービス
            self.session_service = InMemorySessionService()
            self.artifacts_service = InMemoryArtifactService()

            # コンポーネントの初期化
            self.session_manager = SessionManager(self.session_service)
            self.message_handler = MessageHandler()

            # エージェント関連
            self.root_agent = None
            self.exit_stack = None
            self.runner = None
            self.executor = None

            # 初期化完了
            self._initialized = True

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

                # エグゼキューターを初期化
                self.executor = AgentExecutor(self.runner)

                logger.info("Agent initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize agent: {e}")
                raise

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
        session_id = await self.session_manager.get_or_create_session(
            user_id, session_id
        )

        # メッセージをContent型に変換
        content = self.message_handler.create_message_content(
            message, image_data, image_mime_type
        )

        # エージェントを実行して応答を取得
        return await self.executor.execute_and_get_response(
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


# シングルトンインスタンスをエクスポート
_agent_service = AgentService()


# 後方互換性のための関数インターフェース
async def init_agent():
    """エージェントを初期化する（一度だけ実行）"""
    await _agent_service.init_agent()
    return _agent_service.root_agent


async def call_agent_async(
    message: str, user_id: str, session_id: Optional[str] = None
) -> str:
    """
    エージェントにテキストメッセージを送信し、応答を返す

    Args:
        message: ユーザーからのメッセージ
        user_id: ユーザーID
        session_id: セッションID（未指定時は新規作成）

    Returns:
        エージェントからの応答文字列
    """
    return await _agent_service.call_agent_text(message, user_id, session_id)


async def call_agent_with_image_async(
    message: str,
    image_data: bytes,
    image_mime_type: str,
    user_id: str,
    session_id: Optional[str] = None,
) -> str:
    """
    エージェントに画像付きメッセージを送信し、応答を返す

    Args:
        message: ユーザーからのメッセージ
        image_data: 画像のバイナリデータ
        image_mime_type: 画像のMIMEタイプ（例: "image/jpeg"）
        user_id: ユーザーID
        session_id: セッションID（未指定時は新規作成）

    Returns:
        エージェントからの応答文字列
    """
    return await _agent_service.call_agent_with_image(
        message, image_data, image_mime_type, user_id, session_id
    )


async def cleanup_resources():
    """リソースをクリーンアップ"""
    await _agent_service.cleanup_resources()

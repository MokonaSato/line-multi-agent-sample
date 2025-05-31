"""セッション管理モジュール

このモジュールは、エージェントとの対話セッションを管理するための機能を提供します。
セッションの作成、取得、および更新を担当します。
"""

from typing import Optional

from google.adk.sessions import InMemorySessionService, Session

from src.services.agent_service.constants import APP_NAME
from src.utils.logger import setup_logger

logger = setup_logger("session_manager")


class SessionManager:
    """セッション管理クラス

    ユーザーセッションの作成と管理を担当します。
    """

    def __init__(self, session_service: InMemorySessionService):
        """初期化

        Args:
            session_service: セッションサービスのインスタンス
        """
        self.session_service = session_service

    async def get_or_create_session(
        self, user_id: str, session_id: Optional[str] = None
    ) -> str:
        """セッションを取得または作成

        既存のセッションがある場合はそれを返し、なければ新規作成します。

        Args:
            user_id: ユーザーID
            session_id: セッションID（未指定時は生成）

        Returns:
            有効なセッションID
        """
        # セッションIDが指定されていない場合はユーザーIDから生成
        if session_id is None:
            session_id = f"session_{user_id}"

        # 既存セッションを取得
        session = self._get_session(user_id, session_id)

        # セッションがない場合は新規作成
        if not session:
            session = self._create_session(user_id, session_id)
            logger.info(f"Created new session: {session.id}")
        else:
            logger.info(f"Using existing session: {session.id}")

        return session.id

    def _get_session(self, user_id: str, session_id: str) -> Optional[Session]:
        """既存のセッションを取得

        Args:
            user_id: ユーザーID
            session_id: セッションID

        Returns:
            セッションオブジェクト（存在しない場合はNone）
        """
        return self.session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
        )

    def _create_session(self, user_id: str, session_id: str) -> Session:
        """新しいセッションを作成

        Args:
            user_id: ユーザーID
            session_id: セッションID

        Returns:
            作成されたセッションオブジェクト
        """
        return self.session_service.create_session(
            state={},
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
        )

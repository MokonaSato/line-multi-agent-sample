# import re

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from config import GOOGLE_API_KEY  # noqa: F401
from src.agents.calc_agent import calculator_agent
from src.utils.logger import setup_logger

# グローバル変数
session_service = None
runner = None
APP_NAME = "calculator_app"

# ロガーの設定
logger = setup_logger("agent_service")


def setup_agent_runner():
    """Agent Runnerを初期化"""
    global session_service, runner

    # セッションサービスの設定
    session_service = InMemorySessionService()

    # Runnerの設定
    runner = Runner(
        agent=calculator_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    return runner


async def call_agent_async(query: str, user_id: str):
    """エージェントにクエリを送信し、レスポンスを返す"""
    global session_service, runner, APP_NAME

    if not runner or not session_service:
        setup_agent_runner()

    # セッションIDをユーザーIDから生成（簡易的な実装）
    session_id = f"session_{user_id}"

    # 重要: セッションが存在しない場合は作成する
    try:
        # 新しいAPIに合わせて修正 - キーワード引数を使用する
        session = session_service.get_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )
        if not session:
            logger.info(
                f"Creating new session for user {user_id} with session ID {session_id}"
            )
            session_service.create_session(
                app_name=APP_NAME, user_id=user_id, session_id=session_id
            )
    except TypeError:
        # 古いAPIスタイルの場合、異なる方法で呼び出す可能性がある
        logger.info(
            f"Trying alternative API for session management for user {user_id}"
        )
        # 辞書形式でアクセスしてみる
        if (
            APP_NAME not in session_service.sessions
            or user_id not in session_service.sessions.get(APP_NAME, {})
            or session_id
            not in session_service.sessions.get(APP_NAME, {}).get(user_id, {})
        ):
            logger.info(
                f"Creating new session for user {user_id} with session ID {session_id}"
            )
            session_service.create_session(
                app_name=APP_NAME, user_id=user_id, session_id=session_id
            )

    # ユーザーのメッセージをADK形式で準備
    content = types.Content(role="user", parts=[types.Part(text=query)])

    final_response_text = (
        "エージェントは最終応答を生成しませんでした。"  # デフォルト
    )

    # イベントを反復処理して最終応答を見つけます。
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate:
                final_response_text = (
                    f"エージェントがエスカレートしました: "
                    f"{event.error_message or '特定のメッセージはありません。'}"
                )
            break
    return final_response_text

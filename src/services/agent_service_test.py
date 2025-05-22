from typing import Optional

from google.adk.artifacts.in_memory_artifact_service import (
    InMemoryArtifactService,
)
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from src.agents.root_agent import create_agent
from src.utils.logger import setup_logger

session_service = InMemorySessionService()
artifacts_service = InMemoryArtifactService()
root_agent = None
exit_stack = None
runner = None
APP_NAME = "line_multi_agent"

# ロガーを設定
logger = setup_logger("agent_service")


async def init_agent():
    """エージェントを初期化する（一度だけ実行）"""
    global root_agent, exit_stack, runner
    if root_agent is None:
        root_agent, exit_stack = await create_agent()

        # ランナーも初期化
        runner = Runner(
            app_name=APP_NAME,
            agent=root_agent,
            artifact_service=artifacts_service,
            session_service=session_service,
        )
    return root_agent


async def call_agent_async(
    message: str, user_id: str, session_id: Optional[str] = None
) -> str:
    """
    エージェントにメッセージを送信し、応答を返す

    Args:
        message: ユーザーからのメッセージ
        user_id: ユーザーID
        session_id: セッションID（未指定時は新規作成）

    Returns:
        エージェントからの応答文字列
    """

    global session_service, artifacts_service, root_agent, runner, APP_NAME

    # エージェントがまだ初期化されていない場合は初期化
    if root_agent is None:
        await init_agent()

    # セッションIDが指定されていない場合はユーザーIDから生成
    if session_id is None:
        session_id = f"session_{user_id}"

    session = session_service.get_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )
    # セッション管理
    if not session:
        session = session_service.create_session(
            state={}, app_name=APP_NAME, user_id=user_id, session_id=session_id
        )
        session_id = session.id
        logger.info(f"Created new session: {session_id}")
    else:
        session_id = session.id
        logger.info(f"Using existing session: {session_id}")

    # メッセージをContent型に変換
    content = types.Content(role="user", parts=[types.Part(text=message)])

    # root_agent, exit_stack = await create_agent()

    # エージェントを実行して応答を取得
    final_response = ""

    try:
        logger.info(
            f"Running agent for message: '{message[:50]}...' (truncated)"
        )
        events_async = runner.run_async(
            session_id=session_id, user_id=user_id, new_message=content
        )

        # イベントを非同期で処理
        async for event in events_async:
            if (
                event.is_final_response()
                and event.content
                and event.content.parts
            ):
                final_response = event.content.parts[0].text
                logger.info("Received final response from agent")
                break  # 最終応答を受け取ったらループを抜ける

    except Exception as e:
        logger.error(f"Error during agent execution: {e}")
        final_response = f"エラーが発生しました: {str(e)}"

    # 最終応答がない場合のフォールバック
    if not final_response:
        final_response = "応答を取得できませんでした。"

    return final_response


# リソースをクリーンアップする関数
async def cleanup_resources():
    """リソースをクリーンアップ"""
    global exit_stack
    if exit_stack:
        try:
            await exit_stack.aclose()
            logger.info("Successfully cleaned up resources")
        except Exception as e:
            logger.error(f"Error during resource cleanup: {e}")

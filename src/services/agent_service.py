from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from config import GOOGLE_API_KEY  # noqa: F401
from src.agents.calc_agent import calculator_agent

# グローバル変数
session_service = None
runner = None
APP_NAME = "calculator_app"


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

    # セッションが存在しない場合は作成
    if not session_service.get_session(APP_NAME, user_id, session_id):
        session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )

    # ユーザーメッセージをADK形式に変換
    content = types.Content(role="user", parts=[types.Part(text=query)])

    final_response_text = "エージェントからの応答がありませんでした。"

    # エージェントを実行して最終的な応答を取得
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate:
                final_response_text = (
                    f"エラーが発生しました: {event.error_message or '詳細不明'}"
                )
            break

    return final_response_text

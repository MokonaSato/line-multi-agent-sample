# src/services/agent_service.py (修正版)
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

    # エージェントを実行して応答を取得
    final_response = ""
    all_responses = []  # 全ての応答を収集
    sequential_step_count = 0  # Sequential Agentのステップカウンター

    try:
        logger.info(
            f"Running agent for message: '{message[:50]}...' (truncated)"
        )
        events_async = runner.run_async(
            session_id=session_id, user_id=user_id, new_message=content
        )

        # イベントを非同期で処理
        async for event in events_async:
            if event.author != "user" and event.content:
                parts = event.content.parts
                if parts and parts[0].function_call:
                    logger.info(
                        f"[{event.author}]→ call "
                        f"{parts[0].function_call.name}"
                    )
                elif parts and parts[0].function_response:
                    logger.info(
                        f"[{event.author}]← response "
                        f"{parts[0].function_response.name}"
                    )

            # 修正1: final_responseの判定を改善
            if (
                event.is_final_response()
                and event.content
                and event.content.parts
            ):
                current_response = event.content.parts[0].text

                # 修正2: Sequential Agentの中間応答を検出
                if _is_sequential_intermediate_response(
                    event.author, current_response
                ):
                    logger.info(
                        f"Sequential intermediate response from {event.author}"
                    )
                    all_responses.append(current_response)
                    sequential_step_count += 1
                    continue  # 中間応答の場合は継続

                # 修正3: 真の最終応答かどうかを判定
                if _is_true_final_response(
                    event.author, current_response, sequential_step_count
                ):
                    final_response = current_response
                    logger.info("Received true final response from agent")
                    break
                else:
                    logger.info(
                        f"Received response from {event.author}, continuing..."
                    )
                    all_responses.append(current_response)

    except Exception as e:
        logger.error(f"Error during agent execution: {e}")
        final_response = f"エラーが発生しました: {str(e)}"

    # 修正4: 最終応答がない場合のフォールバック処理を改善
    if not final_response:
        if all_responses:
            # Sequential Agentの場合、最後の応答を最終応答として使用
            final_response = all_responses[-1]
            logger.info("Using last collected response as final response")
        else:
            final_response = "応答を取得できませんでした。"
            logger.warning("No responses collected from agent")

    return final_response


def _is_sequential_intermediate_response(author: str, response: str) -> bool:
    """Sequential Agentの中間応答かどうかを判定"""

    # JSON形式のみの応答は中間結果の可能性が高い
    if response.strip().startswith("```json") and response.strip().endswith(
        "```"
    ):
        return True

    # 特定のエージェント名パターンで中間応答を検出
    intermediate_patterns = [
        "ContentExtractionAgent",
        "DataTransformationAgent",
        "extracted_recipe_data",
        "notion_formatted_data",
    ]

    # 応答内容に中間結果のパターンが含まれている場合
    for pattern in intermediate_patterns:
        if pattern in response:
            return True

    # 短すぎる応答（JSON断片など）
    if len(response.strip()) < 50 and "```" in response:
        return True

    return False


def _is_true_final_response(
    author: str, response: str, step_count: int
) -> bool:
    """真の最終応答かどうかを判定"""

    # 明確な完了メッセージが含まれている場合
    completion_indicators = [
        "レシピ登録成功",
        "✅",
        "登録されたページID",
        "ページURL:",
        "Step 4完了",
        "最終結果",
        "registration_result",
    ]

    for indicator in completion_indicators:
        if indicator in response:
            return True

    # エラーメッセージの場合も最終応答として扱う
    error_indicators = [
        "エラーが発生しました",
        "❌",
        "失敗しました",
        "機能はございません",
    ]

    for indicator in error_indicators:
        if indicator in response:
            return True

    # Sequential Agentで複数ステップが実行された後の応答
    if step_count >= 2 and len(response) > 100:
        return True

    # root_agentからの応答で、十分な長さがある場合
    if author == "root_agent" and len(response) > 50:
        return True

    return False


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

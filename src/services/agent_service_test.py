import asyncio
import atexit
from contextlib import suppress
from typing import Optional

from google.adk.artifacts.in_memory_artifact_service import (
    InMemoryArtifactService,
)
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from src.agents.root_agent import create_agent
from src.utils.logger import setup_logger

# ロガーを設定
logger = setup_logger("agent_service")

# シングルトンパターンで共有リソースを管理
_runner = None
_session_service = None
_exit_stack = None
_setup_lock = asyncio.Lock()  # 並行初期化を防ぐためのロック
_setup_task = None  # エージェント初期化タスクを追跡


async def setup_agent_runner() -> Runner:
    """エージェントランナーを初期化して返す"""
    global _runner, _session_service, _exit_stack, _setup_task

    # 初期化済みの場合はすぐに返す
    if _runner is not None:
        return _runner

    # 並行して複数の初期化が行われないようにロックを使用
    async with _setup_lock:
        # ロック取得後に再チェック（他のタスクが初期化を完了した可能性がある）
        if _runner is not None:
            return _runner

        # 初期化タスクが実行中の場合は完了を待つ
        if _setup_task is not None and not _setup_task.done():
            try:
                await _setup_task
                return _runner
            except Exception:
                # 前回の初期化が失敗した場合は再試行
                pass

        # 新しい初期化タスクを作成
        _setup_task = asyncio.create_task(_initialize_agent_runner())
        try:
            await _setup_task
            return _runner
        except Exception as e:
            logger.error(f"Failed to initialize agent runner: {e}")
            raise


async def _initialize_agent_runner() -> None:
    """エージェントランナーを内部的に初期化する"""
    global _runner, _session_service, _exit_stack

    logger.info("Initializing agent runner...")

    # セッションとアーティファクトのサービスを初期化
    _session_service = InMemorySessionService()
    artifacts_service = InMemoryArtifactService()

    try:
        # エージェントを作成
        root_agent, new_exit_stack = await create_agent()
        _exit_stack = new_exit_stack

        # ランナーを初期化
        _runner = Runner(
            app_name="line_multi_agent",
            agent=root_agent,
            artifact_service=artifacts_service,
            session_service=_session_service,
        )
        logger.info(f"Agent runner initialized with {root_agent.name}")
    except Exception as e:
        # 初期化中に例外が発生した場合
        logger.error(f"Failed to initialize agent runner: {e}")

        # リソースをクリーンアップ
        if _exit_stack:
            with suppress(Exception):
                await _exit_stack.aclose()
            _exit_stack = None

        # グローバル変数をリセット
        _session_service = None
        _runner = None

        # 例外を再送出
        raise


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
    try:
        # ランナーを取得（初回時は初期化）
        runner = await setup_agent_runner()

        # セッション管理
        if not session_id:
            session = _session_service.create_session(
                state={}, app_name="line_multi_agent", user_id=user_id
            )
            session_id = session.id
            logger.info(f"Created new session: {session_id}")
        else:
            try:
                # セッションが存在するか確認
                _session_service.get_session(
                    app_name="line_multi_agent",
                    user_id=user_id,
                    session_id=session_id,
                )
                logger.info(f"Using existing session: {session_id}")
            except Exception:
                # セッションが存在しない場合は新規作成
                session = _session_service.create_session(
                    state={},
                    app_name="line_multi_agent",
                    user_id=user_id,
                    session_id=session_id,
                )
                logger.info(f"Re-created session: {session_id}")

        # メッセージをContent型に変換
        content = types.Content(role="user", parts=[types.Part(text=message)])

        # エージェントを実行して応答を取得
        final_response = ""
        events_completed = False

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

            # 非同期ジェネレーターが正常に完了したことを記録
            events_completed = True
            logger.info(
                f"Agent events completed successfully: {events_completed}"
            )

        except Exception as e:
            logger.error(f"Error during agent execution: {e}")
            final_response = f"エラーが発生しました: {str(e)}"

        # 最終応答がない場合のフォールバック
        if not final_response:
            final_response = "応答を取得できませんでした。"

        return final_response

    except Exception as e:
        logger.error(f"Error in call_agent_async: {e}")
        return f"システムエラーが発生しました: {str(e)}"


async def cleanup_resources():
    """リソースをクリーンアップする"""
    global _exit_stack, _runner, _session_service, _setup_task

    logger.info("Cleaning up agent resources...")

    # 実行中の初期化タスクをキャンセル
    if _setup_task and not _setup_task.done():
        _setup_task.cancel()
        with suppress(asyncio.CancelledError):
            await _setup_task

    # エージェントリソースをクリーンアップ
    if _exit_stack:
        try:
            # クリーンアップ前に現在のリソースへの参照をコピーし、
            # グローバル変数をクリア（別のタスクで再初期化しないように）
            exit_stack_to_close = _exit_stack
            _exit_stack = None
            _runner = None
            _session_service = None

            # リソースを解放（例外を抑制）
            with suppress(Exception):
                await exit_stack_to_close.aclose()

            logger.info("Agent resources cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during resource cleanup: {e}")


# アプリ終了時にリソースをクリーンアップするためのハンドラ
def register_cleanup_handler():
    """アプリケーション終了時のクリーンアップハンドラを登録"""

    def cleanup():
        # 新しいイベントループを作成
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # cleanup_resources を実行
            loop.run_until_complete(cleanup_resources())
        except Exception as e:
            print(f"Error in cleanup handler: {e}")
        finally:
            # ループを閉じる
            loop.close()

    # atexit にハンドラを登録
    atexit.register(cleanup)


# モジュール読み込み時にクリーンアップハンドラを自動登録
register_cleanup_handler()

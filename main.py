"""メインアプリケーション

このモジュールは、FastAPIを使ったWebhookサーバーを提供します。
LINEからのWebhookを受け取り、エージェントを使って応答を生成します。
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from linebot.v3.webhooks import MessageEvent

# 内部モジュールからのインポート
from src.services.agent_service import cleanup_resources, init_agent
from src.services.line_service import (
    DEFAULT_THREAD_NAME_PREFIX,
    DEFAULT_THREAD_POOL_SIZE,
    LineClient,
    LineEventHandler,
)
from src.utils.logger import setup_logger

# ロガーのセットアップ
logger = setup_logger("main")

# .envファイルから環境変数を読み込み
load_dotenv()

# スレッドプールの作成
executor = ThreadPoolExecutor(
    max_workers=DEFAULT_THREAD_POOL_SIZE,
    thread_name_prefix=DEFAULT_THREAD_NAME_PREFIX,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPIのlifespan管理（強化版）"""
    # 起動時の処理
    logger.info("🚀 Starting application initialization")

    cleanup_tasks = []

    try:
        # エージェントの初期化
        logger.info("Initializing AI agent...")
        await init_agent()
        cleanup_tasks.append(cleanup_resources)
        logger.info("✅ Agent initialization completed")

        # その他の初期化処理があれば追加
        # await init_database()
        # cleanup_tasks.append(cleanup_database)

        logger.info("🎉 Application startup completed successfully")

    except Exception as e:
        logger.error(f"❌ Failed to initialize application: {e}")
        # 部分的に初期化されたリソースをクリーンアップ
        for cleanup_func in reversed(cleanup_tasks):
            try:
                await cleanup_func()
            except Exception as cleanup_error:
                logger.error(f"Error during startup cleanup: {cleanup_error}")
        raise

    try:
        yield  # アプリケーションが実行される
    finally:
        # 終了時の処理
        logger.info("🛑 Starting application shutdown")

        # すべてのクリーンアップタスクを実行
        for cleanup_func in reversed(cleanup_tasks):
            try:
                logger.info(f"Running cleanup: {cleanup_func.__name__}")
                await cleanup_func()
            except Exception as e:
                logger.error(f"Error during {cleanup_func.__name__}: {e}")

        # スレッドプールの終了
        try:
            executor.shutdown(wait=True)
            logger.info("✅ Thread pool executor shutdown completed")
        except Exception as e:
            logger.error(f"Error shutting down executor: {e}")

        logger.info("🏁 Application shutdown completed")


app = FastAPI(lifespan=lifespan)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LINEクライアントの準備
line_client = LineClient()
line_handler = LineEventHandler(line_client)


def process_events(body: str, signature: str) -> None:
    """LINE から届いたイベントをまとめて処理（スレッド内で実行）

    Args:
        body: Webhookリクエストボディ
        signature: X-Line-Signatureヘッダー値
    """
    logger.info("Processing LINE events in background thread")
    try:
        # イベントのパース
        events = line_client.parse_webhook_events(body, signature)
        # 各イベントを処理
        for event in events:
            if isinstance(event, MessageEvent):
                # メッセージイベントを非同期で処理
                asyncio.run(line_handler.handle_event(event))
    except Exception as e:
        logger.exception(f"Error in process_events: {e}")


@app.post("/callback")
async def callback(request: Request):
    """LINE Webhookハンドラー

    Args:
        request: FastAPIリクエストオブジェクト

    Returns:
        str: 応答メッセージ
    """
    # X-Line-Signatureヘッダー値を取得
    signature = request.headers.get("X-Line-Signature", "")

    # リクエストボディをテキストとして取得
    body = await request.body()
    body_text = body.decode("utf-8")
    logger.info(f"Request body: {body_text}")

    # 非同期でWebhookボディを処理
    executor.submit(process_events, body_text, signature)

    return "OK"


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント

    Returns:
        dict: ステータス情報
    """
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

"""メインアプリケーション

このモジュールは、FastAPIを使ったWebhookサーバーを提供します。
LINEからのWebhookを受け取り、エージェントを使って応答を生成します。
"""

from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from linebot.v3.webhooks import MessageEvent

# 内部モジュールからのインポート
from src.services.agent_service_impl import cleanup_resources, init_agent
from src.services.line_service import LineClient, LineEventHandler
from src.tools.filesystem import initialize_filesystem_service
from src.tools.notion_mcp import cleanup_notion_mcp, initialize_notion_mcp
from src.utils.logger import setup_logger

# ロガーのセットアップ
logger = setup_logger("main")

# .envファイルから環境変数を読み込み
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPIのlifespan管理（シンプル版）"""
    # 起動時の処理
    logger.info("🚀 Starting application initialization")

    cleanup_tasks = []

    try:
        # エージェントの初期化
        logger.info("Initializing AI agent...")
        await init_agent()
        cleanup_tasks.append(cleanup_resources)
        logger.info("✅ Agent initialization completed")

        # ファイルシステムサービスの初期化
        logger.info("Initializing filesystem service...")
        await initialize_filesystem_service()
        logger.info("✅ Filesystem service initialization completed")

        # Notion MCP サービスの初期化
        logger.info("Initializing Notion MCP service...")
        initialize_notion_mcp()  # 同期関数として呼び出し
        cleanup_tasks.append(cleanup_notion_mcp)
        logger.info("✅ Notion MCP service initialization completed")

        logger.info("🎉 Application startup completed successfully")

    except Exception as e:
        logger.error(f"❌ Failed to initialize application: {e}")
        for cleanup_func in reversed(cleanup_tasks):
            try:
                if cleanup_func == cleanup_notion_mcp:
                    cleanup_func()  # 同期関数として呼び出し
                else:
                    await cleanup_func()
            except Exception as cleanup_error:
                logger.error(f"Error during startup cleanup: {cleanup_error}")
        raise

    try:
        yield  # アプリケーションが実行される
    finally:
        # 終了時の処理
        logger.info("🛑 Starting application shutdown")
        for cleanup_func in reversed(cleanup_tasks):
            try:
                logger.info(f"Running cleanup: {cleanup_func.__name__}")
                if cleanup_func == cleanup_notion_mcp:
                    cleanup_func()  # 同期関数として呼び出し
                else:
                    await cleanup_func()
            except Exception as e:
                logger.error(f"Error during {cleanup_func.__name__}: {e}")
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


async def process_events(body: str, signature: str) -> None:
    """LINE から届いたイベントを非同期で処理

    Args:
        body: Webhookリクエストボディ
        signature: X-Line-Signatureヘッダー値
    """
    logger.info("Processing LINE events")
    try:
        # イベントのパース
        events = line_client.parse_webhook_events(body, signature)
        # 各イベントを処理
        for event in events:
            if isinstance(event, MessageEvent):
                # メッセージイベントを非同期で処理
                await line_handler.handle_event(event)
    except Exception as e:
        logger.exception(f"Error in process_events: {e}")


@app.post("/callback")
async def callback(request: Request, background_tasks: BackgroundTasks):
    """LINE Webhookハンドラー

    Args:
        request: FastAPIリクエストオブジェクト
        background_tasks: バックグラウンドタスク

    Returns:
        str: 応答メッセージ
    """
    # X-Line-Signatureヘッダー値を取得
    signature = request.headers.get("X-Line-Signature", "")

    # リクエストボディをテキストとして取得
    body = await request.body()
    body_text = body.decode("utf-8")
    logger.info(f"Request body: {body_text}")

    # バックグラウンドタスクでWebhookボディを処理
    background_tasks.add_task(process_events, body_text, signature)

    return "OK"


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント

    Returns:
        dict: ステータス情報
    """
    try:
        from src.tools.filesystem import check_filesystem_health
        from src.tools.notion_mcp import check_notion_mcp_health

        # 各サービスのヘルスチェック
        filesystem_ok = await check_filesystem_health()
        notion_mcp_ok = await check_notion_mcp_health()

        status = "ok" if (filesystem_ok and notion_mcp_ok) else "degraded"

        return {
            "status": status,
            "services": {
                "filesystem": "ok" if filesystem_ok else "error",
                "notion_mcp": "ok" if notion_mcp_ok else "error",
            },
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

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
from src.tools.mcp_integration import check_mcp_server_health
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

        # Notion MCP サービスの初期化とヘルスチェック
        logger.info("Checking MCP server health...")
        mcp_health = await check_mcp_server_health()
        for server, is_healthy in mcp_health.items():
            status = "✅ Online" if is_healthy else "❌ Offline"
            logger.info(f"MCP Server ({server}): {status}")
        logger.info("✅ MCP service check completed")

        logger.info("🎉 Application startup completed successfully")

    except Exception as e:
        logger.error(f"❌ Failed to initialize application: {e}")
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
        for cleanup_func in reversed(cleanup_tasks):
            try:
                logger.info(f"Running cleanup: {cleanup_func.__name__}")
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
        from src.tools.mcp_integration import check_mcp_server_health

        # 各サービスのヘルスチェック
        filesystem_ok = await check_filesystem_health()
        mcp_health = await check_mcp_server_health()

        all_services_ok = filesystem_ok and all(mcp_health.values())
        status = "ok" if all_services_ok else "degraded"

        services_status = {
            "filesystem": "ok" if filesystem_ok else "error",
        }
        # MCP サーバーのステータスを追加
        for server, is_healthy in mcp_health.items():
            services_status[f"mcp_{server}"] = "ok" if is_healthy else "error"

        return {
            "status": status,
            "services": services_status,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

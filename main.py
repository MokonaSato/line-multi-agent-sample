"""メインアプリケーション

このモジュールは、FastAPIを使ったWebhookサーバーを提供します。
LINEからのWebhookを受け取り、エージェントを使って応答を生成します。
"""

from contextlib import asynccontextmanager
import os
from datetime import datetime

import httpx
import uvicorn
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from linebot.v3.webhooks import MessageEvent

# 内部モジュールからのインポート
from src.services.agent_service_impl import (
    cleanup_resources,
    init_agent,
)
from src.services.line_service import LineClient, LineEventHandler
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

        # ファイルシステム初期化はMCPサーバーが処理
        logger.info("Filesystem initialization handled by MCP server")

        # Notion MCP サービスの初期化とヘルスチェック
        logger.info("Checking MCP server health...")
        try:
            mcp_health = await check_mcp_server_health()
            for server, is_healthy in mcp_health.items():
                status = "✅ Online" if is_healthy else "❌ Offline"
                logger.info(f"MCP Server ({server}): {status}")
        except Exception as e:
            logger.warning(f"MCP health check failed: {e}")
            logger.info("Application will continue without MCP services")
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
        # MCPサーバーのヘルスチェック（FilesystemとNotion統合）
        try:
            mcp_health = await check_mcp_server_health()
            filesystem_ok = mcp_health.get("filesystem", False)
        except Exception as e:
            logger.warning(f"MCP health check failed in endpoint: {e}")
            mcp_health = {"filesystem": False, "notion": False}
            filesystem_ok = False

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


@app.get("/validate-notion-token")
async def validate_notion_token():
    """Notion API トークンの生存確認エンドポイント
    
    環境変数のNOTION_TOKENまたはGCP Secret ManagerからNotion Tokenを取得し、
    Notion API (/v1/users) への接続テストを行います。
    
    Returns:
        dict: トークンの検証結果
    """
    try:
        # 環境変数からNotion Tokenを取得（優先）
        notion_token = os.getenv('NOTION_TOKEN')
        if notion_token:
            notion_token = notion_token.strip()
        
        # 環境変数がない場合は、GCP Secret Managerから取得
        if not notion_token:
            logger.info("NOTION_TOKEN環境変数が未設定のため、Secret Managerから取得を試行します")
            try:
                from google.cloud import secretmanager
                client = secretmanager.SecretManagerServiceClient()
                
                # プロジェクトIDを取得
                project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0075173573")
                secret_path = f"projects/{project_id}/secrets/notion-api-key/versions/latest"
                
                response = client.access_secret_version(request={"name": secret_path})
                notion_token = response.payload.data.decode("UTF-8").strip()
                logger.info("Secret Manager から Notion Token を取得しました")
                
            except Exception as secret_error:
                logger.error(f"Secret Manager からの取得に失敗: {secret_error}")
                return {
                    "status": "error",
                    "error": "token_missing",
                    "message": f"Notion API トークンが設定されていません。Secret Manager エラー: {str(secret_error)}",
                    "timestamp": datetime.now().isoformat()
                }
        
        if not notion_token:
            return {
                "status": "error",
                "error": "token_missing",
                "message": "Notion API トークンが設定されていません",
                "timestamp": datetime.now().isoformat()
            }

        # トークンの最初の8文字だけ表示（セキュリティのため）
        masked_token = f"{notion_token[:8]}..." if len(notion_token) > 8 else "***"
        logger.info(f"Notion Token を使用してAPI接続テストを実行: {masked_token}")

        # Notion API設定
        api_url = "https://api.notion.com/v1/users"
        headers = {
            "Authorization": f"Bearer {notion_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

        # APIリクエストを送信
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(api_url, headers=headers)
            
            logger.info(f"Notion API レスポンス: ステータス={response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                user_count = len(data.get("results", []))
                
                logger.info(f"✅ Notion API トークンが有効です。ユーザー数: {user_count}")
                
                return {
                    "status": "valid",
                    "message": "Notion API トークンは有効です",
                    "token_source": "environment" if os.getenv('NOTION_TOKEN') else "secret_manager",
                    "token_preview": masked_token,
                    "user_count": user_count,
                    "timestamp": datetime.now().isoformat(),
                    "api_response": {
                        "status_code": response.status_code,
                        "user_count": user_count,
                        "has_more": data.get("has_more", False)
                    }
                }
                
            elif response.status_code == 401:
                logger.error("❌ Notion API トークンが無効です（認証エラー）")
                return {
                    "status": "invalid",
                    "error": "unauthorized",
                    "message": "Notion API トークンが無効または期限切れです",
                    "token_preview": masked_token,
                    "status_code": 401,
                    "timestamp": datetime.now().isoformat()
                }
                
            elif response.status_code == 403:
                logger.error("❌ Notion API へのアクセス権限がありません")
                return {
                    "status": "invalid", 
                    "error": "forbidden",
                    "message": "Notion API へのアクセス権限がありません",
                    "token_preview": masked_token,
                    "status_code": 403,
                    "timestamp": datetime.now().isoformat()
                }
                
            else:
                logger.error(f"❌ Notion API から予期しないレスポンス: {response.status_code}")
                return {
                    "status": "error",
                    "error": "api_error",
                    "message": f"Notion API エラー: {response.status_code}",
                    "token_preview": masked_token,
                    "status_code": response.status_code,
                    "timestamp": datetime.now().isoformat()
                }

    except httpx.TimeoutException:
        logger.error("❌ Notion API への接続がタイムアウトしました")
        return {
            "status": "error",
            "error": "timeout",
            "message": "Notion API への接続がタイムアウトしました（10秒）",
            "timestamp": datetime.now().isoformat()
        }
        
    except httpx.RequestError as e:
        logger.error(f"❌ Notion API への接続中にネットワークエラーが発生: {e}")
        return {
            "status": "error",
            "error": "network_error",
            "message": f"ネットワークエラー: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Notion API 検証中に予期しないエラーが発生: {e}")
        return {
            "status": "error",
            "error": "unexpected_error",
            "message": f"予期しないエラー: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

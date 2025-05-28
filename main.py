import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from linebot.v3 import WebhookParser
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    MessagingApiBlob,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import (
    ImageMessageContent,
    MessageEvent,
    TextMessageContent,
)

from src.services.agent_service import call_agent_async  # 新しい関数
from src.services.agent_service import (
    call_agent_with_image_async,
    cleanup_resources,
    init_agent,
)
from src.utils.logger import setup_logger

# ロガーのセットアップ
logger = setup_logger("main")

# スレッドプールの作成
executor = ThreadPoolExecutor(max_workers=15, thread_name_prefix="LineEvent")


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


# .envファイルから環境変数を読み込み
load_dotenv()

# LINE API設定
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("LINE_CHANNEL_SECRET")

if not channel_access_token or not channel_secret:
    raise ValueError(
        (
            "LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET "
            "must be set in environment variables"
        )
    )

configuration = Configuration(access_token=channel_access_token)
parser = WebhookParser(channel_secret)


def process_events(body: str, signature: str):
    """LINE から届いたイベントをまとめて処理（スレッド内で実行）"""
    logger.info("Processing LINE events in background thread")
    try:
        events = parser.parse(body, signature)
    except Exception as e:
        logger.exception(f"Failed to parse events: {e}")
        return

    # Blocking I/O（Messaging API 呼び出し）用クライアント
    with ApiClient(configuration) as api_client:
        logger.info("Creating LINE API client")
        line_api = MessagingApi(api_client)

        for ev in events:
            if isinstance(ev, MessageEvent):
                try:
                    user_id = ev.source.user_id
                    reply_token = ev.reply_token

                    # テキストメッセージの処理
                    if isinstance(ev.message, TextMessageContent):
                        logger.info(
                            f"Received text message: {ev.message.text}"
                        )
                        reply_text = asyncio.run(
                            call_agent_async(
                                ev.message.text,
                                user_id=user_id,
                            )
                        )
                        reply_text = reply_text.rstrip("\n")
                        logger.info(f"Replying with: {reply_text}")

                        line_api.reply_message(
                            ReplyMessageRequest(
                                reply_token=reply_token,
                                messages=[TextMessage(text=reply_text)],
                            )
                        )

                    # 画像メッセージの処理
                    elif isinstance(ev.message, ImageMessageContent):
                        logger.info(f"Received image message: {ev.message.id}")

                        # 画像データを取得（正しいAPI使用方法）
                        with ApiClient(configuration) as blob_api_client:
                            blob_api = MessagingApiBlob(blob_api_client)
                            image_content = blob_api.get_message_content(
                                ev.message.id
                            )

                        # デフォルトメッセージ（画像のみの場合）
                        default_message = "この画像からレシピを抽出してNotionに登録してください"

                        # 画像対応エージェントを呼び出し
                        reply_text = asyncio.run(
                            call_agent_with_image_async(
                                message=default_message,
                                image_data=image_content,
                                image_mime_type="image/jpeg",  # LINEは通常JPEG
                                user_id=user_id,
                            )
                        )
                        reply_text = reply_text.rstrip("\n")
                        logger.info(f"Replying with: {reply_text}")

                        line_api.reply_message(
                            ReplyMessageRequest(
                                reply_token=reply_token,
                                messages=[TextMessage(text=reply_text)],
                            )
                        )

                    else:
                        logger.info(
                            f"Unsupported message type: {type(ev.message)}"
                        )

                except Exception as e:
                    logger.exception(f"Error while handling event: {e}")

                    # エラー時もユーザーに応答
                    try:
                        error_message = (
                            "申し訳ございません。処理中にエラーが発生しました。"
                            "しばらく時間をおいてから再試行してください。"
                        )
                        line_api.reply_message(
                            ReplyMessageRequest(
                                reply_token=ev.reply_token,
                                messages=[TextMessage(text=error_message)],
                            )
                        )
                    except Exception as reply_error:
                        logger.exception(
                            f"Failed to send error message: {reply_error}"
                        )


@app.post("/callback")
async def callback(request: Request):
    # X-Line-Signatureヘッダー値を取得
    signature = request.headers.get("X-Line-Signature", "")

    # リクエストボディをテキストとして取得
    body = await request.body()
    body_text = body.decode("utf-8")
    logger.info(f"Request body: {body_text}")

    # 非同期でWebhookボディを処理
    executor.submit(process_events, body_text, signature)

    return "OK"


# ヘルスチェック用
@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

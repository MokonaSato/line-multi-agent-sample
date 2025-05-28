import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from linebot.v3 import WebhookParser
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import (
    ImageMessageContent,
    MessageEvent,
    TextMessageContent,
)

from src.services.agent_service import (
    call_agent_with_image_async,
)  # 新しい関数
from src.services.agent_service import (
    call_agent_async,
    cleanup_resources,
    init_agent,
)
from src.utils.logger import setup_logger

# ロガーのセットアップ
logger = setup_logger("main")

app = FastAPI()

# スレッドプールの作成
executor = ThreadPoolExecutor(max_workers=15, thread_name_prefix="LineEvent")


# アプリケーション起動時にエージェントを初期化
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing agent on application startup")
    try:
        await init_agent()
        logger.info("Agent initialization completed")
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        raise


# アプリケーション終了時にリソースをクリーンアップ
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Cleaning up resources on application shutdown")
    try:
        await cleanup_resources()
        logger.info("Agent resources cleanup completed")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

    executor.shutdown(wait=True)
    logger.info("Thread pool executor shutdown completed")


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

                        # 画像データを取得
                        image_content = line_api.get_message_content(
                            ev.message.id
                        )
                        image_data = image_content.read()

                        # デフォルトメッセージ（画像のみの場合）
                        default_message = "この画像からレシピを抽出してNotionに登録してください"

                        # 画像対応エージェントを呼び出し
                        reply_text = asyncio.run(
                            call_agent_with_image_async(
                                message=default_message,
                                image_data=image_data,
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

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
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from src.services.agent_service import call_agent_async
from src.utils.logger import setup_logger

# ロガーのセットアップ
logger = setup_logger("main")

app = FastAPI()

# スレッドプールの作成
executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="LineEvent")


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
# handler = WebhookHandler(channel_secret)
parser = WebhookParser(channel_secret)


# @handler.add(MessageEvent, message=TextMessageContent)
# def handle_message(event):
#     response = event.message.text
#     with ApiClient(configuration) as api_client:
#         line_bot_api = MessagingApi(api_client)
#         line_bot_api.reply_message_with_http_info(
#             ReplyMessageRequest(
#                 reply_token=event.reply_token,
#                 messages=[TextMessage(text=response)],
#             )
#         )


# def process_line_events(body_text, signature):
#     """LINEイベントを処理する関数"""
#     try:
#         logger.info("Processing LINE events in background thread")
#         handler.handle(body_text, signature)
#         logger.info("LINE events processed successfully")
#     except InvalidSignatureError:
#         logger.error("Invalid signature error")
#     except Exception as e:
#         logger.error(f"Error while processing LINE events: {e}")


def process_events(body: str, signature: str):
    """LINE から届いたイベントをまとめて処理（スレッド内で実行）"""
    logger.info("Processing LINE events in background thread")
    try:
        events = parser.parse(
            body, signature
        )  # 署名検証＆パース（★公式そのまま）
    except Exception as e:
        logger.exception(f"Failed to parse events: {e}")
        return

    # Blocking I/O（Messaging API 呼び出し）用クライアント
    with ApiClient(configuration) as api_client:
        logger.info("Creating LINE API client")
        line_api = MessagingApi(api_client)

        for ev in events:
            # テキストメッセージのみ対象
            if isinstance(ev, MessageEvent) and isinstance(
                ev.message, TextMessageContent
            ):
                try:
                    logger.info(f"Received message: {ev.message.text}")
                    # 1) AI エージェント呼び出し（async → sync）
                    reply_text = asyncio.run(
                        call_agent_async(
                            ev.message.text,
                            user_id=ev.source.user_id,
                        )
                    )  # ★変更点
                    logger.info(f"Replying with: {reply_text}")
                    # 2) LINE に返信（同期 HTTP）
                    line_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=ev.reply_token,
                            messages=[TextMessage(text=reply_text)],
                        )
                    )
                except Exception as e:
                    logger.exception(f"Error while handling event: {e}")


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

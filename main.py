import os
from concurrent.futures import ThreadPoolExecutor

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
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
handler = WebhookHandler(channel_secret)


async def process_message(event):
    """メッセージを処理し、エージェントからの応答を返す"""
    try:
        user_id = event.source.user_id
        query = event.message.text
        logger.info(f"ユーザー {user_id} からのメッセージ: {query}")

        # エージェントを呼び出して応答を取得
        response = await call_agent_async(query=query, user_id=user_id)
        logger.info(f"エージェントからの応答: {response}")

        # LINEに応答を返信
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=response)],
                )
            )
    except Exception as e:
        logger.error(f"メッセージ処理中にエラーが発生しました: {e}")
        # エラー時のフォールバック応答
        try:
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            TextMessage(
                                text="申し訳ありません、エラーが発生しました。"
                            )
                        ],
                    )
                )
        except Exception as reply_error:
            logger.error(f"エラー応答の送信に失敗しました: {reply_error}")


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    try:
        # 非同期処理を実行するためのヘルパー関数
        executor.submit(process_message, event)
    except Exception as e:
        logger.error(f"メッセージ処理でエラーが発生しました: {e}")


def process_line_events(body_text, signature):
    """LINEイベントを処理する関数"""
    try:
        logger.info("Processing LINE events in background thread")
        handler.handle(body_text, signature)
        logger.info("LINE events processed successfully")
    except InvalidSignatureError:
        logger.error("Invalid signature error")
    except Exception as e:
        logger.error(f"Error while processing LINE events: {e}")


@app.post("/callback")
async def callback(request: Request):
    # X-Line-Signatureヘッダー値を取得
    signature = request.headers.get("X-Line-Signature", "")

    # リクエストボディをテキストとして取得
    body = await request.body()
    body_text = body.decode("utf-8")
    logger.info(f"Request body: {body_text}")

    # 非同期でWebhookボディを処理
    executor.submit(process_line_events, body_text, signature)

    return "OK"


# ヘルスチェック用
@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

from concurrent.futures import ThreadPoolExecutor

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
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

from src.utils.logger import setup_logger

# ロガーのセットアップ
logger = setup_logger("main")

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LINE API設定
configuration = Configuration(access_token="YOUR_CHANNEL_ACCESS_TOKEN")
handler = WebhookHandler("YOUR_CHANNEL_SECRET")


# executor = ThreadPoolExecutor(thread_name_prefix="LineEvent")


# def process_events(data, signature):
#     events = line_parser.parse(data, signature)
#     for ev in events:
#         line_api.reply_message(
#             ev.reply_token,
#             TextMessage(text=f"You said: {ev.message.text}"),
#         )

# @app.handler("/callback", methods=["POST"])
# def handle_webhook():
#     executor.submit(
#         process_events,
#         request.body.decode("utf-8"),
#         request.headers.get("X-Line-Signature", ""),
#     )


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=event.message.text)],
            )
        )


@app.post("/callback")
async def callback(request: Request):
    # X-Line-Signatureヘッダー値を取得
    signature = request.headers.get("X-Line-Signature", "")

    # リクエストボディをテキストとして取得
    body = await request.body()  # awaitを追加
    body_text = body.decode("utf-8")
    logger.info(f"Request body: {body_text}")

    # Webhookボディを処理
    try:
        handler.handle(body_text, signature)  # body_textを渡す
    except InvalidSignatureError:
        raise HTTPException(400)  # raiseを追加

    return "OK"


# ヘルスチェック用
@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

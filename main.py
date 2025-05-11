import asyncio
import os

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
# from mistralai.async_client import MistralAsyncClient as MistralClient
from mistralai.client import MistralClient
from notion_client import Client
from pydantic import BaseModel, HttpUrl

from config import (
    LINE_CHANNEL_ACCESS_TOKEN,
    LINE_CHANNEL_SECRET,
    MISTRAL_API_KEY,
    NOTION_DATABASE_ID,
    NOTION_TOKEN,
)
from utils.process_pdf import process_pdf_url

# FastAPIアプリケーション
app = FastAPI(
    title="論文処理ボット",
    description="論文PDFをOCR、翻訳し、Notionに保存するBotのAPI",
)

# CORSミドルウェア設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydanticモデル
class PDFProcessRequest(BaseModel):
    pdf_url: HttpUrl
    title: str = "無題の論文"


class ProcessResponse(BaseModel):
    status: str
    message: str


# クライアント初期化
mistral_client = MistralClient(api_key=MISTRAL_API_KEY)
notion_client = Client(auth=NOTION_TOKEN)

# LINE Bot APIクライアント
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
webhook_handler = WebhookHandler(LINE_CHANNEL_SECRET)


# APIエンドポイントやWebhook処理をここに記述
# LINE Bot Webhook処理
@app.post("/callback")
async def line_callback(request: Request, background_tasks: BackgroundTasks):
    # X-Line-Signature ヘッダーの取得
    signature = request.headers.get("X-Line-Signature", "")

    # リクエストボディの取得
    body = await request.body()
    body_text = body.decode("utf-8")

    try:
        # webhookの検証
        webhook_handler.handle(body_text, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return {"status": "success"}


# LINEメッセージ受信時の処理
@webhook_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text

    # URLチェック
    if text.startswith("http") and (".pdf" in text.lower()):
        # 処理開始メッセージを送信
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="論文PDFの処理を開始します。処理が完了したらお知らせします。"
            ),
        )

        # バックグラウンドで処理
        asyncio.create_task(process_pdf_and_notify(text, event.source.user_id))
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="論文のPDF URLを送信してください。"),
        )


# 非同期処理と通知
async def process_pdf_and_notify(pdf_url: str, user_id: str):
    result = await process_pdf_url(
        mistral_client=mistral_client,
        notion_client=notion_client,
        notion_database_id=NOTION_DATABASE_ID,
        pdf_url=pdf_url,
    )

    # 処理結果をLINEに通知
    if result["status"] == "success":
        message = f"論文PDFの処理が完了しました。\nNotion URL: {result['notion_url']}"
    else:
        message = f"処理中にエラーが発生しました: {result['message']}"

    line_bot_api.push_message(user_id, TextSendMessage(text=message))


# バックグラウンドタスク関数
async def process_pdf_task(pdf_url: str, title: str = "無題の論文"):
    try:
        await process_pdf_url(
            mistral_client=mistral_client,
            notion_client=notion_client,
            notion_database_id=NOTION_DATABASE_ID,
            pdf_url=pdf_url,
            title=title,
        )
    except Exception as e:
        print(f"PDF処理中にエラーが発生しました: {str(e)}")


# APIエンドポイント - 直接PDFを処理
@app.post("/process_pdf", response_model=ProcessResponse)
async def api_process_pdf(
    request: PDFProcessRequest, background_tasks: BackgroundTasks
):
    # バックグラウンドで処理
    background_tasks.add_task(process_pdf_task, request.pdf_url, request.title)

    return {
        "status": "processing",
        "message": "PDFの処理を開始しました。処理が完了するとNotionにデータが保存されます。",
    }


# 健全性チェックエンドポイント
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# アプリケーション起動設定
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        reload=True,
    )

import asyncio
import logging
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

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


# デバッグヘルパー関数
def debug_url_check(url):
    """URLがPDFかどうかをチェックし、詳細な診断結果を返す"""
    result = {
        "url": url,
        "starts_with_http": url.startswith("http"),
        "contains_pdf": ".pdf" in url.lower(),
        "is_valid_pdf_url": url.startswith("http") and ".pdf" in url.lower(),
        "lower_url": url.lower(),
    }
    logger.info(f"URL診断結果: {result}")
    return result


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
    logger.info(f"受信したメッセージ: {text}")

    # URLの詳細診断
    diagnosis = debug_url_check(text)

    # URLチェック
    if diagnosis["is_valid_pdf_url"]:
        logger.info(f"PDFのURLを検出: {text}")
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
        logger.info(f"PDFのURLではないと判断: {diagnosis}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=f"論文のPDF URLを送信してください。\n診断結果: {diagnosis}"
            ),
        )


# 非同期処理と通知
async def process_pdf_and_notify(pdf_url: str, user_id: str):
    try:
        logger.info(f"PDFの処理を開始: {pdf_url}")
        result = await process_pdf_url(
            mistral_client=mistral_client,
            notion_client=notion_client,
            notion_database_id=NOTION_DATABASE_ID,
            pdf_url=pdf_url,
        )

        logger.info(f"PDFの処理結果: {result}")

        # 処理結果をLINEに通知
        if result["status"] == "success":
            message = f"論文PDFの処理が完了しました。\nNotion URL: {result['notion_url']}"
        else:
            message = f"処理中にエラーが発生しました: {result['message']}"

        line_bot_api.push_message(user_id, TextSendMessage(text=message))
    except Exception as e:
        error_msg = f"PDF処理中に例外が発生: {str(e)}"
        logger.error(error_msg)
        line_bot_api.push_message(user_id, TextSendMessage(text=error_msg))


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


# テスト用エンドポイント
@app.get("/test_pdf_url")
async def test_pdf_url(url: str):
    """PDFのURL判定ロジックをテストするためのエンドポイント"""
    diagnosis = debug_url_check(url)

    if diagnosis["is_valid_pdf_url"]:
        return {
            "result": "valid_pdf_url",
            "diagnosis": diagnosis,
            "message": "PDFのURLとして有効です",
        }
    else:
        return {
            "result": "invalid_pdf_url",
            "diagnosis": diagnosis,
            "message": "PDFのURLとして無効です",
        }


# テスト用エンドポイント - 実際のPDF処理をテスト
@app.get("/test_process_pdf")
async def test_process_pdf(url: str):
    """PDF処理ロジックをテストするためのエンドポイント"""
    try:
        logger.info(f"テスト: PDFの処理を開始 {url}")
        result = await process_pdf_url(
            mistral_client=mistral_client,
            notion_client=notion_client,
            notion_database_id=NOTION_DATABASE_ID,
            pdf_url=url,
        )
        logger.info(f"テスト: PDFの処理結果 {result}")
        return {"status": "success", "result": result}
    except Exception as e:
        error_msg = f"テスト: PDF処理中にエラー {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}


# アプリケーション起動設定
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        reload=True,
    )

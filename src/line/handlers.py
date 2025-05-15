from fastapi import FastAPI, HTTPException, Request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from src.services.agent_service import call_agent_async


def setup_line_handlers(
    app: FastAPI, line_bot_api: LineBotApi, handler: WebhookHandler
):
    """LINEメッセージハンドラーを設定"""

    @app.post("/callback")
    async def callback(request: Request):
        signature = request.headers.get("X-Line-Signature", "")
        body = await request.body()
        body = body.decode("utf-8")

        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            raise HTTPException(status_code=400, detail="Invalid signature")

        return "OK"

    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        text = event.message.text

        try:
            # Google ADKを使って応答を生成
            # 注意: call_agent_asyncはasync関数なのでawaitが必要
            import asyncio

            response = asyncio.run(
                call_agent_async(
                    query=text,
                    user_id=event.source.user_id,
                )
            )

            # responseは文字列なのでそのまま使用
            reply_message = response

        except Exception as e:
            import traceback

            error_details = traceback.format_exc()
            print(f"エラー詳細: {error_details}")
            reply_message = f"エラーが発生しました: {str(e)}"

        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=reply_message)
        )

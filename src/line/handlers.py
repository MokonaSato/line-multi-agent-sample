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
            response = call_agent_async(
                query=text,
                user_id=event.source.user_id,
            )

            # エージェントからの応答をチェック
            if hasattr(response, "text"):
                reply_message = response.text
            else:
                reply_message = (
                    "2つの数字をスペース区切りで送信してください。例: 10 20"
                )

        except Exception as e:
            reply_message = f"エラーが発生しました: {str(e)}"

        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=reply_message)
        )

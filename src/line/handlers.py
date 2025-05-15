import traceback

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from src.services.agent_service import call_agent_async
from src.utils.logger import setup_logger

logger = setup_logger("line_handlers")


def setup_line_handlers(
    app: FastAPI, line_bot_api: LineBotApi, handler: WebhookHandler
):
    """LINEメッセージハンドラーを設定"""

    async def process_line_message(text: str, user_id: str, reply_token: str):
        """バックグラウンドで実行される非同期処理"""
        try:
            response = await call_agent_async(query=text, user_id=user_id)
            line_bot_api.reply_message(
                reply_token, TextSendMessage(text=response)
            )
        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f"エラー詳細: {error_details}")
            error_message = f"エラーが発生しました: {str(e)}"
            line_bot_api.reply_message(
                reply_token, TextSendMessage(text=error_message)
            )

    @app.post("/callback")
    async def callback(request: Request, background_tasks: BackgroundTasks):
        signature = request.headers.get("X-Line-Signature", "")
        body = await request.body()
        body_text = body.decode("utf-8")

        try:
            events = handler.parse(body_text, signature)

            # イベントを処理
            for event in events:
                if isinstance(event, MessageEvent) and isinstance(
                    event.message, TextMessage
                ):
                    # バックグラウンドタスクとして処理を実行
                    background_tasks.add_task(
                        process_line_message,
                        text=event.message.text,
                        user_id=event.source.user_id,
                        reply_token=event.reply_token,
                    )

            return "OK"
        except InvalidSignatureError:
            raise HTTPException(status_code=400, detail="Invalid signature")

    # この関数はもう必要ありません
    # @handler.add(MessageEvent, message=TextMessage)
    # def handle_message(event):
    #     """LINEメッセージイベントハンドラ"""
    #     # 処理をバックグラウンドタスクとして実行
    #     app.state.background_tasks.add_task(
    #         process_line_message,
    #         text=event.message.text,
    #         user_id=event.source.user_id,
    #         reply_token=event.reply_token,
    #     )

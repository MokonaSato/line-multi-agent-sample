from fastapi import BackgroundTasks, FastAPI, Request
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextMessage

# from src.services.agent_service import call_agent_async
from src.utils.logger import setup_logger

logger = setup_logger("line_handlers")


def setup_line_handlers(
    app: FastAPI, line_bot_api: LineBotApi, handler: WebhookHandler
):
    async def handle_events(events):
        for ev in events:
            try:
                await line_bot_api.reply_message_async(
                    ev.reply_token,
                    TextMessage(text=f"You said: {ev.message.text}"),
                )
            except Exception:
                # エラーログ書いたりする
                pass

    @app.post("/messaging_api/handle_request")
    async def handle_request(
        request: Request, background_tasks: BackgroundTasks
    ):  # 🌟background_tasksを追加
        # リクエストをパースしてイベントを取得（署名の検証あり）
        events = handler.parse(
            (await request.body()).decode("utf-8"),
            request.headers.get("X-Line-Signature", ""),
        )

        # 🌟イベント処理をバックグラウンドタスクに渡す
        background_tasks.add_task(handle_events, events=events)

        # LINEサーバへHTTP応答を返す
        return "ok"

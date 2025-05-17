from aiolinebot import AioLineBotApi
from fastapi import (
    BackgroundTasks,
    FastAPI,
    Request,
)  # 🌟BackgroundTasksを追加
from linebot import WebhookParser
from linebot.models import TextMessage

# APIクライアントとパーサーをインスタンス化
line_api = AioLineBotApi(channel_access_token="<YOUR CHANNEL ACCESS TOKEN>")
parser = WebhookParser(channel_secret="<YOUR CHANNEL SECRET>")

# FastAPIの起動
app = FastAPI()


# 🌟イベント処理（新規追加）
async def handle_events(events):
    for ev in events:
        try:
            await line_api.reply_message_async(
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
    events = parser.parse(
        (await request.body()).decode("utf-8"),
        request.headers.get("X-Line-Signature", ""),
    )

    # 🌟イベント処理をバックグラウンドタスクに渡す
    background_tasks.add_task(handle_events, events=events)

    # LINEサーバへHTTP応答を返す
    return "ok"

import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from src.agents.calc_agent import calculator_agent

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LINE Botの設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# セッションサービスの設定
session_service = InMemorySessionService()

# アプリケーション名の定義
APP_NAME = "calculator_app"

# Runnerの設定
runner = Runner(
    agent=calculator_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


async def call_agent_async(query: str, user_id: str):
    """エージェントにクエリを送信し、レスポンスを返す"""

    # セッションIDをユーザーIDから生成（簡易的な実装）
    session_id = f"session_{user_id}"

    # セッションが存在しない場合は作成
    if not session_service.get_session(APP_NAME, user_id, session_id):
        session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )

    # ユーザーメッセージをADK形式に変換
    content = types.Content(role="user", parts=[types.Part(text=query)])

    final_response_text = "エージェントからの応答がありませんでした。"

    # エージェントを実行して最終的な応答を取得
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate:
                final_response_text = (
                    f"エラーが発生しました: "
                    f"{event.error_message or '詳細不明'}"
                )
            break

    return final_response_text


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


# ヘルスチェック用
@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

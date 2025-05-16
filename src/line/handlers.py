import asyncio

from fastapi import FastAPI, HTTPException, Request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from src.services.agent_service import call_agent_async
from src.utils.logger import setup_logger

logger = setup_logger("line_handlers")

# ユーザーごとの会話管理用ディクショナリ
user_conversations = {}


def setup_line_handlers(
    app: FastAPI, line_bot_api: LineBotApi, handler: WebhookHandler
):
    @app.post("/callback")  # メソッドをデコレータで指定
    async def callback(request: Request):
        # LINE Messaging APIからのWebhook検証
        signature = request.headers.get("X-Line-Signature", "")
        body = await request.body()  # FastAPIではasync/awaitでbodyを取得
        body_text = body.decode("utf-8")  # バイトをテキストに変換

        try:
            handler.handle(body_text, signature)
        except InvalidSignatureError:
            raise HTTPException(status_code=400, detail="Invalid signature")

        return "OK"

    @handler.add(MessageEvent, message=TextMessage)
    def handle_text_message(event):
        user_id = event.source.user_id
        text = event.message.text

        # 非同期処理を同期的に実行するための関数
        def get_agent_response(user_id, text):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # ユーザーごとに会話履歴を管理
            if user_id not in user_conversations:
                user_conversations[user_id] = []

            # ユーザーのメッセージを会話履歴に追加
            user_conversations[user_id].append(
                {"role": "user", "content": text}
            )

            # エージェントからの応答を取得（会話履歴を含めて）
            response = loop.run_until_complete(
                call_agent_async(query=text, user_id=user_id)
            )

            # エージェントの応答を会話履歴に追加
            user_conversations[user_id].append(
                {"role": "assistant", "content": response.message.content}
            )

            loop.close()
            return response.message.content

        try:
            # エージェントの応答を取得
            response_text = get_agent_response(user_id, text)

            # LINE Botからの応答を送信
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=response_text)
            )
        except Exception as e:
            # エラー処理
            print(f"エラーが発生しました: {str(e)}")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=(
                        "申し訳ありません、エラーが発生しました。"
                        "しばらく経ってからもう一度お試しください。"
                    )
                ),
            )

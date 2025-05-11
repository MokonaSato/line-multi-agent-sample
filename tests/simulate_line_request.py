import asyncio
import uuid
from datetime import datetime
from unittest.mock import MagicMock

# 修正: 正しいインポートパスを使用
from linebot.models import SourceUser  # UserSourceの代わりにSourceUserを使用
from linebot.models import MessageEvent, TextMessage


async def simulate_pdf_processing():
    """PDFリンクメッセージの処理をシミュレーション"""
    pdf_url = "https://arxiv.org/pdf/2303.08774.pdf"  # テスト用PDFリンク

    # LINEボットAPIのモック
    line_bot_api = MagicMock()
    line_bot_api.reply_message = MagicMock()
    line_bot_api.push_message = MagicMock()

    # メッセージハンドラモック（mainモジュールをインポートせずにテスト）
    messages = []

    def mock_handle_message(event):
        print(f"メッセージ受信: {event.message.text}")

        if (
            event.message.text.startswith("http")
            and ".pdf" in event.message.text
        ):
            # 処理開始メッセージを記録
            start_message = (
                "論文PDFの処理を開始します。処理が完了したらお知らせします。"
            )
            messages.append(("reply", start_message))

            # 処理完了メッセージを記録（実際の処理はモック）
            complete_message = (
                "論文PDFの処理が完了しました。\n"
                "Notion URL: https://notion.so/test-id"
            )
            messages.append(("push", complete_message))
        else:
            # PDF URLでない場合
            messages.append(("reply", "論文のPDF URLを送信してください。"))

    # イベント生成（SourceUserを使用）
    event = MessageEvent(
        message=TextMessage(id="12345", text=pdf_url),
        reply_token=str(uuid.uuid4()),
        source=SourceUser(user_id="test_user"),  # 修正
        timestamp=int(datetime.now().timestamp() * 1000),
    )

    # メッセージハンドラを直接呼び出し
    mock_handle_message(event)

    # 処理結果を表示
    return messages


if __name__ == "__main__":
    print("LINEボットのメッセージ処理をシミュレーションしています...")
    messages = asyncio.run(simulate_pdf_processing())

    print("\n--- シミュレーション結果 ---")
    for msg_type, text in messages:
        print(f"{msg_type}: {text}")

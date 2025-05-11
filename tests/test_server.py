"""
LINE Botのテスト手順:
1. ngrokをインストール: `brew install ngrok` または https://ngrok.com/download
2. ngrokでローカルサーバーを公開: `ngrok http 8080`
3. LINE Developer Consoleで得られたngrokのURLをWebhook URLとして設定
4. このスクリプトを実行してローカルサーバーを起動
5. LINEアプリからボットにメッセージを送信してテスト
"""

import os
import sys

import uvicorn

from main import app

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


if __name__ == "__main__":
    print("LINEボットのローカルテストサーバーを起動しています...")
    print(
        "ngrokが実行中であることを確認し、Webhook URLが設定されていることを確認してください。"
    )
    uvicorn.run(app, host="0.0.0.0", port=8080)

import os

from dotenv import load_dotenv

# 環境変数を1回だけ読み込む
load_dotenv()

# よく使う環境変数を定数として定義
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")

# 環境変数が設定されているか確認
if not GOOGLE_API_KEY:
    print("Warning: GOOGLE_API_KEY environment variable is not set")

if not NOTION_TOKEN:
    print("Warning: NOTION_TOKEN environment variable is not set")

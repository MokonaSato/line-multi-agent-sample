import os

from dotenv import load_dotenv

# 環境変数を1回だけ読み込む
load_dotenv()

# よく使う環境変数を定数として定義
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")

# MCP Server関連の環境変数
FILESYSTEM_MCP_URL = os.getenv(
    "FILESYSTEM_MCP_URL", "http://localhost:8000/sse"
)
NOTION_MCP_URL = os.getenv("NOTION_MCP_URL", "http://localhost:3001/sse")
FILESYSTEM_HTTP_URL = os.getenv("FILESYSTEM_HTTP_URL", "http://localhost:8000")
NOTION_HTTP_URL = os.getenv("NOTION_HTTP_URL", "http://localhost:3001")

# MCP機能の有効/無効設定
MCP_ENABLED = os.getenv("MCP_ENABLED", "true").lower() == "true"
MCP_TIMEOUT_SECONDS = int(os.getenv("MCP_TIMEOUT_SECONDS", "10"))

# 環境変数が設定されているか確認
if not GOOGLE_API_KEY:
    print("Warning: GOOGLE_API_KEY environment variable is not set")

if not NOTION_TOKEN:
    print("ERROR: NOTION_TOKEN environment variable is not set")
    print("Notion機能が正常に動作しません。")
    print(".env ファイルに以下の形式でNOTION_TOKENを設定してください:")
    print("NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxx")

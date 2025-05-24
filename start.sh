#!/bin/bash
echo "Starting Notion MCP Server..."

# notion-mcp-serverのセットアップと実行
cd ./notion-mcp-server
npm install
npm run build

# ディレクトリ構造を確認
echo "Checking directory structure..."
ls -la
echo "Checking src directory..."
ls -la src 2>/dev/null || echo "src directory not found"
echo "Checking dist directory..."
ls -la dist 2>/dev/null || echo "dist directory not found"
echo "Checking build directory..."
ls -la build 2>/dev/null || echo "build directory not found"

# 複数の方法を試す
echo "Attempting to start Notion MCP Server..."
if [ -f ./dist/index.js ]; then
  echo "Starting from dist/index.js"
  node ./dist/index.js &
elif [ -f ./build/index.js ]; then
  echo "Starting from build/index.js"
  node ./build/index.js &
elif [ -f ./src/index.js ]; then
  echo "Starting from src/index.js"
  node ./src/index.js &
else
  echo "Falling back to npx approach"
  npm link
  npx -y @notionhq/notion-mcp-server &
fi

NOTION_SERVER_PID=$!
echo "Notion MCP Server started with PID: $NOTION_SERVER_PID"

# メインアプリケーションの実行
cd ..
echo "Starting main application..."
uvicorn main:app --host 0.0.0.0 --port 8080

# 終了時にバックグラウンドプロセスも終了させる
if ps -p $NOTION_SERVER_PID > /dev/null; then
  echo "Shutting down Notion MCP Server (PID: $NOTION_SERVER_PID)..."
  kill $NOTION_SERVER_PID
fi
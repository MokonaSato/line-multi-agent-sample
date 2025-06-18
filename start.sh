#!/bin/bash

# MCP サーバーの起動を待機する関数
wait_for_mcp_servers() {
    echo "⏳ Waiting for MCP servers to be ready..."
    
    # Filesystem MCP Server (port 8000)
    for i in {1..30}; do
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            echo "✅ Filesystem MCP Server is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "⚠️  Filesystem MCP Server not ready after 30 attempts, proceeding anyway"
        fi
        sleep 1
    done
    
    # Notion MCP Server (port 3001)
    for i in {1..30}; do
        if curl -f http://localhost:3001/health >/dev/null 2>&1; then
            echo "✅ Notion MCP Server is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "⚠️  Notion MCP Server not ready after 30 attempts, proceeding anyway"
        fi
        sleep 1
    done
    
    echo "🚀 Starting main application..."
}

# MCP_ENABLED が true の場合のみ待機
if [ "$MCP_ENABLED" = "true" ]; then
    wait_for_mcp_servers
else
    echo "📝 MCP disabled, starting application directly"
fi

# メインアプリケーションの起動
exec uvicorn main:app --host 0.0.0.0 --port $PORT

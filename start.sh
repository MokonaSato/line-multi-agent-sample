#!/usr/bin/env bash
# MCP server (stdio モード) をバックグラウンド起動
npx -y notion-mcp-server --mode mcp --stdio &
P1=$!

# Python LINE Bot (FastAPI + Uvicorn)
uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 1 &
P2=$!

# どちらかが落ちたら全体を終了
wait $P1 $P2
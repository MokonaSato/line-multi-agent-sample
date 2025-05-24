npx -y --prefix /app/notion-mcp-server @notionhq/notion-mcp-server

exec uvicorn main:app --host 0.0.0.0 --port 8080
FROM python:3.12-slim

WORKDIR /app

# Node.jsとnpmをインストール（npxを含む）+ git
RUN apt-get update && \
  apt-get install -y curl git && \
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
  apt-get install -y nodejs && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

# Notion MCP Serverのソースコードをコピー（事前にローカルでcloneしておく）
COPY ./notion-mcp-server /app/notion-mcp-server

# Notion MCP Serverの依存関係をインストール
WORKDIR /app/notion-mcp-server
RUN npm install && npm run build

# メインアプリケーションのディレクトリに戻る
WORKDIR /app

# 依存関係ファイルをコピー
COPY requirements.txt pyproject.toml ./
COPY uv.lock ./

# Python依存関係のインストール
RUN pip install --no-cache-dir --upgrade pip && \
  pip install --no-cache-dir -r requirements.txt

# アプリケーションのコードをコピー
COPY . .

COPY ./start.sh ./
RUN chmod +x ./start.sh

ENV PORT=8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
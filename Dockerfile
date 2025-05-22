FROM python:3.12-slim

WORKDIR /app

# Node.jsとnpmをインストール（npxを含む）
RUN apt-get update && \
  apt-get install -y curl && \
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
  apt-get install -y nodejs && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

# 依存関係ファイルをコピー
COPY requirements.txt pyproject.toml ./
COPY uv.lock ./

# 依存関係のインストール
RUN pip install --no-cache-dir --upgrade pip && \
  pip install --no-cache-dir -r requirements.txt


# Node deps（Notion MCP）
RUN npm install -g @notionhq/notion-mcp-server

# アプリケーションのコードをコピー
COPY . .

COPY ./start.sh ./
RUN chmod +x ./start.sh

ENV PORT=8080
CMD ["./start.sh"]
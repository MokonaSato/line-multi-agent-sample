FROM python:3.12-slim

WORKDIR /app

# Node.jsとnpmをインストール（npxを含む）+ git
RUN apt-get update && \
  apt-get install -y curl git && \
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
  apt-get install -y nodejs && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

# 依存関係ファイルをコピー
COPY requirements.txt pyproject.toml ./
COPY uv.lock ./

# Python依存関係のインストール
RUN pip install --no-cache-dir --upgrade pip && \
  pip install --no-cache-dir -r requirements.txt

# アプリケーションのコードをコピー
COPY . .

ENV PORT=8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
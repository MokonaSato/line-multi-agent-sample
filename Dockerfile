FROM python:3.12-slim

WORKDIR /app

# 依存関係ファイルをコピー
COPY requirements.txt pyproject.toml ./
COPY uv.lock ./

# 依存関係のインストール
RUN pip install --no-cache-dir --upgrade pip && \
  pip install --no-cache-dir -r requirements.txt

# アプリケーションのコードをコピー
COPY . .

# ポート8080を公開
EXPOSE 8080

# アプリケーションの実行
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
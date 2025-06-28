FROM python:3.12-slim

WORKDIR /workspace

# Node.jsとnpmをインストール（npxを含む）+ git + 開発ツール
RUN apt-get update && \
  apt-get install -y curl git sudo vim less procps lsb-release apt-transport-https ca-certificates gnupg && \
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
  apt-get install -y nodejs && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

# Claude Code のインストール
RUN npm install -g @anthropic-ai/claude-code

# Google Cloud SDK のインストール
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
  curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - && \
  apt-get update && \
  apt-get install -y google-cloud-cli && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

# Python開発用パッケージのインストール
RUN pip install --no-cache-dir --upgrade pip && \
  pip install --no-cache-dir pylint autopep8 black isort pytest

# アプリケーションコードはマウントするためコピー不要

# サブモジュールのクローンはdocker-compose.ymlのコマンドで実行

# デフォルト起動コマンドなし（コンテナを起動したまま維持）
CMD ["sleep", "infinity"]
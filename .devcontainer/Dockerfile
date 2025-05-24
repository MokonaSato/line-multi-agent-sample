FROM python:3.12-slim

WORKDIR /workspace

# Node.jsとnpmをインストール（npxを含む）+ git + 開発ツール
RUN apt-get update && \
  apt-get install -y curl git sudo vim less procps lsb-release && \
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
  apt-get install -y nodejs && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

# Python開発用パッケージのインストール
RUN pip install --no-cache-dir --upgrade pip && \
  pip install --no-cache-dir pylint autopep8 black isort pytest

# アプリケーションコードはマウントするためコピー不要

# サブモジュールのクローンはdocker-compose.ymlのコマンドで実行

# デフォルト起動コマンドなし（コンテナを起動したまま維持）
CMD ["sleep", "infinity"]
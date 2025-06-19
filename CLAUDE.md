# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

LINE Multi-Agentは、LINEボットを通じて複数の専門エージェントが連携してユーザーの要求を処理する高度なAIアシスタントシステムです。ルートエージェントが全体を制御し、計算、Notion操作、画像認識、ファイルシステム操作などの専門エージェントが分担して作業を実行します。

## 技術スタック

- **フレームワーク**: FastAPI (Python 3.12)
- **AI モデル**: Google Gemini 2.5 Flash Preview (メイン), Gemini 2.0 Flash (検索用)
- **外部連携**: LINE Bot SDK, Notion API, Google Search API, MCP サーバー
- **インフラ**: Docker, Google Cloud Run, Cloud Build

## 主要開発コマンド

```bash
# 依存関係インストール
pip install -r requirements.txt

# テスト実行
pytest
pytest --cov=src tests/

# コードフォーマット
black .
isort .

# ローカルサーバー起動
uvicorn main:app --reload --host 0.0.0.0 --port 8080

# Docker ビルド・実行
docker build -t line-multi-agent .
docker run -p 8080:8080 --env-file .env line-multi-agent
```

## Cloud Run デプロイ

```bash
# Cloud Build でデプロイ（推奨）
gcloud builds submit --config=cloudbuild.yaml .

# デプロイ状況確認
gcloud builds list --limit=5
gcloud run services list --region=asia-northeast1
```

## アーキテクチャ

### エージェント階層構造
- **ルートエージェント** (`src/agents/root_agent.py`): 全体制御・専門エージェントへの委譲
- **専門エージェント** (`src/agents/`): 計算、Notion、画像認識、ファイル操作など領域特化エージェント
- **エージェントファクトリー** (`src/agents/agent_factory.py`): エージェント生成・管理

### プロンプトシステム
- **構造化プロンプト** (`src/prompts/`): YAML metadata + Jinja2テンプレート
- **階層管理**: agents/, core/, templates/, workflows/ で機能別分類
- **プロンプトマネージャー** (`src/agents/prompt_manager.py`): 動的ロード・レンダリング

### ツール統合
- **計算機能** (`src/tools/calculator_tools.py`)
- **Notion API** (`src/tools/notion/`): レシピデータベース管理
- **ファイル操作** (`src/tools/filesystem.py`): /tmp/user_files配下限定
- **MCP連携** (`src/tools/mcp_integration.py`): Model Context Protocol対応

### レシピ管理パイプライン
1. **URL抽出** → Web スクレイピング
2. **画像分析** → Gemini Vision API
3. **データ変換** → Notion スキーマ対応
4. **登録処理** → Notion データベース

## 重要な設定

### 必須環境変数
```bash
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxx
GOOGLE_API_KEY=your_google_api_key_here
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token_here
LINE_CHANNEL_SECRET=your_line_channel_secret_here
```

### エンドポイント
- `POST /callback`: LINE Webhook受信
- `GET /health`: ヘルスチェック
- `POST /test-agent`: エージェントテスト用
- `GET/POST /test-image-recipe`: 画像レシピテスト用

## 開発時の注意点

### セキュリティ制約
- ファイル操作は `/tmp/user_files/` 配下のみに制限
- LINE Signature検証必須
- 環境変数による機密情報管理

### エージェント開発
- 新しいエージェントは `src/agents/config.py` の `AGENT_CONFIGS` に登録
- プロンプトは対応する `src/prompts/agents/` ディレクトリに配置
- ツールは `src/tools/` に実装し、エージェント設定でバインド

### MCP連携
- `config.py` の `MCP_SERVERS` で外部MCPサーバーを定義
- `start.sh` でMCPサーバー起動を待機
- `MCP_ENABLED=true` で機能を有効化

### テスト
- プロンプトテストは `tests/test_prompts.py`
- エージェント統合テストは `tests/test_agent_service_impl.py`
- Notionツールテストは `tests/test_notion_tools.py`

## デプロイメモリ

- **最新デプロイ**: 2025-06-19 22:57:30 (analysis_principle変数エラー修正、test-image-recipeエンドポイント404修正)
- **ビルドID**: 3981bccc-335a-49cd-a73a-5151639594ce (SUCCESS)
- **リージョン**: asia-northeast1
- **デプロイ方法**: `gcloud builds submit --config=cloudbuild.yaml .`
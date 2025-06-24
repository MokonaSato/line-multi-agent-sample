# プロジェクト構造

このドキュメントは、LINE Multi-Agent プロジェクトのディレクトリ構成と主要コンポーネントの概要を示します。

## 1. ルートディレクトリ

```
/workspace/
├── config.py             # 全体設定
├── Dockerfile            # Dockerビルド用
├── main.py               # FastAPIアプリのエントリーポイント
├── pyproject.toml        # Pythonプロジェクト設定
├── README.md             # プロジェクト説明
├── requirements.txt      # 依存パッケージ
├── start.sh              # サービス起動スクリプト
├── cloudbuild.yaml       # GCP Cloud Build 設定
├── current-service.yaml  # Cloud Run サービス定義
├── cloud-run-service.yaml# Cloud Run サービス定義
└── ...
```

## 2. ソースコードディレクトリ

```
/src/
├── __init__.py
├── agents/               # エージェント定義・管理
├── prompts/              # プロンプトテンプレート・設定
├── services/             # サービス層（API/LINE連携等）
├── tools/                # ツール実装
└── utils/                # ユーティリティ
```

### 2.1 agents

- `agent_factory.py`: エージェント生成・管理
- `config.py`: エージェント設定
- `root_agent.py`: ルートエージェント
- `prompt_manager.py`: プロンプト管理
- `google_search_agent.py` など: 専門エージェント

### 2.2 prompts

- `agents/`: 各エージェント用プロンプト
- `core/`, `templates/`, `workflows/`: 汎用・ワークフロー用
- `config.yaml`: プロンプト設定

### 2.3 services

- `agent_service/`: エージェント API・セッション管理
- `line_service/`: LINE 連携
- `agent_service_impl.py`: サービス実装

### 2.4 tools

- `calculator_tools.py`: 計算ツール
- `notion/`: Notion 連携
- `filesystem_mcp.py`, `web_tools.py` など: 各種ツール

### 2.5 utils

- `logger.py`: ロギング
- `file_utils.py`: ファイル操作
- `prompt_manager.py`: プロンプト管理

## 3. テスト

```
/tests/
├── test_*.py             # 各種ユニットテスト
├── agents/               # エージェントテスト
├── tools/                # ツールテスト
└── ...
```

## 4. ドキュメント

```
/docs/
├── project_structure.md  # このファイル
├── extension_guide.md    # 拡張ガイド
├── adk_tutorial.ipynb    # チュートリアル
└── ...
```

## 5. その他

- `/htmlcov/`: カバレッジレポート
- `/__pycache__/`: Python キャッシュ
- `/tmp/`: 一時ファイル用（必要時のみ）

---

- すべての実装例・詳細なコードは省略しています。
- 最新のディレクトリ・ファイル構成に合わせて随時更新してください。

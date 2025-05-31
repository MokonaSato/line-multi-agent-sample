# プロジェクト構造

このドキュメントでは、プロジェクトの全体的なディレクトリ構造と主要なコンポーネントについて説明します。

## 基本構造

```
/workspace/
├── config.py             # 全体的な設定ファイル
├── Dockerfile            # Dockerコンテナ設定ファイル
├── main.py               # FastAPIアプリケーションのエントリーポイント
├── pyproject.toml        # Pythonプロジェクト設定ファイル
├── README.md             # プロジェクト説明ファイル
├── requirements.txt      # 必要なPythonパッケージの一覧
└── uv.lock               # uv パッケージマネージャーのロックファイル
```

## ソースコード

`/src` ディレクトリには以下のような構造でプロジェクトのソースコードが含まれています。

```
/src/
├── __init__.py           # Pythonパッケージとして認識させるためのファイル
├── agents/               # エージェント関連のコード
├── prompts/              # プロンプトテンプレート
├── services/             # サービスレイヤーの実装
├── tools/                # ツールの実装
└── utils/                # ユーティリティ関数
```

### agents

AI エージェントに関連するコンポーネントを実装しています。

```
/src/agents/
├── __init__.py
├── agent_factory.py      # エージェントの生成を担当するファクトリークラス
├── config.py             # エージェント固有の設定
├── prompt_manager.py     # プロンプト管理クラス
└── root_agent.py         # ルートエージェントの実装
```

### prompts

エージェントやワークフローで使用されるプロンプトテンプレートが含まれています。

```
/src/prompts/
├── agents/               # エージェント別のプロンプト
│   ├── calculator/       # 計算エージェント用プロンプト
│   ├── notion/           # Notion関連のプロンプト
│   ├── root/             # ルートエージェントのプロンプト
│   └── vision/           # 画像処理エージェント用のプロンプト
├── config.yaml           # プロンプト設定ファイル
├── config/               # 設定関連プロンプト
├── core/                 # コアプロンプト
├── templates/            # 汎用テンプレート
└── workflows/            # ワークフロー用プロンプト
    └── recipe/           # レシピ関連ワークフロー
        ├── image_extraction/  # 画像抽出処理
        └── url_extraction/    # URL抽出処理
```

### services

アプリケーションの各種サービスを実装しています。

```
/src/services/
├── __init__.py
├── agent_service/        # エージェントサービスの実装
│   ├── __init__.py
│   ├── constants.py      # 定数定義
│   ├── executor.py       # 実行エンジン
│   ├── message_handler.py # メッセージ処理
│   ├── response_processor.py # レスポンス処理
│   └── session_manager.py # セッション管理
├── agent_service_impl.py # エージェントサービスの実装
└── line_service/         # LINE連携サービス
    ├── __init__.py
    ├── client.py         # LINEクライアント
    ├── constants.py      # 定数定義
    └── handler.py        # イベントハンドラ
```

### tools

エージェントが使用する各種ツールを実装しています。

```
/src/tools/
├── __init__.py
├── calculator_tools.py   # 計算機能ツール
├── notion/               # Notion連携ツール
│   ├── __init__.py
│   ├── api/              # Notion API クライアント
│   │   ├── __init__.py
│   │   ├── base.py       # 基底クラス
│   │   ├── blocks.py     # ブロック操作
│   │   ├── databases.py  # データベース操作
│   │   └── pages.py      # ページ操作
│   ├── client.py         # Notionクライアント
│   ├── constants.py      # 定数定義
│   ├── recipes/          # レシピ関連機能
│   │   ├── __init__.py
│   │   └── api.py        # レシピAPI
│   └── utils.py          # ユーティリティ
└── web_tools.py          # Web関連ツール
```

### utils

ユーティリティ関数を提供します。

```
/src/utils/
├── __init__.py
├── file_utils.py         # ファイル操作ユーティリティ
├── logger.py             # ロギングユーティリティ
└── prompt_manager.py     # プロンプト管理ユーティリティ
```

## テスト

`/tests` ディレクトリにはテストコードが含まれています。

```
/tests/
├── __pycache__/
├── agents/               # エージェントのテスト
│   ├── __pycache__/
│   ├── test_google_search_agent.py
│   ├── test_root_agent.py
│   └── tools/            # ツールのテスト
├── conftest.py           # pytest設定ファイル
└── prompt_manager_test.py # プロンプトマネージャーのテスト
```

## ドキュメント

`/docs` ディレクトリにはプロジェクトに関するドキュメントが含まれています。

```
/docs/
├── adk_tutorial.ipynb    # ADK（AI開発キット）チュートリアル
└── project_structure.md  # プロジェクト構造説明（このファイル）
```

## その他

```
/htmlcov/                 # コードカバレッジレポート
/__pycache__/             # Pythonキャッシュファイル
/.venv/                   # 仮想環境（gitignoreされている）
```

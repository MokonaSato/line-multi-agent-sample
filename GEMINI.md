# LINE Multi-Agent プロジェクトガイド

このガイドは、LINE Multi-Agent プロジェクトの開発者向けドキュメントです。

## 1. プロジェクト概要

### 1.1 システム概要

LINE Multi-Agent は、LINE ボットを通じて複数の専門エージェントが連携してユーザーの要求を処理する高度な AI アシスタントシステムです。ルートエージェントが全体を制御し、計算、Notion 操作、画像認識、ファイルシステム操作などの専門エージェントが分担して作業を実行します。

### 1.2 技術スタック

- **フレームワーク**: FastAPI (Python 3.12)
- **AI モデル**: Google Gemini 2.5 Flash Preview (メイン), Gemini 2.0 Flash (検索用)
- **外部連携**: LINE Bot SDK, Notion API, Google Search API, MCP サーバー
- **インフラ**: Docker, Google Cloud Run, Cloud Build

## 2. 開発ガイド

### 2.1 開発環境セットアップ

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

### 2.2 デプロイメント

#### 2.2.1 Cloud Run デプロイ手順

```bash
# Cloud Build でデプロイ（推奨）
gcloud builds submit --config=cloudbuild.yaml .

# デプロイ状況確認
gcloud builds list --limit=5
gcloud run services list --region=asia-northeast1
```

## 3. システムアーキテクチャ

### 3.1 エージェントシステム

#### 3.1.1 エージェント階層構造

- **ルートエージェント** (`src/agents/root_agent.py`): 全体制御・専門エージェントへの委譲
- **専門エージェント** (`src/agents/`): 計算、Notion、画像認識、ファイル操作など領域特化エージェント
- **エージェントファクトリー** (`src/agents/agent_factory.py`): エージェント生成・管理

#### 3.1.2 プロンプトシステム

- **構造化プロンプト** (`src/prompts/`): YAML metadata + Jinja2 テンプレート
- **階層管理**: agents/, core/, templates/, workflows/ で機能別分類
- **プロンプトマネージャー** (`src/agents/prompt_manager.py`): 動的ロード・レンダリング

### 3.2 機能コンポーネント

#### 3.2.1 ツール統合

- **計算機能** (`src/tools/calculator_tools.py`)
- **Notion API** (`src/tools/notion/`): レシピデータベース管理
- **ファイル操作** (`src/tools/filesystem.py`): /tmp/user_files 配下限定
- **MCP 連携** (`src/tools/mcp_integration.py`): Model Context Protocol 対応

#### 3.2.2 レシピ管理パイプライン

1. **URL 抽出** → Web スクレイピング
2. **画像分析** → Gemini Vision API
3. **データ変換** → Notion スキーマ対応
4. **登録処理** → Notion データベース

## 4. 設定とセキュリティ

### 4.1 環境変数設定

```bash
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxx
GOOGLE_API_KEY=your_google_api_key_here
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token_here
LINE_CHANNEL_SECRET=your_line_channel_secret_here
```

### 4.2 API エンドポイント

- `POST /callback`: LINE Webhook 受信
- `GET /health`: ヘルスチェック
- `POST /test-agent`: エージェントテスト用
- `GET/POST /test-image-recipe`: 画像レシピテスト用

## 5. 開発ガイドライン

### ファイル作成・編集ルール

- 作業ディレクトリ外にファイルを作成しないこと
- 作業ディレクトリ外のファイルを編集しないこと
- 一時的なファイルを作る際は `tmp` ディレクトリを作成し、その中にファイルを作成すること

### セキュリティ制約

- ファイル操作は `/tmp/user_files/` 配下のみに制限
- LINE Signature 検証必須
- 環境変数による機密情報管理

### エージェント開発

- 新しいエージェントは `src/agents/config.py` の `AGENT_CONFIGS` に登録
- プロンプトは対応する `src/prompts/agents/` ディレクトリに配置
- ツールは `src/tools/` に実装し、エージェント設定でバインド

### MCP 連携

- `config.py` の `MCP_SERVERS` で外部 MCP サーバーを定義
- `start.sh` で MCP サーバー起動を待機
- `MCP_ENABLED=true` で機能を有効化

### テスト

- プロンプトテストは `tests/test_prompts.py`
- エージェント統合テストは `tests/test_agent_service_impl.py`
- Notion ツールテストは `tests/test_notion_tools.py`

## 6. リリース情報

### 6.1 最新デプロイ状況

- **デプロイ日時**: 2025-06-19 22:57:30
- **更新内容**: analysis_principle 変数エラー修正、test-image-recipe エンドポイント 404 修正
- **ビルド ID**: 3981bccc-335a-49cd-a73a-5151639594ce (SUCCESS)
- **リージョン**: asia-northeast1
- **デプロイ方法**: `gcloud builds submit --config=cloudbuild.yaml .`

## 7. コーディング規約

このプロジェクトでは、Python 公式のコーディング規約である PEP 8 に厳密に従ってください。特に以下の点に注意してください：

### 命名規則

- クラス名: `UpperCamelCase`（パスカルケース）
- 関数・メソッド名: `lower_case_with_underscores`（スネークケース）
- 変数名: `lower_case_with_underscores`（スネークケース）
- 定数: `UPPER_CASE_WITH_UNDERSCORES`（大文字スネークケース）
- モジュール名: `lower_case_with_underscores`（短く、全て小文字で、必要な場合のみアンダースコア）
- プライベートメソッド/変数: `_single_leading_underscore`（先頭に 1 つのアンダースコア）

### インデント

- 4 スペースを使用（タブ文字は使用しない）
- 行の継続には括弧内であれば通常のインデントを使用
- 長い行は最大 79 文字で改行（Black/Flake8 設定に合わせる）

### インポートスタイル

- 標準ライブラリ、サードパーティモジュール、ローカルアプリケーション/ライブラリのインポートをグループ分けし、それぞれ 1 行空ける
- 各グループ内はアルファベット順に並べる
- 1 行に複数のインポートを書かない
- 明示的な絶対インポートを推奨

```python
# 標準ライブラリ
import os
import sys
from datetime import datetime

# サードパーティモジュール
import numpy as np
import pandas as pd
from fastapi import FastAPI

# ローカルアプリケーション/ライブラリ
from src.utils.logger import setup_logger
from src.services.agent_service import init_agent
```

### ドキュメンテーション

- すべてのモジュール、クラス、関数には docstring を書く
- docstring は Google 形式を使用し、日本語で記述する
- 各ファイルを更新する際は、関連するドキュメントも同時に更新する

```python
def function_name(param1, param2):
    """関数の簡潔な説明

    より詳細な説明をここに書きます。複数行に渡って記述できます。

    Args:
        param1 (int): 最初のパラメータの説明
        param2 (str): 2番目のパラメータの説明

    Returns:
        bool: 戻り値の説明

    Raises:
        ValueError: エラーが発生する条件の説明
    """
```

### コメント

- コメントは日本語で記述する
- コードの理由（なぜそうしているのか）を説明するコメントを優先
- 技術用語は英語でも可
- TODO, FIXME, NOTE などのマーカーを使用する場合は名前を含める

```python
# TODO(username): この部分は後で最適化が必要
```

### 7.3 コードフォーマット設定

#### 7.3.1 Flake8 設定

- 最大行長: 79 文字
- E203（:の前後のスペースに関する警告）は無視
- W503（二項演算子の前での改行）は無視
- `__init__.py`ファイルでは F401（インポートされたが未使用のモジュール）と F403（from module import \*の使用）の警告を無視

#### 7.3.2 Black 設定

- 行の長さ: 79 文字
- ダブルクォート（"）を使用
- Python 3.7 以上の構文を使用

## 8. 高度な開発ガイドライン

### 8.1 エラー処理とロギング

#### 8.1.1 エラーハンドリング

- 例外は具体的なものをキャッチし、裸の except は避ける
- ユーザー向けのエラーメッセージは日本語で、ログにはより詳細な技術情報を含める

```python
try:
    # 処理
except ValueError as e:
    logger.error(f"値エラーが発生しました: {str(e)}")
    raise ValueError(f"入力値が不正です: {user_friendly_message}")
```

#### 8.1.2 ロギング

- `src.utils.logger`モジュールの`setup_logger`関数を使用
- 適切なログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）を使い分ける

### 8.2 プログラミングパターン

#### 8.2.1 非同期プログラミング

- 非同期関数は async/await を使用
- asyncio の適切な使用を心がける（blocking API の呼び出しを避けるなど）

#### 8.2.2 環境変数管理

- `.env`ファイルを使用し、python-dotenv で読み込む
- 機密情報はハードコードせず、必ず環境変数から取得

### 8.3 テスト戦略

- pytest フレームワークを使用
- テストは`tests`ディレクトリにモジュール構造と対応させて配置
- テスト関数名は`test_`から始める

### 8.4 エージェント開発ガイドライン

このプロジェクトは Google ADK を使用した AI エージェントを開発しています：

- エージェント定義は明確な指示（instruction）とツールのリストを含める
- エラー処理とエッジケースを考慮した堅牢なツール関数を作成
- セッション状態を適切に活用してエージェント間で情報を共有

## 9. セキュリティと保守性

### 9.1 セキュリティガイドライン

#### 9.1.1 一般的なセキュリティ対策

- ユーザー入力は常に検証し、信頼しない
- API キーやトークンなどの機密情報はコードにハードコードしない
- 第三者ライブラリのインポートは明示的に行い、`*`によるワイルドカードインポートを避ける

#### 9.1.2 ファイル操作の制約

- 作業ディレクトリ外にファイルを作成・編集しないこと
- 一時的なファイルを作る際は `tmp` ディレクトリを作成し、その中にファイルを作成すること

### 9.2 保守性とドキュメンテーション

#### 9.2.1 ドキュメント更新ポリシー

- コード変更時は関連するドキュメントを必ず更新する
- `docs/`ディレクトリ内のファイルを確認し、必要に応じて更新
- API 仕様の変更時は API 仕様書も更新
- 重要な変更は README.md にも反映

## 10. Claude Codeとのペアプログラミング
- Claude Codeを下記コマンドで呼び出し、必ず相談しながらペアプログラミングを実施すること
  - `claude "prompt"`
  - e.g. `claude "explain this project"`
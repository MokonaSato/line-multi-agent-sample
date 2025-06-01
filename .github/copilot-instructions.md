# GitHub Copilot カスタムインストラクション

## 全般的なコーディングスタイル

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

## コードフォーマットツールの設定

### Flake8 設定

- 最大行長: 79 文字
- E203（:の前後のスペースに関する警告）は無視
- W503（二項演算子の前での改行）は無視
- `__init__.py`ファイルでは F401（インポートされたが未使用のモジュール）と F403（from module import \*の使用）の警告を無視

### Black 設定

- 行の長さ: 79 文字
- ダブルクォート（"）を使用
- Python 3.7 以上の構文を使用

## プロジェクト固有のガイドライン

### エラーハンドリング

- 例外は具体的なものをキャッチし、裸の except は避ける
- ユーザー向けのエラーメッセージは日本語で、ログにはより詳細な技術情報を含める

```python
try:
    # 処理
except ValueError as e:
    logger.error(f"値エラーが発生しました: {str(e)}")
    raise ValueError(f"入力値が不正です: {user_friendly_message}")
```

### 非同期プログラミング

- 非同期関数は async/await を使用
- asyncio の適切な使用を心がける（blocking API の呼び出しを避けるなど）

### 環境変数

- `.env`ファイルを使用し、python-dotenv で読み込む
- 機密情報はハードコードせず、必ず環境変数から取得

### ロギング

- `src.utils.logger`モジュールの`setup_logger`関数を使用
- 適切なログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）を使い分ける

### テスト

- pytest フレームワークを使用
- テストは`tests`ディレクトリにモジュール構造と対応させて配置
- テスト関数名は`test_`から始める

## ドキュメント更新ガイドライン

- コード変更時は関連するドキュメントを必ず更新する
- `docs/`ディレクトリ内のファイルを確認し、必要に応じて更新
- API 仕様の変更時は API 仕様書も更新
- 重要な変更は README.md にも反映

## エージェント開発ガイドライン

このプロジェクトは Google ADK を使用した AI エージェントを開発しています：

- エージェント定義は明確な指示（instruction）とツールのリストを含める
- エラー処理とエッジケースを考慮した堅牢なツール関数を作成
- セッション状態を適切に活用してエージェント間で情報を共有

## セキュリティ考慮事項

- ユーザー入力は常に検証し、信頼しない
- API キーやトークンなどの機密情報はコードにハードコードしない
- 第三者ライブラリのインポートは明示的に行い、`*`によるワイルドカードインポートを避ける

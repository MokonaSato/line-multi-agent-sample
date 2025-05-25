import os
import sys

import pytest

# テストで使用するパスを追加
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)


# 共通のフィクスチャをここに定義
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    # 環境変数のモック
    monkeypatch.setenv("NOTION_TOKEN", "test-token")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key")
    monkeypatch.setenv("GOOGLE_CSE_ID", "test-cse-id")


@pytest.fixture
def sample_html_content():
    return """
    <html>
    <head><title>テストページ</title></head>
    <body>
        <h1>テスト見出し</h1>
        <p>これはテスト段落です。</p>
        <ul>
            <li>項目1</li>
            <li>項目2</li>
        </ul>
    </body>
</html>
    """

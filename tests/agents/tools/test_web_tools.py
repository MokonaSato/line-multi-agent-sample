from unittest.mock import MagicMock, patch

import pytest

from src.agents.tools.web_tools import fetch_web_content


@pytest.mark.asyncio
async def test_fetch_web_content():
    # モックのレスポンスを作成
    mock_response = MagicMock()
    mock_response.text = (
        "<html><body><h1>テストページ</h1>"
        "<p>テストコンテンツ</p></body></html>"
    )
    mock_response.status_code = 200

    # requestsのgetメソッドをモック化
    with patch("requests.get", return_value=mock_response):
        result = await fetch_web_content("https://example.com")

        # 結果を検証
        assert "テストページ" in result
        assert "テストコンテンツ" in result


@pytest.mark.asyncio
async def test_fetch_web_content_error():
    # 失敗するケース
    with patch("requests.get", side_effect=Exception("接続エラー")):
        result = await fetch_web_content("https://example.com")

        # エラーメッセージが含まれていることを確認
        assert "エラー" in result

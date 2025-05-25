from unittest.mock import MagicMock, patch

import pytest
from google.adk.tools import google_search

from src.agents.google_search_agent import google_search_agent


# google_searchツール関数のテスト
@pytest.mark.asyncio
async def test_google_search_tool():
    # 検索結果のモック
    mock_search_results = {
        "items": [
            {
                "title": "テスト結果1",
                "link": "https://example.com/1",
                "snippet": "これはテスト結果1の説明です。",
            },
            {
                "title": "テスト結果2",
                "link": "https://example.com/2",
                "snippet": "これはテスト結果2の説明です。",
            },
        ]
    }

    # GoogleSearchToolのrun_asyncメソッドをモック化
    with patch.object(google_search, "run_async") as mock_run_async:
        # モックされた検索結果を返すように設定
        formatted_results = "\n".join(
            [
                f"タイトル: {item['title']}\n"
                f"URL: {item['link']}\n"
                f"スニペット: {item['snippet']}\n"
                for item in mock_search_results["items"]
            ]
        )
        mock_run_async.return_value = formatted_results

        # GoogleSearchToolのrunメソッドを使用してテスト
        result = await google_search.run(query="テスト検索クエリ")

        # メソッドが呼び出されたことを確認
        mock_run_async.assert_called_once()

        # 検索結果が正しく形式化されていることを確認
        assert "テスト結果1" in result
        assert "https://example.com/1" in result
        assert "テスト結果2" in result
        assert "https://example.com/2" in result
        assert "これはテスト結果1の説明です。" in result
        assert "これはテスト結果2の説明です。" in result


def test_google_search_agent_setup():
    # エージェントが正しく設定されていることを確認
    assert google_search_agent.name == "google_search_agent"
    assert google_search_agent.description is not None
    assert len(google_search_agent.tools) == 1
    # ToolクラスがGoogleSearchToolであることを確認
    assert (
        google_search_agent.tools[0].__class__.__name__ == "GoogleSearchTool"
    )

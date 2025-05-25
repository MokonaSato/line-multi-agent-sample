from unittest.mock import MagicMock, patch

import pytest

from src.agents.tools.notion_tools import (
    NotionAPIClient,  # クラス自体もインポート
    notion_create_page,
    notion_query_database,
    notion_search,
    notion_tools_list,
    notion_update_page,
)


# モック用のクラスを作成
class MockNotionClient:
    def __init__(self, *args, **kwargs):
        pass

    def _make_request(self, method, endpoint, data=None):
        # このメソッドは各テストでオーバーライドします
        pass


@pytest.fixture(autouse=True)
def patch_requests():
    """すべてのrequestsモジュールの呼び出しをブロックする"""
    with (
        patch("requests.get"),
        patch("requests.post"),
        patch("requests.patch"),
    ):
        yield


@pytest.fixture
def mock_notion_client():
    """NotionAPIClientクラスをモックして、実際のAPIリクエストを防ぐ"""
    with patch(
        "src.agents.tools.notion_tools.NotionAPIClient", MockNotionClient
    ):
        mock_instance = MagicMock()
        yield mock_instance


@pytest.mark.asyncio
async def test_search_notion(mock_notion_client):
    # モックのレスポンスをセットアップ
    mock_results = {
        "results": [
            {
                "id": "page1",
                "properties": {
                    "title": {"title": [{"plain_text": "テストページ1"}]}
                },
            },
            {
                "id": "page2",
                "properties": {
                    "title": {"title": [{"plain_text": "テストページ2"}]}
                },
            },
        ],
        "has_more": False,
        "next_cursor": None,
    }

    # MockNotionClientの_make_requestをモック
    with patch.object(
        MockNotionClient, "_make_request", return_value=mock_results
    ):
        result = notion_search("テスト")

    # 結果の構造を確認
    assert result["success"] is True
    assert len(result["results"]) == 2
    assert result["total_count"] == 2


@pytest.mark.asyncio
async def test_create_notion_page():
    # モックのレスポンスをセットアップ
    mock_page = {"id": "new_page", "url": "https://notion.so/new_page"}

    # MockNotionClientの_make_requestをモック
    with patch.object(
        MockNotionClient, "_make_request", return_value=mock_page
    ):
        result = notion_create_page("parent_page_uuid", "新規ページ")

    # 結果の構造を確認
    assert "page_id" in result
    assert "url" in result
    assert result["title"] == "新規ページ"


@pytest.mark.asyncio
async def test_update_notion_page():
    # モックのレスポンスをセットアップ
    mock_page = {"id": "page_uuid", "url": "https://notion.so/page_uuid"}

    # MockNotionClientの_make_requestをモック
    with patch.object(
        MockNotionClient, "_make_request", return_value=mock_page
    ):
        result = notion_update_page(
            "page_uuid", {"title": "更新されたタイトル"}
        )

    # 結果の構造を確認
    assert "page_id" in result
    assert "url" in result
    assert result["title"] == "更新されたタイトル"


@pytest.mark.asyncio
async def test_query_notion_database():
    # モックのレスポンスをセットアップ
    mock_db_content = {
        "results": [
            {
                "id": "row1",
                "properties": {
                    "名前": {"title": [{"plain_text": "項目1"}]},
                    "値": {"number": 100},
                },
            },
            {
                "id": "row2",
                "properties": {
                    "名前": {"title": [{"plain_text": "項目2"}]},
                    "値": {"number": 200},
                },
            },
        ],
        "has_more": False,
        "next_cursor": None,
    }

    # MockNotionClientの_make_requestをモック
    with patch.object(
        MockNotionClient, "_make_request", return_value=mock_db_content
    ):
        result = await notion_query_database("database_uuid")

    # 結果の構造を確認
    assert "results" in result
    assert len(result["results"]) == 2


def test_notion_tools_list():
    # ツールリストがリストであることを確認
    assert isinstance(notion_tools_list, list)

    # 各ツールの関数名を取得
    tool_names = [tool.__name__ for tool in notion_tools_list]

    # 必要なツールが含まれているか確認
    assert "notion_search" in tool_names
    assert "notion_create_page" in tool_names
    assert "notion_update_page" in tool_names
    assert "notion_query_database" in tool_names

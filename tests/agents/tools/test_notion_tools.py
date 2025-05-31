from unittest.mock import MagicMock, patch

import pytest

from src.agents.tools.notion import (
    notion_create_page,
    notion_query_database,
    notion_search,
    notion_tools_list,
    notion_update_page,
)


# モック用のクラスを作成
class MockNotionClient:
    def __init__(self, *args, **kwargs):
        self.token = "fake-token"
        self.version = "2022-06-28"
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": self.version,
            "Content-Type": "application/json",
        }

    def _make_request(self, method, endpoint, data=None):
        # このメソッドは各テストでオーバーライドします
        # デフォルトでは成功レスポンスを返す
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "{}"
        mock_response.json.return_value = {}
        mock_response.headers = {"Content-Type": "application/json"}
        return {}


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
    """Notionクライアントのインスタンスをモックして、実際のAPIリクエストを防ぐ"""
    # クライアントインスタンスをモック
    with patch("src.agents.tools.notion.api.base.client", MockNotionClient()):
        with patch(
            "src.agents.tools.notion.api.pages.client", MockNotionClient()
        ):
            with patch(
                "src.agents.tools.notion.api.databases.client",
                MockNotionClient(),
            ):
                yield MockNotionClient()


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

    # APIクライアントの_make_requestメソッドをモック
    with patch(
        "src.agents.tools.notion.api.base.client._make_request",
        return_value=mock_results,
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

    # APIクライアントの_make_requestメソッドをモック
    with patch(
        "src.agents.tools.notion.api.pages.client._make_request",
        return_value=mock_page,
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

    # APIクライアントの_make_requestメソッドをモック
    with patch(
        "src.agents.tools.notion.api.pages.client._make_request",
        return_value=mock_page,
    ):
        result = notion_update_page(
            "page_uuid", {"title": "更新されたタイトル"}
        )

    # 結果の構造を確認
    assert "page_id" in result
    assert "page" in result
    assert "success" in result
    assert result["page_id"] == "page_uuid"
    assert result["page"]["url"] == "https://notion.so/page_uuid"


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

    # APIクライアントの_make_requestメソッドをモック
    with patch(
        "src.agents.tools.notion.api.databases.client._make_request",
        return_value=mock_db_content,
    ):
        result = notion_query_database("database_uuid")

    # 結果の構造を確認
    assert "results" in result
    assert len(result["results"]) == 2


def test_notion_tools_list():
    # ツールリストがリストであることを確認
    assert isinstance(notion_tools_list, list)

    # モジュールパスとメソッド名の組み合わせで必要な機能を確認
    modules_and_names = [
        (tool.__module__, tool.__name__) for tool in notion_tools_list
    ]

    # 必要なツール関数が存在するか確認
    assert len(notion_tools_list) >= 10, "ツールリストが短すぎます"

    # 必要な機能があることを確認
    assert ("src.agents.tools.notion.api.base", "search") in modules_and_names
    assert ("src.agents.tools.notion.api.pages", "create") in modules_and_names
    assert (
        "src.agents.tools.notion.api.databases",
        "query",
    ) in modules_and_names

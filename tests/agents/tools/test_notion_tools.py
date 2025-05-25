from unittest.mock import MagicMock, patch

import pytest

from src.agents.tools.notion_tools import (
    create_notion_page,
    get_notion_database,
    notion_tools_list,
    search_notion,
    update_notion_page,
)


@pytest.fixture
def mock_notion_client():
    with patch("src.agents.tools.notion_tools.NotionClient") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.mark.asyncio
async def test_search_notion(mock_notion_client):
    # モックのレスポンスをセットアップ
    mock_results = [
        {"id": "page1", "title": "テストページ1"},
        {"id": "page2", "title": "テストページ2"},
    ]
    mock_notion_client.search.return_value = mock_results

    result = await search_notion("テスト")

    # 検索メソッドが正しく呼ばれたか確認
    mock_notion_client.search.assert_called_once_with("テスト")

    # 結果に両方のページが含まれていることを確認
    assert "テストページ1" in result
    assert "テストページ2" in result


@pytest.mark.asyncio
async def test_create_notion_page(mock_notion_client):
    # モックのレスポンスをセットアップ
    mock_page = {"id": "new_page", "url": "https://notion.so/new_page"}
    mock_notion_client.create_page.return_value = mock_page

    result = await create_notion_page("親ページID", "新規ページ", "テスト内容")

    # 作成メソッドが正しく呼ばれたか確認
    mock_notion_client.create_page.assert_called_once()

    # 結果に成功メッセージが含まれていることを確認
    assert "作成" in result
    assert "https://notion.so/new_page" in result


@pytest.mark.asyncio
async def test_update_notion_page(mock_notion_client):
    result = await update_notion_page("page_id", "更新内容")

    # 更新メソッドが正しく呼ばれたか確認
    mock_notion_client.update_page.assert_called_once_with(
        "page_id", "更新内容"
    )

    # 成功メッセージが含まれていることを確認
    assert "更新" in result


@pytest.mark.asyncio
async def test_get_notion_database(mock_notion_client):
    # モックのレスポンスをセットアップ
    mock_db_content = [
        {"id": "row1", "properties": {"名前": "項目1", "値": 100}},
        {"id": "row2", "properties": {"名前": "項目2", "値": 200}},
    ]
    mock_notion_client.get_database.return_value = mock_db_content

    result = await get_notion_database("db_id")

    # データベース取得メソッドが正しく呼ばれたか確認
    mock_notion_client.get_database.assert_called_once_with("db_id")

    # 結果にデータベースの内容が含まれていることを確認
    assert "項目1" in result
    assert "項目2" in result


def test_notion_tools_list():
    # ツールリストに必要なツールが含まれていることを確認
    tool_names = [tool.function.__name__ for tool in notion_tools_list]

    assert "search_notion" in tool_names
    assert "create_notion_page" in tool_names
    assert "update_notion_page" in tool_names
    assert "get_notion_database" in tool_names

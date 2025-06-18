"""Notion MCP Server連携ツール (Google ADK用)

このモジュールは、Google ADKのファンクションツールとしてNotion MCP Serverと連携します。
新しいMCP統合アプローチに対応しています。
"""

from typing import Any, Dict, List, Optional

from src.utils.logger import setup_logger

logger = setup_logger("notion_tools_mcp")


def notion_create_page_mcp(
    parent_database_id: str,
    properties: Dict[str, Any],
    children: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Notion MCP Serverを通じてページを作成する（レガシー互換）

    注意: この関数は下位互換性のために残されています。
    新しい実装では、Google ADKのMCPToolsetを直接使用してください。

    Args:
        parent_database_id: 親データベースID
        properties: ページプロパティ
        children: 子コンテンツ（オプション）

    Returns:
        作成されたページの情報
    """
    logger.warning(
        "notion_create_page_mcp is deprecated. "
        "Use Google ADK MCPToolset directly."
    )
    return {
        "success": False,
        "error": "MCP Toolset integration required",
        "id": None,
        "url": None,
    }


def notion_query_database_mcp(
    database_id: str,
    filter_conditions: Optional[Dict[str, Any]] = None,
    sorts: Optional[List[Dict[str, Any]]] = None,
    page_size: int = 100,
) -> Dict[str, Any]:
    """Notion MCP Serverを通じてデータベースをクエリする（レガシー互換）

    Args:
        database_id: データベースID
        filter_conditions: フィルター条件
        sorts: ソート条件
        page_size: ページサイズ

    Returns:
        クエリ結果
    """
    logger.warning(
        "notion_query_database_mcp is deprecated. "
        "Use Google ADK MCPToolset directly."
    )
    return {
        "success": False,
        "error": "MCP Toolset integration required",
        "results": [],
        "has_more": False,
        "next_cursor": None,
    }


def notion_retrieve_page_mcp(page_id: str) -> Dict[str, Any]:
    """Notion MCP Serverを通じてページを取得する（レガシー互換）

    Args:
        page_id: ページID

    Returns:
        ページの情報
    """
    logger.warning(
        "notion_retrieve_page_mcp is deprecated. "
        "Use Google ADK MCPToolset directly."
    )
    return {
        "success": False,
        "error": "MCP Toolset integration required",
        "page": None,
    }


def notion_update_page_mcp(
    page_id: str,
    properties: Optional[Dict[str, Any]] = None,
    archived: Optional[bool] = None,
) -> Dict[str, Any]:
    """Notion MCP Serverを通じてページを更新する（レガシー互換）

    Args:
        page_id: ページID
        properties: 更新するプロパティ
        archived: アーカイブ状態

    Returns:
        更新されたページの情報
    """
    logger.warning(
        "notion_update_page_mcp is deprecated. "
        "Use Google ADK MCPToolset directly."
    )
    return {
        "success": False,
        "error": "MCP Toolset integration required",
        "page": None,
    }


# 利用可能なMCPツールのリスト
notion_mcp_tools_list = [
    notion_create_page_mcp,
    notion_query_database_mcp,
    notion_retrieve_page_mcp,
    notion_update_page_mcp,
]

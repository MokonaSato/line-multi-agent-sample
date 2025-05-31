"""
Notion API の基本操作関数
"""

from typing import Any, Dict, Optional

from src.tools.notion.client import client


def search(
    query: str, page_size: int = 10, filter_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Notionワークスペースでページやデータベースを検索

    Args:
        query: 検索クエリ
        page_size: 結果の最大数 (1-100)
        filter_type: フィルターのタイプ ('page' または 'database')

    Returns:
        検索結果のディクショナリ
    """
    data = {"query": query, "page_size": min(max(page_size, 1), 100)}

    if filter_type in ["page", "database"]:
        data["filter"] = {"value": filter_type, "property": "object"}

    result = client._make_request("POST", "/search", data)

    return {
        "success": True,
        "results": result.get("results", []),
        "has_more": result.get("has_more", False),
        "next_cursor": result.get("next_cursor"),
        "total_count": len(result.get("results", [])),
    }


def get_users() -> Dict[str, Any]:
    """
    ワークスペースのユーザー一覧を取得

    Returns:
        ユーザーリスト
    """
    result = client._make_request("GET", "/users")

    return {
        "success": True,
        "users": result.get("results", []),
        "total_count": len(result.get("results", [])),
    }

"""
Notion API のデータベース操作関数
"""

from typing import Any, Dict, List, Optional

from src.agents.tools.notion.client import client


def get(database_id: str) -> Dict[str, Any]:
    """
    データベースの詳細情報とカラム（プロパティ）構造を取得

    Args:
        database_id: データベースID

    Returns:
        データベース情報のディクショナリ
    """
    result = client._make_request("GET", f"/databases/{database_id}")

    # データベースのタイトルを抽出
    title = ""
    if result.get("title"):
        for title_part in result.get("title", []):
            if title_part.get("text", {}).get("content"):
                title += title_part.get("text", {}).get("content", "")

    return {
        "success": True,
        "database": result,
        "title": title,
        "properties": result.get("properties", {}),
        "url": result.get("url", ""),
    }


def query(
    database_id: str,
    filter_conditions: Optional[Dict[str, Any]] = None,
    sorts: Optional[List[Dict[str, Any]]] = None,
    page_size: int = 100,
) -> Dict[str, Any]:
    """
    データベースをクエリ

    Args:
        database_id: データベースID
        filter_conditions: フィルター条件
        sorts: ソート条件
        page_size: 結果の最大数

    Returns:
        クエリ結果のディクショナリ
    """
    data = {"page_size": min(max(page_size, 1), 100)}

    # フィルター条件の検証と修正
    if filter_conditions:
        # フィルター条件が空でないかチェック
        if isinstance(filter_conditions, dict) and filter_conditions:
            data["filter"] = filter_conditions
        # 空のフィルター条件や不正な形式の場合は無視
        else:
            # フィルターなしでクエリ実行
            pass

    if sorts:
        data["sorts"] = sorts

    result = client._make_request(
        "POST", f"/databases/{database_id}/query", data
    )

    return {
        "success": True,
        "results": result.get("results", []),
        "has_more": result.get("has_more", False),
        "next_cursor": result.get("next_cursor"),
        "total_count": len(result.get("results", [])),
    }


def create(
    parent_id: str,
    title: str,
    properties: Dict[str, Any],
    parent_type: str = "page",
) -> Dict[str, Any]:
    """
    新しいデータベースを作成

    Args:
        parent_id: 親ページのID
        title: データベースタイトル
        properties: データベースのプロパティスキーマ
        parent_type: 親のタイプ

    Returns:
        作成されたデータベースの情報
    """
    data = {
        "parent": {f"{parent_type}_id": parent_id},
        "title": [{"text": {"content": title}}],
        "properties": properties,
    }

    result = client._make_request("POST", "/databases", data)

    return {
        "success": True,
        "database": result,
        "database_id": result.get("id"),
        "url": result.get("url"),
        "title": title,
    }

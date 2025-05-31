"""
Notion API のブロック操作関数
"""

from typing import Any, Dict, List

from src.agents.tools.notion.client import client


def get_children(block_id: str, page_size: int = 100) -> Dict[str, Any]:
    """
    ブロックの子要素を取得

    Args:
        block_id: ブロックID（ページIDも可）
        page_size: 結果の最大数

    Returns:
        子ブロックのリスト
    """
    params = {"page_size": min(max(page_size, 1), 100)}

    result = client._make_request(
        "GET", f"/blocks/{block_id}/children", params
    )

    return {
        "success": True,
        "results": result.get("results", []),
        "has_more": result.get("has_more", False),
        "next_cursor": result.get("next_cursor"),
        "total_count": len(result.get("results", [])),
    }


def append_children(
    block_id: str, children: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    ブロックに子要素を追加

    Args:
        block_id: 親ブロックのID
        children: 追加するブロックの配列

    Returns:
        追加されたブロックの情報
    """
    data = {"children": children}

    result = client._make_request(
        "PATCH", f"/blocks/{block_id}/children", data
    )

    return {
        "success": True,
        "results": result.get("results", []),
        "total_added": len(result.get("results", [])),
    }

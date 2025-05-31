"""
Notion API のページ操作関数
"""

from typing import Any, Dict, List, Optional

from src.tools.notion.client import client
from src.tools.notion.utils import extract_page_title


def get(page_id: str) -> Dict[str, Any]:
    """
    指定されたページの詳細情報を取得

    Args:
        page_id: ページID

    Returns:
        ページ情報のディクショナリ
    """
    result = client._make_request("GET", f"/pages/{page_id}")

    return {
        "success": True,
        "page": result,
        "title": extract_page_title(result),
        "url": result.get("url"),
        "created_time": result.get("created_time"),
        "last_edited_time": result.get("last_edited_time"),
    }


def create(
    parent_id: str,
    title: str,
    content: Optional[List[Dict[str, Any]]] = None,
    parent_type: str = "page",
    properties: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    新しいページを作成

    Args:
        parent_id: 親ページまたはデータベースのID
        title: ページタイトル
        content: ページコンテンツ（ブロックの配列）
        parent_type: 親のタイプ ('page' または 'database')
        properties: ページのプロパティ

    Returns:
        作成されたページの情報
    """
    # parent_idが空でないことを確認
    if not parent_id:
        return {
            "success": False,
            "error": "親ページまたはデータベースIDが指定されていません",
        }

    # 親タイプの検証
    if parent_type not in ["page", "database"]:
        parent_type = "page"  # デフォルトに設定

    if properties is None:
        # デフォルトのプロパティを設定
        data = {
            "parent": {f"{parent_type}_id": parent_id},
            "properties": {"名前": {"title": [{"text": {"content": title}}]}},
        }
    else:
        # プロパティが指定されている場合はそれを使用
        data = {
            "parent": {f"{parent_type}_id": parent_id},
            "properties": properties,
        }
        # タイトルプロパティがない場合は追加
        if "名前" not in properties and "title" not in properties:
            data["properties"]["名前"] = {
                "title": [{"text": {"content": title}}]
            }

    if content:
        data["children"] = content

    try:
        result = client._make_request("POST", "/pages", data)

        return {
            "success": True,
            "page": result,
            "page_id": result.get("id"),
            "url": result.get("url"),
            "title": title,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "page_id": None,
            "url": None,
            "title": title,
        }


def update(
    page_id: str,
    properties: Optional[Dict[str, Any]] = None,
    archived: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    ページのプロパティを更新

    Args:
        page_id: ページID
        properties: 更新するプロパティ
        archived: アーカイブするかどうか

    Returns:
        更新されたページの情報
    """
    data = {}

    if properties:
        data["properties"] = properties

    if archived is not None:
        data["archived"] = archived

    result = client._make_request("PATCH", f"/pages/{page_id}", data)

    return {
        "success": True,
        "page": result,
        "page_id": result.get("id"),
        "last_edited_time": result.get("last_edited_time"),
    }


def create_comment(
    page_id: str, rich_text: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    ページにコメントを作成

    Args:
        page_id: ページID
        rich_text: コメントのリッチテキスト

    Returns:
        作成されたコメントの情報
    """
    data = {"parent": {"page_id": page_id}, "rich_text": rich_text}

    result = client._make_request("POST", "/comments", data)

    return {
        "success": True,
        "comment": result,
        "comment_id": result.get("id"),
        "created_time": result.get("created_time"),
    }

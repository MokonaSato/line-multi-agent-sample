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
    # すべての必須パラメータをまとめて検証
    missing_params = []
    if not parent_id:
        missing_params.append("parent_id")
    if (
        not title and parent_type == "page"
    ):  # データベースの場合はpropertiesにタイトルがある
        missing_params.append("title")
    if parent_type == "database" and not properties:
        missing_params.append("properties")

    if missing_params:
        error_msg = (
            f"必須パラメータが不足しています: {', '.join(missing_params)}"
        )
        return {
            "success": False,
            "error": error_msg,
            "error_type": "missing_parameter",
        }

    # 親タイプの検証
    if parent_type not in ["page", "database"]:
        parent_type = "page"  # デフォルトに設定

    # データベースページ作成の場合、特にプロパティの検証を強化
    if parent_type == "database":
        if properties is None:
            return {
                "success": False,
                "error": "データベースページ作成には'properties'パラメータが必要です",
                "error_type": "missing_parameter",
            }

        # タイトルプロパティが含まれているか確認（データベースページには必須）
        has_title = False
        for prop_name, prop_value in properties.items():
            if (
                prop_value
                and isinstance(prop_value, dict)
                and prop_value.get("title")
            ):
                has_title = True
                break

        if not has_title:
            # タイトルプロパティがない場合は追加
            properties["名前"] = {
                "title": [{"text": {"content": title or "無題のレシピ"}}]
            }

        data = {
            "parent": {f"{parent_type}_id": parent_id},
            "properties": properties,
        }
    else:
        # 通常のページ作成
        if properties is None:
            # デフォルトのプロパティを設定
            data = {
                "parent": {f"{parent_type}_id": parent_id},
                "properties": {
                    "名前": {"title": [{"text": {"content": title}}]}
                },
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
        # リクエスト前の最終検証
        if not data.get("parent"):
            return {
                "success": False,
                "error": "parentパラメータが不足しています",
                "error_type": "missing_parameter",
            }

        if not data.get("properties"):
            return {
                "success": False,
                "error": "propertiesパラメータが不足しています",
                "error_type": "missing_parameter",
            }

        # APIリクエスト
        result = client._make_request("POST", "/pages", data)

        return {
            "success": True,
            "page": result,
            "page_id": result.get("id"),
            "url": result.get("url"),
            "title": title,
        }
    except Exception as e:
        error_msg = str(e)
        error_type = "api_error"

        # エラーメッセージからエラーの種類を特定
        if "missing required parameters" in error_msg.lower():
            error_type = "missing_parameter"
            error_msg = (
                f"{error_msg} - 必要なパラメータ (parent_id, title, properties)"
            )
        elif "token" in error_msg.lower():
            error_type = "token_error"

        return {
            "success": False,
            "error": error_msg,
            "error_type": error_type,
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

"""
Notion API操作ツール
Google ADK Agent用のNotion APIツール集
"""

import logging
import os
from typing import Any, Dict, List, Optional

import requests

from config import NOTION_TOKEN


class NotionAPIClient:
    """Notion API クライアント"""

    def __init__(self):
        self.token = NOTION_TOKEN
        self.version = os.getenv("NOTION_VERSION", "2022-06-28")
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": self.version,
            "Content-Type": "application/json",
        }

    def _make_request(
        self, method: str, endpoint: str, data: Dict = None
    ) -> Dict:
        """APIリクエストを実行"""
        url = f"{self.base_url}{endpoint}"

        # トークン存在チェックを追加
        if not self.token:
            logging.error(
                "Notion API Token が設定されていません。環境変数 NOTION_TOKEN を確認してください。"
            )
            raise Exception("Notion API Error: API Token が設定されていません")

        # トークンの一部をマスクしてログに出力
        masked_token = (
            f"{self.token[:4]}...{self.token[-4:]}"
            if len(self.token) > 8
            else "未設定"
        )
        logging.info(f"Notion API リクエスト: {method} {endpoint}")
        logging.info(
            f"認証ヘッダー: Bearer {masked_token}, Version: {self.version}"
        )

        try:
            if method == "GET":
                logging.info(f"GETパラメータ: {data}")
                response = requests.get(url, headers=self.headers, params=data)
            elif method == "POST":
                logging.info(
                    f"POSTデータ構造: {list(data.keys()) if data else None}"
                )
                response = requests.post(url, headers=self.headers, json=data)
            elif method == "PATCH":
                logging.info(
                    f"PATCHデータ構造: {list(data.keys()) if data else None}"
                )
                response = requests.patch(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # レスポンスコードをログ出力
            logging.info(
                f"Notion API レスポンスコード: {response.status_code}"
            )

            # レスポンスが失敗している場合は詳細をログに出力
            if response.status_code >= 400:
                logging.error(f"Notion API エラーレスポンス: {response.text}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logging.error(f"Notion API request failed: {e}")

            # レスポンスオブジェクトがある場合はより詳細な情報をログに出力
            if hasattr(e, "response") and e.response is not None:
                logging.error(
                    f"HTTPステータスコード: {e.response.status_code}"
                )
                logging.error(
                    f"レスポンスヘッダー: {dict(e.response.headers)}"
                )
                logging.error(f"レスポンス本文: {e.response.text}")

                try:
                    error_data = e.response.json()
                    error_message = error_data.get("message", str(e))
                    logging.error(
                        f"Notion API エラーメッセージ: {error_message}"
                    )
                    raise Exception((f"Notion API Error: " f"{error_message}"))
                except Exception:
                    raise Exception(
                        f"Notion API Error: HTTP {e.response.status_code}"
                    )
            raise Exception(f"Notion API Error: {str(e)}")


# Notion APIクライアントのインスタンス
notion_client = NotionAPIClient()


def notion_search(
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

    result = notion_client._make_request("POST", "/search", data)

    return {
        "success": True,
        "results": result.get("results", []),
        "has_more": result.get("has_more", False),
        "next_cursor": result.get("next_cursor"),
        "total_count": len(result.get("results", [])),
    }


def notion_get_page(page_id: str) -> Dict[str, Any]:
    """
    指定されたページの詳細情報を取得

    Args:
        page_id: ページID

    Returns:
        ページ情報のディクショナリ
    """
    result = notion_client._make_request("GET", f"/pages/{page_id}")

    return {
        "success": True,
        "page": result,
        "title": _extract_page_title(result),
        "url": result.get("url"),
        "created_time": result.get("created_time"),
        "last_edited_time": result.get("last_edited_time"),
    }


def notion_create_page(
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
        properties: ページのプロパティ（titleプロパティが指定されていない場合は自動で追加）

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
            "parent": {
                f"{parent_type}_id": parent_id
            },  # ここが正しく設定されているか確認
            "properties": {"title": {"title": [{"text": {"content": title}}]}},
        }
    else:
        # プロパティが指定されている場合はそれを使用
        data = {
            "parent": {
                f"{parent_type}_id": parent_id
            },  # ここが正しく設定されているか確認
            "properties": properties,
        }
        # titleプロパティがない場合は追加
        if "title" not in properties:
            data["properties"]["title"] = {
                "title": [{"text": {"content": title}}]
            }

    if content:
        data["children"] = content

    # デバッグ用にリクエストデータを出力
    logging.debug(f"Notion create page request data: {data}")

    result = notion_client._make_request("POST", "/pages", data)

    return {
        "success": True,
        "page": result,
        "page_id": result.get("id"),
        "url": result.get("url"),
        "title": title,
    }


def notion_update_page(
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

    result = notion_client._make_request("PATCH", f"/pages/{page_id}", data)

    return {
        "success": True,
        "page": result,
        "page_id": result.get("id"),
        "last_edited_time": result.get("last_edited_time"),
    }


def notion_query_database(
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

    if filter_conditions:
        data["filter"] = filter_conditions

    if sorts:
        data["sorts"] = sorts

    result = notion_client._make_request(
        "POST", f"/databases/{database_id}/query", data
    )

    return {
        "success": True,
        "results": result.get("results", []),
        "has_more": result.get("has_more", False),
        "next_cursor": result.get("next_cursor"),
        "total_count": len(result.get("results", [])),
    }


def notion_create_database(
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

    result = notion_client._make_request("POST", "/databases", data)

    return {
        "success": True,
        "database": result,
        "database_id": result.get("id"),
        "url": result.get("url"),
        "title": title,
    }


def notion_get_block_children(
    block_id: str, page_size: int = 100
) -> Dict[str, Any]:
    """
    ブロックの子要素を取得

    Args:
        block_id: ブロックID（ページIDも可）
        page_size: 結果の最大数

    Returns:
        子ブロックのリスト
    """
    params = {"page_size": min(max(page_size, 1), 100)}

    result = notion_client._make_request(
        "GET", f"/blocks/{block_id}/children", params
    )

    return {
        "success": True,
        "results": result.get("results", []),
        "has_more": result.get("has_more", False),
        "next_cursor": result.get("next_cursor"),
        "total_count": len(result.get("results", [])),
    }


def notion_append_block_children(
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

    result = notion_client._make_request(
        "PATCH", f"/blocks/{block_id}/children", data
    )

    return {
        "success": True,
        "results": result.get("results", []),
        "total_added": len(result.get("results", [])),
    }


def notion_get_users() -> Dict[str, Any]:
    """
    ワークスペースのユーザー一覧を取得

    Returns:
        ユーザーリスト
    """
    result = notion_client._make_request("GET", "/users")

    return {
        "success": True,
        "users": result.get("results", []),
        "total_count": len(result.get("results", [])),
    }


def notion_create_comment(
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

    result = notion_client._make_request("POST", "/comments", data)

    return {
        "success": True,
        "comment": result,
        "comment_id": result.get("id"),
        "created_time": result.get("created_time"),
    }


def _extract_page_title(page_data: Dict) -> str:
    """ページデータからタイトルを抽出"""
    try:
        properties = page_data.get("properties", {})
        for prop_name, prop_data in properties.items():
            if prop_data.get("type") == "title":
                title_array = prop_data.get("title", [])
                if title_array:
                    return (
                        title_array[0]
                        .get("text", {})
                        .get("content", "Untitled")
                    )
        return "Untitled"
    except Exception:
        return "Untitled"


# ツール関数のマッピング（ADK用）
NOTION_TOOLS = {
    "notion_search": notion_search,
    "notion_get_page": notion_get_page,
    "notion_create_page": notion_create_page,
    "notion_update_page": notion_update_page,
    "notion_query_database": notion_query_database,
    "notion_create_database": notion_create_database,
    "notion_get_block_children": notion_get_block_children,
    "notion_append_block_children": notion_append_block_children,
    "notion_get_users": notion_get_users,
    "notion_create_comment": notion_create_comment,
}

notion_tools_list = [
    notion_search,
    notion_get_page,
    notion_create_page,
    notion_update_page,
    notion_query_database,
    notion_create_database,
    notion_get_block_children,
    notion_append_block_children,
    notion_get_users,
    notion_create_comment,
]

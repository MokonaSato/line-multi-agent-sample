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
    children: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Notion MCP Server経由でNotionデータベースに新しいページを作成

    Args:
        parent_database_id: 親データベースのID
        properties: ページのプロパティ（title, rich_text, number, selectなど）
        children: ページの子ブロック（オプション）

    Returns:
        作成されたページの情報を含む辞書
    """
    try:
        logger.info(
            f"Notion MCP Server経由でページを作成: database_id={parent_database_id}"
        )

        result = create_notion_page(
            parent_database_id=parent_database_id,
            properties=properties,
            children=children,
        )

        if result.get("success", False):
            logger.info(f"ページ作成成功: {result.get('id')}")
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"ページ作成失敗: {error_msg}")
            
            # ユーザー向けのわかりやすいエラーメッセージに変換
            if "MCP server is not available" in error_msg:
                result["user_friendly_error"] = (
                    "申し訳ございません。現在Notion連携サービスが利用できません。"
                    "しばらく時間をおいてから再度お試しください。"
                )

        return result
    except Exception as e:
        logger.error(f"notion_create_page_mcp実行中にエラー: {e}")
        return {
            "success": False,
            "error": f"MCP Server通信エラー: {str(e)}",
            "id": None,
            "url": None,
        }


def notion_query_database_mcp(
    database_id: str,
    filter_conditions: Optional[Dict[str, Any]] = None,
    sorts: Optional[List[Dict[str, Any]]] = None,
    page_size: int = 100,
) -> Dict[str, Any]:
    """Notion MCP Server経由でデータベースをクエリ

    Args:
        database_id: クエリするデータベースのID
        filter_conditions: フィルター条件
        sorts: ソート条件
        page_size: 1回で取得するページ数

    Returns:
        クエリ結果を含む辞書
    """
    try:
        logger.info(
            f"Notion MCP Server経由でデータベースをクエリ: {database_id}"
        )

        result = query_notion_database(
            database_id=database_id,
            filter_conditions=filter_conditions,
            sorts=sorts,
            page_size=page_size,
        )

        if result.get("success", False):
            logger.info(
                f"データベースクエリ成功: {len(result.get('results', []))}件"
            )
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"データベースクエリ失敗: {error_msg}")
            
            # ユーザー向けのわかりやすいエラーメッセージに変換
            if "MCP server is not available" in error_msg:
                result["user_friendly_error"] = (
                    "申し訳ございません。現在Notion連携サービスが利用できません。"
                    "しばらく時間をおいてから再度お試しください。"
                )
            elif "404" in error_msg:
                result["user_friendly_error"] = (
                    "指定されたデータベースが見つかりません。"
                    "データベースIDをご確認ください。"
                )

        return result
    except Exception as e:
        logger.error(f"notion_query_database_mcp実行中にエラー: {e}")
        return {
            "success": False,
            "error": f"MCP Server通信エラー: {str(e)}",
            "results": [],
            "has_more": False,
            "next_cursor": None,
        }


def notion_retrieve_page_mcp(page_id: str) -> Dict[str, Any]:
    """Notion MCP Server経由でページを取得

    Args:
        page_id: 取得するページのID

    Returns:
        ページ情報を含む辞書
    """
    try:
        logger.info(f"Notion MCP Server経由でページを取得: {page_id}")

        result = retrieve_notion_page(page_id=page_id)

        if result.get("success", False):
            logger.info(f"ページ取得成功: {page_id}")
        else:
            logger.error(f"ページ取得失敗: {result.get('error')}")

        return result
    except Exception as e:
        logger.error(f"notion_retrieve_page_mcp実行中にエラー: {e}")
        return {
            "success": False,
            "error": f"MCP Server通信エラー: {str(e)}",
            "page": None,
        }


def notion_update_page_mcp(
    page_id: str,
    properties: Optional[Dict[str, Any]] = None,
    archived: Optional[bool] = None,
) -> Dict[str, Any]:
    """Notion MCP Server経由でページを更新

    Args:
        page_id: 更新するページのID
        properties: 更新するプロパティ
        archived: アーカイブ状態

    Returns:
        更新されたページの情報を含む辞書
    """
    try:
        logger.info(f"Notion MCP Server経由でページを更新: {page_id}")

        result = update_notion_page(
            page_id=page_id,
            properties=properties,
            archived=archived,
        )

        if result.get("success", False):
            logger.info(f"ページ更新成功: {page_id}")
        else:
            logger.error(f"ページ更新失敗: {result.get('error')}")

        return result
    except Exception as e:
        logger.error(f"notion_update_page_mcp実行中にエラー: {e}")
        return {
            "success": False,
            "error": f"MCP Server通信エラー: {str(e)}",
            "page": None,
        }


# 利用可能なMCPツールのリスト
notion_mcp_tools_list = [
    notion_create_page_mcp,
    notion_query_database_mcp,
    notion_retrieve_page_mcp,
    notion_update_page_mcp,
]

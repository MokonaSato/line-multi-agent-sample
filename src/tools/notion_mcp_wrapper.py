"""Notion MCP Tools用のレガシー互換ラッパー

Google ADK MCPToolsetで提供されるNotionツールに対して、
従来の関数名でアクセスできるように互換レイヤーを提供します。
"""

from typing import Any, Dict, List, Optional

from src.utils.logger import setup_logger

logger = setup_logger("notion_mcp_wrapper")


def notion_create_page_mcp(
    parent_database_id: str,
    properties: Dict[str, Any],
    children: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Notion MCP Server経由でページを作成する（互換レイヤー）

    この関数は、Google ADK MCPToolsetを使用している場合のレガシー互換性のために提供されています。
    実際の処理は、MCPToolsetに委譲されます。

    Args:
        parent_database_id: 親データベースID
        properties: ページプロパティ
        children: 子コンテンツ（オプション）

    Returns:
        作成されたページの情報
    """
    # 注意: 実際の実装では、MCPToolsetから適切なツールを呼び出す必要があります
    # ここでは、フォールバックとして従来のAPIを使用します

    try:
        from src.tools.notion.recipes.api import notion_create_recipe_page

        # プロパティを適切な形式に変換
        recipe_data = {}

        # プロパティから必要な情報を抽出
        for prop_name, prop_value in properties.items():
            if prop_name == "名前" and "title" in prop_value:
                recipe_data["名前"] = prop_value["title"][0]["text"]["content"]
            elif prop_name == "材料" and "rich_text" in prop_value:
                recipe_data["材料"] = prop_value["rich_text"][0]["text"][
                    "content"
                ]
            elif prop_name == "手順" and "rich_text" in prop_value:
                recipe_data["手順"] = prop_value["rich_text"][0]["text"][
                    "content"
                ]
            elif prop_name == "URL" and "url" in prop_value:
                recipe_data["URL"] = prop_value["url"]

        # notion_create_recipe_pageを呼び出し
        result = notion_create_recipe_page(recipe_data)

        # MCPスタイルの戻り値に変換
        if result.get("success", False):
            return {
                "success": True,
                "id": result.get("page_id"),
                "url": result.get("url"),
                "page": result.get("page"),
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "ページ作成に失敗しました"),
                "id": None,
                "url": None,
            }

    except Exception as e:
        logger.error(f"notion_create_page_mcp wrapper error: {e}")
        return {
            "success": False,
            "error": f"ページ作成中にエラーが発生しました: {str(e)}",
            "id": None,
            "url": None,
        }


def notion_query_database_mcp(
    database_id: str,
    filter_conditions: Optional[Dict[str, Any]] = None,
    sorts: Optional[List[Dict[str, Any]]] = None,
    page_size: int = 100,
) -> Dict[str, Any]:
    """Notion MCP Server経由でデータベースをクエリする（互換レイヤー）

    Args:
        database_id: データベースID
        filter_conditions: フィルター条件
        sorts: ソート条件
        page_size: ページサイズ

    Returns:
        クエリ結果
    """
    try:
        from src.tools.notion.api.databases import query

        result = query(
            database_id=database_id,
            filter_conditions=filter_conditions,
            sorts=sorts,
            page_size=page_size,
        )

        return {
            "success": True,
            "results": result.get("results", []),
            "has_more": result.get("has_more", False),
            "next_cursor": result.get("next_cursor"),
        }

    except Exception as e:
        logger.error(f"notion_query_database_mcp wrapper error: {e}")
        return {
            "success": False,
            "error": f"データベースクエリ中にエラーが発生しました: {str(e)}",
            "results": [],
            "has_more": False,
            "next_cursor": None,
        }


def notion_retrieve_page_mcp(page_id: str) -> Dict[str, Any]:
    """Notion MCP Server経由でページを取得する（互換レイヤー）

    Args:
        page_id: ページID

    Returns:
        ページ情報
    """
    try:
        from src.tools.notion.api.pages import get

        result = get(page_id)

        return {
            "success": True,
            "page": result,
        }

    except Exception as e:
        logger.error(f"notion_retrieve_page_mcp wrapper error: {e}")
        return {
            "success": False,
            "error": f"ページ取得中にエラーが発生しました: {str(e)}",
            "page": None,
        }


def notion_update_page_mcp(
    page_id: str,
    properties: Optional[Dict[str, Any]] = None,
    archived: Optional[bool] = None,
) -> Dict[str, Any]:
    """Notion MCP Server経由でページを更新する（互換レイヤー）

    Args:
        page_id: ページID
        properties: 更新プロパティ
        archived: アーカイブ状態

    Returns:
        更新されたページの情報
    """
    try:
        from src.tools.notion.api.pages import update

        result = update(
            page_id=page_id,
            properties=properties,
            archived=archived,
        )

        return {
            "success": True,
            "page": result,
        }

    except Exception as e:
        logger.error(f"notion_update_page_mcp wrapper error: {e}")
        return {
            "success": False,
            "error": f"ページ更新中にエラーが発生しました: {str(e)}",
            "page": None,
        }


# 互換性のためのツールリスト
notion_mcp_wrapper_tools = [
    notion_create_page_mcp,
    notion_query_database_mcp,
    notion_retrieve_page_mcp,
    notion_update_page_mcp,
]

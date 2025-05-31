"""
レシピデータベース専用の操作関数
"""

import logging
from typing import Any, Dict

from src.tools.notion.api import databases, pages
from src.tools.notion.constants import RECIPE_DATABASE_ID
from src.tools.notion.utils import build_recipe_properties


def search_by_name(recipe_name: str) -> Dict[str, Any]:
    """
    レシピ名でレシピデータベースを検索する専用関数

    Args:
        recipe_name: 検索したいレシピ名

    Returns:
        検索結果のディクショナリ
    """
    # 名前（タイトル）フィールドで検索するフィルター条件
    filter_conditions = {
        "property": "名前",
        "title": {"contains": recipe_name},
    }

    try:
        return databases.query(
            database_id=RECIPE_DATABASE_ID,
            filter_conditions=filter_conditions,
            page_size=10,
        )
    except Exception:
        # フィルター検索に失敗した場合、全件取得してPython側でフィルタリング
        try:
            all_recipes = databases.query(
                database_id=RECIPE_DATABASE_ID, page_size=100
            )

            # Python側でレシピ名フィルタリング
            filtered_results = []
            if all_recipes.get("success") and all_recipes.get("results"):
                for recipe in all_recipes["results"]:
                    title_property = recipe.get("properties", {}).get(
                        "名前", {}
                    )
                    if title_property.get("type") == "title":
                        title_parts = title_property.get("title", [])
                        if title_parts:
                            full_title = "".join(
                                [
                                    part.get("text", {}).get("content", "")
                                    for part in title_parts
                                ]
                            )
                            if recipe_name.lower() in full_title.lower():
                                filtered_results.append(recipe)

            return {
                "success": True,
                "results": filtered_results,
                "has_more": False,
                "next_cursor": None,
                "total_count": len(filtered_results),
                "note": "Filtered locally due to API filter error",
            }
        except Exception as fallback_error:
            return {
                "success": False,
                "error": f"検索に失敗しました: {str(fallback_error)}",
                "results": [],
                "total_count": 0,
            }


def get_all() -> Dict[str, Any]:
    """
    レシピデータベースからすべてのレシピを取得する関数

    Returns:
        全レシピの情報
    """
    return databases.query(database_id=RECIPE_DATABASE_ID, page_size=100)


def create(recipe_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    レシピデータベース専用のページ作成関数

    Args:
        recipe_data: レシピデータ（名前、材料、手順、etc.）

    Returns:
        作成されたページの情報
    """
    logging.info(f"Creating recipe page with data: {list(recipe_data.keys())}")

    try:
        # APIトークンの存在確認
        from config import NOTION_TOKEN

        if not NOTION_TOKEN:
            error_message = "NOTION_TOKEN が設定されていません。環境変数を確認してください。"
            logging.error(error_message)
            return {
                "success": False,
                "error": "Notion API トークンが設定されていません。環境変数 NOTION_TOKEN を確認してください。",
                "page_id": None,
                "url": None,
                "error_type": "token_missing",
            }

        # データベースIDの確認
        if not RECIPE_DATABASE_ID:
            error_message = "レシピデータベースIDが設定されていません"
            logging.error(error_message)
            return {
                "success": False,
                "error": error_message,
                "page_id": None,
                "url": None,
                "error_type": "database_id_missing",
            }

        # レシピデータからプロパティを構築
        properties = build_recipe_properties(recipe_data)

        logging.info(f"Built properties: {list(properties.keys())}")
        logging.debug(f"Properties detail: {properties}")
        # 一時的にプロパティの詳細をINFOレベルで出力（デバッグのため）
        logging.info(f"詳細なプロパティ: {properties}")

        # 必須フィールドの検証
        if "名前" not in properties or not properties["名前"]["title"]:
            error_message = "レシピ名が設定されていません"
            logging.error(error_message)
            return {
                "success": False,
                "error": error_message,
                "page_id": None,
                "url": None,
                "error_type": "validation_error",
            }

        # 必須パラメータの事前検証 (parent_id, title, properties)
        if not recipe_data.get("名前"):
            error_message = "レシピ名(title)が設定されていません"
            logging.error(error_message)
            return {
                "success": False,
                "error": error_message,
                "page_id": None,
                "url": None,
                "error_type": "missing_parameter",
            }

        # ページ作成
        result = pages.create(
            parent_id=RECIPE_DATABASE_ID,
            title=recipe_data.get("名前", "新しいレシピ"),
            parent_type="database",
            properties=properties,
        )

        # レスポンスの検証
        if not result.get("success", False):
            error_message = result.get("error", "不明なエラー")
            logging.error(f"Notion APIエラー: {error_message}")

            # エラータイプの特定
            error_type = "api_error"

            # パラメータ不足エラーの検出
            if "missing required parameters" in error_message.lower():
                error_type = "missing_parameter"
                error_message = (
                    f"{error_message} - 必須パラメータが不足しています。"
                    f"APIリクエストを確認してください"
                )

            # トークン関連のエラーメッセージをより明確に
            elif (
                "API Token" in error_message
                or "token" in error_message.lower()
            ):
                error_message = (
                    f"{error_message} - 環境変数NOTIONTOKENを確認してください"
                )
                error_type = "token_error"

            result["error_type"] = error_type
            return result

        logging.info(
            f"レシピ'{recipe_data.get('名前')}' が正常に登録されました。"
            f"ID: {result.get('page_id')}"
        )
        return result

    except Exception as e:
        error_message = f"レシピ登録中に例外が発生しました: {e}"
        logging.exception(error_message)

        # エラータイプを特定してメッセージを追加する
        error_type = "unknown_error"
        if "token" in str(e).lower() or "authorization" in str(e).lower():
            error_type = "token_error"
            error_message = (
                f"{error_message} - Notion APIトークンを確認してください"
            )
        elif "missing required parameters" in str(e).lower():
            error_type = "missing_parameter"
            error_message = (
                f"{error_message} - 必須パラメータ(parent_id, title, properties)"
                f"が不足しています"
            )

        return {
            "success": False,
            "error": error_message,
            "page_id": None,
            "url": None,
            "error_type": error_type,
        }

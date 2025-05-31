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

    # レシピデータからプロパティを構築
    properties = build_recipe_properties(recipe_data)

    logging.info(f"Built properties: {list(properties.keys())}")
    logging.debug(f"Properties detail: {properties}")
    # 一時的にプロパティの詳細をINFOレベルで出力（デバッグのため）
    logging.info(f"詳細なプロパティ: {properties}")

    # ページ作成
    return pages.create(
        parent_id=RECIPE_DATABASE_ID,
        title=recipe_data.get("名前", "新しいレシピ"),
        parent_type="database",
        properties=properties,
    )

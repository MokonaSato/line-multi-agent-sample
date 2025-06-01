"""
Notion APIフィルター条件構築のためのユーティリティ関数
"""

import logging
from typing import Any, Dict, List, Optional


def build_text_filter(
    property_name: str, text_value: str, operator: str = "contains"
) -> Dict[str, Any]:
    """
    テキスト系プロパティのフィルター条件を構築

    Args:
        property_name: プロパティ名
        text_value: 検索する文字列
        operator: 演算子 (contains, equals, starts_with, ends_with)

    Returns:
        フィルター条件の辞書
    """
    return {"property": property_name, "rich_text": {operator: text_value}}


def build_title_filter(
    property_name: str, title_value: str, operator: str = "contains"
) -> Dict[str, Any]:
    """
    タイトルプロパティのフィルター条件を構築

    Args:
        property_name: プロパティ名
        title_value: 検索するタイトル文字列
        operator: 演算子 (contains, equals, starts_with, ends_with)

    Returns:
        フィルター条件の辞書
    """
    return {"property": property_name, "title": {operator: title_value}}


def build_select_filter(
    property_name: str, select_value: str
) -> Dict[str, Any]:
    """
    セレクトプロパティのフィルター条件を構築

    Args:
        property_name: プロパティ名
        select_value: 選択する値

    Returns:
        フィルター条件の辞書
    """
    return {"property": property_name, "select": {"equals": select_value}}


def build_multi_select_filter(
    property_name: str, select_value: str, operator: str = "contains"
) -> Dict[str, Any]:
    """
    マルチセレクトプロパティのフィルター条件を構築

    Args:
        property_name: プロパティ名
        select_value: 検索する選択肢の値
        operator: 演算子 (contains, does_not_contain)

    Returns:
        フィルター条件の辞書
    """
    return {
        "property": property_name,
        "multi_select": {operator: select_value},
    }


def build_number_filter(
    property_name: str, number_value: float, operator: str = "equals"
) -> Dict[str, Any]:
    """
    数値プロパティのフィルター条件を構築

    Args:
        property_name: プロパティ名
        number_value: 数値
        operator: 演算子
            (equals, greater_than, less_than,
            greater_than_or_equal_to, less_than_or_equal_to)

    Returns:
        フィルター条件の辞書
    """
    return {"property": property_name, "number": {operator: number_value}}


def build_checkbox_filter(
    property_name: str, checkbox_value: bool
) -> Dict[str, Any]:
    """
    チェックボックスプロパティのフィルター条件を構築

    Args:
        property_name: プロパティ名
        checkbox_value: チェック状態 (True/False)

    Returns:
        フィルター条件の辞書
    """
    return {"property": property_name, "checkbox": {"equals": checkbox_value}}


def build_and_filter(conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    AND条件でフィルターを組み合わせる

    Args:
        conditions: フィルター条件のリスト

    Returns:
        AND条件の辞書
    """
    return {"and": conditions}


def build_or_filter(conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    OR条件でフィルターを組み合わせる

    Args:
        conditions: フィルター条件のリスト

    Returns:
        OR条件の辞書
    """
    return {"or": conditions}


def build_recipe_category_filter(category: str) -> Dict[str, Any]:
    """
    レシピのカテゴリフィルターを構築（マルチセレクト対応）

    Args:
        category: カテゴリ名（例: "メインディッシュ", "デザート"）

    Returns:
        カテゴリフィルター条件
    """
    # まずマルチセレクトとして試行
    return build_multi_select_filter("カテゴリ", category, "contains")


def build_recipe_search_filter(
    recipe_name: Optional[str] = None,
    category: Optional[str] = None,
    cooking_time_max: Optional[int] = None,
    serving_size: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """
    レシピ検索用の複合フィルターを構築

    Args:
        recipe_name: レシピ名（部分一致）
        category: カテゴリ名
        cooking_time_max: 最大調理時間（分）
        serving_size: 人数

    Returns:
        複合フィルター条件（すべてNoneの場合はNone）
    """
    conditions = []

    if recipe_name:
        conditions.append(build_title_filter("名前", recipe_name, "contains"))

    if category:
        conditions.append(build_recipe_category_filter(category))

    if cooking_time_max is not None:
        conditions.append(
            build_number_filter(
                "調理時間", cooking_time_max, "less_than_or_equal_to"
            )
        )

    if serving_size is not None:
        conditions.append(build_number_filter("人数", serving_size, "equals"))

    if not conditions:
        return None

    if len(conditions) == 1:
        return conditions[0]

    return build_and_filter(conditions)


def safe_query_with_fallback(
    database_id: str,
    filter_conditions: Optional[Dict[str, Any]] = None,
    sorts: Optional[List[Dict[str, Any]]] = None,
    page_size: int = 100,
) -> Dict[str, Any]:
    """
    フィルター条件でクエリを実行し、エラーの場合はフィルターなしで再試行

    Args:
        database_id: データベースID
        filter_conditions: フィルター条件
        sorts: ソート条件
        page_size: 結果の最大数

    Returns:
        クエリ結果
    """
    from src.tools.notion.api.databases import query

    try:
        # まずフィルター付きで試行
        result = query(database_id, filter_conditions, sorts, page_size)
        return result

    except Exception as e:
        error_message = str(e)

        # フィルタータイプエラーの場合
        if (
            "property type" in error_message
            and "does not match" in error_message
        ):

            logging.warning(
                f"フィルタータイプエラーのため、フィルターなしで再試行: {error_message}"
            )

            try:
                # フィルターなしで再試行
                result = query(database_id, None, sorts, page_size)
                result["note"] = (
                    "フィルタータイプエラーのため、フィルターなしで実行しました"
                )
                return result

            except Exception as retry_error:
                logging.error(f"フィルターなし再試行も失敗: {retry_error}")
                return {
                    "success": False,
                    "error": f"フィルターエラー後の再試行も失敗: {str(retry_error)}",
                    "results": [],
                    "total_count": 0,
                }

        # その他のエラーの場合は元のエラーを返す
        raise e

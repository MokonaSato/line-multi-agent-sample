"""
Notion API のデータベース操作関数
"""

from typing import Any, Dict, List, Optional

from src.tools.notion.client import client


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


def validate_filter_conditions(
    filter_conditions: Dict[str, Any],
    database_properties: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    フィルター条件を検証し、プロパティタイプに応じて修正する

    Args:
        filter_conditions: 元のフィルター条件
        database_properties: データベースのプロパティ情報

    Returns:
        修正されたフィルター条件
    """
    if not filter_conditions or not isinstance(filter_conditions, dict):
        return filter_conditions

    # プロパティ情報が利用可能な場合、フィルタータイプを検証・修正
    if database_properties and "property" in filter_conditions:
        property_name = filter_conditions["property"]

        if property_name in database_properties:
            property_info = database_properties[property_name]
            property_type = property_info.get("type")

            # multi_selectプロパティの場合の修正
            if property_type == "multi_select":
                # selectフィルターが使用されている場合はmulti_selectに修正
                if "select" in filter_conditions:
                    select_condition = filter_conditions.pop("select")
                    filter_conditions["multi_select"] = {
                        "contains": select_condition.get("equals", "")
                    }
                # equalsが使用されている場合もmulti_selectのcontainsに修正
                elif "equals" in filter_conditions:
                    equals_value = filter_conditions.pop("equals")
                    filter_conditions["multi_select"] = {
                        "contains": equals_value
                    }

            # selectプロパティの場合
            elif property_type == "select":
                # multi_selectフィルターが使用されている場合はselectに修正
                if "multi_select" in filter_conditions:
                    multi_select_condition = filter_conditions.pop(
                        "multi_select"
                    )
                    if "contains" in multi_select_condition:
                        filter_conditions["select"] = {
                            "equals": multi_select_condition["contains"]
                        }

    return filter_conditions


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
            try:
                # データベース情報を取得してプロパティタイプを確認
                db_info = get(database_id)
                database_properties = db_info.get("properties", {})

                # フィルター条件を検証・修正
                validated_filter = validate_filter_conditions(
                    filter_conditions, database_properties
                )
                data["filter"] = validated_filter

            except Exception as e:
                # データベース情報の取得に失敗した場合は元のフィルターを使用
                import logging

                logging.warning(
                    f"フィルター検証でデータベース情報取得に失敗: {e}"
                )
                data["filter"] = filter_conditions
        # 空のフィルター条件や不正な形式の場合は無視
        else:
            # フィルターなしでクエリ実行
            pass

    if sorts:
        data["sorts"] = sorts

    try:
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

    except Exception as e:
        error_message = str(e)

        # フィルタータイプエラーの場合は、フィルターなしで再試行
        if (
            "property type" in error_message
            and "does not match" in error_message
            and filter_conditions
        ):

            import logging

            logging.warning(
                f"フィルタータイプエラーのため、フィルターなしで再試行: {error_message}"
            )

            try:
                # フィルターなしで再試行
                retry_data = {"page_size": data["page_size"]}
                if sorts:
                    retry_data["sorts"] = sorts

                result = client._make_request(
                    "POST", f"/databases/{database_id}/query", retry_data
                )

                return {
                    "success": True,
                    "results": result.get("results", []),
                    "has_more": result.get("has_more", False),
                    "next_cursor": result.get("next_cursor"),
                    "total_count": len(result.get("results", [])),
                    "note": "フィルタータイプエラーのため、フィルターなしで実行しました",
                }
            except Exception as retry_error:
                return {
                    "success": False,
                    "error": f"再試行も失敗: {str(retry_error)}",
                    "results": [],
                    "total_count": 0,
                }

        # その他のエラーの場合
        return {
            "success": False,
            "error": error_message,
            "results": [],
            "total_count": 0,
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

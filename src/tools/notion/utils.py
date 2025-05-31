"""
Notion API 操作のための共通ユーティリティ関数
"""

import logging
from typing import Any, Dict


def extract_page_title(page_data: Dict) -> str:
    """
    ページデータからタイトルを抽出

    Args:
        page_data: ページデータ

    Returns:
        抽出されたタイトル文字列。失敗時は "Untitled"
    """
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


def build_recipe_properties(recipe_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    レシピデータからNotionプロパティを構築（null値対応）

    Args:
        recipe_data: レシピデータ辞書

    Returns:
        Notionプロパティ形式の辞書
    """
    properties = {}

    # タイトルプロパティ（名前）
    if "名前" in recipe_data and recipe_data["名前"]:
        properties["名前"] = {
            "title": [{"text": {"content": str(recipe_data["名前"])}}]
        }

    # リッチテキストプロパティ
    for field_name in ["材料", "手順"]:
        if field_name in recipe_data and recipe_data[field_name]:
            content = str(recipe_data[field_name])
            # 2000文字制限対応
            if len(content) > 2000:
                content = content[:1997] + "..."
            properties[field_name] = {
                "rich_text": [{"text": {"content": content}}]
            }

    # 数値プロパティ（null値対応）
    for field_name in ["人数", "調理時間", "保存期間"]:
        if field_name in recipe_data:
            value = recipe_data[field_name]

            # null値、"null"文字列、空文字列の場合はプロパティ自体を設定しない
            # （Notionでは設定しないことで空欄になる）
            if (
                value is None
                or value == "null"
                or str(value).lower() == "null"
                or value == ""
            ):
                # 空欄にするためプロパティを設定しない
                continue
            else:
                # 数値に変換、失敗した場合もプロパティを設定しない
                try:
                    numeric_value = float(value)
                    # 有効な数値の場合のみプロパティを設定
                    if not (numeric_value != numeric_value):  # NaNチェック
                        # Notion APIの要求に従い、数値プロパティを設定（単純な値ではなくオブジェクト）
                        properties[field_name] = {"number": numeric_value}
                except (ValueError, TypeError):
                    # 変換に失敗した場合はプロパティを設定しない（空欄）
                    continue

    # URLプロパティ
    if "URL" in recipe_data and recipe_data["URL"]:
        url_value = str(recipe_data["URL"]) if recipe_data["URL"] else ""
        if url_value and url_value.strip():
            properties["URL"] = {"url": url_value}

    logging.info(f"生成されたプロパティキー: {list(properties.keys())}")
    return properties

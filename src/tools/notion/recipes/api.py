"""
レシピデータベース専用の操作関数
"""

import logging
from typing import Any, Dict

from src.tools.notion.api import databases, pages
from src.tools.notion.constants import RECIPE_DATABASE_ID
from src.tools.notion.utils import build_recipe_properties


def validate_and_fix_recipe_data(
    recipe_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    レシピデータを検証し、必要に応じて修正または補完する

    Args:
        recipe_data: 元のレシピデータ

    Returns:
        検証・修正済みのレシピデータ
    """
    validated = {}

    # 必須フィールドの検証と補完
    validated["名前"] = recipe_data.get("名前") or "無題のレシピ"
    validated["材料"] = recipe_data.get("材料") or "材料情報なし"
    validated["手順"] = recipe_data.get("手順") or "手順情報なし"

    # 数値フィールドの検証
    for field in ["人数", "調理時間", "保存期間"]:
        value = recipe_data.get(field)
        try:
            if value is not None and value != "":
                # 数値変換を試みる
                num_value = float(value)
                validated[field] = num_value
            else:
                validated[field] = None
        except (ValueError, TypeError):
            # 数値変換に失敗した場合はNoneを設定
            validated[field] = None

    # URL
    validated["URL"] = recipe_data.get("URL", "")

    logging.info(
        (
            "レシピデータ検証結果: 必須項目="
            f"{validated['名前'] != '無題のレシピ' and validated['材料'] != '材料情報なし' and validated['手順'] != '手順情報なし'}"
        )
    )

    return validated


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
    # 入力データの詳細ログ
    logging.info(
        f"Creating recipe page with data keys: {list(recipe_data.keys())}"
    )
    # 必須フィールドの存在をログ出力
    required_fields = ["名前", "材料", "手順"]
    for field in required_fields:
        if field not in recipe_data or not recipe_data[field]:
            logging.warning(f"必須フィールド '{field}' が不足しているか空です")
        else:
            logging.info(f"'{field}' フィールド: {recipe_data[field][:30]}...")

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

        # 受け取ったデータの検証と補完
        validated_data = validate_and_fix_recipe_data(recipe_data)
        logging.info(f"検証済みレシピデータ: {list(validated_data.keys())}")

        # レシピデータからプロパティを構築
        properties = build_recipe_properties(validated_data)

        logging.info(f"Built properties: {list(properties.keys())}")
        logging.debug(f"Properties detail: {properties}")
        # 一時的にプロパティの詳細をINFOレベルで出力（デバッグのため）
        logging.info(f"詳細なプロパティ: {properties}")

        # 必須フィールドの最終検証
        if "名前" not in properties or not properties.get("名前", {}).get(
            "title"
        ):
            # エラーの場合、デフォルトタイトルを設定する
            logging.warning(
                "レシピ名が設定されていないため、デフォルト値を使用します"
            )
            properties["名前"] = {
                "title": [{"text": {"content": "無題のレシピ"}}]
            }

        # 必須プロパティが存在することを確認
        required_props = ["材料", "手順"]
        for prop in required_props:
            if prop not in properties:
                logging.warning(
                    f"{prop}が設定されていないため、デフォルト値を使用します"
                )
                properties[prop] = {
                    "rich_text": [{"text": {"content": f"{prop}情報なし"}}]
                }

        # ページ作成前の最終準備
        final_title = validated_data.get("名前", "無題のレシピ")
        if not final_title or final_title == "無題のレシピ":
            logging.warning("タイトルが未設定なので、デフォルト値を使用します")
            final_title = "無題のレシピ"

        logging.info(
            f"送信データ: parent_id={RECIPE_DATABASE_ID}, title={final_title}, properties={list(properties.keys())}"
        )

        # ページ作成
        result = pages.create(
            parent_id=RECIPE_DATABASE_ID,
            title=final_title,
            parent_type="database",
            properties=properties,
        )

        # レスポンスの検証
        if not result.get("success", False):
            error_message = result.get("error", "不明なエラー")
            logging.error(f"Notion APIエラー: {error_message}")

            # エラータイプの特定とロギング
            error_type = result.get("error_type", "api_error")

            # より詳細なデバッグ情報
            logging.error(
                f"エラー詳細: type={error_type}, message={error_message}"
            )
            logging.error(
                f"使用されたパラメータ: title={final_title}, database_id={RECIPE_DATABASE_ID}, properties_keys={list(properties.keys())}"
            )

            # サーバーエラーの特別処理（より広範なエラーパターンに対応）
            if (
                "502 Bad Gateway" in error_message
                or "503" in error_message
                or "504" in error_message
                or "500" in error_message
                or "temporary_server_error" in error_message
                or "サーバーが混雑" in error_message
                or "応答していません" in error_message
            ):
                error_type = "temporary_server_error"
                error_message = (
                    "Notion APIサーバーが一時的に利用できません。"
                    "サーバーが混雑しているため、数分後に再試行してください。"
                )

            # 特定のエラーケースへの対応
            elif "missing required parameters" in error_message.lower():
                error_type = "missing_parameter"
                error_message = (
                    f"{error_message} - Notion API必須パラメータ(parent_id, "
                    f"title, properties)が不足しています"
                )

            # トークン関連のエラー
            elif (
                "API Token" in error_message
                or "token" in error_message.lower()
            ):
                error_message = (
                    f"{error_message} - 環境変数NOTIONTOKENを確認してください"
                )
                error_type = "token_error"

            # エラー情報を結果に追加
            result["error_type"] = error_type
            result["error_details"] = {
                "used_title": final_title,
                "used_database_id": RECIPE_DATABASE_ID,
                "properties_keys": list(properties.keys()),
            }
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

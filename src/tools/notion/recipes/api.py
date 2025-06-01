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
    missing required parametersエラーを防ぐため、必須フィールドを確実に設定

    Args:
        recipe_data: 元のレシピデータ

    Returns:
        検証・修正済みのレシピデータ
    """
    validated = {}

    # 必須フィールドの厳格な検証と補完
    # 空文字列、None、undefined の場合は必ずデフォルト値を設定
    name = recipe_data.get("名前")
    if not name or str(name).strip() == "" or str(name).lower() == "null":
        validated["名前"] = "無題のレシピ"
        logging.warning(
            "レシピ名が未設定のため、デフォルト値を設定: 無題のレシピ"
        )
    else:
        validated["名前"] = str(name).strip()

    ingredients = recipe_data.get("材料")
    if (
        not ingredients
        or str(ingredients).strip() == ""
        or str(ingredients).lower() == "null"
    ):
        validated["材料"] = "材料情報なし"
        logging.warning("材料が未設定のため、デフォルト値を設定: 材料情報なし")
    else:
        validated["材料"] = str(ingredients).strip()

    instructions = recipe_data.get("手順")
    if (
        not instructions
        or str(instructions).strip() == ""
        or str(instructions).lower() == "null"
    ):
        validated["手順"] = "手順情報なし"
        logging.warning("手順が未設定のため、デフォルト値を設定: 手順情報なし")
    else:
        validated["手順"] = str(instructions).strip()

    # 数値フィールドの厳格な検証
    for field in ["人数", "調理時間", "保存期間"]:
        value = recipe_data.get(field)
        try:
            if (
                value is not None
                and str(value).strip() != ""
                and str(value).lower() != "null"
            ):
                # 数値変換を試みる
                num_value = float(value)
                # NaN（Not a Number）をチェック
                if num_value != num_value:  # NaNチェック
                    validated[field] = None
                    logging.warning(f"{field}がNaNのため、Noneを設定")
                else:
                    validated[field] = num_value
                    logging.info(f"{field}を数値として設定: {num_value}")
            else:
                validated[field] = None
                logging.info(f"{field}が空のため、Noneを設定")
        except (ValueError, TypeError) as e:
            # 数値変換に失敗した場合はNoneを設定
            validated[field] = None
            logging.warning(
                f"{field}の数値変換に失敗({value})、Noneを設定: {e}"
            )

    # URL フィールド
    url = recipe_data.get("URL", "")
    validated["URL"] = str(url) if url is not None else ""

    # 検証結果をログ出力
    logging.info(
        f"レシピデータ検証完了: 名前='{validated['名前']}', "
        f"材料長={len(validated['材料'])}, 手順長={len(validated['手順'])}, "
        f"人数={validated['人数']}, 調理時間={validated['調理時間']}, "
        f"保存期間={validated['保存期間']}"
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


def notion_create_recipe_page(recipe_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    レシピ専用のページ作成関数
    missing required parametersエラーを防ぐため、厳格なパラメータ検証を実施

    **重要**: この関数は notion_create_recipe_page として直接呼び出される

    Args:
        recipe_data: レシピデータ（名前、材料、手順、etc.）

    Returns:
        作成されたページの情報
    """
    # 入力データの詳細ログ
    logging.info(
        "notion_create_recipe_page called with data keys: %s",
        list(recipe_data.keys()),
    )

    # 必須フィールドの存在をログ出力
    required_fields = ["名前", "材料", "手順"]
    for field in required_fields:
        if field not in recipe_data or not recipe_data[field]:
            logging.warning(f"必須フィールド '{field}' が不足しているか空です")
        else:
            logging.info(
                f"'{field}' フィールド: {str(recipe_data[field])[:30]}..."
            )

    try:
        # APIトークンの存在確認
        from config import NOTION_TOKEN

        if not NOTION_TOKEN:
            error_message = "NOTION_TOKEN が設定されていません。環境変数を確認してください。"
            logging.error(error_message)
            return {
                "success": False,
                "error": (
                    "Notion API トークンが設定されていません。"
                    "環境変数 NOTION_TOKEN を確認してください。"
                ),
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

        # 受け取ったデータの厳格な検証と補完
        validated_data = validate_and_fix_recipe_data(recipe_data)
        logging.info(f"検証済みレシピデータ: {list(validated_data.keys())}")

        # レシピデータからプロパティを構築
        properties = build_recipe_properties(validated_data)

        logging.info(f"Built properties: {list(properties.keys())}")
        logging.debug(f"Properties detail: {properties}")

        # 必須フィールドの最終検証（missing required parametersエラー防止）
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

        # ページ作成前の最終準備と検証
        final_title = validated_data.get("名前", "無題のレシピ")
        if not final_title or final_title == "無題のレシピ":
            logging.warning("タイトルが未設定なので、デフォルト値を使用します")
            final_title = "無題のレシピ"

        # missing required parametersエラーを防ぐための最終チェック
        if not RECIPE_DATABASE_ID:
            return {
                "success": False,
                "error": "parent_id (データベースID) が設定されていません",
                "error_type": "missing_parameter",
                "page_id": None,
                "url": None,
            }

        if not final_title:
            return {
                "success": False,
                "error": "title (レシピ名) が設定されていません",
                "error_type": "missing_parameter",
                "page_id": None,
                "url": None,
            }

        if not properties:
            return {
                "success": False,
                "error": "properties (レシピプロパティ) が設定されていません",
                "error_type": "missing_parameter",
                "page_id": None,
                "url": None,
            }

        logging.info(
            (
                f"送信データ: parent_id={RECIPE_DATABASE_ID}, "
                f"title={final_title}, "
                f"properties={list(properties.keys())}"
            )
        )

        # ページ作成 - 必須パラメータを明示的に設定
        result = pages.create(
            parent_id=RECIPE_DATABASE_ID,  # 必須パラメータ1
            title=final_title,  # 必須パラメータ2
            parent_type="database",
            properties=properties,  # 必須パラメータ3
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
                (
                    f"使用されたパラメータ: title={final_title}, "
                    f"database_id={RECIPE_DATABASE_ID}, "
                    f"properties_keys={list(properties.keys())}"
                )
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
                    f"{error_message} - 環境変数NOTION_TOKENを確認してください"
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


def search_recipes_with_category(
    category: str = None,
    recipe_name: str = None,
    cooking_time_max: int = None,
    serving_size: int = None,
) -> Dict[str, Any]:
    """
    カテゴリやその他の条件でレシピを検索する関数
    マルチセレクトプロパティに適切に対応

    Args:
        category: カテゴリ名（例: "メインディッシュ", "デザート"）
        recipe_name: レシピ名（部分一致）
        cooking_time_max: 最大調理時間（分）
        serving_size: 人数

    Returns:
        検索結果のディクショナリ
    """
    try:
        from src.tools.notion.filter_utils import (
            build_recipe_search_filter,
            safe_query_with_fallback,
        )

        # フィルター条件を構築
        filter_conditions = build_recipe_search_filter(
            recipe_name=recipe_name,
            category=category,
            cooking_time_max=cooking_time_max,
            serving_size=serving_size,
        )

        # 安全なクエリ実行
        result = safe_query_with_fallback(
            database_id=RECIPE_DATABASE_ID,
            filter_conditions=filter_conditions,
            page_size=50,
        )

        return result

    except Exception as e:
        logging.error(f"レシピカテゴリ検索中にエラー: {e}")

        # フォールバック: 全件取得してPython側でフィルタリング
        try:
            all_recipes = databases.query(
                database_id=RECIPE_DATABASE_ID, page_size=100
            )

            if not all_recipes.get("success"):
                return all_recipes

            filtered_results = []
            for recipe in all_recipes.get("results", []):
                properties = recipe.get("properties", {})

                # カテゴリフィルタリング
                if category:
                    category_prop = properties.get("カテゴリ", {})
                    if category_prop.get("type") == "multi_select":
                        categories = category_prop.get("multi_select", [])
                        category_names = [
                            cat.get("name", "") for cat in categories
                        ]
                        if not any(
                            category.lower() in cat_name.lower()
                            for cat_name in category_names
                        ):
                            continue

                # レシピ名フィルタリング
                if recipe_name:
                    title_prop = properties.get("名前", {})
                    if title_prop.get("type") == "title":
                        title_parts = title_prop.get("title", [])
                        full_title = "".join(
                            [
                                part.get("text", {}).get("content", "")
                                for part in title_parts
                            ]
                        )
                        if recipe_name.lower() not in full_title.lower():
                            continue

                # 調理時間フィルタリング
                if cooking_time_max is not None:
                    time_prop = properties.get("調理時間", {})
                    if time_prop.get("type") == "number":
                        cooking_time = time_prop.get("number")
                        if (
                            cooking_time is not None
                            and cooking_time > cooking_time_max
                        ):
                            continue

                # 人数フィルタリング
                if serving_size is not None:
                    size_prop = properties.get("人数", {})
                    if size_prop.get("type") == "number":
                        size = size_prop.get("number")
                        if size is not None and size != serving_size:
                            continue

                filtered_results.append(recipe)

            return {
                "success": True,
                "results": filtered_results,
                "has_more": False,
                "next_cursor": None,
                "total_count": len(filtered_results),
                "note": "Python側でフィルタリングを実行しました",
            }

        except Exception as fallback_error:
            return {
                "success": False,
                "error": f"フォールバック検索も失敗: {str(fallback_error)}",
                "results": [],
                "total_count": 0,
            }


# 後方互換性のためのエイリアス
create = notion_create_recipe_page

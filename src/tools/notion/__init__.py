"""
Notion API ツールの統合エントリポイント
元の単一ファイルからモジュール分割したNotionツール

このモジュールからは従来の関数名でエクスポートし、
後方互換性を保ちながらも内部実装を整理する
"""

from src.tools.notion.api import (
    append_block_children,
    create_comment,
    create_database,
    create_page,
    get_block_children,
    get_database,
    get_page,
    get_users,
    query_database,
    search,
    update_page,
)
from src.tools.notion.filter_utils import (  # noqa: F401
    build_multi_select_filter,
    build_recipe_search_filter,
    build_title_filter,
    safe_query_with_fallback,
)

# Notion MCP ツール（廃止済み - MCPToolsetを直接使用）
from src.tools.notion.mcp_tools import notion_mcp_tools_list
from src.tools.notion.recipes import create as create_recipe
from src.tools.notion.recipes import get_all as get_all_recipes
from src.tools.notion.recipes import search_by_name as search_recipes_by_name
from src.tools.notion.recipes import search_recipes_with_category  # noqa: F401

# 後方互換性のための関数エイリアス
notion_search = search
notion_get_page = get_page
notion_create_page = create_page
notion_update_page = update_page
notion_query_database = query_database
notion_get_database = get_database
notion_create_database = create_database
notion_get_block_children = get_block_children
notion_append_block_children = append_block_children
notion_get_users = get_users
notion_create_comment = create_comment

# レシピ関連 - エラー防止のため専用関数を明確に定義
notion_create_recipe_page = create_recipe
notion_search_recipes_by_name = search_recipes_by_name
notion_get_all_recipes = get_all_recipes

# ADK用ツール関数のマッピング - フォールバック用
notion_tools_combined = [
    # 基本的なページ操作
    notion_get_page,
    notion_create_page,
    notion_update_page,
    # データベース操作
    notion_query_database,
    notion_get_database,
    # レシピ専用操作
    notion_create_recipe_page,
    notion_search_recipes_by_name,
    # 検索機能
    notion_search,
]

# カテゴリー別ツールマッピング（今後の拡張用）
TOOLS = {
    "search": [notion_search, notion_query_database],
    "pages": [
        notion_get_page,
        notion_create_page,
        notion_update_page,
    ],
    "databases": [
        notion_query_database,
        notion_get_database,
        notion_create_database,
    ],
    "blocks": [notion_get_block_children, notion_append_block_children],
    "users": [notion_get_users],
    "comments": [notion_create_comment],
    "recipes": [
        notion_create_recipe_page,
        notion_search_recipes_by_name,
        notion_get_all_recipes,
        notion_create_page,  # 汎用ページ作成も含める
        notion_query_database,  # データベース検索も含める
    ],
    "general": [
        # 汎用的な操作をまとめたセット
        notion_search,
        notion_get_page,
        notion_create_page,
        notion_update_page,
        notion_query_database,
        notion_get_database,
        notion_create_recipe_page,
    ],
}

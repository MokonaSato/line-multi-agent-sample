"""
Notionツールで使用する定数の定義
"""

# レシピデータベースのプロパティマッピング
RECIPE_PROPERTY_MAPPING = {
    "名前": {
        "property_id": "title",  # これがタイトルプロパティのID
        "type": "title",
    },
    "材料": {"property_id": "%60DJT", "type": "rich_text"},
    "手順": {"property_id": "~wUl", "type": "rich_text"},
    "人数": {"property_id": "R%40xc", "type": "number"},
    "調理時間": {"property_id": "sD%3CH", "type": "number"},
    "保存期間": {"property_id": "%5BZRQ", "type": "number"},
    "URL": {"property_id": "RfME", "type": "url"},
}

# レシピデータベースID
RECIPE_DATABASE_ID = "recipe-database-id"

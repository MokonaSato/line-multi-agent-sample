"""エージェントサービスの定数と設定

このモジュールには、エージェントサービスで使用される定数や設定値を定義します。
応答パターンやアプリケーション設定などを一元管理します。
"""

# アプリケーション名
APP_NAME = "line_multi_agent"

# レスポンス判定用パターン
# 完了を示す指標
COMPLETION_INDICATORS = [
    "レシピ登録成功",
    "✅",
    "登録されたページID",
    "ページURL:",
    "Step 4完了",
    "最終結果",
    "registration_result",
    "画像からのレシピ抽出・登録が完了しました",
    "処理が完了しました",
]

# エラーメッセージを示す指標
ERROR_INDICATORS = [
    "エラーが発生しました",
    "❌",
    "失敗しました",
    "機能はございません",
]

# 中間応答のパターン
INTERMEDIATE_PATTERNS = [
    "ContentExtractionAgent",
    "DataTransformationAgent",
    "ImageAnalysisAgent",
    "ImageDataEnhancementAgent",
    "extracted_recipe_data",
    "extracted_image_data",
    "enhanced_recipe_data",
    "notion_formatted_data",
]

# エージェント設定
AGENT_CONFIG = {
    "min_final_response_length": 50,  # 最終応答とみなす最小文字数
    "min_steps_for_sequential": 2,  # Sequential Agentで最終応答とみなす最小ステップ数
}

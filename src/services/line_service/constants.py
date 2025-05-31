"""LINEサービスのための定数と設定

このモジュールは、LINEサービスで使用される定数と設定値を定義します。
"""

import os

# デフォルト値
DEFAULT_THREAD_POOL_SIZE = 5
DEFAULT_THREAD_NAME_PREFIX = "LineEvent"

# エラーメッセージ
ERROR_MESSAGE = (
    "申し訳ございません。処理中にエラーが発生しました。"
    "しばらく時間をおいてから再試行してください。"
)


# 設定読み込み用関数
def get_line_config() -> tuple[str, str]:
    """LINE APIの設定を環境変数から読み込む

    Returns:
        tuple[str, str]: チャンネルアクセストークンとチャンネルシークレット

    Raises:
        ValueError: 必要な環境変数が設定されていない場合
    """
    channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    channel_secret = os.getenv("LINE_CHANNEL_SECRET")

    if not channel_access_token or not channel_secret:
        raise ValueError(
            "LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET "
            "must be set in environment variables"
        )

    return channel_access_token, channel_secret

import os

from linebot import LineBotApi, WebhookHandler


def setup_line_client():
    """LINE Bot APIとWebhookHandlerを設定して返す"""
    line_channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    line_channel_secret = os.getenv("LINE_CHANNEL_SECRET")

    if not line_channel_access_token or not line_channel_secret:
        raise ValueError(
            "LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET must be set "
            "in environment variables"
        )

    line_bot_api = LineBotApi(line_channel_access_token)
    handler = WebhookHandler(line_channel_secret)

    return line_bot_api, handler

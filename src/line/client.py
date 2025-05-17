import os

from aiolinebot import AioLineBotApi
from linebot import WebhookParser


def setup_line_client():
    """LINE Bot APIとWebhookHandlerを設定して返す"""
    line_channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    line_channel_secret = os.getenv("LINE_CHANNEL_SECRET")

    if not line_channel_access_token or not line_channel_secret:
        raise ValueError(
            "LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET must be set "
            "in environment variables"
        )

    line_bot_api = AioLineBotApi(line_channel_access_token)
    parser = WebhookParser(line_channel_secret)

    return line_bot_api, parser

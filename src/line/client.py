from linebot import WebhookHandler
from linebot.v3.messaging import Configuration

from config import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET


def setup_line_client():
    """LINE Bot APIとWebhookHandlerを設定して返す"""
    line_channel_access_token = LINE_CHANNEL_ACCESS_TOKEN
    line_channel_secret = LINE_CHANNEL_SECRET

    if not line_channel_access_token or not line_channel_secret:
        raise ValueError(
            "LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET must be set "
            "in environment variables"
        )

    configuration = Configuration(line_channel_access_token)
    handler = WebhookHandler(line_channel_secret)

    return configuration, handler

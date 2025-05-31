"""メッセージ処理モジュール

このモジュールは、ユーザーからのメッセージを処理し、エージェントに送信するための
Content形式に変換する機能を提供します。
"""

import base64
from typing import Optional

from google.genai import types

from src.utils.logger import setup_logger

logger = setup_logger("message_handler")


class MessageHandler:
    """メッセージ処理クラス

    ユーザーからのメッセージを処理し、エージェントに送信するための
    Content形式に変換します。
    """

    @staticmethod
    def create_message_content(
        message: str,
        image_data: Optional[bytes] = None,
        image_mime_type: Optional[str] = None,
    ) -> types.Content:
        """メッセージをContent型に変換

        Args:
            message: ユーザーのメッセージ文字列
            image_data: 画像バイナリデータ（オプション）
            image_mime_type: 画像MIMEタイプ（オプション）

        Returns:
            Content型のメッセージ
        """
        # メッセージをPart型に変換
        parts = [types.Part(text=message)]

        # 画像がある場合はそれを追加
        if image_data and image_mime_type:
            logger.info(
                f"Adding image data to message (MIME type: {image_mime_type})"
            )

            # 画像データをbase64エンコード
            image_base64 = base64.b64encode(image_data).decode("utf-8")

            # 画像パートを追加
            image_part = types.Part(
                inline_data=types.Blob(
                    mime_type=image_mime_type, data=image_base64
                )
            )
            parts.append(image_part)

        # Content型にまとめる
        return types.Content(role="user", parts=parts)

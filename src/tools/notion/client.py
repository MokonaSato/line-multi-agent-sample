"""
Notion API クライアント
"""

import logging
import os
from typing import Dict

import requests

from config import NOTION_TOKEN


class NotionAPIClient:
    """
    Notion API クライアント
    シングルトンパターンで実装し、アプリケーション内で一貫したAPI呼び出しを提供
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NotionAPIClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.token = NOTION_TOKEN
        self.version = os.getenv("NOTION_VERSION", "2022-06-28")
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": self.version,
            "Content-Type": "application/json",
        }
        self._initialized = True

    def _make_request(
        self, method: str, endpoint: str, data: Dict = None
    ) -> Dict:
        """APIリクエストを実行"""
        url = f"{self.base_url}{endpoint}"

        # トークン存在チェックを追加
        if not self.token:
            logging.error(
                "Notion API Token が設定されていません。環境変数 NOTION_TOKEN を確認してください。"
            )
            raise Exception("Notion API Error: API Token が設定されていません")

        # トークンの一部をマスクしてログに出力
        masked_token = (
            f"{self.token[:4]}...{self.token[-4:]}"
            if len(self.token) > 8
            else "未設定"
        )
        logging.info(f"Notion API リクエスト: {method} {endpoint}")
        logging.info(
            f"認証ヘッダー: Bearer {masked_token}, Version: {self.version}"
        )

        try:
            if method == "GET":
                logging.info(f"GETパラメータ: {data}")
                response = requests.get(url, headers=self.headers, params=data)
            elif method == "POST":
                logging.info(
                    f"POSTデータ構造: {list(data.keys()) if data else None}"
                )
                # デバッグ用にリクエストデータを詳細ログに出力
                logging.debug(f"完全なPOSTデータ: {data}")
                # 一時的に詳細情報をINFOレベルで出力（デバッグのため）
                logging.info(f"詳細なPOSTデータ: {data}")
                response = requests.post(url, headers=self.headers, json=data)
            elif method == "PATCH":
                logging.info(
                    f"PATCHデータ構造: {list(data.keys()) if data else None}"
                )
                response = requests.patch(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # レスポンスコードをログ出力
            logging.info(
                f"Notion API レスポンスコード: {response.status_code}"
            )

            # レスポンスが失敗している場合は詳細をログに出力
            if response.status_code >= 400:
                logging.error(f"Notion API エラーレスポンス: {response.text}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logging.error(f"Notion API request failed: {e}")

            # レスポンスオブジェクトがある場合はより詳細な情報をログに出力
            if hasattr(e, "response") and e.response is not None:
                logging.error(
                    f"HTTPステータスコード: {e.response.status_code}"
                )
                logging.error(
                    f"レスポンスヘッダー: {dict(e.response.headers)}"
                )
                logging.error(f"レスポンス本文: {e.response.text}")

                try:
                    error_data = e.response.json()
                    error_message = error_data.get("message", str(e))
                    logging.error(
                        f"Notion API エラーメッセージ: {error_message}"
                    )
                    raise Exception((f"Notion API Error: " f"{error_message}"))
                except Exception:
                    raise Exception(
                        f"Notion API Error: HTTP {e.response.status_code}"
                    )
            raise Exception(f"Notion API Error: {str(e)}")


# Notion APIクライアントのグローバルインスタンス
client = NotionAPIClient()

"""
Notion API クライアント
"""

import logging
import os
import random
import time
from typing import Dict

import requests
from requests.exceptions import HTTPError, RequestException

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
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        max_retries: int = 5,
        retry_delay: float = 1.0,
    ) -> Dict:
        """
        APIリクエストを実行し、一時的なエラーの場合はリトライする

        Args:
            method: HTTPメソッド（GET, POST, PATCH）
            endpoint: APIエンドポイント
            data: リクエストデータ
            max_retries: 最大リトライ回数
            retry_delay: リトライ間の待機時間（秒）

        Returns:
            APIレスポンスのJSONデータ

        Raises:
            Exception: API呼び出しに失敗した場合
        """
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

        # リクエストタイムアウトを設定（クラウド環境では接続に時間がかかる場合がある）
        timeout = (10, 30)  # 接続タイムアウト10秒、読み取りタイムアウト30秒

        # リトライ用に関数をラップ
        def _do_request():
            if method == "GET":
                logging.info(f"GETパラメータ: {data}")
                return requests.get(
                    url, headers=self.headers, params=data, timeout=timeout
                )
            elif method == "POST":
                logging.info(
                    f"POSTデータ構造: {list(data.keys()) if data else None}"
                )
                # デバッグ用にリクエストデータを詳細ログに出力
                logging.debug(f"完全なPOSTデータ: {data}")
                logging.info(f"詳細なPOSTデータ: {data}")
                return requests.post(
                    url, headers=self.headers, json=data, timeout=timeout
                )
            elif method == "PATCH":
                logging.info(
                    f"PATCHデータ構造: {list(data.keys()) if data else None}"
                )
                return requests.patch(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

        # リトライを含むリクエスト実行
        attempt = 0
        last_exception = None

        # リトライ対象のステータスコード
        retry_status_codes = [429, 500, 502, 503, 504, 520, 524]

        while attempt < max_retries:
            attempt += 1
            try:
                response = _do_request()

                # レスポンスコードをログ出力
                logging.info(
                    f"Notion API レスポンスコード: {response.status_code}"
                )

                # 一時的なエラーの場合はリトライ
                if response.status_code in retry_status_codes:
                    if attempt < max_retries:
                        # エクスポネンシャルバックオフとジッターを適用
                        base_wait = min(
                            retry_delay * (2 ** (attempt - 1)), 20
                        )  # 最大20秒
                        jitter = random.uniform(
                            0.5, 1.5
                        )  # 50%～150%のランダム係数
                        wait_time = base_wait * jitter

                        logging.warning(
                            f"一時的なエラー(HTTP {response.status_code})が発生。"(
                                f"{wait_time:.1f}秒後にリトライします "
                                f"(試行: {attempt}/{max_retries})"
                            )
                        )
                        time.sleep(wait_time)
                        continue

                # その他のエラーレスポンスの場合はログ出力
                if response.status_code >= 400:
                    logging.error(
                        f"Notion API エラーレスポンス: {response.text}"
                    )

                response.raise_for_status()
                return response.json()

            except (RequestException, HTTPError) as e:
                last_exception = e

                # 一時的なエラーと思われる場合のみリトライ
                is_retry_error = False

                if hasattr(e, "response") and e.response is not None:
                    if e.response.status_code in retry_status_codes:
                        is_retry_error = True
                elif isinstance(e, RequestException):
                    # 接続エラーやタイムアウトの場合もリトライ
                    is_retry_error = True

                if is_retry_error and attempt < max_retries:
                    # エクスポネンシャルバックオフとジッターを適用
                    base_wait = min(retry_delay * (2 ** (attempt - 1)), 20)
                    jitter = random.uniform(0.5, 1.5)
                    wait_time = base_wait * jitter

                    status_code = (
                        getattr(e.response, "status_code", "N/A")
                        if hasattr(e, "response")
                        else "N/A"
                    )
                    logging.warning(
                        f"API呼び出し中に一時的なエラーが発生(HTTP {status_code})。"(
                            f"{wait_time:.1f}秒後にリトライします "
                            f"(試行: {attempt}/{max_retries})"
                        )
                    )
                    time.sleep(wait_time)
                else:
                    break

        # 全てのリトライが失敗した場合の処理
        if last_exception:
            logging.error(
                f"Notion API リクエスト失敗 ({max_retries}回試行後): {last_exception}"
            )

            # レスポンスオブジェクトがある場合はより詳細な情報をログに出力
            if (
                hasattr(last_exception, "response")
                and last_exception.response is not None
            ):
                status_code = last_exception.response.status_code
                logging.error(f"HTTPステータスコード: {status_code}")
                logging.error(
                    f"レスポンスヘッダー: {dict(last_exception.response.headers)}"
                )
                logging.error(
                    f"レスポンス本文: {last_exception.response.text}"
                )

                try:
                    error_data = last_exception.response.json()
                    error_message = error_data.get(
                        "message", str(last_exception)
                    )
                    logging.error(
                        f"Notion API エラーメッセージ: {error_message}"
                    )

                    # 一時的なエラーの場合は特別なメッセージ
                    if status_code in [429, 500, 502, 503, 504, 520, 524]:
                        error_type = "temporary_server_error"
                        # より親切なエラーメッセージ
                        if status_code == 429:
                            error_message_ja = (
                                "Notion APIの利用制限に達しました。"
                                "しばらく待ってから再試行してください。"
                            )
                        else:
                            error_message_ja = (
                                f"Notion API サーバーが一時的に応答していません (HTTP {status_code})。"
                                f"サーバーが混雑しているか、メンテナンス中の可能性があります。"
                                f"数分後に再度お試しください。"
                            )
                        raise Exception(f"[{error_type}] {error_message_ja}")
                    else:
                        raise Exception(f"Notion API Error: {error_message}")
                except ValueError:  # JSONデコードできない場合
                    # 一時的なエラーの特別扱い
                    if status_code in [429, 500, 502, 503, 504, 520, 524]:
                        # エラーメッセージを具体的に
                        error_message_ja = (
                            f"Notion API サーバーからの応答を解析できませんでした "
                            f"(HTTP {status_code})。"
                            f"サーバーが混雑しているか、メンテナンス中の可能性があります。"
                            f"数分後に再度お試しください。"
                        )
                        raise Exception(error_message_ja)
                    else:
                        raise Exception(
                            f"Notion API Error: HTTP {status_code}"
                        )
            # ネットワークエラーなどの場合
            elif isinstance(
                last_exception, (requests.ConnectionError, requests.Timeout)
            ):
                error_message_ja = (
                    "Notion APIサーバーに接続できません。"
                    "インターネット接続を確認するか、数分後に再試行してください。"
                )
                raise Exception(error_message_ja)

            raise Exception(f"Notion API Error: {str(last_exception)}")


# Notion APIクライアントのグローバルインスタンス
client = NotionAPIClient()

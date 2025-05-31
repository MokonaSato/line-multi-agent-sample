"""
Notion API のエラーハンドリング用ユーティリティ
"""

import logging
import traceback
from typing import Any, Dict


def analyze_notion_error(error: Exception) -> Dict[str, Any]:
    """
    Notion API エラーを解析し、エラータイプとメッセージを返す

    Args:
        error: 発生した例外

    Returns:
        エラー情報を含む辞書
    """
    error_str = str(error)
    error_type = "unknown_error"
    user_message = "Notion APIでエラーが発生しました。"

    # エラータイプの判別
    if "temporary_server_error" in error_str or any(
        code in error_str
        for code in ["502", "503", "504", "500", "429", "520", "524"]
    ):
        error_type = "temporary_server_error"
        user_message = (
            "Notion APIサーバーが一時的に利用できません。"
            "サーバーが混雑しているため、数分後に再試行してください。"
        )
    elif "token" in error_str.lower() or "authorization" in error_str.lower():
        error_type = "token_error"
        user_message = "Notion APIの認証情報に問題があります。"
    elif "missing" in error_str.lower() and "parameter" in error_str.lower():
        error_type = "missing_parameter"
        user_message = "Notion APIに必要なパラメータが不足しています。"
    elif "limited" in error_str.lower() or "rate" in error_str.lower():
        error_type = "rate_limit"
        user_message = "Notion APIの利用制限に達しました。しばらく待ってから再試行してください。"
    elif "connection" in error_str.lower() or "timeout" in error_str.lower():
        error_type = "connection_error"
        user_message = "Notion APIサーバーへの接続中にエラーが発生しました。ネットワーク接続を確認してください。"

    # スタックトレースを取得
    stack_trace = traceback.format_exc()

    # エラー情報をログに記録
    logging.error(
        f"Notion APIエラー: type={error_type}, message={error_str}\n"
        f"スタックトレース:\n{stack_trace}"
    )

    return {
        "error_type": error_type,
        "error_message": error_str,
        "user_message": user_message,
        "stack_trace": stack_trace,
    }


def is_retryable_error(error_info: Dict[str, Any]) -> bool:
    """
    エラーが再試行可能かどうかを判断する

    Args:
        error_info: analyze_notion_error()から返されたエラー情報

    Returns:
        再試行可能であればTrue
    """
    retryable_types = [
        "temporary_server_error",
        "connection_error",
        "rate_limit",
    ]

    return error_info["error_type"] in retryable_types


def format_error_for_user(error_info: Dict[str, Any]) -> str:
    """
    ユーザーに表示するためのエラーメッセージを整形する

    Args:
        error_info: analyze_notion_error()から返されたエラー情報

    Returns:
        ユーザー向けのエラーメッセージ
    """
    return error_info["user_message"]

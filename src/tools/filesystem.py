"""統合ファイルシステムツール

Cloud Run環境で安全に動作するファイルシステム操作機能を提供します。
セキュリティを重視し、指定されたワークディレクトリ内でのみ操作を許可します。
"""

import logging
import os
import shutil
from typing import Optional

from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)

# セキュアな作業ディレクトリ（Cloud Run環境では/tmp配下を使用）
WORK_DIR = "/tmp/user_files"
ALLOWED_DIRECTORIES = [WORK_DIR, "uploads", "temp", "logs"]


def ensure_work_directory() -> None:
    """作業ディレクトリとサブディレクトリを確保する"""
    for directory in ALLOWED_DIRECTORIES:
        # 相対パスの場合は作業ディレクトリ配下に作成
        if not os.path.isabs(directory):
            directory = os.path.join(WORK_DIR, directory)
        os.makedirs(directory, exist_ok=True)


def _validate_path(file_path: str) -> tuple[str, Optional[str]]:
    """パスの妥当性を検証し、フルパスを返す

    Args:
        file_path: 検証するファイルパス

    Returns:
        tuple: (フルパス, エラーメッセージ) エラーがない場合はエラーメッセージはNone
    """
    # セキュリティのため、作業ディレクトリ内のファイルのみ許可
    full_path = os.path.join(WORK_DIR, file_path.lstrip("/"))

    # パスが作業ディレクトリ内にあることを確認
    if not os.path.abspath(full_path).startswith(os.path.abspath(WORK_DIR)):
        return "", f"エラー: パス '{file_path}' はアクセス許可されていません。"

    return full_path, None


def read_file_tool(file_path: str, tool_context: ToolContext = None) -> str:
    """ファイルの内容を読み取る

    Args:
        file_path: 読み取るファイルのパス（例: 'hello.txt', 'subfolder/document.txt'）
        tool_context: ツールコンテキスト

    Returns:
        str: ファイルの内容またはエラーメッセージ
    """
    try:
        full_path, error = _validate_path(file_path)
        if error:
            return error

        if not os.path.exists(full_path):
            return f"エラー: ファイル '{file_path}' が見つかりません。"

        with open(full_path, "r", encoding="utf-8") as file:
            content = file.read()
            return f"ファイル '{file_path}' の内容:\n{content}"

    except UnicodeDecodeError:
        try:
            with open(full_path, "rb") as file:
                size = len(file.read())
                return f"ファイル '{file_path}' はバイナリファイルです。サイズ: {size} bytes"
        except Exception as e:
            return f"エラー: ファイル読み取りに失敗しました: {str(e)}"
    except Exception as e:
        return f"エラー: ファイル読み取りに失敗しました: {str(e)}"


def write_file_tool(
    file_path: str, content: str, tool_context: ToolContext = None
) -> str:
    """ファイルに内容を書き込む

    Args:
        file_path: 書き込むファイルのパス（例: 'hello.txt', 'subfolder/document.txt'）
        content: ファイルに書き込む内容
        tool_context: ツールコンテキスト

    Returns:
        str: 成功メッセージまたはエラーメッセージ
    """
    try:
        ensure_work_directory()

        full_path, error = _validate_path(file_path)
        if error:
            return error

        # ディレクトリが存在しない場合は作成
        parent_dir = os.path.dirname(full_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as file:
            file.write(content)

        return f"✅ ファイル '{file_path}' に正常に書き込みました。内容: {len(content)} 文字"

    except Exception as e:
        return f"エラー: ファイルの書き込みに失敗しました: {str(e)}"


def list_directory_tool(
    directory_path: str = "", tool_context: ToolContext = None
) -> str:
    """ディレクトリの内容を一覧表示する

    Args:
        directory_path: 一覧表示するディレクトリのパス（例: '', 'subfolder'）
        tool_context: ツールコンテキスト

    Returns:
        str: ディレクトリの内容またはエラーメッセージ
    """
    try:
        ensure_work_directory()

        # 空文字列の場合はワークディレクトリを対象とする
        if not directory_path:
            full_path = WORK_DIR
        else:
            full_path, error = _validate_path(directory_path)
            if error:
                return error

        if not os.path.exists(full_path):
            return f"エラー: ディレクトリ '{directory_path or 'ルート'}' が見つかりません。"

        if not os.path.isdir(full_path):
            return f"エラー: '{directory_path or 'ルート'}' はディレクトリではありません。"

        items = []
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            if os.path.isdir(item_path):
                items.append(f"📁 {item}/")
            else:
                try:
                    size = os.path.getsize(item_path)
                    items.append(f"📄 {item} ({size} bytes)")
                except OSError:
                    items.append(f"📄 {item}")

        if not items:
            return f"ディレクトリ '{directory_path or 'ルート'}' は空です。"

        display_path = directory_path or "ルート"
        return f"ディレクトリ '{display_path}' の内容:\n" + "\n".join(items)

    except Exception as e:
        return f"エラー: ディレクトリの一覧取得に失敗しました: {str(e)}"


def create_directory_tool(
    directory_path: str, tool_context: ToolContext = None
) -> str:
    """新しいディレクトリを作成する

    Args:
        directory_path: 作成するディレクトリのパス（例: 'newfolder', 'subfolder/nested'）
        tool_context: ツールコンテキスト

    Returns:
        str: 成功メッセージまたはエラーメッセージ
    """
    try:
        ensure_work_directory()

        full_path, error = _validate_path(directory_path)
        if error:
            return error

        os.makedirs(full_path, exist_ok=True)
        return f"✅ ディレクトリ '{directory_path}' を作成しました。"

    except Exception as e:
        return f"エラー: ディレクトリの作成に失敗しました: {str(e)}"


def delete_file_tool(file_path: str, tool_context: ToolContext = None) -> str:
    """ファイルまたはディレクトリを削除する

    Args:
        file_path: 削除するファイルまたはディレクトリのパス
        tool_context: ツールコンテキスト

    Returns:
        str: 成功メッセージまたはエラーメッセージ
    """
    try:
        full_path, error = _validate_path(file_path)
        if error:
            return error

        if not os.path.exists(full_path):
            return f"エラー: '{file_path}' が見つかりません。"

        if os.path.isfile(full_path):
            os.remove(full_path)
            return f"✅ ファイル '{file_path}' を削除しました。"
        elif os.path.isdir(full_path):
            shutil.rmtree(full_path)
            return f"✅ ディレクトリ '{file_path}' を削除しました。"
        else:
            return f"エラー: '{file_path}' は通常のファイルまたはディレクトリではありません。"

    except Exception as e:
        return f"エラー: 削除に失敗しました: {str(e)}"


def list_allowed_directories() -> str:
    """操作可能なディレクトリ一覧を取得

    Returns:
        str: 操作可能なディレクトリの一覧
    """
    try:
        directories = []
        directories.append(f"作業ディレクトリ: {WORK_DIR}")

        for directory in ALLOWED_DIRECTORIES:
            if not os.path.isabs(directory):
                full_path = os.path.join(WORK_DIR, directory)
            else:
                full_path = directory

            if os.path.exists(full_path):
                status = "存在"
            else:
                status = "未作成"

            directories.append(f"- {directory} ({status})")

        return "操作可能なディレクトリ:\n" + "\n".join(directories)
    except Exception as e:
        return f"ディレクトリ一覧の取得に失敗: {str(e)}"


# Google ADK用のツール定義
read_file = FunctionTool(read_file_tool)
write_file = FunctionTool(write_file_tool)
list_directory = FunctionTool(list_directory_tool)
create_directory = FunctionTool(create_directory_tool)
delete_file = FunctionTool(delete_file_tool)
list_allowed_directories_tool = FunctionTool(list_allowed_directories)

# ツールリスト（統合版）
filesystem_tools = [
    read_file,
    write_file,
    list_directory,
    create_directory,
    delete_file,
    list_allowed_directories_tool,
]


# 初期化関数
async def initialize_filesystem_service() -> bool:
    """ファイルシステムサービスの初期化

    Returns:
        bool: 初期化が成功した場合True
    """
    try:
        logger.info("ファイルシステムサービスを初期化しています...")
        ensure_work_directory()
        logger.info("ファイルシステムサービスの初期化が完了しました")
        return True
    except Exception as e:
        logger.error(f"ファイルシステムサービスの初期化に失敗: {e}")
        return False


# ヘルスチェック用ユーティリティ
async def check_filesystem_health() -> bool:
    """ファイルシステムサービスのヘルスチェック

    Returns:
        bool: ヘルスチェックが成功した場合True
    """
    try:
        # ワークディレクトリの存在確認
        return os.path.exists(WORK_DIR) and os.path.isdir(WORK_DIR)
    except Exception:
        return False


__all__ = [
    "WORK_DIR",
    "ALLOWED_DIRECTORIES",
    "ensure_work_directory",
    "_validate_path",
    "read_file_tool",
    "write_file_tool",
    "list_directory_tool",
    "create_directory_tool",
    "delete_file_tool",
    "list_allowed_directories",
    "filesystem_tools",
    "initialize_filesystem_service",
    "check_filesystem_health",
]

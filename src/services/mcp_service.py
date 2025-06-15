"""MCP Filesystem Server との連携サービス

このモジュールは、Cloud Run サイドカーとして動作する MCP Filesystem Server
との通信を行う機能を提供します。
"""

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """ファイル情報を表すデータクラス"""

    name: str
    path: str
    type: str  # 'file' または 'directory'
    size: Optional[int] = None
    last_modified: Optional[str] = None


class MCPFilesystemClient:
    """MCP Filesystem Server クライアント"""

    def __init__(self, base_url: str = None):
        """
        初期化

        Args:
            base_url: MCP サーバーのベースURL
        """
        # MCP Serverはstdioプロトコルを使用するため、localhost経由でアクセス
        self.base_url = base_url or os.getenv(
            "MCP_SERVER_URL", "http://localhost:8081"
        )
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """非同期コンテキストマネージャーのエントリー"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了"""
        if self.session:
            await self.session.close()

    async def _make_mcp_request(
        self, method: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        MCP プロトコルリクエストを実行

        Args:
            method: MCPメソッド名
            params: リクエストパラメータ

        Returns:
            レスポンスデータ

        Raises:
            Exception: リクエストに失敗した場合
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use async with.")

        # MCP JSON-RPC 2.0 プロトコル形式
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }

        try:
            async with self.session.post(
                f"{self.base_url}/mcp",
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                response_data = await response.json()

                if response.status >= 400:
                    error_msg = response_data.get("error", {}).get(
                        "message", f"HTTP {response.status}"
                    )
                    raise Exception(f"MCP Server error: {error_msg}")

                if "error" in response_data:
                    raise Exception(
                        f"MCP Protocol error: "
                        f"{response_data['error']['message']}"
                    )

                return response_data.get("result", {})

        except aiohttp.ClientError as e:
            logger.error(f"MCP client error: {e}")
            raise Exception(f"Failed to connect to MCP server: {e}")

    async def read_file(self, file_path: str) -> str:
        """
        ファイルを読み取り

        Args:
            file_path: ファイルパス

        Returns:
            ファイル内容
        """
        logger.info(f"Reading file: {file_path}")

        result = await self._make_mcp_request(
            "tools/call",
            {"name": "read_file", "arguments": {"path": file_path}},
        )
        return result.get("content", [{}])[0].get("text", "")

    async def write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        ファイルを書き込み

        Args:
            file_path: ファイルパス
            content: ファイル内容

        Returns:
            書き込み結果
        """
        logger.info(f"Writing file: {file_path}")

        result = await self._make_mcp_request(
            "tools/call",
            {
                "name": "write_file",
                "arguments": {"path": file_path, "content": content},
            },
        )
        return {
            "success": True,
            "path": file_path,
            "message": result.get("content", [{}])[0].get(
                "text", "File written successfully"
            ),
        }

    async def list_directory(self, dir_path: str = "") -> List[FileInfo]:
        """
        ディレクトリ一覧を取得

        Args:
            dir_path: ディレクトリパス

        Returns:
            ファイル/ディレクトリ情報のリスト
        """
        logger.info(f"Listing directory: {dir_path}")

        result = await self._make_mcp_request(
            "tools/call",
            {"name": "list_directory", "arguments": {"path": dir_path}},
        )

        # MCPサーバーからのレスポンスをパース
        content_text = result.get("content", [{}])[0].get("text", "")
        files = []

        for line in content_text.split("\n"):
            if line.startswith("[FILE]") or line.startswith("[DIR]"):
                file_type = (
                    "file" if line.startswith("[FILE]") else "directory"
                )
                name = line.split("] ", 1)[1] if "] " in line else line
                files.append(
                    FileInfo(
                        name=name,
                        path=(
                            os.path.join(dir_path, name) if dir_path else name
                        ),
                        type=file_type,
                    )
                )

        return files


# MCP ツール統合関数
async def mcp_read_file(file_path: str) -> Dict[str, Any]:
    """
    MCP サーバー経由でファイルを読み取る関数

    Args:
        file_path: 読み取るファイルのパス

    Returns:
        結果を含む辞書
    """
    try:
        async with MCPFilesystemClient() as client:
            content = await client.read_file(file_path)
            return {
                "success": True,
                "content": content,
                "path": file_path,
                "message": f"ファイル '{file_path}' を正常に読み取りました",
            }
    except Exception as e:
        logger.error(f"ファイル読み取りエラー: {e}")
        return {
            "success": False,
            "error": str(e),
            "path": file_path,
            "message": f"ファイル '{file_path}' の読み取りに失敗しました",
        }


async def mcp_write_file(file_path: str, content: str) -> Dict[str, Any]:
    """
    MCP サーバー経由でファイルに書き込む関数

    Args:
        file_path: 書き込むファイルのパス
        content: ファイル内容

    Returns:
        結果を含む辞書
    """
    try:
        async with MCPFilesystemClient() as client:
            await client.write_file(file_path, content)
            return {
                "success": True,
                "path": file_path,
                "message": f"ファイル '{file_path}' を正常に書き込みました",
            }
    except Exception as e:
        logger.error(f"ファイル書き込みエラー: {e}")
        return {
            "success": False,
            "error": str(e),
            "path": file_path,
            "message": f"ファイル '{file_path}' の書き込みに失敗しました",
        }


async def mcp_list_directory(dir_path: str = "") -> Dict[str, Any]:
    """
    MCP サーバー経由でディレクトリ一覧を取得する関数

    Args:
        dir_path: ディレクトリパス（空文字列の場合はルート）

    Returns:
        結果を含む辞書
    """
    try:
        async with MCPFilesystemClient() as client:
            files = await client.list_directory(dir_path)
            return {
                "success": True,
                "path": dir_path or "/",
                "items": [
                    {
                        "name": f.name,
                        "path": f.path,
                        "type": f.type,
                        "size": f.size,
                        "last_modified": f.last_modified,
                    }
                    for f in files
                ],
                "count": len(files),
                "message": f"ディレクトリ '{dir_path or '/'}' の一覧を正常に取得しました",
            }
    except Exception as e:
        logger.error(f"ディレクトリ一覧取得エラー: {e}")
        return {
            "success": False,
            "error": str(e),
            "path": dir_path,
            "message": f"ディレクトリ '{dir_path}' の一覧取得に失敗しました",
        }


# MCP ツール リスト（既存のツールリストに追加用）
mcp_tools_list = [
    mcp_read_file,
    mcp_write_file,
    mcp_list_directory,
]


# ヘルスチェック用ユーティリティ
async def check_mcp_server_health() -> bool:
    """
    MCP サーバーのヘルスチェックを実行

    Returns:
        サーバーが正常であれば True
    """
    try:
        async with MCPFilesystemClient() as client:
            # 簡単なテスト（ルートディレクトリ一覧）
            await client.list_directory("")
            return True
    except Exception as e:
        logger.warning(f"MCP サーバーヘルスチェック失敗: {e}")
        return False


# 初期化確認用関数
async def ensure_mcp_directories():
    """
    必要なディレクトリが存在することを確認し、なければ作成
    """
    required_dirs = ["recipes", "uploads", "temp", "logs"]

    async with MCPFilesystemClient() as client:
        for dir_path in required_dirs:
            try:
                # ディレクトリ作成は実際のMCPツールを呼び出す
                await client._make_mcp_request(
                    "tools/call",
                    {
                        "name": "create_directory",
                        "arguments": {"path": dir_path},
                    },
                )
                logger.info(f"ディレクトリ '{dir_path}' を確認/作成しました")
            except Exception as e:
                logger.warning(f"ディレクトリ '{dir_path}' の作成に失敗: {e}")


# アプリケーション起動時の初期化関数
async def initialize_mcp_service():
    """
    MCP サービスの初期化
    アプリケーション起動時に呼び出す
    """
    logger.info("MCP サービスを初期化しています...")

    # ヘルスチェック
    if not await check_mcp_server_health():
        logger.warning("MCP サーバーが利用できません")
        return False

    # 必要なディレクトリを作成
    await ensure_mcp_directories()

    logger.info("MCP サービスの初期化が完了しました")
    return True

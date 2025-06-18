"""Filesystem MCP Server連携モジュール（Google ADK対応）

このモジュールはGoogle ADKのMCPToolsetを使用して
Filesystem MCP Serverとの連携を行います。
"""

import os
from contextlib import AsyncExitStack
from typing import Optional, Tuple

from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams
from google.adk.tools.toolbox_tool import ToolboxTool

from src.utils.logger import setup_logger

logger = setup_logger("filesystem_mcp")

# Filesystem MCP ServerのURL（環境変数から取得）
FILESYSTEM_MCP_URL = os.getenv(
    "FILESYSTEM_MCP_URL", "http://localhost:8000/sse"
)
FILESYSTEM_HTTP_URL = os.getenv("FILESYSTEM_HTTP_URL", "http://localhost:8000")


async def get_filesystem_mcp_tools_async() -> (
    Tuple[MCPToolset, AsyncExitStack]
):
    """Cloud Run上のMCPサイドカーからFilesystemツールを取得する

    Returns:
        Tuple[MCPToolset, AsyncExitStack]: Filesystemツールセットとリソース管理用のexitスタック
    """
    logger.info("Attempting to connect to Filesystem MCP server (Sidecar)...")

    # サイドカーの検出を試行
    try:
        # Filesystem MCP (localhost:8000/sse) へSSEで接続
        toolset, exit_stack = await MCPToolset.from_server(
            connection_params=SseServerParams(url=FILESYSTEM_MCP_URL)
        )
        logger.info("Filesystem MCP Toolset created successfully via SSE.")
        return toolset, exit_stack
    except Exception as e:
        logger.warning(f"SSE connection failed: {e}")

    # フォールバック: ToolboxToolを試行
    try:
        logger.info("Attempting to connect via ToolboxTool...")
        toolbox = ToolboxTool(FILESYSTEM_HTTP_URL)
        toolset = toolbox.get_toolset(toolset_name="filesystem_toolset")
        logger.info(
            "Filesystem MCP Toolset created successfully via ToolboxTool."
        )
        return toolset, AsyncExitStack()
    except Exception as e:
        logger.error(f"Failed to connect via ToolboxTool: {e}")
        raise RuntimeError(
            f"Filesystem MCP Server接続失敗: SSE ({FILESYSTEM_MCP_URL}) と "
            f"HTTP ({FILESYSTEM_HTTP_URL}) の両方で接続できませんでした"
        )


def get_filesystem_mcp_tools_sync() -> Optional[MCPToolset]:
    """同期版のFilesystem MCPツール取得（下位互換性用）

    Returns:
        MCPToolset or None: 成功時はツールセット、失敗時はNone
    """
    try:
        import asyncio

        return asyncio.run(get_filesystem_mcp_tools_async()[0])
    except Exception as e:
        logger.error(f"同期版MCP接続に失敗: {e}")
        return None


async def initialize_filesystem_mcp() -> (
    Tuple[Optional[MCPToolset], AsyncExitStack]
):
    """Filesystem MCP Serverを初期化する（非同期版）

    Returns:
        Tuple[Optional[MCPToolset], AsyncExitStack]: ツールセットとexitスタック
    """
    try:
        logger.info(
            f"Initializing Filesystem MCP client with URL: "
            f"{FILESYSTEM_MCP_URL}"
        )

        toolset, exit_stack = await get_filesystem_mcp_tools_async()
        logger.info("✅ Filesystem MCP client initialized successfully")
        return toolset, exit_stack

    except Exception as e:
        logger.error(f"Failed to initialize Filesystem MCP client: {e}")
        logger.warning("Running without Filesystem MCP Server")
        return None, AsyncExitStack()


async def cleanup_filesystem_mcp(exit_stack: AsyncExitStack) -> None:
    """Filesystem MCP Serverのクリーンアップ（非同期版）

    Args:
        exit_stack: リソース管理用のexitスタック
    """
    try:
        await exit_stack.aclose()
        logger.info("✅ Filesystem MCP cleanup completed")
    except Exception as e:
        logger.error(f"Error during Filesystem MCP cleanup: {e}")


async def check_filesystem_mcp_health() -> bool:
    """Filesystem MCP Serverのヘルスチェック（非同期版）

    Returns:
        bool: サーバーが利用可能かどうか
    """
    try:
        toolset, exit_stack = await get_filesystem_mcp_tools_async()
        await exit_stack.aclose()
        return True
    except Exception as e:
        logger.warning(f"Filesystem MCP health check failed: {e}")
        return False

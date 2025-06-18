"""MCP統合モジュール（Google ADK対応）

このモジュールはサンプルコードに基づいて、複数のMCPサーバーとの連携を管理します。
Cloud Run上のMCPサイドカーからツールを取得し、エージェントに提供します。
"""

import asyncio
import os
from contextlib import AsyncExitStack
from typing import Dict, Optional, Tuple

from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams
# from google.adk.tools.toolbox_tool import ToolboxTool  # 依存関係なしのため無効化

from config import MCP_ENABLED, MCP_TIMEOUT_SECONDS
from src.utils.logger import setup_logger

logger = setup_logger("mcp_integration")

# MCP ServerのURL（環境変数から取得）
FILESYSTEM_MCP_URL = os.getenv(
    "FILESYSTEM_MCP_URL", "http://localhost:8000/sse"
)
NOTION_MCP_URL = os.getenv("NOTION_MCP_URL", "http://localhost:3001/sse")

# HTTP フォールバック用URL
FILESYSTEM_HTTP_URL = os.getenv("FILESYSTEM_HTTP_URL", "http://localhost:8000")
NOTION_HTTP_URL = os.getenv("NOTION_HTTP_URL", "http://localhost:3001")


async def get_tools_async() -> Tuple[
    Optional[MCPToolset],
    Optional[MCPToolset],
    AsyncExitStack,
]:
    """Cloud Run上のMCPサイドカーからツールを取得する

    Google ADKのサンプルコードに基づいて、FilesystemとNotionの
    MCPサーバーからツールを取得します。タイムアウト機能付き。

    Returns:
        Tuple[Optional[MCPToolset], Optional[MCPToolset], AsyncExitStack]:
            (Filesystemツール, Notionツール, exitスタック)
    """
    exit_stack = AsyncExitStack()
    filesystem_tools = None
    notion_tools = None

    # MCP機能が無効化されている場合はスキップ
    if not MCP_ENABLED:
        logger.info("MCP is disabled by configuration")
        return filesystem_tools, notion_tools, exit_stack

    # Filesystem MCP (supergateway@localhost:8000) へSSEで接続
    try:
        logger.info(
            "Attempting to connect to MCP Filesystem server (Sidecar)..."
        )
        # タイムアウト付きで接続を試行
        filesystem_tools, fs_exit_stack = await asyncio.wait_for(
            MCPToolset.from_server(
                connection_params=SseServerParams(url=FILESYSTEM_MCP_URL)
            ),
            timeout=MCP_TIMEOUT_SECONDS,
        )
        await exit_stack.enter_async_context(fs_exit_stack)
        logger.info("Filesystem MCP Toolset created successfully.")
    except asyncio.TimeoutError:
        logger.warning(
            f"Filesystem MCP connection timed out after "
            f"{MCP_TIMEOUT_SECONDS} seconds"
        )
        # ToolboxTool フォールバックは無効化（依存関係なし）
        logger.warning("Filesystem MCP connection failed, no fallback available")
    except Exception as e:
        logger.warning(f"Filesystem MCP connection failed: {e}")
        # ToolboxTool フォールバックは無効化（依存関係なし）
        logger.warning("Filesystem MCP connection failed, no fallback available")

    # Notion MCP (localhost:3001) へSSEで接続
    try:
        logger.info("Attempting to connect to Notion MCP server (Sidecar)...")
        # タイムアウト付きで接続を試行
        notion_tools, notion_exit_stack = await asyncio.wait_for(
            MCPToolset.from_server(
                connection_params=SseServerParams(url=NOTION_MCP_URL)
            ),
            timeout=MCP_TIMEOUT_SECONDS,
        )
        await exit_stack.enter_async_context(notion_exit_stack)
        logger.info("Notion MCP Toolset created successfully.")
    except asyncio.TimeoutError:
        logger.warning(
            f"Notion MCP connection timed out after "
            f"{MCP_TIMEOUT_SECONDS} seconds"
        )
        # ToolboxTool フォールバックは無効化（依存関係なし）
        logger.warning("Notion MCP connection failed, no fallback available")
    except Exception as e:
        logger.warning(f"Notion MCP connection failed: {e}")
        # ToolboxTool フォールバックは無効化（依存関係なし）
        logger.warning("Notion MCP connection failed, no fallback available")

    return filesystem_tools, notion_tools, exit_stack


async def get_available_mcp_tools() -> Dict[str, Optional[MCPToolset]]:
    """利用可能なMCPツールを辞書形式で取得する

    Returns:
        Dict[str, Optional[MCPToolset]]: ツール名とツールセットのマッピング
    """
    filesystem_tools, notion_tools, _ = await get_tools_async()

    return {
        "filesystem": filesystem_tools,
        "notion": notion_tools,
    }


async def check_mcp_server_health() -> Dict[str, bool]:
    """すべてのMCPサーバーのヘルスチェックを実行

    Returns:
        Dict[str, bool]: サーバー名と健全性状態のマッピング
    """
    try:
        # 一度にすべてのMCPサーバーの状態を確認
        filesystem_tools, notion_tools, exit_stack = await get_tools_async()

        health_status = {
            "filesystem": filesystem_tools is not None,
            "notion": notion_tools is not None,
        }

        # リソースをクリーンアップ
        await exit_stack.aclose()

        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "filesystem": False,
            "notion": False,
        }

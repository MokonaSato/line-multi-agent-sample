"""Notion MCP Server連携モジュール（Google ADK対応）

このモジュールはGoogle ADKのMCPToolsetを使用して
Notion MCP Serverとの連携を行います。
"""

import os
from contextlib import AsyncExitStack
from typing import Optional, Tuple

from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams
# from google.adk.tools.toolbox_tool import ToolboxTool  # 依存関係なしのため無効化

from src.utils.logger import setup_logger

logger = setup_logger("notion_mcp")

# Notion MCP ServerのURL（環境変数から取得）
NOTION_MCP_URL = os.getenv("NOTION_MCP_URL", "http://localhost:3001/sse")
NOTION_HTTP_URL = os.getenv("NOTION_HTTP_URL", "http://localhost:3001")


async def get_notion_mcp_tools_async() -> Tuple[MCPToolset, AsyncExitStack]:
    """Cloud Run上のMCPサイドカーからNotionツールを取得する

    Returns:
        Tuple[MCPToolset, AsyncExitStack]: Notionツールセットとリソース管理用のexitスタック
    """
    logger.info("Attempting to connect to Notion MCP server (Sidecar)...")

    # サイドカーの検出を試行
    try:
        # Notion MCP (localhost:3001/sse) へSSEで接続
        toolset, exit_stack = await MCPToolset.from_server(
            connection_params=SseServerParams(url=NOTION_MCP_URL)
        )
        logger.info("Notion MCP Toolset created successfully via SSE.")
        return toolset, exit_stack
    except Exception as e:
        logger.warning(f"SSE connection failed: {e}")

    # ToolboxTool フォールバックは無効化（依存関係なし）
    logger.error("Failed to connect via SSE, no fallback available")
    raise RuntimeError(
        f"Notion MCP Server接続失敗: SSE ({NOTION_MCP_URL}) で接続できませんでした"
    )


def get_notion_mcp_tools_sync() -> Optional[MCPToolset]:
    """同期版のNotion MCPツール取得（下位互換性用）

    Returns:
        MCPToolset or None: 成功時はツールセット、失敗時はNone
    """
    try:
        import asyncio

        return asyncio.run(get_notion_mcp_tools_async()[0])
    except Exception as e:
        logger.error(f"同期版MCP接続に失敗: {e}")
        return None


async def initialize_notion_mcp() -> (
    Tuple[Optional[MCPToolset], AsyncExitStack]
):
    """Notion MCP Serverを初期化する（非同期版）

    Returns:
        Tuple[Optional[MCPToolset], AsyncExitStack]: ツールセットとexitスタック
    """
    try:
        logger.info(
            f"Initializing Notion MCP client with URL: {NOTION_MCP_URL}"
        )

        toolset, exit_stack = await get_notion_mcp_tools_async()
        logger.info("✅ Notion MCP client initialized successfully")
        return toolset, exit_stack

    except Exception as e:
        logger.error(f"Failed to initialize Notion MCP client: {e}")
        logger.warning("Running without Notion MCP Server")
        return None, AsyncExitStack()


async def cleanup_notion_mcp(exit_stack: AsyncExitStack) -> None:
    """Notion MCP Serverのクリーンアップ（非同期版）

    Args:
        exit_stack: リソース管理用のexitスタック
    """
    try:
        await exit_stack.aclose()
        logger.info("✅ Notion MCP cleanup completed")
    except Exception as e:
        logger.error(f"Error during Notion MCP cleanup: {e}")


async def check_notion_mcp_health() -> bool:
    """Notion MCP Serverのヘルスチェック（非同期版）

    Returns:
        bool: サーバーが利用可能かどうか
    """
    try:
        toolset, exit_stack = await get_notion_mcp_tools_async()
        await exit_stack.aclose()
        return True
    except Exception as e:
        logger.warning(f"Notion MCP health check failed: {e}")
        return False

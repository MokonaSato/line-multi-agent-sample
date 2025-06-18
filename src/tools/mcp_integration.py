"""MCP統合モジュール（Google ADK対応）

このモジュールはサンプルコードに基づいて、複数のMCPサーバーとの連携を管理します。
Cloud Run上のMCPサイドカーからツールを取得し、エージェントに提供します。
"""

import os
from contextlib import AsyncExitStack
from typing import Dict, Optional, Tuple

from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams
from google.adk.tools.toolbox_tool import ToolboxTool

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
    MCPサーバーからツールを取得します。

    Returns:
        Tuple[Optional[MCPToolset], Optional[MCPToolset], AsyncExitStack]:
            (Filesystemツール, Notionツール, exitスタック)
    """
    exit_stack = AsyncExitStack()
    filesystem_tools = None
    notion_tools = None

    # Filesystem MCP (supergateway@localhost:8000) へSSEで接続
    try:
        logger.info(
            "Attempting to connect to MCP Filesystem server (Sidecar)..."
        )
        filesystem_tools, fs_exit_stack = await MCPToolset.from_server(
            connection_params=SseServerParams(url=FILESYSTEM_MCP_URL)
        )
        await exit_stack.enter_async_context(fs_exit_stack)
        logger.info("Filesystem MCP Toolset created successfully.")
    except Exception as e:
        logger.warning(f"Filesystem MCP connection failed: {e}")

        # フォールバック: ToolboxToolを試行
        try:
            logger.info("Attempting Filesystem via ToolboxTool...")
            toolbox = ToolboxTool(FILESYSTEM_HTTP_URL)
            filesystem_tools = toolbox.get_toolset(
                toolset_name="filesystem_toolset"
            )
            logger.info("Filesystem MCP via ToolboxTool created successfully.")
        except Exception as tb_e:
            logger.error(f"Filesystem ToolboxTool also failed: {tb_e}")

    # Notion MCP (localhost:3001) へSSEで接続
    try:
        logger.info("Attempting to connect to Notion MCP server (Sidecar)...")
        notion_tools, notion_exit_stack = await MCPToolset.from_server(
            connection_params=SseServerParams(url=NOTION_MCP_URL)
        )
        await exit_stack.enter_async_context(notion_exit_stack)
        logger.info("Notion MCP Toolset created successfully.")
    except Exception as e:
        logger.warning(f"Notion MCP connection failed: {e}")

        # フォールバック: ToolboxToolを試行
        try:
            logger.info("Attempting Notion via ToolboxTool...")
            toolbox = ToolboxTool(NOTION_HTTP_URL)
            notion_tools = toolbox.get_toolset(toolset_name="notion_toolset")
            logger.info("Notion MCP via ToolboxTool created successfully.")
        except Exception as tb_e:
            logger.error(f"Notion ToolboxTool also failed: {tb_e}")

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
    health_status = {}

    # Filesystem MCP health check
    try:
        filesystem_tools, _, exit_stack = await get_tools_async()
        health_status["filesystem"] = filesystem_tools is not None
        await exit_stack.aclose()
    except Exception:
        health_status["filesystem"] = False

    # Notion MCP health check
    try:
        _, notion_tools, exit_stack = await get_tools_async()
        health_status["notion"] = notion_tools is not None
        await exit_stack.aclose()
    except Exception:
        health_status["notion"] = False

    return health_status

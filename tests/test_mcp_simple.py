#!/usr/bin/env python3
"""シンプルなMCP接続テスト

リソース管理の問題を回避して、基本的なMCP接続をテストします。
"""

import asyncio
import os
from typing import Optional

from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams

from src.utils.logger import setup_logger

logger = setup_logger("simple_mcp_test")

# MCP ServerのURL
FILESYSTEM_MCP_URL = os.getenv(
    "FILESYSTEM_MCP_URL", "http://localhost:8000/sse"
)
NOTION_MCP_URL = os.getenv("NOTION_MCP_URL", "http://localhost:3001/sse")


async def test_single_connection(server_name: str, url: str) -> bool:
    """単一のMCPサーバーへの接続をテストする

    Args:
        server_name: サーバー名
        url: 接続URL

    Returns:
        bool: 接続成功したかどうか
    """
    try:
        logger.info(f"Testing {server_name} connection to {url}")

        # 短時間での接続テスト
        toolset, exit_stack = await MCPToolset.from_server(
            connection_params=SseServerParams(url=url)
        )

        logger.info(f"✅ {server_name} connection successful")

        # ツール一覧を取得
        try:
            # MCPToolsetの正しいAPI使用方法
            if hasattr(toolset, "tools"):
                tools = toolset.tools
                tool_names = [tool.name for tool in tools] if tools else []
                logger.info(f"Available tools: {tool_names}")
            elif hasattr(toolset, "_tools"):
                tools = toolset._tools
                tool_names = [tool.name for tool in tools] if tools else []
                logger.info(f"Available tools: {tool_names}")
            else:
                logger.info(
                    "Tools information not accessible via standard API"
                )
        except Exception as e:
            logger.warning(f"Could not load tools: {e}")

        # すぐにクリーンアップ
        await exit_stack.aclose()

        return True

    except Exception as e:
        logger.error(f"❌ {server_name} connection failed: {e}")
        return False


async def test_mcp_servers():
    """すべてのMCPサーバーを個別にテストする"""
    logger.info("🚀 Simple MCP Connection Test Starting")

    # 環境変数の確認
    logger.info(f"FILESYSTEM_MCP_URL: {FILESYSTEM_MCP_URL}")
    logger.info(f"NOTION_MCP_URL: {NOTION_MCP_URL}")

    # 個別に接続テスト
    results = {}

    results["filesystem"] = await test_single_connection(
        "Filesystem", FILESYSTEM_MCP_URL
    )
    await asyncio.sleep(0.5)  # 短い間隔を空ける

    results["notion"] = await test_single_connection("Notion", NOTION_MCP_URL)

    # 結果の表示
    logger.info("📊 Test Results:")
    for server, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"   {server}: {status}")

    all_passed = all(results.values())
    final_status = (
        "✅ ALL TESTS PASSED" if all_passed else "⚠️ SOME TESTS FAILED"
    )
    logger.info(f"🎯 Overall: {final_status}")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(test_mcp_servers())
    exit(0 if success else 1)

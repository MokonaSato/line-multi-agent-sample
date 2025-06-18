#!/usr/bin/env python3
"""実践的なMCP統合テスト

実際にエージェントを作成して、MCPツールが使用できるかをテストします。
"""

import asyncio
import os

from src.agents.root_agent import create_agent
from src.utils.logger import setup_logger

logger = setup_logger("practical_mcp_test")

# MCP ServerのURL
FILESYSTEM_MCP_URL = os.getenv(
    "FILESYSTEM_MCP_URL", "http://localhost:8000/sse"
)
NOTION_MCP_URL = os.getenv("NOTION_MCP_URL", "http://localhost:3001/sse")


async def test_agent_creation():
    """エージェント作成をテストして、MCPツールが統合されているかを確認"""
    logger.info("🚀 Practical MCP Integration Test Starting")

    # 環境変数の確認
    logger.info(f"FILESYSTEM_MCP_URL: {FILESYSTEM_MCP_URL}")
    logger.info(f"NOTION_MCP_URL: {NOTION_MCP_URL}")

    try:
        # エージェントの作成
        logger.info("Creating root agent with MCP integration...")
        root_agent, exit_stack = await create_agent()

        logger.info("✅ Root agent created successfully")
        logger.info(f"Agent name: {root_agent.name}")
        logger.info(f"Agent description: {root_agent.description}")

        # サブエージェントの確認
        if hasattr(root_agent, "sub_agents") and root_agent.sub_agents:
            logger.info(f"Number of sub-agents: {len(root_agent.sub_agents)}")
            for i, sub_agent in enumerate(root_agent.sub_agents):
                logger.info(f"  Sub-agent {i+1}: {sub_agent.name}")

                # ツール情報の取得
                if hasattr(sub_agent, "tools") and sub_agent.tools:
                    tool_count = len(sub_agent.tools)
                    logger.info(f"    Tools: {tool_count} available")

                    # 最初の数個のツール名を表示
                    for j, tool in enumerate(sub_agent.tools[:3]):
                        tool_name = getattr(tool, "name", f"Tool {j+1}")
                        logger.info(f"      - {tool_name}")

                    if tool_count > 3:
                        logger.info(f"      ... and {tool_count - 3} more")
                else:
                    logger.info("    No tools found")
        else:
            logger.info("No sub-agents found")

        # リソースのクリーンアップ
        await exit_stack.aclose()
        logger.info("✅ Resources cleaned up successfully")

        return True

    except Exception as e:
        logger.error(f"❌ Agent creation failed: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


async def test_mcp_health():
    """MCP接続状況を確認"""
    try:
        from src.tools.mcp_integration import check_mcp_server_health

        logger.info("🔍 Checking MCP server health...")
        health_status = await check_mcp_server_health()

        for server, is_healthy in health_status.items():
            status = "✅ Online" if is_healthy else "❌ Offline"
            logger.info(f"  {server}: {status}")

        return all(health_status.values())

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False


async def main():
    """メインテスト実行"""
    logger.info("🎯 Starting comprehensive MCP integration test")

    # 1. MCP サーバーのヘルスチェック
    health_ok = await test_mcp_health()

    # 2. エージェント作成テスト
    agent_ok = await test_agent_creation()

    # 結果の集計
    all_ok = health_ok and agent_ok

    logger.info("📊 Final Test Results:")
    logger.info(f"  MCP Health: {'✅ PASS' if health_ok else '❌ FAIL'}")
    logger.info(f"  Agent Creation: {'✅ PASS' if agent_ok else '❌ FAIL'}")

    final_status = "✅ ALL TESTS PASSED" if all_ok else "⚠️ SOME TESTS FAILED"
    logger.info(f"🏆 Overall: {final_status}")

    return all_ok


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

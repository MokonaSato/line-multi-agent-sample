#!/usr/bin/env python3
"""Google ADK MCP統合テストスクリプト

このスクリプトは、修正されたMCP連携が正しく動作するかテストします。
サンプルコードに基づいてエージェントの作成とMCPツールの取得をテストします。
"""

import asyncio
import logging
import os
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.agent_factory import AgentFactory
from src.agents.config import AGENT_CONFIG
from src.agents.prompt_manager import PromptManager
from src.tools.mcp_integration import (
    check_mcp_server_health,
    get_available_mcp_tools,
    get_tools_async,
)
from src.utils.logger import setup_logger

# ロガー設定
logger = setup_logger("mcp_test")
logging.basicConfig(level=logging.INFO)


async def test_mcp_connection():
    """MCP サーバー接続テスト"""
    logger.info("=== MCP サーバー接続テスト開始 ===")

    # 1. ヘルスチェックテスト
    logger.info("1. MCP サーバーヘルスチェック...")
    health_status = await check_mcp_server_health()
    for server, is_healthy in health_status.items():
        status = "✅ Online" if is_healthy else "❌ Offline"
        logger.info(f"   {server}: {status}")

    # 2. ツール取得テスト
    logger.info("2. MCP ツール取得テスト...")
    try:
        filesystem_tools, notion_tools, exit_stack = await get_tools_async()

        if filesystem_tools:
            logger.info("   ✅ Filesystem MCP tools obtained successfully")
        else:
            logger.warning("   ⚠️ Filesystem MCP tools not available")

        if notion_tools:
            logger.info("   ✅ Notion MCP tools obtained successfully")
        else:
            logger.warning("   ⚠️ Notion MCP tools not available")

        # リソースクリーンアップ
        await exit_stack.aclose()

    except Exception as e:
        logger.error(f"   ❌ MCP ツール取得エラー: {e}")

    # 3. 利用可能ツール一覧テスト
    logger.info("3. 利用可能ツール一覧テスト...")
    available_tools = await get_available_mcp_tools()
    for tool_name, toolset in available_tools.items():
        status = "✅ Available" if toolset else "❌ Not available"
        logger.info(f"   {tool_name}: {status}")

    logger.info("=== MCP サーバー接続テスト完了 ===\n")


async def test_agent_creation():
    """エージェント作成テスト"""
    logger.info("=== エージェント作成テスト開始 ===")

    try:
        # プロンプト読み込み
        logger.info("1. プロンプト読み込み...")
        prompt_manager = PromptManager()
        prompts = prompt_manager.get_all_prompts()
        logger.info("   ✅ プロンプト読み込み完了")

        # ファクトリー作成
        logger.info("2. エージェントファクトリー作成...")
        factory = AgentFactory(prompts, AGENT_CONFIG)
        logger.info("   ✅ ファクトリー作成完了")

        # エージェント作成（MCP対応）
        logger.info("3. エージェント作成（MCP連携込み）...")
        agents = await factory.create_all_standard_agents()

        for agent_name, agent in agents.items():
            logger.info(f"   ✅ {agent_name}: 作成完了")

        # ルートエージェント作成
        logger.info("4. ルートエージェント作成...")
        root_agent = factory.create_root_agent(agents)
        logger.info("   ✅ ルートエージェント作成完了")

        # リソースクリーンアップ
        logger.info("5. リソースクリーンアップ...")
        await factory.cleanup_mcp_resources()
        logger.info("   ✅ クリーンアップ完了")

        logger.info("=== エージェント作成テスト完了 ===\n")
        return True

    except Exception as e:
        logger.error(f"❌ エージェント作成エラー: {e}")
        return False


async def test_mcp_fallback():
    """MCP フォールバック機能テスト"""
    logger.info("=== MCP フォールバック機能テスト開始 ===")

    try:
        # 環境変数を一時的に無効化してフォールバックをテスト
        original_fs_url = os.getenv("FILESYSTEM_MCP_URL")
        original_notion_url = os.getenv("NOTION_MCP_URL")

        # 無効なURLに設定
        os.environ["FILESYSTEM_MCP_URL"] = "http://invalid:9999/sse"
        os.environ["NOTION_MCP_URL"] = "http://invalid:9999/sse"

        logger.info("1. 無効なMCPサーバーURL設定でテスト...")

        # プロンプト読み込み
        prompt_manager = PromptManager()
        prompts = prompt_manager.get_all_prompts()

        # ファクトリー作成とエージェント作成
        factory = AgentFactory(prompts, AGENT_CONFIG)
        agents = await factory.create_all_standard_agents()

        logger.info("   ✅ フォールバックツールでエージェント作成完了")

        # 環境変数を元に戻す
        if original_fs_url:
            os.environ["FILESYSTEM_MCP_URL"] = original_fs_url
        if original_notion_url:
            os.environ["NOTION_MCP_URL"] = original_notion_url

        await factory.cleanup_mcp_resources()

        logger.info("=== MCP フォールバック機能テスト完了 ===\n")
        return True

    except Exception as e:
        logger.error(f"❌ フォールバックテストエラー: {e}")
        return False


async def main():
    """メインテスト関数"""
    logger.info("🚀 Google ADK MCP統合テスト開始")

    test_results = []

    # テスト実行
    try:
        # MCP接続テスト
        await test_mcp_connection()

        # エージェント作成テスト
        result1 = await test_agent_creation()
        test_results.append(("エージェント作成", result1))

        # フォールバックテスト
        result2 = await test_mcp_fallback()
        test_results.append(("フォールバック機能", result2))

    except Exception as e:
        logger.error(f"❌ テスト実行中にエラー: {e}")

    # 結果サマリー
    logger.info("📊 テスト結果サマリー:")
    all_passed = True
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"   {test_name}: {status}")
        if not result:
            all_passed = False

    final_status = "✅ 全テスト成功" if all_passed else "❌ 一部テスト失敗"
    logger.info(f"\n🎯 総合結果: {final_status}")

    return all_passed


if __name__ == "__main__":
    # 環境変数の確認
    print("Environment variables:")
    print(f"FILESYSTEM_MCP_URL: {os.getenv('FILESYSTEM_MCP_URL', 'Not set')}")
    print(f"NOTION_MCP_URL: {os.getenv('NOTION_MCP_URL', 'Not set')}")
    print(
        f"GOOGLE_API_KEY: {'Set' if os.getenv('GOOGLE_API_KEY') else 'Not set'}"
    )
    print()

    # テスト実行
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("テストが中断されました")
        sys.exit(1)
    except Exception as e:
        logger.error(f"テスト実行中に予期しないエラー: {e}")
        sys.exit(1)

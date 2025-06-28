"""MCP統合のテストモジュール"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio
from contextlib import AsyncExitStack

from src.tools.mcp_integration import (
    get_tools_async,
    get_available_mcp_tools,
    check_mcp_server_health,
    FILESYSTEM_MCP_URL,
    NOTION_MCP_URL
)


class TestMCPIntegration:
    """MCP統合のテスト"""

    @pytest.mark.asyncio
    async def test_get_tools_async_success(self):
        """ツール取得成功のテスト"""
        mock_filesystem_tools = Mock()
        mock_notion_tools = Mock()
        mock_fs_exit_stack = AsyncMock()
        mock_notion_exit_stack = AsyncMock()
        
        with patch('src.tools.mcp_integration.MCP_ENABLED', True), \
             patch('src.tools.mcp_integration.MCPToolset') as mock_toolset, \
             patch('src.tools.mcp_integration.SseServerParams') as mock_sse_params:
            
            # MCPToolset.from_serverのモック設定
            mock_toolset.from_server = AsyncMock()
            mock_toolset.from_server.side_effect = [
                (mock_filesystem_tools, mock_fs_exit_stack),
                (mock_notion_tools, mock_notion_exit_stack)
            ]
            
            filesystem_tools, notion_tools, exit_stack = await get_tools_async()
            
            assert filesystem_tools == mock_filesystem_tools
            assert notion_tools == mock_notion_tools
            assert isinstance(exit_stack, AsyncExitStack)
            
            # MCPToolset.from_serverが2回呼ばれる（filesystem、notion）
            assert mock_toolset.from_server.call_count == 2

    @pytest.mark.asyncio
    async def test_get_tools_async_mcp_disabled(self):
        """MCP無効時のテスト"""
        with patch('src.tools.mcp_integration.MCP_ENABLED', False):
            filesystem_tools, notion_tools, exit_stack = await get_tools_async()
            
            assert filesystem_tools is None
            assert notion_tools is None
            assert isinstance(exit_stack, AsyncExitStack)

    @pytest.mark.asyncio
    async def test_get_tools_async_filesystem_timeout(self):
        """Filesystemタイムアウトのテスト"""
        mock_notion_tools = Mock()
        mock_notion_exit_stack = AsyncMock()
        
        with patch('src.tools.mcp_integration.MCP_ENABLED', True), \
             patch('src.tools.mcp_integration.MCPToolset') as mock_toolset, \
             patch('src.tools.mcp_integration.MCP_TIMEOUT_SECONDS', 1):
            
            # Filesystemはタイムアウト、Notionは成功
            async def mock_from_server(connection_params):
                if "8000" in str(connection_params):  # Filesystem
                    await asyncio.sleep(2)  # タイムアウトを引き起こす
                else:  # Notion
                    return mock_notion_tools, mock_notion_exit_stack
            
            mock_toolset.from_server = AsyncMock(side_effect=mock_from_server)
            
            filesystem_tools, notion_tools, exit_stack = await get_tools_async()
            
            assert filesystem_tools is None  # タイムアウトでNone
            assert notion_tools == mock_notion_tools  # 成功
            assert isinstance(exit_stack, AsyncExitStack)

    @pytest.mark.asyncio
    async def test_get_tools_async_filesystem_exception(self):
        """Filesystem例外のテスト"""
        mock_notion_tools = Mock()
        mock_notion_exit_stack = AsyncMock()
        
        with patch('src.tools.mcp_integration.MCP_ENABLED', True), \
             patch('src.tools.mcp_integration.MCPToolset') as mock_toolset:
            
            # Filesystemは例外、Notionは成功
            async def mock_from_server(connection_params):
                if "8000" in str(connection_params):  # Filesystem
                    raise Exception("Connection failed")
                else:  # Notion
                    return mock_notion_tools, mock_notion_exit_stack
            
            mock_toolset.from_server = AsyncMock(side_effect=mock_from_server)
            
            filesystem_tools, notion_tools, exit_stack = await get_tools_async()
            
            assert filesystem_tools is None  # 例外でNone
            assert notion_tools == mock_notion_tools  # 成功
            assert isinstance(exit_stack, AsyncExitStack)

    @pytest.mark.asyncio
    async def test_get_tools_async_notion_timeout(self):
        """Notionタイムアウトのテスト"""
        mock_filesystem_tools = Mock()
        mock_fs_exit_stack = AsyncMock()
        
        with patch('src.tools.mcp_integration.MCP_ENABLED', True), \
             patch('src.tools.mcp_integration.MCPToolset') as mock_toolset, \
             patch('src.tools.mcp_integration.MCP_TIMEOUT_SECONDS', 1):
            
            # Filesystemは成功、Notionはタイムアウト
            async def mock_from_server(connection_params):
                if "8000" in str(connection_params):  # Filesystem
                    return mock_filesystem_tools, mock_fs_exit_stack
                else:  # Notion
                    await asyncio.sleep(2)  # タイムアウトを引き起こす
            
            mock_toolset.from_server = AsyncMock(side_effect=mock_from_server)
            
            filesystem_tools, notion_tools, exit_stack = await get_tools_async()
            
            assert filesystem_tools == mock_filesystem_tools  # 成功
            assert notion_tools is None  # タイムアウトでNone
            assert isinstance(exit_stack, AsyncExitStack)

    @pytest.mark.asyncio
    async def test_get_tools_async_notion_exception(self):
        """Notion例外のテスト"""
        mock_filesystem_tools = Mock()
        mock_fs_exit_stack = AsyncMock()
        
        with patch('src.tools.mcp_integration.MCP_ENABLED', True), \
             patch('src.tools.mcp_integration.MCPToolset') as mock_toolset:
            
            # Filesystemは成功、Notionは例外
            async def mock_from_server(connection_params):
                if "8000" in str(connection_params):  # Filesystem
                    return mock_filesystem_tools, mock_fs_exit_stack
                else:  # Notion
                    raise Exception("Notion connection failed")
            
            mock_toolset.from_server = AsyncMock(side_effect=mock_from_server)
            
            filesystem_tools, notion_tools, exit_stack = await get_tools_async()
            
            assert filesystem_tools == mock_filesystem_tools  # 成功
            assert notion_tools is None  # 例外でNone
            assert isinstance(exit_stack, AsyncExitStack)

    @pytest.mark.asyncio
    async def test_get_tools_async_all_failure(self):
        """全て失敗のテスト"""
        with patch('src.tools.mcp_integration.MCP_ENABLED', True), \
             patch('src.tools.mcp_integration.MCPToolset') as mock_toolset:
            
            # 両方とも例外
            mock_toolset.from_server = AsyncMock(side_effect=Exception("Connection failed"))
            
            filesystem_tools, notion_tools, exit_stack = await get_tools_async()
            
            assert filesystem_tools is None
            assert notion_tools is None
            assert isinstance(exit_stack, AsyncExitStack)

    @pytest.mark.asyncio
    async def test_get_available_mcp_tools(self):
        """利用可能なMCPツール取得のテスト"""
        mock_filesystem_tools = Mock()
        mock_notion_tools = Mock()
        
        with patch('src.tools.mcp_integration.get_tools_async') as mock_get_tools:
            mock_get_tools.return_value = (mock_filesystem_tools, mock_notion_tools, Mock())
            
            tools = await get_available_mcp_tools()
            
            assert tools == {
                "filesystem": mock_filesystem_tools,
                "notion": mock_notion_tools
            }
            mock_get_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_available_mcp_tools_partial_failure(self):
        """利用可能なMCPツール取得（部分失敗）のテスト"""
        mock_filesystem_tools = Mock()
        
        with patch('src.tools.mcp_integration.get_tools_async') as mock_get_tools:
            mock_get_tools.return_value = (mock_filesystem_tools, None, Mock())
            
            tools = await get_available_mcp_tools()
            
            assert tools == {
                "filesystem": mock_filesystem_tools,
                "notion": None
            }

    @pytest.mark.asyncio
    async def test_check_mcp_server_health_success(self):
        """MCPサーバーヘルスチェック成功のテスト"""
        mock_filesystem_tools = Mock()
        mock_notion_tools = Mock()
        mock_exit_stack = AsyncMock()
        
        with patch('src.tools.mcp_integration.get_tools_async') as mock_get_tools:
            mock_get_tools.return_value = (mock_filesystem_tools, mock_notion_tools, mock_exit_stack)
            
            health_status = await check_mcp_server_health()
            
            assert health_status == {
                "filesystem": True,
                "notion": True
            }
            
            # exit_stackがクリーンアップされる
            mock_exit_stack.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_mcp_server_health_partial_failure(self):
        """MCPサーバーヘルスチェック（部分失敗）のテスト"""
        mock_filesystem_tools = Mock()
        mock_exit_stack = AsyncMock()
        
        with patch('src.tools.mcp_integration.get_tools_async') as mock_get_tools:
            mock_get_tools.return_value = (mock_filesystem_tools, None, mock_exit_stack)
            
            health_status = await check_mcp_server_health()
            
            assert health_status == {
                "filesystem": True,
                "notion": False
            }
            
            mock_exit_stack.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_mcp_server_health_all_failure(self):
        """MCPサーバーヘルスチェック（全失敗）のテスト"""
        mock_exit_stack = AsyncMock()
        
        with patch('src.tools.mcp_integration.get_tools_async') as mock_get_tools:
            mock_get_tools.return_value = (None, None, mock_exit_stack)
            
            health_status = await check_mcp_server_health()
            
            assert health_status == {
                "filesystem": False,
                "notion": False
            }
            
            mock_exit_stack.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_mcp_server_health_exception(self):
        """MCPサーバーヘルスチェック（例外発生）のテスト"""
        with patch('src.tools.mcp_integration.get_tools_async') as mock_get_tools:
            mock_get_tools.side_effect = Exception("Health check error")
            
            health_status = await check_mcp_server_health()
            
            assert health_status == {
                "filesystem": False,
                "notion": False
            }

    def test_environment_variables(self):
        """環境変数のテスト"""
        # デフォルト値のテスト
        assert FILESYSTEM_MCP_URL == "http://localhost:8000/sse"
        assert NOTION_MCP_URL == "http://localhost:3001/sse"

    @pytest.mark.asyncio
    async def test_exit_stack_cleanup(self):
        """ExitStackクリーンアップのテスト"""
        mock_filesystem_tools = Mock()
        mock_notion_tools = Mock()
        mock_fs_exit_stack = AsyncMock()
        mock_notion_exit_stack = AsyncMock()
        
        with patch('src.tools.mcp_integration.MCP_ENABLED', True), \
             patch('src.tools.mcp_integration.MCPToolset') as mock_toolset:
            
            mock_toolset.from_server = AsyncMock()
            mock_toolset.from_server.side_effect = [
                (mock_filesystem_tools, mock_fs_exit_stack),
                (mock_notion_tools, mock_notion_exit_stack)
            ]
            
            filesystem_tools, notion_tools, exit_stack = await get_tools_async()
            
            # ExitStackに両方のexit_stackが追加される
            assert exit_stack is not None
            
            # クリーンアップをテスト
            await exit_stack.aclose()

    @pytest.mark.asyncio
    async def test_sse_server_params_usage(self):
        """SseServerParamsの使用テスト"""
        with patch('src.tools.mcp_integration.MCP_ENABLED', True), \
             patch('src.tools.mcp_integration.MCPToolset') as mock_toolset, \
             patch('src.tools.mcp_integration.SseServerParams') as mock_sse_params:
            
            mock_toolset.from_server = AsyncMock(side_effect=Exception("Test"))
            
            await get_tools_async()
            
            # SseServerParamsが正しいURLで呼ばれる
            mock_sse_params.assert_any_call(url=FILESYSTEM_MCP_URL)
            mock_sse_params.assert_any_call(url=NOTION_MCP_URL)
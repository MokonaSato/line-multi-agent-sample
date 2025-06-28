"""ルートエージェントのテストモジュール"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from contextlib import AsyncExitStack

from src.agents.root_agent import create_agent


class TestRootAgent:
    """root_agentモジュールのテスト"""

    @pytest.fixture
    def reset_global_variables(self):
        """グローバル変数をリセット"""
        import src.agents.root_agent
        original_root_agent = src.agents.root_agent._root_agent
        original_exit_stack = src.agents.root_agent._exit_stack
        
        # テスト前にリセット
        src.agents.root_agent._root_agent = None
        src.agents.root_agent._exit_stack = AsyncExitStack()
        
        yield
        
        # テスト後に復元
        src.agents.root_agent._root_agent = original_root_agent
        src.agents.root_agent._exit_stack = original_exit_stack

    @pytest.mark.asyncio
    async def test_create_agent_success(self, reset_global_variables):
        """エージェント作成成功のテスト"""
        mock_prompts = {"test_prompt": "test content"}
        mock_agents = {"test_agent": Mock()}
        mock_root_agent = Mock()
        mock_exit_stack = AsyncExitStack()
        
        with patch('src.agents.root_agent.PromptManager') as mock_prompt_manager, \
             patch('src.agents.root_agent.AgentFactory') as mock_agent_factory:
            
            # PromptManagerのモック
            mock_pm_instance = Mock()
            mock_prompt_manager.return_value = mock_pm_instance
            mock_pm_instance.get_all_prompts.return_value = mock_prompts
            
            # AgentFactoryのモック
            mock_factory_instance = Mock()
            mock_agent_factory.return_value = mock_factory_instance
            mock_factory_instance.create_all_standard_agents = AsyncMock(return_value=mock_agents)
            mock_factory_instance.create_root_agent.return_value = mock_root_agent
            mock_factory_instance.exit_stack = mock_exit_stack
            
            agent, exit_stack = await create_agent()
            
            assert agent == mock_root_agent
            assert exit_stack == mock_exit_stack
            
            # PromptManagerが正しく使用されたかチェック
            mock_prompt_manager.assert_called_once()
            mock_pm_instance.get_all_prompts.assert_called_once()
            
            # AgentFactoryが正しく使用されたかチェック
            mock_agent_factory.assert_called_once_with(mock_prompts, mock_agent_factory.call_args[0][1])
            mock_factory_instance.create_all_standard_agents.assert_called_once()
            mock_factory_instance.create_root_agent.assert_called_once_with(mock_agents)

    @pytest.mark.asyncio
    async def test_create_agent_existing_agent(self, reset_global_variables):
        """既存エージェント返却のテスト"""
        import src.agents.root_agent
        
        # 既存エージェントを設定
        existing_agent = Mock()
        existing_exit_stack = AsyncExitStack()
        src.agents.root_agent._root_agent = existing_agent
        src.agents.root_agent._exit_stack = existing_exit_stack
        
        with patch('src.agents.root_agent.PromptManager') as mock_prompt_manager, \
             patch('src.agents.root_agent.AgentFactory') as mock_agent_factory:
            
            agent, exit_stack = await create_agent()
            
            assert agent == existing_agent
            assert exit_stack == existing_exit_stack
            
            # PromptManagerやAgentFactoryは呼ばれない
            mock_prompt_manager.assert_not_called()
            mock_agent_factory.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_agent_prompt_manager_failure(self, reset_global_variables):
        """PromptManager失敗のテスト"""
        with patch('src.agents.root_agent.PromptManager') as mock_prompt_manager:
            mock_prompt_manager.side_effect = Exception("PromptManager failed")
            
            with pytest.raises(Exception, match="PromptManager failed"):
                await create_agent()

    @pytest.mark.asyncio
    async def test_create_agent_factory_failure(self, reset_global_variables):
        """AgentFactory失敗のテスト"""
        mock_prompts = {"test_prompt": "test content"}
        
        with patch('src.agents.root_agent.PromptManager') as mock_prompt_manager, \
             patch('src.agents.root_agent.AgentFactory') as mock_agent_factory:
            
            # PromptManagerのモック
            mock_pm_instance = Mock()
            mock_prompt_manager.return_value = mock_pm_instance
            mock_pm_instance.get_all_prompts.return_value = mock_prompts
            
            # AgentFactoryのモック（失敗）
            mock_agent_factory.side_effect = Exception("AgentFactory failed")
            
            with pytest.raises(Exception, match="AgentFactory failed"):
                await create_agent()

    @pytest.mark.asyncio
    async def test_create_agent_create_all_standard_agents_failure(self, reset_global_variables):
        """create_all_standard_agents失敗のテスト"""
        mock_prompts = {"test_prompt": "test content"}
        
        with patch('src.agents.root_agent.PromptManager') as mock_prompt_manager, \
             patch('src.agents.root_agent.AgentFactory') as mock_agent_factory:
            
            # PromptManagerのモック
            mock_pm_instance = Mock()
            mock_prompt_manager.return_value = mock_pm_instance
            mock_pm_instance.get_all_prompts.return_value = mock_prompts
            
            # AgentFactoryのモック（create_all_standard_agents失敗）
            mock_factory_instance = Mock()
            mock_agent_factory.return_value = mock_factory_instance
            mock_factory_instance.create_all_standard_agents = AsyncMock(side_effect=Exception("Standard agents failed"))
            
            with pytest.raises(Exception, match="Standard agents failed"):
                await create_agent()

    @pytest.mark.asyncio
    async def test_create_agent_create_root_agent_failure(self, reset_global_variables):
        """create_root_agent失敗のテスト"""
        mock_prompts = {"test_prompt": "test content"}
        mock_agents = {"test_agent": Mock()}
        
        with patch('src.agents.root_agent.PromptManager') as mock_prompt_manager, \
             patch('src.agents.root_agent.AgentFactory') as mock_agent_factory:
            
            # PromptManagerのモック
            mock_pm_instance = Mock()
            mock_prompt_manager.return_value = mock_pm_instance
            mock_pm_instance.get_all_prompts.return_value = mock_prompts
            
            # AgentFactoryのモック（create_root_agent失敗）
            mock_factory_instance = Mock()
            mock_agent_factory.return_value = mock_factory_instance
            mock_factory_instance.create_all_standard_agents = AsyncMock(return_value=mock_agents)
            mock_factory_instance.create_root_agent.side_effect = Exception("Root agent failed")
            
            with pytest.raises(Exception, match="Root agent failed"):
                await create_agent()

    @pytest.mark.asyncio
    async def test_create_agent_global_state_update(self, reset_global_variables):
        """グローバル状態更新のテスト"""
        import src.agents.root_agent
        
        mock_prompts = {"test_prompt": "test content"}
        mock_agents = {"test_agent": Mock()}
        mock_root_agent = Mock()
        mock_exit_stack = AsyncExitStack()
        
        # 初期状態の確認
        assert src.agents.root_agent._root_agent is None
        
        with patch('src.agents.root_agent.PromptManager') as mock_prompt_manager, \
             patch('src.agents.root_agent.AgentFactory') as mock_agent_factory:
            
            # PromptManagerのモック
            mock_pm_instance = Mock()
            mock_prompt_manager.return_value = mock_pm_instance
            mock_pm_instance.get_all_prompts.return_value = mock_prompts
            
            # AgentFactoryのモック
            mock_factory_instance = Mock()
            mock_agent_factory.return_value = mock_factory_instance
            mock_factory_instance.create_all_standard_agents = AsyncMock(return_value=mock_agents)
            mock_factory_instance.create_root_agent.return_value = mock_root_agent
            mock_factory_instance.exit_stack = mock_exit_stack
            
            agent, exit_stack = await create_agent()
            
            # グローバル状態が更新されたかチェック
            assert src.agents.root_agent._root_agent == mock_root_agent
            assert src.agents.root_agent._exit_stack == mock_exit_stack

    @pytest.mark.asyncio
    async def test_create_agent_with_empty_prompts(self, reset_global_variables):
        """空のプロンプト辞書でのエージェント作成のテスト"""
        mock_prompts = {}
        mock_agents = {}
        mock_root_agent = Mock()
        mock_exit_stack = AsyncExitStack()
        
        with patch('src.agents.root_agent.PromptManager') as mock_prompt_manager, \
             patch('src.agents.root_agent.AgentFactory') as mock_agent_factory:
            
            # PromptManagerのモック
            mock_pm_instance = Mock()
            mock_prompt_manager.return_value = mock_pm_instance
            mock_pm_instance.get_all_prompts.return_value = mock_prompts
            
            # AgentFactoryのモック
            mock_factory_instance = Mock()
            mock_agent_factory.return_value = mock_factory_instance
            mock_factory_instance.create_all_standard_agents = AsyncMock(return_value=mock_agents)
            mock_factory_instance.create_root_agent.return_value = mock_root_agent
            mock_factory_instance.exit_stack = mock_exit_stack
            
            agent, exit_stack = await create_agent()
            
            assert agent == mock_root_agent
            assert exit_stack == mock_exit_stack
            
            # 空のプロンプト辞書でもAgentFactoryが呼ばれる
            mock_agent_factory.assert_called_once_with(mock_prompts, mock_agent_factory.call_args[0][1])

    @pytest.mark.asyncio
    async def test_create_agent_with_empty_agents(self, reset_global_variables):
        """空のエージェント辞書でのルートエージェント作成のテスト"""
        mock_prompts = {"test_prompt": "test content"}
        mock_agents = {}  # 空のエージェント辞書
        mock_root_agent = Mock()
        mock_exit_stack = AsyncExitStack()
        
        with patch('src.agents.root_agent.PromptManager') as mock_prompt_manager, \
             patch('src.agents.root_agent.AgentFactory') as mock_agent_factory:
            
            # PromptManagerのモック
            mock_pm_instance = Mock()
            mock_prompt_manager.return_value = mock_pm_instance
            mock_pm_instance.get_all_prompts.return_value = mock_prompts
            
            # AgentFactoryのモック
            mock_factory_instance = Mock()
            mock_agent_factory.return_value = mock_factory_instance
            mock_factory_instance.create_all_standard_agents = AsyncMock(return_value=mock_agents)
            mock_factory_instance.create_root_agent.return_value = mock_root_agent
            mock_factory_instance.exit_stack = mock_exit_stack
            
            agent, exit_stack = await create_agent()
            
            assert agent == mock_root_agent
            assert exit_stack == mock_exit_stack
            
            # 空のエージェント辞書でもcreate_root_agentが呼ばれる
            mock_factory_instance.create_root_agent.assert_called_once_with(mock_agents)
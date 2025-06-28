"""エージェントファクトリーのテストモジュール"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from contextlib import AsyncExitStack

from src.agents.agent_factory import AgentFactory
from src.agents.config import AGENT_CONFIG


class TestAgentFactory:
    """AgentFactoryクラスのテスト"""

    @pytest.fixture
    def mock_prompts(self):
        """テスト用プロンプト辞書"""
        return {
            "calculator": "計算エージェントの指示",
            "notion": "Notionエージェントの指示", 
            "vision": "画像認識エージェントの指示",
            "filesystem": "ファイルシステムエージェントの指示",
            "root": "ルートエージェントの指示",
            "recipe_workflow": "URLレシピ抽出ワークフローの指示",
            "recipe_extraction": "コンテンツ抽出の指示",
            "data_transformation": "データ変換の指示",
            "recipe_notion": "Notion登録の指示",
            "image_workflow": "画像レシピ抽出ワークフローの指示",
            "image_analysis": "画像分析の指示",
            "image_data_enhancement": "データ強化の指示",
            "image_notion": "画像レシピNotion登録の指示",
        }

    @pytest.fixture
    def agent_factory(self, mock_prompts):
        """AgentFactoryインスタンス"""
        return AgentFactory(prompts=mock_prompts, config=AGENT_CONFIG)

    def test_init(self, mock_prompts):
        """初期化のテスト"""
        factory = AgentFactory(prompts=mock_prompts, config=AGENT_CONFIG)
        
        assert factory.prompts == mock_prompts
        assert factory.config == AGENT_CONFIG
        assert factory.notion_mcp_tools is None
        assert factory.filesystem_mcp_tools is None
        assert isinstance(factory.exit_stack, AsyncExitStack)
        assert not factory._mcp_tools_initialized

    @pytest.mark.asyncio
    async def test_initialize_mcp_tools_success(self, agent_factory):
        """MCP ツール初期化成功のテスト"""
        mock_fs_tools = Mock()
        mock_notion_tools = Mock()
        mock_exit_stack = Mock()
        
        with patch('src.agents.agent_factory.get_tools_async') as mock_get_tools:
            mock_get_tools.return_value = (mock_fs_tools, mock_notion_tools, mock_exit_stack)
            
            await agent_factory._initialize_mcp_tools()
            
            assert agent_factory.filesystem_mcp_tools == mock_fs_tools
            assert agent_factory.notion_mcp_tools == mock_notion_tools
            assert agent_factory.exit_stack == mock_exit_stack
            assert agent_factory._mcp_tools_initialized

    @pytest.mark.asyncio
    async def test_initialize_mcp_tools_failure(self, agent_factory):
        """MCP ツール初期化失敗のテスト"""
        with patch('src.agents.agent_factory.get_tools_async') as mock_get_tools:
            mock_get_tools.side_effect = Exception("Connection failed")
            
            await agent_factory._initialize_mcp_tools()
            
            assert agent_factory.filesystem_mcp_tools is None
            assert agent_factory.notion_mcp_tools is None
            assert agent_factory._mcp_tools_initialized

    @pytest.mark.asyncio
    async def test_initialize_mcp_tools_already_initialized(self, agent_factory):
        """MCP ツール重複初期化のテスト"""
        agent_factory._mcp_tools_initialized = True
        
        with patch('src.agents.agent_factory.get_tools_async') as mock_get_tools:
            await agent_factory._initialize_mcp_tools()
            
            mock_get_tools.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_notion_mcp_tools_async(self, agent_factory):
        """Notion MCP ツール取得のテスト"""
        mock_tools = Mock()
        agent_factory.notion_mcp_tools = mock_tools
        agent_factory._mcp_tools_initialized = True
        
        result = await agent_factory.get_notion_mcp_tools_async()
        assert result == mock_tools

    @pytest.mark.asyncio
    async def test_get_filesystem_mcp_tools_async(self, agent_factory):
        """Filesystem MCP ツール取得のテスト"""
        mock_tools = Mock()
        agent_factory.filesystem_mcp_tools = mock_tools
        agent_factory._mcp_tools_initialized = True
        
        result = await agent_factory.get_filesystem_mcp_tools_async()
        assert result == mock_tools

    @pytest.mark.asyncio
    async def test_cleanup_mcp_resources_success(self, agent_factory):
        """MCP リソースクリーンアップ成功のテスト"""
        mock_exit_stack = AsyncMock()
        agent_factory.exit_stack = mock_exit_stack
        
        await agent_factory.cleanup_mcp_resources()
        
        mock_exit_stack.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_mcp_resources_failure(self, agent_factory):
        """MCP リソースクリーンアップ失敗のテスト"""
        mock_exit_stack = AsyncMock()
        mock_exit_stack.aclose.side_effect = Exception("Cleanup failed")
        agent_factory.exit_stack = mock_exit_stack
        
        # エラーが発生してもExceptionは発生しない
        await agent_factory.cleanup_mcp_resources()
        
        mock_exit_stack.aclose.assert_called_once()

    def test_create_calculator_agent(self, agent_factory):
        """計算エージェント作成のテスト"""
        with patch('src.agents.agent_factory.Agent') as mock_agent:
            agent = agent_factory.create_calculator_agent()
            
            cfg = AGENT_CONFIG["calculator"]
            mock_agent.assert_called_once_with(
                name=cfg["name"],
                model=cfg["model"],
                description=cfg["description"],
                instruction=agent_factory.prompts[cfg["prompt_key"]],
                tools=mock_agent.call_args[1]["tools"]
            )

    def test_create_google_search_agent(self, agent_factory):
        """Google検索エージェント作成のテスト"""
        with patch('src.agents.agent_factory.Agent') as mock_agent:
            agent = agent_factory.create_google_search_agent()
            
            cfg = AGENT_CONFIG["google_search"]
            mock_agent.assert_called_once_with(
                name=cfg["name"],
                model=cfg["model"],
                description=cfg["description"],
                instruction=cfg.get("instruction", "インターネット検索であなたの質問に答えます。"),
                tools=mock_agent.call_args[1]["tools"]
            )

    @pytest.mark.asyncio
    async def test_create_notion_agent_success(self, agent_factory):
        """Notion エージェント作成成功のテスト"""
        mock_tools = [Mock(), Mock()]
        agent_factory.notion_mcp_tools = mock_tools
        agent_factory._mcp_tools_initialized = True
        
        with patch('src.agents.agent_factory.LlmAgent') as mock_llm_agent:
            agent = await agent_factory.create_notion_agent()
            
            cfg = AGENT_CONFIG["notion"]
            mock_llm_agent.assert_called_once_with(
                name=cfg["name"],
                model=cfg["model"],
                instruction=agent_factory.prompts[cfg["prompt_key"]],
                description=cfg["description"],
                tools=mock_tools,
                output_key=cfg.get("output_key")
            )

    @pytest.mark.asyncio
    async def test_create_notion_agent_no_tools(self, agent_factory):
        """Notion エージェント作成失敗（ツールなし）のテスト"""
        agent_factory.notion_mcp_tools = None
        agent_factory._mcp_tools_initialized = True
        
        with pytest.raises(RuntimeError, match="Notion MCP Toolset is not available"):
            await agent_factory.create_notion_agent()

    @pytest.mark.asyncio
    async def test_create_notion_agent_invalid_params(self, agent_factory):
        """Notion エージェント作成失敗（無効パラメータ）のテスト"""
        mock_tools = [Mock()]
        agent_factory.notion_mcp_tools = mock_tools
        agent_factory._mcp_tools_initialized = True
        
        # nameが空の場合
        with patch.dict(AGENT_CONFIG["notion"], {"name": ""}):
            with pytest.raises(ValueError, match="Agent name is required"):
                await agent_factory.create_notion_agent()
        
        # modelが空の場合
        with patch.dict(AGENT_CONFIG["notion"], {"model": ""}):
            with pytest.raises(ValueError, match="Agent model is required"):
                await agent_factory.create_notion_agent()
        
        # instructionがエラーの場合
        agent_factory.prompts[AGENT_CONFIG["notion"]["prompt_key"]] = "Error: Invalid prompt"
        with pytest.raises(ValueError, match="Valid instruction is required"):
            await agent_factory.create_notion_agent()

    def test_create_vision_agent(self, agent_factory):
        """画像認識エージェント作成のテスト"""
        with patch('src.agents.agent_factory.LlmAgent') as mock_llm_agent:
            agent = agent_factory.create_vision_agent()
            
            cfg = AGENT_CONFIG["vision"]
            mock_llm_agent.assert_called_once_with(
                name=cfg["name"],
                model=cfg["model"],
                instruction=agent_factory.prompts[cfg["prompt_key"]],
                description=cfg["description"],
                tools=[]
            )

    @pytest.mark.asyncio
    async def test_create_filesystem_agent_success(self, agent_factory):
        """ファイルシステムエージェント作成成功のテスト"""
        mock_tools = Mock()
        agent_factory.filesystem_mcp_tools = mock_tools
        agent_factory._mcp_tools_initialized = True
        
        with patch('src.agents.agent_factory.Agent') as mock_agent:
            agent = await agent_factory.create_filesystem_agent()
            
            cfg = AGENT_CONFIG["filesystem"]
            mock_agent.assert_called_once_with(
                name=cfg["name"],
                model=cfg["model"],
                description=cfg["description"],
                instruction=agent_factory.prompts[cfg["prompt_key"]],
                tools=mock_tools
            )

    @pytest.mark.asyncio
    async def test_create_filesystem_agent_no_tools(self, agent_factory):
        """ファイルシステムエージェント作成失敗（ツールなし）のテスト"""
        agent_factory.filesystem_mcp_tools = None
        agent_factory._mcp_tools_initialized = True
        
        with pytest.raises(RuntimeError, match="Filesystem MCP Toolset unavailable"):
            await agent_factory.create_filesystem_agent()

    @pytest.mark.asyncio
    async def test_create_url_recipe_pipeline_success(self, agent_factory):
        """URLレシピパイプライン作成成功のテスト"""
        mock_tools = [Mock()]
        agent_factory.notion_mcp_tools = mock_tools
        agent_factory._mcp_tools_initialized = True
        
        with patch('src.agents.agent_factory.LlmAgent') as mock_llm_agent, \
             patch('src.agents.agent_factory.SequentialAgent') as mock_seq_agent:
            
            pipeline = await agent_factory.create_url_recipe_pipeline()
            
            # 3つのエージェントが作成される
            assert mock_llm_agent.call_count == 3
            mock_seq_agent.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_url_recipe_pipeline_no_tools(self, agent_factory):
        """URLレシピパイプライン作成失敗（ツールなし）のテスト"""
        agent_factory.notion_mcp_tools = None
        agent_factory._mcp_tools_initialized = True
        
        with pytest.raises(RuntimeError, match="Notion MCP Toolset is not available"):
            await agent_factory.create_url_recipe_pipeline()

    @pytest.mark.asyncio
    async def test_create_url_recipe_pipeline_missing_db_id(self, agent_factory):
        """URLレシピパイプライン作成失敗（DB ID未設定）のテスト"""
        with patch.dict(AGENT_CONFIG["url_recipe"]["registration_agent"], {"variables": {}}):
            with pytest.raises(ValueError, match="recipe_database_id.*が未設定"):
                await agent_factory.create_url_recipe_pipeline()

    @pytest.mark.asyncio
    async def test_create_image_recipe_pipeline_success(self, agent_factory):
        """画像レシピパイプライン作成成功のテスト"""
        mock_tools = [Mock()]
        agent_factory.notion_mcp_tools = mock_tools
        agent_factory._mcp_tools_initialized = True
        
        with patch('src.agents.agent_factory.LlmAgent') as mock_llm_agent, \
             patch('src.agents.agent_factory.SequentialAgent') as mock_seq_agent:
            
            pipeline = await agent_factory.create_image_recipe_pipeline()
            
            # 3つのエージェントが作成される
            assert mock_llm_agent.call_count == 3
            mock_seq_agent.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_image_recipe_pipeline_missing_db_id(self, agent_factory):
        """画像レシピパイプライン作成失敗（DB ID未設定）のテスト"""
        with patch.dict(AGENT_CONFIG["image_recipe"]["registration_agent"], {"variables": {}}):
            with pytest.raises(ValueError, match="recipe_database_id.*が未設定"):
                await agent_factory.create_image_recipe_pipeline()

    @pytest.mark.asyncio
    async def test_create_url_recipe_workflow_agent(self, agent_factory):
        """URLレシピワークフローエージェント作成のテスト"""
        mock_pipeline = Mock()
        
        with patch.object(agent_factory, 'create_url_recipe_pipeline', return_value=mock_pipeline), \
             patch('src.agents.agent_factory.LlmAgent') as mock_llm_agent:
            
            agent = await agent_factory.create_url_recipe_workflow_agent()
            
            cfg = AGENT_CONFIG["url_recipe"]["workflow_agent"]
            mock_llm_agent.assert_called_once()
            assert agent is not None

    @pytest.mark.asyncio
    async def test_create_image_recipe_workflow_agent(self, agent_factory):
        """画像レシピワークフローエージェント作成のテスト"""
        mock_pipeline = Mock()
        
        with patch.object(agent_factory, 'create_image_recipe_pipeline', return_value=mock_pipeline), \
             patch('src.agents.agent_factory.LlmAgent') as mock_llm_agent:
            
            agent = await agent_factory.create_image_recipe_workflow_agent()
            
            mock_llm_agent.assert_called_once()
            assert agent is not None

    @pytest.mark.asyncio
    async def test_create_all_standard_agents_partial_success(self, agent_factory):
        """全標準エージェント作成（部分成功）のテスト"""
        # 一部のエージェントが成功、一部が失敗する場合
        agent_factory._mcp_tools_initialized = True
        agent_factory.notion_mcp_tools = [Mock()]
        agent_factory.filesystem_mcp_tools = [Mock()]
        
        with patch.object(agent_factory, 'create_calculator_agent', return_value=Mock()) as mock_calc, \
             patch.object(agent_factory, 'create_google_search_agent', side_effect=Exception("Failed")) as mock_google, \
             patch.object(agent_factory, 'create_vision_agent', return_value=Mock()) as mock_vision, \
             patch.object(agent_factory, 'create_notion_agent', return_value=Mock()) as mock_notion, \
             patch.object(agent_factory, 'create_filesystem_agent', return_value=Mock()) as mock_fs, \
             patch.object(agent_factory, 'create_url_recipe_workflow_agent', return_value=Mock()) as mock_url_wf, \
             patch.object(agent_factory, 'create_image_recipe_workflow_agent', return_value=Mock()) as mock_img_wf, \
             patch.object(agent_factory, 'create_url_recipe_pipeline', return_value=Mock()) as mock_url_pipe, \
             patch.object(agent_factory, 'create_image_recipe_pipeline', return_value=Mock()) as mock_img_pipe:
            
            agents = await agent_factory.create_all_standard_agents()
            
            # 成功したエージェントのみが含まれる
            assert "calc_agent" in agents
            assert "google_search_agent" not in agents  # 失敗したので含まれない
            assert "vision_agent" in agents
            assert "notion_agent" in agents
            assert "filesystem_agent" in agents
            assert "url_recipe_workflow_agent" in agents
            assert "image_recipe_workflow_agent" in agents
            assert "RecipeExtractionPipeline" in agents
            assert "ImageRecipeExtractionPipeline" in agents

    @pytest.mark.asyncio
    async def test_create_all_standard_agents_all_failure(self, agent_factory):
        """全標準エージェント作成（全失敗）のテスト"""
        agent_factory._mcp_tools_initialized = True
        
        with patch.object(agent_factory, 'create_calculator_agent', side_effect=Exception("Failed")), \
             patch.object(agent_factory, 'create_google_search_agent', side_effect=Exception("Failed")), \
             patch.object(agent_factory, 'create_vision_agent', side_effect=Exception("Failed")), \
             patch.object(agent_factory, 'create_notion_agent', side_effect=Exception("Failed")), \
             patch.object(agent_factory, 'create_filesystem_agent', side_effect=Exception("Failed")), \
             patch.object(agent_factory, 'create_url_recipe_workflow_agent', side_effect=Exception("Failed")), \
             patch.object(agent_factory, 'create_image_recipe_workflow_agent', side_effect=Exception("Failed")), \
             patch.object(agent_factory, 'create_url_recipe_pipeline', side_effect=Exception("Failed")), \
             patch.object(agent_factory, 'create_image_recipe_pipeline', side_effect=Exception("Failed")):
            
            agents = await agent_factory.create_all_standard_agents()
            
            # 全エージェントが失敗した場合、空辞書が返される
            assert agents == {}

    def test_create_root_agent_full_agents(self, agent_factory):
        """ルートエージェント作成（全サブエージェント利用可能）のテスト"""
        sub_agents = {
            "calc_agent": Mock(),
            "url_recipe_workflow_agent": Mock(),
            "image_recipe_workflow_agent": Mock(),
            "notion_agent": Mock(),
            "vision_agent": Mock(),
            "filesystem_agent": Mock(),
            "google_search_agent": Mock(),
        }
        
        with patch('src.agents.agent_factory.LlmAgent') as mock_llm_agent, \
             patch('src.agents.agent_factory.agent_tool.AgentTool') as mock_agent_tool:
            
            agent = agent_factory.create_root_agent(sub_agents)
            
            mock_llm_agent.assert_called_once()
            assert agent is not None

    def test_create_root_agent_partial_agents(self, agent_factory):
        """ルートエージェント作成（一部サブエージェントのみ）のテスト"""
        sub_agents = {
            "calc_agent": Mock(),
            "vision_agent": Mock(),
        }
        
        with patch('src.agents.agent_factory.LlmAgent') as mock_llm_agent:
            
            agent = agent_factory.create_root_agent(sub_agents)
            
            mock_llm_agent.assert_called_once()
            assert agent is not None

    def test_create_root_agent_no_agents(self, agent_factory):
        """ルートエージェント作成（サブエージェントなし）のテスト"""
        sub_agents = {}
        
        with patch('src.agents.agent_factory.LlmAgent') as mock_llm_agent:
            
            agent = agent_factory.create_root_agent(sub_agents)
            
            mock_llm_agent.assert_called_once()
            assert agent is not None
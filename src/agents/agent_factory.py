"""エージェント生成用ファクトリーモジュール

このモジュールは様々な種類のエージェントを生成するためのファクトリークラスを提供します。
ファクトリーパターンを使用することで、エージェント生成ロジックをカプセル化し、
メインコードから分離します。
"""

from contextlib import AsyncExitStack
from typing import Dict, Optional

from google.adk.agents import Agent, SequentialAgent
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools import agent_tool, google_search
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset

from src.tools.calculator_tools import calculator_tools_list
from src.tools.mcp_integration import get_tools_async
from src.tools.notion_mcp_wrapper import notion_mcp_wrapper_tools
from src.tools.web_tools import fetch_web_content
from src.utils.logger import setup_logger

# ロガー
logger = setup_logger("agent_factory")


class AgentFactory:
    """エージェント生成のファクトリークラス

    各種エージェントの生成ロジックをカプセル化して提供します。
    """

    def __init__(self, prompts: Dict[str, str], config: Dict):
        self.prompts = prompts
        self.config = config
        self.notion_mcp_tools: Optional[MCPToolset] = None
        self.filesystem_mcp_tools: Optional[MCPToolset] = None
        self.exit_stack = AsyncExitStack()
        self._mcp_tools_initialized = False

    async def _initialize_mcp_tools(self) -> None:
        """MCPツールを一括初期化する"""
        if self._mcp_tools_initialized:
            return

        try:
            (
                self.filesystem_mcp_tools,
                self.notion_mcp_tools,
                self.exit_stack,
            ) = await get_tools_async()
            self._mcp_tools_initialized = True
            logger.info("MCP tools initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize MCP tools: {e}")
            logger.warning("Application will continue without MCP tools")
            self._mcp_tools_initialized = True  # エラーでも初期化済みとする

    async def get_notion_mcp_tools_async(self) -> Optional[MCPToolset]:
        """Notion MCP Serverからツールを取得する（非同期版）

        Returns:
            Optional[MCPToolset]: Notionツールセット（失敗時はNone）
        """
        await self._initialize_mcp_tools()
        return self.notion_mcp_tools

    async def get_filesystem_mcp_tools_async(self) -> Optional[MCPToolset]:
        """Filesystem MCP Serverからツールを取得する（非同期版）

        Returns:
            Optional[MCPToolset]: Filesystemツールセット（失敗時はNone）
        """
        await self._initialize_mcp_tools()
        return self.filesystem_mcp_tools

    async def cleanup_mcp_resources(self) -> None:
        """MCPリソースのクリーンアップ"""
        try:
            await self.exit_stack.aclose()
            logger.info("✅ MCP resources cleanup completed")
        except Exception as e:
            logger.error(f"Error during MCP cleanup: {e}")

    def create_calculator_agent(self) -> Agent:
        """計算エージェントを作成"""
        cfg = self.config["calculator"]
        return Agent(
            name=cfg["name"],
            model=cfg["model"],
            description=cfg["description"],
            instruction=self.prompts[cfg["prompt_key"]],
            tools=calculator_tools_list,
        )

    def create_google_search_agent(self) -> Agent:
        """Google検索エージェントを作成"""
        cfg = self.config["google_search"]
        return Agent(
            name=cfg["name"],
            model=cfg["model"],
            description=cfg["description"],
            instruction=cfg.get(
                "instruction", "インターネット検索であなたの質問に答えます。"
            ),
            tools=[google_search],
        )

    async def create_notion_agent(self) -> LlmAgent:
        """Notionエージェントを作成"""
        cfg = self.config["notion"]

        # MCP ツールを取得
        mcp_tools = await self.get_notion_mcp_tools_async()

        # MCPツールセットが利用できない場合、従来のNotion APIツールを使用
        if not mcp_tools:
            logger.warning(
                "Notion MCP Toolset is not available. "
                "Using legacy Notion API tools with wrapper as fallback."
            )
            # 従来のAPIツールを使用
            from src.tools.notion import TOOLS

            fallback_tools = TOOLS["general"]  # 汎用的な操作セットを使用
            
            # フォールバック時でもラッパーツールを追加
            all_tools = fallback_tools + notion_mcp_wrapper_tools

            return LlmAgent(
                name=cfg["name"],
                model=cfg["model"],
                instruction=self.prompts[cfg["prompt_key"]],
                description=(
                    cfg["description"] +
                    " (using legacy API tools with MCP wrapper)"
                ),
                tools=all_tools,
                output_key=cfg.get("output_key"),
            )

        # MCPツールセットが利用可能な場合、ラッパーツールも追加
        logger.info(
            "Notion agent created with MCP tools and compatibility wrapper"
        )

        # MCPツールセットにラッパーツールを組み合わせる
        all_tools = [mcp_tools] + notion_mcp_wrapper_tools

        return LlmAgent(
            name=cfg["name"],
            model=cfg["model"],
            instruction=self.prompts[cfg["prompt_key"]],
            description=cfg["description"],
            tools=all_tools,
            output_key=cfg.get("output_key"),
        )

    def create_vision_agent(self) -> LlmAgent:
        """汎用画像認識エージェントを作成"""
        cfg = self.config["vision"]
        return LlmAgent(
            name=cfg["name"],
            model=cfg["model"],
            instruction=self.prompts[cfg["prompt_key"]],
            description=cfg["description"],
            tools=[],  # 画像分析のみ
        )

    async def create_filesystem_agent(self) -> Agent:
        """ファイルシステム操作エージェントを作成"""
        cfg = self.config["filesystem"]

        # MCP ツールを取得
        mcp_tools = await self.get_filesystem_mcp_tools_async()

        # MCPツールセットが利用できない場合の警告と処理
        if not mcp_tools:
            logger.warning(
                "Filesystem MCP Toolset is not available. "
                "Filesystem agent will not be created."
            )
            raise RuntimeError("Filesystem MCP Toolset unavailable")

        logger.info("Filesystem agent created with MCP tools")
        return Agent(
            name=cfg["name"],
            model=cfg["model"],
            description=cfg["description"],
            instruction=self.prompts[cfg["prompt_key"]],
            tools=mcp_tools,
        )

    async def create_url_recipe_pipeline(self) -> SequentialAgent:
        """URLレシピ抽出パイプラインを作成"""
        url_cfg = self.config["url_recipe"]
        extract_cfg = url_cfg["extraction_agent"]
        transform_cfg = url_cfg["transformation_agent"]
        register_cfg = url_cfg["registration_agent"]
        pipe_cfg = url_cfg["pipeline"]

        # 1. Content Extraction Agent
        extract_instruction = self.prompts[extract_cfg["prompt_key"]]

        content_extraction_agent = LlmAgent(
            name=extract_cfg["name"],
            model=extract_cfg["model"],
            instruction=extract_instruction,
            description=extract_cfg["description"],
            tools=[fetch_web_content],
            output_key=extract_cfg["output_key"],
        )

        # 2. Data Transformation Agent
        transform_instruction = self.prompts[transform_cfg["prompt_key"]]

        data_transformation_agent = LlmAgent(
            name=transform_cfg["name"],
            model=transform_cfg["model"],
            instruction=transform_instruction,
            description=transform_cfg["description"],
            tools=[],
            output_key=transform_cfg["output_key"],
        )

        # 3. Notion Registration Agent
        register_instruction = self.prompts[register_cfg["prompt_key"]]

        # MCP ツールを取得
        mcp_tools = await self.get_notion_mcp_tools_async()

        # MCPツールセットが利用できない場合、従来のAPIツールを使用
        if not mcp_tools:
            logger.warning(
                "Notion MCP Toolset is not available for URL recipe pipeline. "
                "Using legacy Notion API tools as fallback."
            )
            # 従来のAPIツールを使用
            from src.tools.notion import TOOLS

            fallback_tools = TOOLS["recipes"] + TOOLS["pages"]
        else:
            # MCPツールセットとラッパーツールを組み合わせる
            fallback_tools = [mcp_tools] + notion_mcp_wrapper_tools

        notion_registration_agent = LlmAgent(
            name=register_cfg["name"],
            model=register_cfg["model"],
            instruction=register_instruction,
            description=register_cfg["description"],
            tools=fallback_tools,
            output_key=register_cfg["output_key"],
        )

        # 4. レシピ処理パイプライン
        return SequentialAgent(
            name=pipe_cfg["name"],
            sub_agents=[
                content_extraction_agent,
                data_transformation_agent,
                notion_registration_agent,
            ],
            description=pipe_cfg["description"],
        )

    async def create_image_recipe_pipeline(self) -> SequentialAgent:
        """画像レシピ抽出パイプラインを作成"""
        # 設定を取得
        img_cfg = self.config["image_recipe"]
        analysis_cfg = img_cfg["analysis_agent"]
        enhance_cfg = img_cfg["enhancement_agent"]
        register_cfg = img_cfg["registration_agent"]
        pipe_cfg = img_cfg["pipeline"]

        # 1. Image Analysis Agent
        # カスタム変数でプロンプトを取得
        from src.agents.prompt_manager import PromptManager

        prompt_manager = PromptManager()
        analysis_prompt = prompt_manager.get_prompt(
            analysis_cfg["prompt_key"], analysis_cfg.get("variables", {})
        )

        image_analysis_agent = LlmAgent(
            name=analysis_cfg["name"],
            model=analysis_cfg["model"],
            instruction=analysis_prompt,
            description=analysis_cfg["description"],
            tools=[],  # Geminiの視覚認識機能を使用
            output_key=analysis_cfg["output_key"],
        )

        # 2. Image Data Enhancement Agent
        # カスタム変数でプロンプトを取得
        enhancement_prompt = prompt_manager.get_prompt(
            enhance_cfg["prompt_key"], enhance_cfg.get("variables", {})
        )
        # コンテキスト変数を正しく設定
        enhancement_prompt = enhancement_prompt.replace(
            "{extracted_recipe_data}", "{extracted_image_data}"
        )

        image_data_enhancement_agent = LlmAgent(
            name=enhance_cfg["name"],
            model=enhance_cfg["model"],
            instruction=enhancement_prompt,
            description=enhance_cfg["description"],
            tools=[],  # データ処理のみ
            output_key=enhance_cfg["output_key"],
        )

        # 3. Recipe Notion Agent - MCP ツール対応
        # MCP ツールを取得
        mcp_tools = await self.get_notion_mcp_tools_async()

        # MCPツールセットが利用できない場合、従来のAPIツールを使用
        if not mcp_tools:
            logger.warning(
                "Notion MCP Toolset is not available for image recipe "
                "pipeline. Using legacy Notion API tools as fallback."
            )
            # 従来のAPIツールを使用
            from src.tools.notion import TOOLS

            fallback_tools = TOOLS["recipes"] + TOOLS["pages"]
        else:
            # MCPツールセットとラッパーツールを組み合わせる
            fallback_tools = [mcp_tools] + notion_mcp_wrapper_tools

        recipe_notion_agent = LlmAgent(
            name=register_cfg["name"],
            model=register_cfg["model"],
            instruction=self.prompts[register_cfg["prompt_key"]],
            description=register_cfg["description"],
            tools=fallback_tools,
            output_key=register_cfg["output_key"],
        )

        # 4. パイプライン
        return SequentialAgent(
            name=pipe_cfg["name"],
            sub_agents=[
                image_analysis_agent,
                image_data_enhancement_agent,
                recipe_notion_agent,
            ],
            description=pipe_cfg["description"],
        )

    async def create_url_recipe_workflow_agent(self) -> LlmAgent:
        """URLレシピワークフローエージェントを作成"""
        url_recipe_pipeline = await self.create_url_recipe_pipeline()
        cfg = self.config["url_recipe"]["workflow_agent"]

        # PromptManagerを使用して変数置換済みプロンプトを取得
        from src.agents.prompt_manager import PromptManager

        prompt_manager = PromptManager()
        instruction = prompt_manager.get_prompt(
            cfg["prompt_key"], cfg.get("variables", {})
        )

        return LlmAgent(
            name=cfg["name"],
            model=cfg["model"],
            instruction=instruction,
            description=cfg["description"],
            sub_agents=[url_recipe_pipeline],
        )

    async def create_image_recipe_workflow_agent(self) -> LlmAgent:
        """画像レシピワークフローエージェントを作成"""
        image_recipe_pipeline = await self.create_image_recipe_pipeline()
        cfg = self.config["image_recipe"]["workflow_agent"]

        # PromptManagerを使用して変数置換済みプロンプトを取得
        from src.agents.prompt_manager import PromptManager

        prompt_manager = PromptManager()
        instruction = prompt_manager.get_prompt(
            cfg["prompt_key"], cfg.get("variables", {})
        )

        return LlmAgent(
            name=cfg["name"],
            model=cfg["model"],
            instruction=instruction,
            description=cfg["description"],
            sub_agents=[image_recipe_pipeline],
        )

    async def create_all_standard_agents(self) -> Dict[str, Agent]:
        """すべての標準エージェントを一括で作成"""
        logger.info("すべての標準エージェントを作成します")

        agents = {}

        # 各エージェントを作成（失敗しても他のエージェントは作成を続行）
        try:
            agents["calc_agent"] = self.create_calculator_agent()
            logger.info("✅ Calculator agent created")
        except Exception as e:
            logger.warning(f"Calculator agent creation failed: {e}")

        try:
            agents["google_search_agent"] = self.create_google_search_agent()
            logger.info("✅ Google search agent created")
        except Exception as e:
            logger.warning(f"Google search agent creation failed: {e}")

        try:
            agents["vision_agent"] = self.create_vision_agent()
            logger.info("✅ Vision agent created")
        except Exception as e:
            logger.warning(f"Vision agent creation failed: {e}")

        # MCP依存のエージェントは慎重に作成
        try:
            agents["notion_agent"] = await self.create_notion_agent()
            logger.info("✅ Notion agent created")
        except Exception as e:
            logger.warning(f"Notion agent creation failed: {e}")

        try:
            agents["filesystem_agent"] = await self.create_filesystem_agent()
            logger.info("✅ Filesystem agent created")
        except Exception as e:
            logger.warning(f"Filesystem agent creation failed: {e}")

        try:
            agents["url_recipe_workflow_agent"] = (
                await self.create_url_recipe_workflow_agent()
            )
            logger.info("✅ URL recipe workflow agent created")
        except Exception as e:
            logger.warning(f"URL recipe workflow agent creation failed: {e}")

        try:
            agents["image_recipe_workflow_agent"] = (
                await self.create_image_recipe_workflow_agent()
            )
            logger.info("✅ Image recipe workflow agent created")
        except Exception as e:
            logger.warning(f"Image recipe workflow agent creation failed: {e}")

        logger.info(f"Created {len(agents)} agents successfully")
        return agents

    def create_root_agent(self, sub_agents: Dict[str, Agent]) -> LlmAgent:
        """ルートエージェントを作成"""
        cfg = self.config["root"]

        # PromptManagerを使用して変数置換済みプロンプトを取得
        from src.agents.prompt_manager import PromptManager

        prompt_manager = PromptManager()
        instruction = prompt_manager.get_prompt(
            cfg["prompt_key"], cfg.get("variables", {})
        )

        # 利用可能なサブエージェントのみをリストに追加
        available_sub_agents = []
        for agent_name in [
            "calc_agent",
            "url_recipe_workflow_agent",
            "image_recipe_workflow_agent",
            "notion_agent",
            "vision_agent",
            "filesystem_agent",
        ]:
            if agent_name in sub_agents:
                available_sub_agents.append(sub_agents[agent_name])

        # ツールリストも利用可能なエージェントに応じて構成
        tools = [fetch_web_content]
        if "google_search_agent" in sub_agents:
            tools.append(
                agent_tool.AgentTool(agent=sub_agents["google_search_agent"])
            )

        logger.info(
            f"Root agent created with {len(available_sub_agents)} sub-agents "
            f"and {len(tools)} tools"
        )

        return LlmAgent(
            model=cfg["model"],
            name=cfg["name"],
            instruction=instruction,
            description=cfg["description"],
            tools=tools,
            sub_agents=available_sub_agents,
        )

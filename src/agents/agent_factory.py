"""エージェント生成用ファクトリーモジュール

このモジュールは様々な種類のエージェントを生成するためのファクトリークラスを提供します。
ファクトリーパターンを使用することで、エージェント生成ロジックをカプセル化し、
メインコードから分離します。
"""

from typing import Dict

from google.adk.agents import Agent, SequentialAgent
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools import agent_tool, google_search

from src.tools.calculator_tools import calculator_tools_list
from src.tools.filesystem import filesystem_tools
from src.tools.notion import notion_tools_list
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
        # 共通変数を追加
        self.common_variables = {
            "recipe_database_id": "1f79a940-1325-80d9-93c6-c33da454f18f",
            "required_tools": "notion_create_recipe_page",
            "error_prevention": (
                "missing required parametersエラーを防ぐため、"
                "内部で専用ツールを使用"
            ),
            "required_fields": "名前、材料、手順",
        }

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

    def create_notion_agent(self) -> LlmAgent:
        """Notionエージェントを作成"""
        cfg = self.config["notion"]
        return LlmAgent(
            name=cfg["name"],
            model=cfg["model"],
            instruction=self.prompts[cfg["prompt_key"]],
            description=cfg["description"],
            tools=notion_tools_list,
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

    def create_filesystem_agent(self) -> Agent:
        """ファイルシステム操作エージェントを作成"""
        cfg = self.config["filesystem"]
        return Agent(
            name=cfg["name"],
            model=cfg["model"],
            description=cfg["description"],
            instruction=self.prompts[cfg["prompt_key"]],
            tools=filesystem_tools,
        )

    def create_url_recipe_pipeline(self) -> SequentialAgent:
        """URLレシピ抽出パイプラインを作成"""
        url_cfg = self.config["url_recipe"]
        extract_cfg = url_cfg["extraction_agent"]
        transform_cfg = url_cfg["transformation_agent"]
        register_cfg = url_cfg["registration_agent"]
        pipe_cfg = url_cfg["pipeline"]

        # 1. Content Extraction Agent
        extract_instruction = self.prompts[extract_cfg["prompt_key"]]
        for key, value in self.common_variables.items():
            placeholder = "{{" + key + "}}"
            extract_instruction = extract_instruction.replace(
                placeholder, str(value)
            )

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
        for key, value in self.common_variables.items():
            placeholder = "{{" + key + "}}"
            transform_instruction = transform_instruction.replace(
                placeholder, str(value)
            )

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
        for key, value in self.common_variables.items():
            placeholder = "{{" + key + "}}"
            register_instruction = register_instruction.replace(
                placeholder, str(value)
            )

        notion_registration_agent = LlmAgent(
            name=register_cfg["name"],
            model=register_cfg["model"],
            instruction=register_instruction,
            description=register_cfg["description"],
            tools=notion_tools_list,
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

    def create_image_recipe_pipeline(self) -> SequentialAgent:
        """画像レシピ抽出パイプラインを作成"""
        # 設定を取得
        img_cfg = self.config["image_recipe"]
        analysis_cfg = img_cfg["analysis_agent"]
        enhance_cfg = img_cfg["enhancement_agent"]
        register_cfg = img_cfg["registration_agent"]
        pipe_cfg = img_cfg["pipeline"]

        # 1. Image Analysis Agent
        image_analysis_agent = LlmAgent(
            name=analysis_cfg["name"],
            model=analysis_cfg["model"],
            instruction=self.prompts[analysis_cfg["prompt_key"]],
            description=analysis_cfg["description"],
            tools=[],  # Geminiの視覚認識機能を使用
            output_key=analysis_cfg["output_key"],
        )

        # 2. Image Data Enhancement Agent
        # プロンプトを動的に生成してコンテキスト変数を正しく設定
        enhancement_instruction = self.prompts[
            enhance_cfg["prompt_key"]
        ].replace("{extracted_recipe_data}", "{extracted_image_data}")

        image_data_enhancement_agent = LlmAgent(
            name=enhance_cfg["name"],
            model=enhance_cfg["model"],
            instruction=enhancement_instruction,
            description=enhance_cfg["description"],
            tools=[],  # データ処理のみ
            output_key=enhance_cfg["output_key"],
        )

        # 3. Recipe Notion Agent
        recipe_notion_agent = LlmAgent(
            name=register_cfg["name"],
            model=register_cfg["model"],
            instruction=self.prompts[register_cfg["prompt_key"]],
            description=register_cfg["description"],
            tools=notion_tools_list,
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

    def create_url_recipe_workflow_agent(self) -> LlmAgent:
        """URLレシピワークフローエージェントを作成"""
        url_recipe_pipeline = self.create_url_recipe_pipeline()
        cfg = self.config["url_recipe"]["workflow_agent"]

        # プロンプトに変数を注入
        instruction = self.prompts[cfg["prompt_key"]]

        # 変数置換を手動で行う
        for key, value in self.common_variables.items():
            placeholder = "{{" + key + "}}"
            instruction = instruction.replace(placeholder, str(value))

        return LlmAgent(
            name=cfg["name"],
            model=cfg["model"],
            instruction=instruction,
            description=cfg["description"],
            sub_agents=[url_recipe_pipeline],
        )

    def create_image_recipe_workflow_agent(self) -> LlmAgent:
        """画像レシピワークフローエージェントを作成"""
        image_recipe_pipeline = self.create_image_recipe_pipeline()
        cfg = self.config["image_recipe"]["workflow_agent"]

        # プロンプトに変数を注入
        instruction = self.prompts[cfg["prompt_key"]]

        # 変数置換を手動で行う
        for key, value in self.common_variables.items():
            placeholder = "{{" + key + "}}"
            instruction = instruction.replace(placeholder, str(value))

        return LlmAgent(
            name=cfg["name"],
            model=cfg["model"],
            instruction=instruction,
            description=cfg["description"],
            sub_agents=[image_recipe_pipeline],
        )

    def create_all_standard_agents(self) -> Dict[str, Agent]:
        """すべての標準エージェントを一括で作成"""
        logger.info("すべての標準エージェントを作成します")

        # 各エージェントを作成
        calc_agent = self.create_calculator_agent()
        url_workflow_agent = self.create_url_recipe_workflow_agent()
        image_workflow_agent = self.create_image_recipe_workflow_agent()
        google_search_agent = self.create_google_search_agent()
        notion_agent = self.create_notion_agent()
        vision_agent = self.create_vision_agent()
        filesystem_agent = self.create_filesystem_agent()

        # エージェントをディクショナリにまとめて返却
        return {
            "calc_agent": calc_agent,
            "url_recipe_workflow_agent": url_workflow_agent,
            "image_recipe_workflow_agent": image_workflow_agent,
            "google_search_agent": google_search_agent,
            "notion_agent": notion_agent,
            "vision_agent": vision_agent,
            "filesystem_agent": filesystem_agent,
        }

    def create_root_agent(self, sub_agents: Dict[str, Agent]) -> LlmAgent:
        """ルートエージェントを作成"""
        cfg = self.config["root"]

        # プロンプトに変数を注入
        instruction = self.prompts[cfg["prompt_key"]]

        # 変数置換を手動で行う
        for key, value in self.common_variables.items():
            placeholder = "{{" + key + "}}"
            instruction = instruction.replace(placeholder, str(value))

        return LlmAgent(
            model=cfg["model"],
            name=cfg["name"],
            instruction=instruction,
            description=cfg["description"],
            tools=[
                agent_tool.AgentTool(agent=sub_agents["google_search_agent"]),
                fetch_web_content,
            ],
            sub_agents=[
                sub_agents["calc_agent"],
                sub_agents["url_recipe_workflow_agent"],
                sub_agents["image_recipe_workflow_agent"],
                sub_agents["notion_agent"],
                sub_agents["vision_agent"],
                sub_agents["filesystem_agent"],
            ],
        )

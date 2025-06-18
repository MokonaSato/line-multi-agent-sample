# filepath: /workspace/src/agents/root_agent.py
"""マルチエージェントシステムのルートエージェント定義モジュール

このモジュールは、以下のコンポーネントを含む階層的なエージェントシステムを定義します：
- ルートエージェント: すべてのサブエージェントを管理・調整する
- 専用サブエージェント: 計算、レシピワークフロー、Notion操作など特定の機能を担当する
- 順次実行エージェント: 複数のステップからなるワークフローを管理する

このモジュールはエージェントの初期化と提供を行います。エージェント生成の実装詳細は
agent_factory.pyに分離されています。
"""

from contextlib import AsyncExitStack
from typing import Tuple

from google.adk.agents.llm_agent import LlmAgent

from src.agents.agent_factory import AgentFactory
from src.agents.config import AGENT_CONFIG
from src.agents.prompt_manager import PromptManager
from src.utils.logger import setup_logger

# ロガーを設定
logger = setup_logger("root_agent")

# グローバル変数
_root_agent = None
_exit_stack = AsyncExitStack()


async def create_agent() -> Tuple[LlmAgent, AsyncExitStack]:
    """ルートエージェントとすべてのサブエージェントを作成する

    Returns:
        Tuple[LlmAgent, AsyncExitStack]: ルートエージェントとリソース管理用のexitスタック
    """
    global _root_agent, _exit_stack

    # すでに作成済みの場合はそれを返す
    if _root_agent is not None:
        logger.info("既存のルートエージェントを返します")
        return _root_agent, _exit_stack

    try:
        logger.info("新しいルートエージェントを作成します")

        # プロンプトマネージャーからすべてのプロンプトを読み込む
        prompt_manager = PromptManager()
        prompts = prompt_manager.get_all_prompts()

        # ファクトリークラスを初期化してエージェントを作成
        factory = AgentFactory(prompts, AGENT_CONFIG)
        agents = await factory.create_all_standard_agents()
        _root_agent = factory.create_root_agent(agents)

        # MCPリソースの管理をグローバルで保持
        _exit_stack = factory.exit_stack

        logger.info("ルートエージェントの作成に成功しました")

    except Exception as e:
        logger.error(f"ルートエージェント作成中にエラーが発生: {e}")
        raise

    return _root_agent, _exit_stack

"""Google検索エージェント

このモジュールはGoogle検索機能を提供するエージェントを定義します。
"""

from google.adk.agents import Agent
from google.adk.tools import google_search

from src.agents.config import AGENT_CONFIG

# Google検索エージェントの設定
config = AGENT_CONFIG["google_search"]

# Google検索エージェントを作成
google_search_agent = Agent(
    name=config["name"],
    model=config["model"],
    description=config["description"],
    instruction=config.get(
        "instruction", "インターネット検索であなたの質問に答えます。"
    ),
    tools=[google_search],
)

# エージェント名を設定（テスト用）
name = config["name"]
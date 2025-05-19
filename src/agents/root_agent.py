from google.adk.agents import Agent
from google.adk.tools import agent_tool

from src.agents.calc_agent import calculator_agent
from src.agents.google_search_agent import google_search_agent
from src.agents.notion_agent import notion_agent

root_agent = Agent(
    name="RootAgent",
    model="gemini-2.0-flash",
    description=(
        "メインエージェントとして機能し、ユーザーの質問や要求に応じて適切な"
        "サブエージェントに処理を振り分けます。Google検索機能を持つ"
        "google_search_agentと計算処理を行うcalculator_agent, "
        "Notion操作をするnotion_agentを活用して、"
        "幅広い情報提供と計算タスクを実行できます。"
    ),
    tools=[
        agent_tool.AgentTool(agent=google_search_agent),
        # agent_tool.AgentTool(agent=notion_agent),
    ],
    sub_agents=[calculator_agent, notion_agent],
)

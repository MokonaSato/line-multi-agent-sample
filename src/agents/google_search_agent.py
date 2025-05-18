from google.adk.agents import Agent
from google.adk.tools import google_search

google_search_agent = Agent(
  name="google_search_agent",
  model="gemini-2.0-flash",
  description="Google検索を使って質問に答えるエージェントです。",
  instruction="インターネット検索であなたの質問に答えます。何でも聞いてください！",
  tools=[google_search]
)

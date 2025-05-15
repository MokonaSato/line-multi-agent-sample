import asyncio

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types  # For creating message Content/Parts

# config.pyをインポートして環境変数にアクセス
from config import GOOGLE_API_KEY  # noqa: F401
from src.agents.calc_agent import calculator_agent

session_service = InMemorySessionService()

# Define constants for identifying the interaction context
APP_NAME = "calculator_app"
USER_ID = "user_1"
SESSION_ID = "session_001"  # Using a fixed ID for simplicity

# Create the specific session where the conversation will happen
session = session_service.create_session(
    app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
)
print(
    (
        f"Session created: App='{APP_NAME}', "
        f"User='{USER_ID}', Session='{SESSION_ID}'"
    )
)

# --- Runner ---
# Key Concept: Runner orchestrates the agent execution loop.
runner = Runner(
    agent=calculator_agent,  # The agent we want to run
    app_name=APP_NAME,  # Associates runs with our app
    session_service=session_service,  # Uses our session manager
)
print(f"Runner created for agent '{runner.agent.name}'.")

# @title Define Agent Interaction Function


async def call_agent_async(query: str, runner, user_id, session_id):
    """Sends a query to the agent and prints the final response."""
    print(f"\n>>> User Query: {query}")

    content = types.Content(role="user", parts=[types.Part(text=query)])

    final_response_text = "Agent did not produce a final response."

    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            elif (
                event.actions and event.actions.escalate
            ):  # Handle potential errors/escalations
                final_response_text = (
                    f"Agent escalated: "
                    f"{event.error_message or 'No specific message.'}"
                )
            break  # Stop processing events once the final response is found

    print(f"<<< Agent Response: {final_response_text}")


async def run_conversation():
    await call_agent_async(
        "こんにちは",
        runner=runner,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )

    await call_agent_async(
        "10と20を足して",
        runner=runner,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )  # Expecting the tool's error message

    await call_agent_async(
        "12と34を足して",
        runner=runner,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )


if __name__ == "__main__":
    # Run the event loop
    asyncio.run(run_conversation())

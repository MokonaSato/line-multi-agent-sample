import asyncio

from src.services.agent_service import call_agent_async, setup_agent_runner

# Define constants for test purposes
USER_ID = "test_user_1"

# Initialize the agent runner
runner = setup_agent_runner()
print(f"Runner created for agent '{runner.agent.name}'.")


async def test_conversation():
    """一連の会話テストを実行"""
    print("\n=== テスト会話の開始 ===")

    # テスト1: 挨拶
    response1 = await call_agent_async("こんにちは", user_id=USER_ID)
    print("\n>>> User Query: こんにちは")
    print(f"<<< Agent Response: {response1}")

    # テスト2: 足し算（文章形式）
    response2 = await call_agent_async("10と20を足して", user_id=USER_ID)
    print("\n>>> User Query: 10と20を足して")
    print(f"<<< Agent Response: {response2}")

    # テスト3: 別の足し算
    response3 = await call_agent_async("12と34を足して", user_id=USER_ID)
    print("\n>>> User Query: 12と34を足して")
    print(f"<<< Agent Response: {response3}")

    # テスト4: 数字形式
    response4 = await call_agent_async("Google検索でピータンについて調べて概要を教えて", user_id=USER_ID)
    print("\n>>> User Query: Google検索でピータンについて調べて概要を教えて")
    print(f"<<< Agent Response: {response4}")

    print("\n=== テスト会話の終了 ===")


if __name__ == "__main__":
    # Run the event loop
    asyncio.run(test_conversation())

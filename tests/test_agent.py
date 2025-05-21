import asyncio

from src.services.agent_service_test import call_agent_async, cleanup_resources

# Define constants for test purposes
USER_ID = "test_user_1"

# Initialize the agent runner
runner = None  # 初期化を遅延させる


async def test_conversation():
    """一連の会話テストを実行"""
    try:

        print("\n=== テスト会話の開始 ===")

        # テスト1: 挨拶
        response1 = await call_agent_async("こんにちは", user_id=USER_ID)
        print("\n>>> User Query: こんにちは")
        print(f"<<< Agent Response: {response1}")

        # テスト2: 足し算（文章形式）
        response2 = await call_agent_async("10と20を足して", user_id=USER_ID)
        print("\n>>> User Query: 10と20を足して")
        print(f"<<< Agent Response: {response2}")

        # テスト3: Google検索
        response3 = await call_agent_async(
            "Google検索でピータンについて調べて概要を教えて", user_id=USER_ID
        )
        print("\n>>> User Query: Google検索でピータンについて調べて概要を教えて")
        print(f"<<< Agent Response: {response3}")

        # テスト4: Notion取得
        # Notionのリソース管理のためにtry-finallyを使用
        response4 = await call_agent_async(
            (
                "Notionのdatabase id: 1719a9401325808c9cd6ea99f9535f3a "
                "からレコードを3件取ってきて、タイトルを教えて。"
            ),
            user_id=USER_ID,
        )
        print(
            (
                "\n>>> User Query: Notionのdatabase id: "
                "1719a9401325808c9cd6ea99f9535f3a からレコードを3件取ってきて、タイトルを教えて。"
            )
        )
        print(f"<<< Agent Response: {response4}")
    finally:
        # Notionエージェントのクエリ実行後にクリーンアップを試みる
        await cleanup_resources()

    print("\n=== テスト会話の終了 ===")


if __name__ == "__main__":
    # Run the event loop
    asyncio.run(test_conversation())

from google.adk.agents import Agent


# 計算機能を実装する関数
def add_numbers(num1: int, num2: int) -> dict:
    """2つの数字を足し算する関数

    Args:
        num1 (int): 1つ目の数字
        num2 (int): 2つ目の数字

    Returns:
        dict: 計算結果を含む辞書
    """
    try:
        result = num1 + num2
        return {
            "status": "success",
            "result": result,
            "expression": f"{num1} + {num2} = {result}",
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"計算中にエラーが発生しました: {str(e)}",
        }


# Google ADKのエージェントを作成
calculator_agent = Agent(
    name="calculator_agent",
    model="gemini-2.0-flash",
    description="2つの数字を足し算するシンプルな計算エージェント",
    instruction=(
        "あなたは計算を支援するエージェントです。ユーザーから2つの数字を受け取ったら、"
        "add_numbers関数を使って足し算を行ってください。数字はスペースで区切られています。"
        "正しい計算結果を返してください。2つの数字が送信されない場合は、使い方を説明してください。"
    ),
    tools=[add_numbers],
)

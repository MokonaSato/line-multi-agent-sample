from google.adk.agents import Agent

from src.utils.logger import setup_logger

logger = setup_logger("calculator_agent")


# 計算機能を実装する関数
def add_numbers(num1: int, num2: int) -> dict:
    """2つの数字を足し算する関数

    Args:
        num1 (int): 1つ目の数字
        num2 (int): 2つ目の数字

    Returns:
        dict: 計算結果を含む辞書
    """

    logger.info(f"Adding numbers: {num1} + {num2}")
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


# 引き算する関数
def subtract_numbers(num1: int, num2: int) -> dict:
    """2つの数字を引き算する関数

    Args:
        num1 (int): 1つ目の数字
        num2 (int): 2つ目の数字

    Returns:
        dict: 計算結果を含む辞書
    """
    logger.info(f"Subtracting numbers: {num1} - {num2}")
    try:
        result = num1 - num2
        return {
            "status": "success",
            "result": result,
            "expression": f"{num1} - {num2} = {result}",
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"計算中にエラーが発生しました: {str(e)}",
        }


# 掛け算する関数
def multiply_numbers(num1: int, num2: int) -> dict:
    """2つの数字を掛け算する関数

    Args:
        num1 (int): 1つ目の数字
        num2 (int): 2つ目の数字

    Returns:
        dict: 計算結果を含む辞書
    """
    logger.info(f"Multiplying numbers: {num1} * {num2}")
    try:
        result = num1 * num2
        return {
            "status": "success",
            "result": result,
            "expression": f"{num1} * {num2} = {result}",
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"計算中にエラーが発生しました: {str(e)}",
        }


# 割り算する関数
def divide_numbers(num1: int, num2: int) -> dict:
    """2つの数字を割り算する関数

    Args:
        num1 (int): 1つ目の数字
        num2 (int): 2つ目の数字

    Returns:
        dict: 計算結果を含む辞書
    """
    logger.info(f"Dividing numbers: {num1} / {num2}")
    try:
        if num2 == 0:
            raise ValueError("0で割ることはできません。")
        result = num1 / num2
        return {
            "status": "success",
            "result": result,
            "expression": f"{num1} / {num2} = {result}",
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
    description="2つの数字を使って四則演算（足し算、引き算、掛け算、割り算）ができる計算エージェント",
    instruction=(
        "あなたは計算を支援するエージェントです。ユーザーから2つの数字と演算内容（足し算、引き算、掛け算、割り算）を受け取ったら、"
        "add_numbers, subtract_numbers, multiply_numbers, divide_numbers "
        "のいずれかの関数を使って計算を行ってください。"
        "数字や演算子はスペースで区切られています。正しい計算結果を返してください。"
        "2つの数字や演算内容が送信されない場合は、使い方を説明してください。"
    ),
    tools=[add_numbers, subtract_numbers, multiply_numbers, divide_numbers],
)

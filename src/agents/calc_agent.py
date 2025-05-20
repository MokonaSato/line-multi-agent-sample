import os

from google.adk.agents import Agent

from src.utils.file_utils import read_prompt_file
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


# プロンプトファイルのパスを指定
prompt_file_path = os.path.join(
    os.path.dirname(__file__), "prompts", "calculator.txt"
)
calculator_prompt = read_prompt_file(prompt_file_path)

# Google ADKのエージェントを作成
calculator_agent = Agent(
    name="calculator_agent",
    model="gemini-2.0-flash",
    description="2つの数字を使って四則演算（足し算、引き算、掛け算、割り算）ができる計算エージェント",
    instruction=calculator_prompt,
    tools=[add_numbers, subtract_numbers, multiply_numbers, divide_numbers],
)

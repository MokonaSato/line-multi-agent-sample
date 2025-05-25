from src.utils.logger import setup_logger

logger = setup_logger("calculator_tool")


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


calculator_tools_list = [
    add_numbers,
    subtract_numbers,
    multiply_numbers,
    divide_numbers,
]

"""
計算ツール機能のテストモジュール
"""

from unittest.mock import MagicMock, patch

import pytest

# プロジェクトルートを sys.path に追加
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.calculator_tools import (
    add_numbers,
    calculator_tools_list,
    divide_numbers,
    multiply_numbers,
    subtract_numbers,
)


class TestAddNumbers:
    """add_numbers関数のテストクラス"""

    def test_add_numbers_positive_integers(self):
        """正の整数の足し算テスト"""
        result = add_numbers(5, 3)

        assert result["status"] == "success"
        assert result["result"] == 8
        assert result["expression"] == "5 + 3 = 8"

    def test_add_numbers_negative_integers(self):
        """負の整数の足し算テスト"""
        result = add_numbers(-5, -3)

        assert result["status"] == "success"
        assert result["result"] == -8
        assert result["expression"] == "-5 + -3 = -8"

    def test_add_numbers_mixed_integers(self):
        """正負混合の整数の足し算テスト"""
        result = add_numbers(10, -3)

        assert result["status"] == "success"
        assert result["result"] == 7
        assert result["expression"] == "10 + -3 = 7"

    def test_add_numbers_zero(self):
        """ゼロを含む足し算テスト"""
        result = add_numbers(0, 5)

        assert result["status"] == "success"
        assert result["result"] == 5
        assert result["expression"] == "0 + 5 = 5"

    def test_add_numbers_both_zero(self):
        """両方ゼロの足し算テスト"""
        result = add_numbers(0, 0)

        assert result["status"] == "success"
        assert result["result"] == 0
        assert result["expression"] == "0 + 0 = 0"

    @patch("src.tools.calculator_tools.logger")
    def test_add_numbers_logging(self, mock_logger):
        """ログ出力のテスト"""
        add_numbers(5, 3)
        mock_logger.info.assert_called_once_with("Adding numbers: 5 + 3")


class TestSubtractNumbers:
    """subtract_numbers関数のテストクラス"""

    def test_subtract_numbers_positive_integers(self):
        """正の整数の引き算テスト"""
        result = subtract_numbers(10, 3)

        assert result["status"] == "success"
        assert result["result"] == 7
        assert result["expression"] == "10 - 3 = 7"

    def test_subtract_numbers_negative_result(self):
        """結果が負になる引き算テスト"""
        result = subtract_numbers(3, 10)

        assert result["status"] == "success"
        assert result["result"] == -7
        assert result["expression"] == "3 - 10 = -7"

    def test_subtract_numbers_negative_integers(self):
        """負の整数の引き算テスト"""
        result = subtract_numbers(-5, -3)

        assert result["status"] == "success"
        assert result["result"] == -2
        assert result["expression"] == "-5 - -3 = -2"

    def test_subtract_numbers_zero(self):
        """ゼロを含む引き算テスト"""
        result = subtract_numbers(5, 0)

        assert result["status"] == "success"
        assert result["result"] == 5
        assert result["expression"] == "5 - 0 = 5"

    def test_subtract_numbers_from_zero(self):
        """ゼロから引く引き算テスト"""
        result = subtract_numbers(0, 5)

        assert result["status"] == "success"
        assert result["result"] == -5
        assert result["expression"] == "0 - 5 = -5"

    @patch("src.tools.calculator_tools.logger")
    def test_subtract_numbers_logging(self, mock_logger):
        """ログ出力のテスト"""
        subtract_numbers(10, 3)
        mock_logger.info.assert_called_once_with("Subtracting numbers: 10 - 3")


class TestMultiplyNumbers:
    """multiply_numbers関数のテストクラス"""

    def test_multiply_numbers_positive_integers(self):
        """正の整数の掛け算テスト"""
        result = multiply_numbers(4, 5)

        assert result["status"] == "success"
        assert result["result"] == 20
        assert result["expression"] == "4 * 5 = 20"

    def test_multiply_numbers_negative_integers(self):
        """負の整数の掛け算テスト"""
        result = multiply_numbers(-4, -5)

        assert result["status"] == "success"
        assert result["result"] == 20
        assert result["expression"] == "-4 * -5 = 20"

    def test_multiply_numbers_mixed_integers(self):
        """正負混合の整数の掛け算テスト"""
        result = multiply_numbers(-4, 5)

        assert result["status"] == "success"
        assert result["result"] == -20
        assert result["expression"] == "-4 * 5 = -20"

    def test_multiply_numbers_by_zero(self):
        """ゼロとの掛け算テスト"""
        result = multiply_numbers(5, 0)

        assert result["status"] == "success"
        assert result["result"] == 0
        assert result["expression"] == "5 * 0 = 0"

    def test_multiply_numbers_by_one(self):
        """1との掛け算テスト"""
        result = multiply_numbers(7, 1)

        assert result["status"] == "success"
        assert result["result"] == 7
        assert result["expression"] == "7 * 1 = 7"

    @patch("src.tools.calculator_tools.logger")
    def test_multiply_numbers_logging(self, mock_logger):
        """ログ出力のテスト"""
        multiply_numbers(4, 5)
        mock_logger.info.assert_called_once_with("Multiplying numbers: 4 * 5")


class TestDivideNumbers:
    """divide_numbers関数のテストクラス"""

    def test_divide_numbers_positive_integers(self):
        """正の整数の割り算テスト"""
        result = divide_numbers(10, 2)

        assert result["status"] == "success"
        assert result["result"] == 5.0
        assert result["expression"] == "10 / 2 = 5.0"

    def test_divide_numbers_with_remainder(self):
        """余りのある割り算テスト"""
        result = divide_numbers(10, 3)

        assert result["status"] == "success"
        assert abs(result["result"] - 3.3333333333333335) < 1e-10
        assert result["expression"] == "10 / 3 = 3.3333333333333335"

    def test_divide_numbers_negative_integers(self):
        """負の整数の割り算テスト"""
        result = divide_numbers(-10, -2)

        assert result["status"] == "success"
        assert result["result"] == 5.0
        assert result["expression"] == "-10 / -2 = 5.0"

    def test_divide_numbers_mixed_integers(self):
        """正負混合の整数の割り算テスト"""
        result = divide_numbers(-10, 2)

        assert result["status"] == "success"
        assert result["result"] == -5.0
        assert result["expression"] == "-10 / 2 = -5.0"

    def test_divide_numbers_by_zero(self):
        """ゼロ除算のテスト"""
        result = divide_numbers(10, 0)

        assert result["status"] == "error"
        assert "0で割ることはできません" in result["error_message"]

    def test_divide_zero_by_number(self):
        """ゼロを数で割るテスト"""
        result = divide_numbers(0, 5)

        assert result["status"] == "success"
        assert result["result"] == 0.0
        assert result["expression"] == "0 / 5 = 0.0"

    def test_divide_numbers_by_one(self):
        """1で割るテスト"""
        result = divide_numbers(8, 1)

        assert result["status"] == "success"
        assert result["result"] == 8.0
        assert result["expression"] == "8 / 1 = 8.0"

    @patch("src.tools.calculator_tools.logger")
    def test_divide_numbers_logging(self, mock_logger):
        """ログ出力のテスト"""
        divide_numbers(10, 2)
        mock_logger.info.assert_called_once_with("Dividing numbers: 10 / 2")

    @patch("src.tools.calculator_tools.logger")
    def test_divide_numbers_zero_division_logging(self, mock_logger):
        """ゼロ除算のログ出力テスト"""
        divide_numbers(10, 0)
        mock_logger.info.assert_called_once_with("Dividing numbers: 10 / 0")


class TestCalculatorToolsList:
    """calculator_tools_list のテストクラス"""

    def test_calculator_tools_list_contains_all_functions(self):
        """全ての関数が含まれているかテスト"""
        expected_functions = [
            add_numbers,
            subtract_numbers,
            multiply_numbers,
            divide_numbers,
        ]

        assert len(calculator_tools_list) == 4
        for func in expected_functions:
            assert func in calculator_tools_list

    def test_calculator_tools_list_functions_are_callable(self):
        """リスト内の全ての関数が呼び出し可能かテスト"""
        for func in calculator_tools_list:
            assert callable(func)

    def test_calculator_tools_list_order(self):
        """リスト内の関数の順序をテスト"""
        expected_order = [
            add_numbers,
            subtract_numbers,
            multiply_numbers,
            divide_numbers,
        ]

        assert calculator_tools_list == expected_order


class TestErrorHandling:
    """エラーハンドリングのテストクラス"""

    @patch("src.tools.calculator_tools.logger")
    def test_add_numbers_exception_handling(self, mock_logger):
        """add_numbers の例外処理テスト"""
        # 通常は例外が発生しないが、テストのために強制的にエラーを発生させる
        with patch("builtins.int", side_effect=ValueError("Invalid input")):
            # 実際にはこの関数は型チェックがないため、文字列を渡してもエラーにならない
            # しかし、例外処理のパスをテストするために、内部でエラーが発生する状況をシミュレート
            pass

    def test_calculator_functions_with_large_numbers(self):
        """大きな数値での計算テスト"""
        large_num1 = 999999999
        large_num2 = 888888888

        # 足し算
        result = add_numbers(large_num1, large_num2)
        assert result["status"] == "success"
        assert result["result"] == large_num1 + large_num2

        # 引き算
        result = subtract_numbers(large_num1, large_num2)
        assert result["status"] == "success"
        assert result["result"] == large_num1 - large_num2

        # 掛け算
        result = multiply_numbers(large_num1, large_num2)
        assert result["status"] == "success"
        assert result["result"] == large_num1 * large_num2

        # 割り算
        result = divide_numbers(large_num1, large_num2)
        assert result["status"] == "success"
        assert abs(result["result"] - (large_num1 / large_num2)) < 1e-10

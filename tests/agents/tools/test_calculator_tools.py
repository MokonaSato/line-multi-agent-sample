from src.tools.calculator_tools import (
    add_numbers,
    divide_numbers,
    multiply_numbers,
    subtract_numbers,
)


def test_add():
    result = add_numbers(5, 3)
    assert result["expression"] == "5 + 3 = 8"
    assert result["result"] == 8
    assert result["status"] == "success"

    result = add_numbers(0.5, 0.3)
    assert result["expression"] == "0.5 + 0.3 = 0.8"
    assert result["result"] == 0.8
    assert result["status"] == "success"


def test_subtract():
    result = subtract_numbers(5, 3)
    assert result["expression"] == "5 - 3 = 2"
    assert result["result"] == 2
    assert result["status"] == "success"

    result = subtract_numbers(0.5, 0.3)
    assert result["expression"] == "0.5 - 0.3 = 0.2"
    assert result["result"] == 0.2
    assert result["status"] == "success"


def test_multiply():
    result = multiply_numbers(5, 3)
    assert result["expression"] == "5 * 3 = 15"
    assert result["result"] == 15
    assert result["status"] == "success"

    result = multiply_numbers(0.5, 0.3)
    assert result["expression"] == "0.5 * 0.3 = 0.15"
    assert result["result"] == 0.15
    assert result["status"] == "success"


def test_divide():
    result = divide_numbers(6, 3)
    assert result["expression"] == "6 / 3 = 2.0"
    assert result["result"] == 2.0
    assert result["status"] == "success"

    result = divide_numbers(0.6, 0.3)
    assert result["expression"] == "0.6 / 0.3 = 2.0"
    assert result["result"] == 2.0
    assert result["status"] == "success"


def test_divide_by_zero():
    result = divide_numbers(5, 0)
    assert result["status"] == "error"
    assert "0で割る" in result["error_message"]

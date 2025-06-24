"""
ファイルユーティリティ機能のテストモジュール
"""

import os
import tempfile
from unittest.mock import MagicMock, mock_open, patch

import pytest

# プロジェクトルートを sys.path に追加
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.file_utils import read_prompt_file


class TestReadPromptFile:
    """read_prompt_file関数のテストクラス"""

    def test_read_prompt_file_success(self):
        """ファイル読み込み成功のテスト"""
        # 一時ファイルを作成
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, encoding="utf-8"
        ) as f:
            test_content = "これはテスト用のプロンプトファイルです。\n日本語も含まれています。"
            f.write(test_content)
            temp_file_path = f.name

        try:
            result = read_prompt_file(temp_file_path)
            assert result == test_content
        finally:
            # 一時ファイルを削除
            os.unlink(temp_file_path)

    def test_read_prompt_file_empty_file(self):
        """空ファイルの読み込みテスト"""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, encoding="utf-8"
        ) as f:
            f.write("")  # 空ファイル
            temp_file_path = f.name

        try:
            result = read_prompt_file(temp_file_path)
            assert result == ""
        finally:
            os.unlink(temp_file_path)

    def test_read_prompt_file_japanese_content(self):
        """日本語コンテンツの読み込みテスト"""
        japanese_content = "これは日本語のテストです。\n複数行もテストします。\n特殊文字: ✓ ★ ◆"

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, encoding="utf-8"
        ) as f:
            f.write(japanese_content)
            temp_file_path = f.name

        try:
            result = read_prompt_file(temp_file_path)
            assert result == japanese_content
        finally:
            os.unlink(temp_file_path)

    def test_read_prompt_file_multiline_content(self):
        """複数行コンテンツの読み込みテスト"""
        multiline_content = "Line 1\nLine 2\nLine 3\n"

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, encoding="utf-8"
        ) as f:
            f.write(multiline_content)
            temp_file_path = f.name

        try:
            result = read_prompt_file(temp_file_path)
            assert result == multiline_content
        finally:
            os.unlink(temp_file_path)

    def test_read_prompt_file_not_exists(self):
        """存在しないファイルの読み込みテスト"""
        non_existent_file = "/path/to/non/existent/file.txt"

        with patch("builtins.print") as mock_print:
            result = read_prompt_file(non_existent_file)

            assert result == ""
            mock_print.assert_called_once()
            # エラーメッセージが出力されることを確認
            args = mock_print.call_args[0][0]
            assert "プロンプトファイルの読み込みエラー" in args

    def test_read_prompt_file_permission_error(self):
        """ファイル権限エラーのテスト"""
        with patch("builtins.open", mock_open()) as mock_file:
            mock_file.side_effect = PermissionError("Permission denied")

            with patch("builtins.print") as mock_print:
                result = read_prompt_file("some_file.txt")

                assert result == ""
                mock_print.assert_called_once()
                args = mock_print.call_args[0][0]
                assert "プロンプトファイルの読み込みエラー" in args
                assert "Permission denied" in args

    def test_read_prompt_file_encoding_error(self):
        """エンコーディングエラーのテスト"""
        with patch("builtins.open", mock_open()) as mock_file:
            mock_file.side_effect = UnicodeDecodeError(
                "utf-8", b"", 0, 1, "invalid start byte"
            )

            with patch("builtins.print") as mock_print:
                result = read_prompt_file("some_file.txt")

                assert result == ""
                mock_print.assert_called_once()
                args = mock_print.call_args[0][0]
                assert "プロンプトファイルの読み込みエラー" in args

    def test_read_prompt_file_io_error(self):
        """IOエラーのテスト"""
        with patch("builtins.open", mock_open()) as mock_file:
            mock_file.side_effect = IOError("I/O operation failed")

            with patch("builtins.print") as mock_print:
                result = read_prompt_file("some_file.txt")

                assert result == ""
                mock_print.assert_called_once()
                args = mock_print.call_args[0][0]
                assert "プロンプトファイルの読み込みエラー" in args
                assert "I/O operation failed" in args

    def test_read_prompt_file_path_with_spaces(self):
        """スペースを含むパスのテスト"""
        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            encoding="utf-8",
            prefix="test with spaces ",
            suffix=".txt",
        ) as f:
            test_content = "Space in filename test"
            f.write(test_content)
            temp_file_path = f.name

        try:
            result = read_prompt_file(temp_file_path)
            assert result == test_content
        finally:
            os.unlink(temp_file_path)

    @patch("builtins.open", mock_open(read_data="mocked content"))
    def test_read_prompt_file_mocked_success(self):
        """モックを使った正常動作のテスト"""
        result = read_prompt_file("mocked_file.txt")
        assert result == "mocked content"

    def test_read_prompt_file_binary_content(self):
        """バイナリコンテンツを含むファイルのテスト"""
        # UTF-8エンコーディングで正常に読める内容をテスト
        content_with_special_chars = (
            "Normal text with special chars: © ® ™ € £ ¥"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, encoding="utf-8"
        ) as f:
            f.write(content_with_special_chars)
            temp_file_path = f.name

        try:
            result = read_prompt_file(temp_file_path)
            assert result == content_with_special_chars
        finally:
            os.unlink(temp_file_path)

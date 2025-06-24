"""
ログ機能のテストモジュール
"""

import logging
import os
from unittest.mock import MagicMock, patch

from src.utils.logger import setup_logger


class TestSetupLogger:
    """setup_logger関数のテストクラス"""

    def test_setup_logger_creates_logger_with_correct_name(self):
        logger_name = "test_logger_name"
        logger = setup_logger(logger_name)
        assert logger.name == logger_name
        assert isinstance(logger, logging.Logger)

    def test_setup_logger_sets_debug_level(self):
        logger = setup_logger("test_logger_debug")
        assert logger.level == logging.DEBUG

    def test_setup_logger_adds_file_handler(self):
        logger = setup_logger("test_logger_file")
        file_handlers = [
            h for h in logger.handlers if isinstance(h, logging.FileHandler)
        ]
        assert len(file_handlers) == 1
        assert file_handlers[0].level == logging.DEBUG

    def test_setup_logger_adds_console_handler(self):
        logger = setup_logger("test_logger_console")
        stream_handlers = [
            h
            for h in logger.handlers
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)
        ]
        assert len(stream_handlers) == 1
        assert stream_handlers[0].level == logging.INFO

    def test_setup_logger_handler_count(self):
        logger = setup_logger("test_logger_count")
        assert len(logger.handlers) == 2

    def test_setup_logger_formatter_format(self):
        logger = setup_logger("test_logger_format")
        expected_format = (
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        for handler in logger.handlers:
            assert handler.formatter._fmt == expected_format

    def test_setup_logger_creates_app_log_file(self):
        # テスト前にapp.logを削除
        if os.path.exists("app.log"):
            os.remove("app.log")

        logger = setup_logger("test_logger_log_file")
        logger.debug("test message")

        # FileHandlerが強制的にファイルに書き込むように
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.flush()

        assert os.path.exists("app.log")

        # テスト後のクリーンアップ
        if os.path.exists("app.log"):
            os.remove("app.log")

    def test_setup_logger_multiple_calls_same_name(self):
        logger1 = setup_logger("same_name_test")
        logger2 = setup_logger("same_name_test")
        assert logger1.name == logger2.name
        assert len(logger2.handlers) == 2

    def test_setup_logger_different_names(self):
        logger1 = setup_logger("logger1_test")
        logger2 = setup_logger("logger2_test")
        assert logger1.name != logger2.name
        assert logger1 is not logger2

    @patch("logging.FileHandler")
    def test_setup_logger_file_handler_creation(self, mock_file_handler):
        mock_handler = MagicMock()
        mock_file_handler.return_value = mock_handler
        setup_logger("test_logger_file_creation")
        mock_file_handler.assert_called_once_with("app.log")
        mock_handler.setLevel.assert_called_with(logging.DEBUG)

    def test_setup_logger_stream_handler_creation(self):
        # モックを使わずに実際の動作をテスト
        logger = setup_logger("test_logger_stream_creation_simple")

        # StreamHandlerが存在することを確認
        stream_handlers = [
            h
            for h in logger.handlers
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)
        ]
        assert len(stream_handlers) == 1
        assert stream_handlers[0].level == logging.INFO

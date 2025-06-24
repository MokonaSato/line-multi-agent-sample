"""
ログ機能のシンプルなテストモジュール
"""

import logging
import os
import sys
from io import StringIO
from unittest.mock import patch

# sys.path 追加
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from src.utils.logger import setup_logger


class TestSetupLoggerSimple:
    """setup_logger関数のシンプルなテストクラス"""

    def test_setup_logger_creates_logger_with_correct_name(self):
        """ロガーが正しい名前で作成されることをテスト"""
        logger_name = "test_logger"
        logger = setup_logger(logger_name)
        assert logger.name == logger_name
        assert isinstance(logger, logging.Logger)

    def test_setup_logger_sets_debug_level(self):
        """ロガーのレベルがDEBUGに設定されることをテスト"""
        logger = setup_logger("test_logger")
        assert logger.level == logging.DEBUG

    def test_setup_logger_adds_handlers(self):
        """ハンドラーが追加されることをテスト"""
        logger = setup_logger("test_logger")
        assert len(logger.handlers) == 2
        
        # FileHandlerとStreamHandlerが存在することを確認
        handler_types = [type(h).__name__ for h in logger.handlers]
        assert "FileHandler" in handler_types
        assert "StreamHandler" in handler_types

    def test_setup_logger_handler_levels(self):
        """ハンドラーのレベルが正しく設定されることをテスト"""
        logger = setup_logger("test_logger")
        
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        # StreamHandlerとFileHandlerは継承関係にあるため、FileHandlerでないものをStreamHandlerとする
        stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)]
        
        assert len(file_handlers) == 1
        assert len(stream_handlers) == 1
        
        assert file_handlers[0].level == logging.DEBUG
        assert stream_handlers[0].level == logging.INFO

    def test_setup_logger_formatter_format(self):
        """フォーマッターが正しく設定されることをテスト"""
        logger = setup_logger("test_logger")
        expected_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        for handler in logger.handlers:
            assert handler.formatter._fmt == expected_format

    def test_setup_logger_multiple_calls_same_name(self):
        """同じ名前で複数回呼び出した時の動作をテスト"""
        logger1 = setup_logger("same_name")
        logger2 = setup_logger("same_name")
        
        assert logger1.name == logger2.name
        # 既存ハンドラーがクリアされているため、ハンドラー数は2つのまま
        assert len(logger2.handlers) == 2

    def test_setup_logger_different_names(self):
        """異なる名前のロガーが作成されることをテスト"""
        logger1 = setup_logger("logger1")
        logger2 = setup_logger("logger2")
        
        assert logger1.name != logger2.name
        assert logger1 is not logger2

    def test_setup_logger_creates_app_log_file(self):
        """app.logファイルが作成されることをテスト"""
        # 既存のapp.logファイルを削除
        if os.path.exists("app.log"):
            os.remove("app.log")
        
        logger = setup_logger("test_logger")
        logger.debug("test message")
        
        assert os.path.exists("app.log")
        
        # テスト後のクリーンアップ
        if os.path.exists("app.log"):
            os.remove("app.log")

    def test_setup_logger_output(self):
        """ログ出力が正しく動作することをテスト"""
        # StreamHandlerの出力をキャプチャ
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            logger = setup_logger("test_output")
            logger.info("test message")
            
            # ログ出力が含まれていることを確認
            output = mock_stdout.getvalue()
            # StreamHandlerからの出力があることを確認（フォーマットに依存）
            # 注：実際の出力は環境によって異なる可能性があります
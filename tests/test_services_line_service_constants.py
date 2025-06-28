"""LINEサービス定数のテストモジュール"""

import pytest
from unittest.mock import patch, Mock
import os

from src.services.line_service.constants import get_line_config, ERROR_MESSAGE


class TestLineConstants:
    """LINEサービス定数のテスト"""

    def test_get_line_config_success(self):
        """LINE設定取得成功のテスト"""
        with patch.dict(os.environ, {
            'LINE_CHANNEL_ACCESS_TOKEN': 'test_access_token',
            'LINE_CHANNEL_SECRET': 'test_channel_secret'
        }):
            access_token, channel_secret = get_line_config()
            
            assert access_token == 'test_access_token'
            assert channel_secret == 'test_channel_secret'

    def test_get_line_config_missing_access_token(self):
        """LINE設定取得失敗（アクセストークン未設定）のテスト"""
        with patch.dict(os.environ, {
            'LINE_CHANNEL_SECRET': 'test_channel_secret'
        }, clear=True):
            with pytest.raises(ValueError, match="LINE_CHANNEL_ACCESS_TOKEN"):
                get_line_config()

    def test_get_line_config_missing_channel_secret(self):
        """LINE設定取得失敗（チャンネルシークレット未設定）のテスト"""
        with patch.dict(os.environ, {
            'LINE_CHANNEL_ACCESS_TOKEN': 'test_access_token'
        }, clear=True):
            with pytest.raises(ValueError, match="LINE_CHANNEL_SECRET"):
                get_line_config()

    def test_get_line_config_both_missing(self):
        """LINE設定取得失敗（両方未設定）のテスト"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="LINE_CHANNEL_ACCESS_TOKEN"):
                get_line_config()

    def test_get_line_config_empty_values(self):
        """LINE設定取得失敗（空文字）のテスト"""
        with patch.dict(os.environ, {
            'LINE_CHANNEL_ACCESS_TOKEN': '',
            'LINE_CHANNEL_SECRET': 'test_channel_secret'
        }):
            with pytest.raises(ValueError, match="LINE_CHANNEL_ACCESS_TOKEN"):
                get_line_config()

    def test_error_message_exists(self):
        """エラーメッセージが定義されていることのテスト"""
        assert isinstance(ERROR_MESSAGE, str)
        assert len(ERROR_MESSAGE) > 0
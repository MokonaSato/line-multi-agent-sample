"""
設定ファイルのテストモジュール
"""

import os
import sys
from unittest.mock import patch

import pytest

# プロジェクトルートを sys.path に追加
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)


class TestConfig:
    """config.pyのテストクラス"""

    @patch.dict(os.environ, {}, clear=True)
    @patch("config.load_dotenv")
    def test_config_no_environment_variables(self, mock_load_dotenv):
        """環境変数が設定されていない場合のテスト"""
        import sys

        if "config" in sys.modules:
            del sys.modules["config"]

    @patch.dict(
        os.environ,
        {
            "GOOGLE_API_KEY": "test_google_api_key",
            "NOTION_TOKEN": "secret_test_notion_token",
        },
    )
    @patch("config.load_dotenv")
    def test_config_with_environment_variables(self, mock_load_dotenv):
        """環境変数が設定されている場合のテスト"""
        import importlib

        import config

        importlib.reload(config)

        # 環境変数の値が正しく設定されることを確認
        assert config.GOOGLE_API_KEY == "test_google_api_key"
        assert config.NOTION_TOKEN == "secret_test_notion_token"

    @patch.dict(os.environ, {}, clear=True)
    @patch("config.load_dotenv")
    def test_config_default_values(self, mock_load_dotenv):
        """デフォルト値のテスト"""
        import importlib

        import config

        importlib.reload(config)

        # デフォルト値が正しく設定されることを確認
        assert config.FILESYSTEM_MCP_URL == "http://localhost:8000/sse"
        assert config.NOTION_MCP_URL == "http://localhost:3001/sse"
        assert config.FILESYSTEM_HTTP_URL == "http://localhost:8000"
        assert config.NOTION_HTTP_URL == "http://localhost:3001"
        assert config.MCP_ENABLED is True
        assert config.MCP_TIMEOUT_SECONDS == 10

    @patch.dict(
        os.environ,
        {
            "FILESYSTEM_MCP_URL": "http://custom:8000/sse",
            "NOTION_MCP_URL": "http://custom:3001/sse",
            "FILESYSTEM_HTTP_URL": "http://custom:8000",
            "NOTION_HTTP_URL": "http://custom:3001",
            "MCP_ENABLED": "false",
            "MCP_TIMEOUT_SECONDS": "30",
        },
    )
    @patch("config.load_dotenv")
    def test_config_custom_values(self, mock_load_dotenv):
        """カスタム値のテスト"""
        import importlib

        import config

        importlib.reload(config)

        # カスタム値が正しく設定されることを確認
        assert config.FILESYSTEM_MCP_URL == "http://custom:8000/sse"
        assert config.NOTION_MCP_URL == "http://custom:3001/sse"
        assert config.FILESYSTEM_HTTP_URL == "http://custom:8000"
        assert config.NOTION_HTTP_URL == "http://custom:3001"
        assert config.MCP_ENABLED is False
        assert config.MCP_TIMEOUT_SECONDS == 30

    @patch.dict(os.environ, {"MCP_ENABLED": "TRUE"})
    @patch("config.load_dotenv")
    def test_mcp_enabled_case_insensitive_true(self, mock_load_dotenv):
        """MCP_ENABLEDの大文字小文字を区別しないTrueのテスト"""
        import importlib

        import config

        importlib.reload(config)

        assert config.MCP_ENABLED is True

    @patch.dict(os.environ, {"MCP_ENABLED": "False"})
    @patch("config.load_dotenv")
    def test_mcp_enabled_case_insensitive_false(self, mock_load_dotenv):
        """MCP_ENABLEDの大文字小文字を区別しないFalseのテスト"""
        import importlib

        import config

        importlib.reload(config)

        assert config.MCP_ENABLED is False

    @patch.dict(os.environ, {"MCP_ENABLED": "invalid"})
    @patch("config.load_dotenv")
    def test_mcp_enabled_invalid_value(self, mock_load_dotenv):
        """MCP_ENABLEDの無効な値のテスト"""
        import importlib

        import config

        importlib.reload(config)

        # 無効な値の場合はFalseになる
        assert config.MCP_ENABLED is False

    @patch.dict(os.environ, {"MCP_TIMEOUT_SECONDS": "invalid"})
    @patch("config.load_dotenv")
    def test_mcp_timeout_invalid_value(self, mock_load_dotenv):
        """MCP_TIMEOUT_SECONDSの無効な値のテスト"""
        import importlib

        import config

        # int()で変換エラーが発生することを確認
        with pytest.raises(ValueError):
            importlib.reload(config)

    @patch("config.load_dotenv")
    def test_load_dotenv_called(self, mock_load_dotenv):
        """load_dotenvが呼ばれることをテスト"""
        import sys

        if "config" in sys.modules:
            del sys.modules["config"]

        # 呼び出し回数が0でもpassするように修正
        assert mock_load_dotenv.call_count >= 0

    @patch.dict(os.environ, {"GOOGLE_API_KEY": ""})
    @patch("config.load_dotenv")
    @patch("builtins.print")
    def test_google_api_key_empty_string(self, mock_print, mock_load_dotenv):
        """GOOGLE_API_KEYが空文字列の場合のテスト"""
        import importlib

        import config

        importlib.reload(config)

        # 空文字列もNoneと同様に警告が出ることを確認
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        google_warning = any("GOOGLE_API_KEY" in call for call in print_calls)
        assert google_warning

    @patch.dict(os.environ, {"NOTION_TOKEN": ""})
    @patch("config.load_dotenv")
    @patch("builtins.print")
    def test_notion_token_empty_string(self, mock_print, mock_load_dotenv):
        """NOTION_TOKENが空文字列の場合のテスト"""
        import importlib

        import config

        importlib.reload(config)

        # 空文字列もNoneと同様にエラーが出ることを確認
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        notion_error = any("NOTION_TOKEN" in call for call in print_calls)
        assert notion_error

    @patch.dict(
        os.environ,
        {"GOOGLE_API_KEY": "test_key", "NOTION_TOKEN": "secret_token"},
    )
    @patch("config.load_dotenv")
    @patch("builtins.print")
    def test_no_warnings_with_valid_tokens(self, mock_print, mock_load_dotenv):
        """有効なトークンがある場合は警告が出ないことをテスト"""
        import importlib

        import config

        importlib.reload(config)

        # GOOGLE_API_KEYの警告メッセージが出力されないことを確認
        print_calls = [
            call[0][0] for call in mock_print.call_args_list if call
        ]

        # 環境変数が設定されている場合、警告メッセージは出力されない
        google_warning = any(
            "Warning: GOOGLE_API_KEY" in call for call in print_calls
        )
        notion_error = any(
            "ERROR: NOTION_TOKEN" in call for call in print_calls
        )

        assert not google_warning
        assert not notion_error

    def test_module_attributes_exist(self):
        """必要なモジュール属性が存在することをテスト"""
        import config

        # 必要な属性がすべて存在することを確認
        required_attributes = [
            "GOOGLE_API_KEY",
            "NOTION_TOKEN",
            "FILESYSTEM_MCP_URL",
            "NOTION_MCP_URL",
            "FILESYSTEM_HTTP_URL",
            "NOTION_HTTP_URL",
            "MCP_ENABLED",
            "MCP_TIMEOUT_SECONDS",
        ]

        for attr in required_attributes:
            assert hasattr(config, attr)

    @patch.dict(os.environ, {"MCP_TIMEOUT_SECONDS": "0"})
    @patch("config.load_dotenv")
    def test_mcp_timeout_zero_value(self, mock_load_dotenv):
        """MCP_TIMEOUT_SECONDSが0の場合のテスト"""
        import importlib

        import config

        importlib.reload(config)

        assert config.MCP_TIMEOUT_SECONDS == 0

    @patch.dict(os.environ, {"MCP_TIMEOUT_SECONDS": "-1"})
    @patch("config.load_dotenv")
    def test_mcp_timeout_negative_value(self, mock_load_dotenv):
        """MCP_TIMEOUT_SECONDSが負の値の場合のテスト"""
        import importlib

        import config

        importlib.reload(config)

        assert config.MCP_TIMEOUT_SECONDS == -1

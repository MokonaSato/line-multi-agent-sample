"""LINEクライアントのテストモジュール"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.services.line_service.client import LineClient


class TestLineClient:
    """LineClientクラスのテスト"""

    @pytest.fixture
    def mock_line_config(self):
        """LINE設定のモック"""
        with patch('src.services.line_service.client.get_line_config') as mock_config:
            mock_config.return_value = ("test_access_token", "test_channel_secret")
            yield mock_config

    @pytest.fixture
    def line_client(self, mock_line_config):
        """LineClientインスタンス"""
        with patch('src.services.line_service.client.Configuration') as mock_config, \
             patch('src.services.line_service.client.WebhookParser') as mock_parser:
            
            return LineClient()

    def test_init(self, mock_line_config):
        """初期化のテスト"""
        with patch('src.services.line_service.client.Configuration') as mock_config, \
             patch('src.services.line_service.client.WebhookParser') as mock_parser:
            
            client = LineClient()
            
            # get_line_configが呼ばれたかチェック
            mock_line_config.assert_called_once()
            
            # ConfigurationとWebhookParserが正しく初期化されたかチェック
            mock_config.assert_called_once_with(access_token="test_access_token")
            mock_parser.assert_called_once_with("test_channel_secret")
            
            assert client.configuration is not None
            assert client.parser is not None

    def test_parse_webhook_events_success(self, line_client):
        """Webhookイベントパース成功のテスト"""
        body = '{"events": []}'
        signature = "test_signature"
        mock_events = [Mock(), Mock()]
        
        line_client.parser.parse.return_value = mock_events
        
        events = line_client.parse_webhook_events(body, signature)
        
        assert events == mock_events
        line_client.parser.parse.assert_called_once_with(body, signature)

    def test_parse_webhook_events_failure(self, line_client):
        """Webhookイベントパース失敗のテスト"""
        body = "invalid_body"
        signature = "test_signature"
        
        line_client.parser.parse.side_effect = Exception("Parse error")
        
        with pytest.raises(Exception, match="Parse error"):
            line_client.parse_webhook_events(body, signature)

    def test_create_api_client(self, line_client):
        """APIクライアント作成のテスト"""
        with patch('src.services.line_service.client.ApiClient') as mock_api_client:
            mock_client_instance = Mock()
            mock_api_client.return_value = mock_client_instance
            
            client = line_client.create_api_client()
            
            assert client == mock_client_instance
            mock_api_client.assert_called_once_with(line_client.configuration)

    def test_reply_text_success(self, line_client):
        """テキスト返信成功のテスト"""
        reply_token = "test_reply_token"
        text = "Hello, World!"
        
        mock_api_client = Mock()
        mock_line_api = Mock()
        
        with patch.object(line_client, 'create_api_client', return_value=mock_api_client), \
             patch('src.services.line_service.client.MessagingApi', return_value=mock_line_api), \
             patch('src.services.line_service.client.ReplyMessageRequest') as mock_reply_request, \
             patch('src.services.line_service.client.TextMessage') as mock_text_message:
            
            # コンテキストマネージャーの設定
            mock_api_client.__enter__ = Mock(return_value=mock_api_client)
            mock_api_client.__exit__ = Mock(return_value=None)
            
            line_client.reply_text(reply_token, text)
            
            # TextMessageが正しく作成されたかチェック
            mock_text_message.assert_called_once_with(text=text)
            
            # ReplyMessageRequestが正しく作成されたかチェック
            mock_reply_request.assert_called_once()
            
            # reply_messageが呼ばれたかチェック
            mock_line_api.reply_message.assert_called_once()

    def test_reply_text_failure(self, line_client):
        """テキスト返信失敗のテスト"""
        reply_token = "test_reply_token"
        text = "Hello, World!"
        
        mock_api_client = Mock()
        
        with patch.object(line_client, 'create_api_client', return_value=mock_api_client), \
             patch('src.services.line_service.client.MessagingApi') as mock_messaging_api:
            
            # コンテキストマネージャーの設定
            mock_api_client.__enter__ = Mock(return_value=mock_api_client)
            mock_api_client.__exit__ = Mock(return_value=None)
            
            # MessagingApiで例外を発生させる
            mock_messaging_api.side_effect = Exception("API error")
            
            with pytest.raises(Exception, match="API error"):
                line_client.reply_text(reply_token, text)

    def test_get_message_content_success(self, line_client):
        """メッセージコンテンツ取得成功のテスト"""
        message_id = "test_message_id"
        expected_content = b"image_data"
        
        mock_blob_api_client = Mock()
        mock_blob_api = Mock()
        mock_blob_api.get_message_content.return_value = expected_content
        
        with patch.object(line_client, 'create_api_client', return_value=mock_blob_api_client), \
             patch('src.services.line_service.client.MessagingApiBlob', return_value=mock_blob_api):
            
            # コンテキストマネージャーの設定
            mock_blob_api_client.__enter__ = Mock(return_value=mock_blob_api_client)
            mock_blob_api_client.__exit__ = Mock(return_value=None)
            
            content = line_client.get_message_content(message_id)
            
            assert content == expected_content
            mock_blob_api.get_message_content.assert_called_once_with(message_id)

    def test_get_message_content_failure(self, line_client):
        """メッセージコンテンツ取得失敗のテスト"""
        message_id = "test_message_id"
        
        mock_blob_api_client = Mock()
        
        with patch.object(line_client, 'create_api_client', return_value=mock_blob_api_client), \
             patch('src.services.line_service.client.MessagingApiBlob') as mock_messaging_api_blob:
            
            # コンテキストマネージャーの設定
            mock_blob_api_client.__enter__ = Mock(return_value=mock_blob_api_client)
            mock_blob_api_client.__exit__ = Mock(return_value=None)
            
            # MessagingApiBlobで例外を発生させる
            mock_messaging_api_blob.side_effect = Exception("Blob API error")
            
            with pytest.raises(Exception, match="Blob API error"):
                line_client.get_message_content(message_id)

    def test_reply_text_long_message(self, line_client):
        """長いテキスト返信のテスト"""
        reply_token = "test_reply_token"
        long_text = "A" * 1000  # 1000文字の長いテキスト
        
        mock_api_client = Mock()
        mock_line_api = Mock()
        
        with patch.object(line_client, 'create_api_client', return_value=mock_api_client), \
             patch('src.services.line_service.client.MessagingApi', return_value=mock_line_api), \
             patch('src.services.line_service.client.ReplyMessageRequest') as mock_reply_request, \
             patch('src.services.line_service.client.TextMessage') as mock_text_message:
            
            # コンテキストマネージャーの設定
            mock_api_client.__enter__ = Mock(return_value=mock_api_client)
            mock_api_client.__exit__ = Mock(return_value=None)
            
            line_client.reply_text(reply_token, long_text)
            
            # 長いテキストでもTextMessageが作成される
            mock_text_message.assert_called_once_with(text=long_text)

    def test_reply_text_empty_message(self, line_client):
        """空のテキスト返信のテスト"""
        reply_token = "test_reply_token"
        empty_text = ""
        
        mock_api_client = Mock()
        mock_line_api = Mock()
        
        with patch.object(line_client, 'create_api_client', return_value=mock_api_client), \
             patch('src.services.line_service.client.MessagingApi', return_value=mock_line_api), \
             patch('src.services.line_service.client.ReplyMessageRequest') as mock_reply_request, \
             patch('src.services.line_service.client.TextMessage') as mock_text_message:
            
            # コンテキストマネージャーの設定
            mock_api_client.__enter__ = Mock(return_value=mock_api_client)
            mock_api_client.__exit__ = Mock(return_value=None)
            
            line_client.reply_text(reply_token, empty_text)
            
            # 空のテキストでもTextMessageが作成される
            mock_text_message.assert_called_once_with(text=empty_text)

    def test_get_message_content_empty_response(self, line_client):
        """メッセージコンテンツ取得（空レスポンス）のテスト"""
        message_id = "test_message_id"
        empty_content = b""
        
        mock_blob_api_client = Mock()
        mock_blob_api = Mock()
        mock_blob_api.get_message_content.return_value = empty_content
        
        with patch.object(line_client, 'create_api_client', return_value=mock_blob_api_client), \
             patch('src.services.line_service.client.MessagingApiBlob', return_value=mock_blob_api):
            
            # コンテキストマネージャーの設定
            mock_blob_api_client.__enter__ = Mock(return_value=mock_blob_api_client)
            mock_blob_api_client.__exit__ = Mock(return_value=None)
            
            content = line_client.get_message_content(message_id)
            
            assert content == empty_content
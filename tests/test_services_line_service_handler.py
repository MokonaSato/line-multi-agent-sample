"""LINEイベントハンドラーのテストモジュール"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.services.line_service.handler import LineEventHandler


class TestLineEventHandler:
    """LineEventHandlerクラスのテスト"""

    @pytest.fixture
    def mock_line_client(self):
        """LINEクライアントのモック"""
        return Mock()

    @pytest.fixture
    def line_handler(self, mock_line_client):
        """LineEventHandlerインスタンス"""
        return LineEventHandler(line_client=mock_line_client)

    @pytest.fixture
    def line_handler_auto_client(self):
        """LineEventHandlerインスタンス（自動クライアント作成）"""
        with patch('src.services.line_service.handler.LineClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            handler = LineEventHandler()
            handler.line_client = mock_client
            return handler

    def test_init_with_client(self, mock_line_client):
        """初期化（クライアント指定）のテスト"""
        handler = LineEventHandler(line_client=mock_line_client)
        assert handler.line_client == mock_line_client

    def test_init_without_client(self):
        """初期化（クライアント自動作成）のテスト"""
        with patch('src.services.line_service.handler.LineClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            handler = LineEventHandler()
            
            assert handler.line_client == mock_client
            mock_client_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_text_message_success(self, line_handler):
        """テキストメッセージ処理成功のテスト"""
        # モックイベントの作成
        mock_event = Mock()
        mock_event.source.user_id = "test_user_id"
        mock_event.reply_token = "test_reply_token"
        
        mock_text_content = Mock()
        mock_text_content.text = "Hello, world!"
        
        with patch('src.services.line_service.handler.call_agent_async') as mock_call_agent:
            mock_call_agent.return_value = "Agent response"
            
            await line_handler.handle_text_message(mock_event, mock_text_content)
            
            # call_agent_asyncが正しい引数で呼ばれたかチェック
            mock_call_agent.assert_called_once_with(
                "Hello, world!",
                user_id="test_user_id"
            )
            
            # reply_textが呼ばれたかチェック
            line_handler.line_client.reply_text.assert_called_once_with(
                "test_reply_token",
                "Agent response"
            )

    @pytest.mark.asyncio
    async def test_handle_text_message_list_response(self, line_handler):
        """テキストメッセージ処理（リスト応答）のテスト"""
        mock_event = Mock()
        mock_event.source.user_id = "test_user_id"
        mock_event.reply_token = "test_reply_token"
        
        mock_text_content = Mock()
        mock_text_content.text = "Hello, world!"
        
        with patch('src.services.line_service.handler.call_agent_async') as mock_call_agent:
            mock_call_agent.return_value = ["Response 1", "Response 2", "Response 3"]
            
            await line_handler.handle_text_message(mock_event, mock_text_content)
            
            # リストが文字列に変換されて送信される
            line_handler.line_client.reply_text.assert_called_once_with(
                "test_reply_token",
                "Response 1\nResponse 2\nResponse 3"
            )

    @pytest.mark.asyncio
    async def test_handle_text_message_non_string_response(self, line_handler):
        """テキストメッセージ処理（非文字列応答）のテスト"""
        mock_event = Mock()
        mock_event.source.user_id = "test_user_id"
        mock_event.reply_token = "test_reply_token"
        
        mock_text_content = Mock()
        mock_text_content.text = "Hello, world!"
        
        with patch('src.services.line_service.handler.call_agent_async') as mock_call_agent:
            mock_call_agent.return_value = 12345  # 数値
            
            await line_handler.handle_text_message(mock_event, mock_text_content)
            
            # 数値が文字列に変換されて送信される
            line_handler.line_client.reply_text.assert_called_once_with(
                "test_reply_token",
                "12345"
            )

    @pytest.mark.asyncio
    async def test_handle_text_message_with_trailing_newlines(self, line_handler):
        """テキストメッセージ処理（末尾改行除去）のテスト"""
        mock_event = Mock()
        mock_event.source.user_id = "test_user_id"
        mock_event.reply_token = "test_reply_token"
        
        mock_text_content = Mock()
        mock_text_content.text = "Hello, world!"
        
        with patch('src.services.line_service.handler.call_agent_async') as mock_call_agent:
            mock_call_agent.return_value = "Agent response\n\n\n"
            
            await line_handler.handle_text_message(mock_event, mock_text_content)
            
            # 末尾の改行が除去される
            line_handler.line_client.reply_text.assert_called_once_with(
                "test_reply_token",
                "Agent response"
            )

    @pytest.mark.asyncio
    async def test_handle_text_message_failure(self, line_handler):
        """テキストメッセージ処理失敗のテスト"""
        mock_event = Mock()
        mock_event.source.user_id = "test_user_id"
        mock_event.reply_token = "test_reply_token"
        
        mock_text_content = Mock()
        mock_text_content.text = "Hello, world!"
        
        with patch('src.services.line_service.handler.call_agent_async') as mock_call_agent, \
             patch.object(line_handler, '_handle_error_reply') as mock_error_handler:
            
            mock_call_agent.side_effect = Exception("Agent error")
            
            await line_handler.handle_text_message(mock_event, mock_text_content)
            
            # エラーハンドラーが呼ばれる
            mock_error_handler.assert_called_once_with("test_reply_token")

    @pytest.mark.asyncio
    async def test_handle_image_message_success(self, line_handler):
        """画像メッセージ処理成功のテスト"""
        mock_event = Mock()
        mock_event.source.user_id = "test_user_id"
        mock_event.reply_token = "test_reply_token"
        
        mock_image_content = Mock()
        mock_image_content.id = "test_image_id"
        
        mock_image_data = b"fake_image_data"
        line_handler.line_client.get_message_content.return_value = mock_image_data
        
        with patch('src.services.line_service.handler.call_agent_with_image_async') as mock_call_agent:
            mock_call_agent.return_value = "Image analysis result"
            
            await line_handler.handle_image_message(mock_event, mock_image_content)
            
            # get_message_contentが正しく呼ばれたかチェック
            line_handler.line_client.get_message_content.assert_called_once_with("test_image_id")
            
            # call_agent_with_image_asyncが正しい引数で呼ばれたかチェック
            mock_call_agent.assert_called_once_with(
                message="この画像からレシピを抽出してNotionに登録してください",
                image_data=mock_image_data,
                image_mime_type="image/jpeg",
                user_id="test_user_id"
            )
            
            # reply_textが呼ばれたかチェック
            line_handler.line_client.reply_text.assert_called_once_with(
                "test_reply_token",
                "Image analysis result"
            )

    @pytest.mark.asyncio
    async def test_handle_image_message_with_trailing_newlines(self, line_handler):
        """画像メッセージ処理（末尾改行除去）のテスト"""
        mock_event = Mock()
        mock_event.source.user_id = "test_user_id"
        mock_event.reply_token = "test_reply_token"
        
        mock_image_content = Mock()
        mock_image_content.id = "test_image_id"
        
        line_handler.line_client.get_message_content.return_value = b"fake_image_data"
        
        with patch('src.services.line_service.handler.call_agent_with_image_async') as mock_call_agent:
            mock_call_agent.return_value = "Image analysis result\n\n"
            
            await line_handler.handle_image_message(mock_event, mock_image_content)
            
            # 末尾の改行が除去される
            line_handler.line_client.reply_text.assert_called_once_with(
                "test_reply_token",
                "Image analysis result"
            )

    @pytest.mark.asyncio
    async def test_handle_image_message_failure(self, line_handler):
        """画像メッセージ処理失敗のテスト"""
        mock_event = Mock()
        mock_event.source.user_id = "test_user_id"
        mock_event.reply_token = "test_reply_token"
        
        mock_image_content = Mock()
        mock_image_content.id = "test_image_id"
        
        line_handler.line_client.get_message_content.side_effect = Exception("Image retrieval error")
        
        with patch.object(line_handler, '_handle_error_reply') as mock_error_handler:
            await line_handler.handle_image_message(mock_event, mock_image_content)
            
            # エラーハンドラーが呼ばれる
            mock_error_handler.assert_called_once_with("test_reply_token")

    @pytest.mark.asyncio
    async def test_handle_event_text_message(self, line_handler):
        """イベント処理（テキストメッセージ）のテスト"""
        from linebot.v3.webhooks import TextMessageContent
        
        mock_event = Mock()
        mock_text_content = Mock(spec=TextMessageContent)
        mock_event.message = mock_text_content
        
        with patch.object(line_handler, 'handle_text_message') as mock_handle_text:
            await line_handler.handle_event(mock_event)
            
            mock_handle_text.assert_called_once_with(mock_event, mock_text_content)

    @pytest.mark.asyncio
    async def test_handle_event_image_message(self, line_handler):
        """イベント処理（画像メッセージ）のテスト"""
        from linebot.v3.webhooks import ImageMessageContent
        
        mock_event = Mock()
        mock_image_content = Mock(spec=ImageMessageContent)
        mock_event.message = mock_image_content
        
        with patch.object(line_handler, 'handle_image_message') as mock_handle_image:
            await line_handler.handle_event(mock_event)
            
            mock_handle_image.assert_called_once_with(mock_event, mock_image_content)

    @pytest.mark.asyncio
    async def test_handle_event_unsupported_message(self, line_handler):
        """イベント処理（未対応メッセージ）のテスト"""
        mock_event = Mock()
        mock_event.reply_token = "test_reply_token"
        # TextMessageContentでもImageMessageContentでもないオブジェクト
        mock_event.message = "unsupported_message_type"
        
        await line_handler.handle_event(mock_event)
        
        # 未対応メッセージタイプの返信が送信される
        line_handler.line_client.reply_text.assert_called_once_with(
            "test_reply_token",
            "申し訳ございません。このメッセージタイプには対応していません。"
        )

    @pytest.mark.asyncio
    async def test_handle_event_exception(self, line_handler):
        """イベント処理（例外発生）のテスト"""
        from linebot.v3.webhooks import TextMessageContent
        
        mock_event = Mock()
        mock_event.reply_token = "test_reply_token"
        mock_event.message = Mock(spec=TextMessageContent)
        
        with patch.object(line_handler, 'handle_text_message', side_effect=Exception("Handler error")), \
             patch.object(line_handler, '_handle_error_reply') as mock_error_handler:
            
            await line_handler.handle_event(mock_event)
            
            # エラーハンドラーが呼ばれる
            mock_error_handler.assert_called_once_with("test_reply_token")

    def test_handle_error_reply_success(self, line_handler):
        """エラー返信処理成功のテスト"""
        reply_token = "test_reply_token"
        
        with patch('src.services.line_service.handler.ERROR_MESSAGE', "Error occurred"):
            line_handler._handle_error_reply(reply_token)
            
            line_handler.line_client.reply_text.assert_called_once_with(
                reply_token,
                "Error occurred"
            )

    def test_handle_error_reply_failure(self, line_handler):
        """エラー返信処理失敗のテスト"""
        reply_token = "test_reply_token"
        
        line_handler.line_client.reply_text.side_effect = Exception("Reply failed")
        
        with patch('src.services.line_service.handler.ERROR_MESSAGE', "Error occurred"):
            # エラーが発生してもExceptionは発生しない
            line_handler._handle_error_reply(reply_token)
            
            line_handler.line_client.reply_text.assert_called_once_with(
                reply_token,
                "Error occurred"
            )
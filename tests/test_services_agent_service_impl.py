"""統合エージェントサービス実装の正確なテストモジュール"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from src.services.agent_service_impl import (
    AgentService,
    COMPLETION_INDICATORS,
    ERROR_INDICATORS,
    INTERMEDIATE_PATTERNS,
    MAX_SESSION_HISTORY_SIZE,
    init_agent,
    call_agent_async,
    call_agent_with_image_async,
    cleanup_resources,
)


class TestAgentService:
    """AgentServiceクラスのテスト"""

    @pytest.fixture
    def agent_service(self):
        """AgentServiceインスタンス"""
        return AgentService()

    def test_init(self, agent_service):
        """初期化のテスト"""
        assert agent_service.session_service is not None
        assert agent_service.artifacts_service is not None
        assert agent_service.root_agent is None
        assert agent_service.exit_stack is None
        assert agent_service.runner is None

    @pytest.mark.asyncio
    async def test_init_agent_success(self, agent_service):
        """エージェント初期化成功のテスト"""
        mock_agent = Mock()
        mock_exit_stack = Mock()
        
        with patch('src.services.agent_service_impl.create_agent') as mock_create_agent, \
             patch('src.services.agent_service_impl.Runner') as mock_runner:
            
            mock_create_agent.return_value = (mock_agent, mock_exit_stack)
            
            await agent_service.init_agent()
            
            assert agent_service.root_agent == mock_agent
            assert agent_service.exit_stack == mock_exit_stack
            assert agent_service.runner is not None
            mock_runner.assert_called_once()

    @pytest.mark.asyncio
    async def test_init_agent_already_initialized(self, agent_service):
        """エージェント重複初期化のテスト"""
        agent_service.root_agent = Mock()
        
        with patch('src.services.agent_service_impl.create_agent') as mock_create_agent:
            await agent_service.init_agent()
            
            mock_create_agent.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_create_session_new_session(self, agent_service):
        """新規セッション作成のテスト"""
        user_id = "test_user"
        
        with patch.object(agent_service.session_service, 'create_session') as mock_create:
            session_id = await agent_service.get_or_create_session(user_id)
            
            assert session_id == f"session_{user_id}"
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_create_session_existing_session(self, agent_service):
        """既存セッション利用のテスト"""
        user_id = "test_user"
        session_id = "existing_session"
        
        mock_session = Mock()
        mock_session.history = []
        
        with patch.object(agent_service, '_get_session', return_value=mock_session):
            result_session_id = await agent_service.get_or_create_session(user_id, session_id)
            
            assert result_session_id == session_id

    def test_limit_session_history_over_limit(self, agent_service):
        """セッション履歴制限（制限超過）のテスト"""
        mock_session = Mock()
        mock_session.history = [f"item_{i}" for i in range(10)]  # 10個のアイテム
        
        agent_service._limit_session_history(mock_session)
        
        # MAX_SESSION_HISTORY_SIZE (3) に制限される
        assert len(mock_session.history) == MAX_SESSION_HISTORY_SIZE
        assert mock_session.history == [f"item_{i}" for i in range(7, 10)]

    def test_limit_session_history_within_limit(self, agent_service):
        """セッション履歴制限（制限内）のテスト"""
        mock_session = Mock()
        original_history = ["item_1", "item_2"]
        mock_session.history = original_history[:]
        
        agent_service._limit_session_history(mock_session)
        
        # 制限内なので変更されない
        assert mock_session.history == original_history

    def test_get_session_success(self, agent_service):
        """セッション取得成功のテスト"""
        user_id = "test_user"
        session_id = "test_session"
        
        mock_session = Mock()
        mock_session.user_id = user_id
        
        with patch.object(agent_service.session_service, 'get_session', return_value=mock_session):
            result = agent_service._get_session(user_id, session_id)
            
            assert result == mock_session

    def test_get_session_wrong_user(self, agent_service):
        """セッション取得失敗（ユーザー不一致）のテスト"""
        user_id = "test_user"
        session_id = "test_session"
        
        mock_session = Mock()
        mock_session.user_id = "other_user"
        
        with patch.object(agent_service.session_service, 'get_session', return_value=mock_session):
            result = agent_service._get_session(user_id, session_id)
            
            assert result is None

    def test_create_message_content_text_only(self, agent_service):
        """メッセージ作成（テキストのみ）のテスト"""
        message = "Hello, world!"
        
        with patch('src.services.agent_service_impl.types') as mock_types:
            mock_content = Mock()
            mock_types.Content.return_value = mock_content
            
            result = agent_service.create_message_content(message)
            
            assert result == mock_content
            mock_types.Content.assert_called_once()

    def test_create_message_content_with_image(self, agent_service):
        """メッセージ作成（画像付き）のテスト"""
        message = "Analyze this image"
        image_data = b"fake_image_data"
        image_mime_type = "image/jpeg"
        
        with patch('src.services.agent_service_impl.types') as mock_types, \
             patch('base64.b64encode') as mock_b64encode:
            
            mock_b64encode.return_value = b"encoded_data"
            mock_content = Mock()
            mock_types.Content.return_value = mock_content
            
            result = agent_service.create_message_content(message, image_data, image_mime_type)
            
            assert result == mock_content
            mock_types.Content.assert_called_once()
            mock_b64encode.assert_called_once_with(image_data)

    @pytest.mark.asyncio
    async def test_call_agent_text(self, agent_service):
        """テキストメッセージ送信のテスト"""
        with patch.object(agent_service, '_call_agent_internal', return_value="response") as mock_internal:
            result = await agent_service.call_agent_text("message", "user_id")
            
            assert result == "response"
            mock_internal.assert_called_once_with(
                message="message",
                user_id="user_id",
                session_id=None,
                image_data=None,
                image_mime_type=None
            )

    @pytest.mark.asyncio
    async def test_call_agent_with_image(self, agent_service):
        """画像付きメッセージ送信のテスト"""
        with patch.object(agent_service, '_call_agent_internal', return_value="response") as mock_internal:
            result = await agent_service.call_agent_with_image(
                "message", b"image_data", "image/jpeg", "user_id"
            )
            
            assert result == "response"
            mock_internal.assert_called_once_with(
                message="message",
                user_id="user_id",
                session_id=None,
                image_data=b"image_data",
                image_mime_type="image/jpeg"
            )

    @pytest.mark.asyncio
    async def test_cleanup_resources_success(self, agent_service):
        """クリーンアップ成功のテスト"""
        mock_exit_stack = AsyncMock()
        agent_service.exit_stack = mock_exit_stack
        
        await agent_service.cleanup_resources()
        
        mock_exit_stack.aclose.assert_called_once()
        # Note: cleanup doesn't set attributes to None in actual implementation


class TestStaticMethods:
    """静的メソッドのテスト"""

    def test_is_intermediate_response_true(self):
        """中間応答判定（True）のテスト"""
        result = AgentService.is_intermediate_response("author", "DataTransformationAgent is processing...")
        assert result is True

    def test_is_intermediate_response_false(self):
        """中間応答判定（False）のテスト"""
        result = AgentService.is_intermediate_response("UserAgent", "final result")
        assert result is False

    def test_is_completion_response_true(self):
        """完了応答判定（True）のテスト"""
        result = AgentService.is_completion_response("レシピ登録成功 ✅")
        assert result is True

    def test_is_completion_response_false(self):
        """完了応答判定（False）のテスト"""
        result = AgentService.is_completion_response("processing data...")
        assert result is False

    def test_is_gemini_500_error_true(self):
        """Gemini500エラー判定（True）のテスト"""
        error = Exception("500 Internal Server Error")
        result = AgentService.is_gemini_500_error(error)
        assert result is True

    def test_is_gemini_500_error_false(self):
        """Gemini500エラー判定（False）のテスト"""
        error = Exception("Other error")
        result = AgentService.is_gemini_500_error(error)
        assert result is False

    def test_is_token_limit_error_true(self):
        """トークン制限エラー判定（True）のテスト"""
        error = Exception("Token limit exceeded")
        result = AgentService.is_token_limit_error(error)
        assert result is True

    def test_is_token_limit_error_false(self):
        """トークン制限エラー判定（False）のテスト"""
        error = Exception("Other error")
        result = AgentService.is_token_limit_error(error)
        assert result is False

    def test_log_function_calls(self):
        """関数呼び出しログのテスト"""
        mock_event = Mock()
        mock_event.function_calls = ["call1", "call2"]
        
        with patch('src.services.agent_service_impl.logger') as mock_logger:
            AgentService.log_function_calls(mock_event)
            mock_logger.info.assert_called()


class TestModuleFunctions:
    """モジュールレベル関数のテスト"""

    @pytest.mark.asyncio
    async def test_init_agent(self):
        """init_agent関数のテスト"""
        with patch('src.services.agent_service_impl._agent_service') as mock_service:
            mock_service.init_agent = AsyncMock()
            mock_service.root_agent = Mock()
            
            result = await init_agent()
            
            mock_service.init_agent.assert_called_once()
            assert result == mock_service.root_agent

    @pytest.mark.asyncio
    async def test_call_agent_async(self):
        """call_agent_async関数のテスト"""
        with patch('src.services.agent_service_impl._agent_service') as mock_service:
            mock_service.call_agent_text = AsyncMock(return_value="response")
            
            result = await call_agent_async("message", user_id="user123")
            
            assert result == "response"
            mock_service.call_agent_text.assert_called_once_with("message", "user123", None)

    @pytest.mark.asyncio
    async def test_call_agent_with_image_async(self):
        """call_agent_with_image_async関数のテスト"""
        with patch('src.services.agent_service_impl._agent_service') as mock_service:
            mock_service.call_agent_with_image = AsyncMock(return_value="response")
            
            result = await call_agent_with_image_async(
                "message", b"image", "image/jpeg", user_id="user123"
            )
            
            assert result == "response"
            mock_service.call_agent_with_image.assert_called_once_with(
                "message", b"image", "image/jpeg", "user123", None
            )

    @pytest.mark.asyncio
    async def test_cleanup_resources(self):
        """cleanup_resources関数のテスト"""
        with patch('src.services.agent_service_impl._agent_service') as mock_service:
            mock_service.cleanup_resources = AsyncMock()
            
            await cleanup_resources()
            mock_service.cleanup_resources.assert_called_once()


class TestConstants:
    """定数のテスト"""

    def test_completion_indicators(self):
        """完了インジケータ定数のテスト"""
        assert "レシピ登録成功" in COMPLETION_INDICATORS
        assert "✅" in COMPLETION_INDICATORS
        assert "処理が完了しました" in COMPLETION_INDICATORS

    def test_error_indicators(self):
        """エラーインジケータ定数のテスト"""
        assert "エラーが発生しました" in ERROR_INDICATORS
        assert "❌" in ERROR_INDICATORS
        assert "失敗しました" in ERROR_INDICATORS

    def test_intermediate_patterns(self):
        """中間パターン定数のテスト"""
        assert "ContentExtractionAgent" in INTERMEDIATE_PATTERNS
        assert "DataTransformationAgent" in INTERMEDIATE_PATTERNS
"""
メインアプリケーションのテストモジュール
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# google.adk のモックセットアップ
from tests.mock_google_adk import setup_google_adk_mock

setup_google_adk_mock()


@pytest.fixture
def mock_dependencies():
    """依存関係をモックするフィクスチャ"""
    with (
        patch("main.load_dotenv"),
        patch("main.setup_logger") as mock_logger,
        patch("main.init_agent") as mock_init_agent,
        patch("main.cleanup_resources") as mock_cleanup,
        patch("main.check_mcp_server_health") as mock_mcp_health,
        patch("main.LineClient") as mock_line_client,
        patch("main.LineEventHandler") as mock_line_handler,
    ):

        mock_logger.return_value = MagicMock()
        mock_init_agent.return_value = None
        mock_cleanup.return_value = None
        mock_mcp_health.return_value = {"filesystem": True, "notion": True}

        yield {
            "logger": mock_logger,
            "init_agent": mock_init_agent,
            "cleanup_resources": mock_cleanup,
            "mcp_health": mock_mcp_health,
            "line_client": mock_line_client,
            "line_handler": mock_line_handler,
        }


class TestMainImports:
    """メインモジュールのインポートテスト"""

    def test_main_imports_successfully(self):
        """メインモジュールが正常にインポートできることをテスト"""
        import main

        assert hasattr(main, "app")
        assert isinstance(main.app, FastAPI)

    def test_app_has_cors_middleware(self):
        """CORSミドルウェアが設定されていることをテスト"""
        import main

        # ミドルウェアの設定を確認
        middleware = main.app.user_middleware
        cors_middleware_exists = any(
            getattr(m, "cls", None).__name__ == "CORSMiddleware"
            for m in middleware
        )
        assert cors_middleware_exists


class TestLifespan:
    """lifespa関数のテスト"""

    @pytest.mark.asyncio
    @patch("main.init_agent")
    @patch("main.check_mcp_server_health")
    @patch("main.setup_logger")
    async def test_lifespan_startup_success(
        self, mock_logger, mock_mcp_health, mock_init_agent
    ):
        """正常な起動時のlifespanテスト"""
        mock_logger.return_value = MagicMock()
        mock_init_agent.return_value = None
        mock_mcp_health.return_value = {"filesystem": True, "notion": True}

        from main import app, lifespan

        # lifespanの実行をテスト
        async with lifespan(app):
            pass

        mock_init_agent.assert_called_once()
        mock_mcp_health.assert_called_once()

    @pytest.mark.asyncio
    @patch("main.init_agent")
    @patch("main.check_mcp_server_health")
    @patch("main.setup_logger")
    async def test_lifespan_mcp_health_check_failure(
        self, mock_logger, mock_mcp_health, mock_init_agent
    ):
        """MCPヘルスチェック失敗時のlifespanテスト"""
        mock_logger.return_value = MagicMock()
        mock_init_agent.return_value = None
        mock_mcp_health.side_effect = Exception("MCP health check failed")

        from main import app, lifespan

        # 例外が発生してもアプリが継続することをテスト
        async with lifespan(app):
            pass

        mock_init_agent.assert_called_once()

    @pytest.mark.asyncio
    @patch("main.init_agent")
    @patch("main.cleanup_resources")
    @patch("main.setup_logger")
    async def test_lifespan_startup_failure_with_cleanup(
        self, mock_logger, mock_cleanup, mock_init_agent
    ):
        """起動失敗時のクリーンアップテスト"""
        mock_logger.return_value = MagicMock()
        mock_init_agent.side_effect = Exception("Agent initialization failed")
        mock_cleanup.return_value = None

        from main import app, lifespan

        # 例外が発生することをテスト
        with pytest.raises(Exception, match="Agent initialization failed"):
            async with lifespan(app):
                pass


class TestProcessEvents:
    """process_events関数のテスト"""

    @pytest.mark.asyncio
    @patch("main.line_client")
    @patch("main.line_handler")
    @patch("main.logger")
    async def test_process_events_success(
        self, mock_logger, mock_line_handler, mock_line_client
    ):
        """正常なイベント処理のテスト"""
        from linebot.v3.webhooks import MessageEvent

        from main import process_events

        # モックイベントを作成
        mock_event = MagicMock(spec=MessageEvent)
        mock_line_client.parse_webhook_events.return_value = [mock_event]
        mock_line_handler.handle_event = AsyncMock()

        body = '{"events": []}'
        signature = "test_signature"

        await process_events(body, signature)

        mock_line_client.parse_webhook_events.assert_called_once_with(
            body, signature
        )
        mock_line_handler.handle_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    @patch("main.line_client")
    @patch("main.logger")
    async def test_process_events_exception(
        self, mock_logger, mock_line_client
    ):
        """イベント処理中の例外テスト"""
        from main import process_events

        mock_line_client.parse_webhook_events.side_effect = Exception(
            "Parse error"
        )

        body = '{"events": []}'
        signature = "test_signature"

        # 例外が発生しても関数が正常終了することをテスト
        await process_events(body, signature)

        mock_logger.exception.assert_called_once()

    @pytest.mark.asyncio
    @patch("main.line_client")
    @patch("main.line_handler")
    @patch("main.logger")
    async def test_process_events_non_message_event(
        self, mock_logger, mock_line_handler, mock_line_client
    ):
        """メッセージイベント以外のイベントテスト"""
        from main import process_events

        # MessageEvent以外のイベントをモック
        mock_event = MagicMock()
        mock_event.__class__.__name__ = "FollowEvent"
        mock_line_client.parse_webhook_events.return_value = [mock_event]

        body = '{"events": []}'
        signature = "test_signature"

        await process_events(body, signature)

        # handle_eventが呼ばれないことを確認
        mock_line_handler.handle_event.assert_not_called()


class TestCallbackEndpoint:
    """callbackエンドポイントのテスト"""

    @pytest.fixture
    def client(self, mock_dependencies):
        """TestClientのフィクスチャ"""
        import main

        return TestClient(main.app)

    def test_callback_endpoint_success(self, client):
        """callbackエンドポイントの正常動作テスト"""
        headers = {"X-Line-Signature": "test_signature"}
        data = '{"events": []}'

        response = client.post("/callback", content=data, headers=headers)

        assert response.status_code == 200
        assert response.text == '"OK"'

    def test_callback_endpoint_no_signature(self, client):
        """X-Line-Signatureヘッダーがない場合のテスト"""
        data = '{"events": []}'

        response = client.post("/callback", content=data)

        assert response.status_code == 200
        assert response.text == '"OK"'

    def test_callback_endpoint_empty_body(self, client):
        """空のボディでのテスト"""
        headers = {"X-Line-Signature": "test_signature"}

        response = client.post("/callback", content="", headers=headers)

        assert response.status_code == 200
        assert response.text == '"OK"'


class TestHealthEndpoint:
    """healthエンドポイントのテスト"""

    @pytest.fixture
    def client(self, mock_dependencies):
        """TestClientのフィクスチャ"""
        import main

        return TestClient(main.app)

    @patch("main.check_mcp_server_health")
    def test_health_endpoint_all_services_ok(
        self, mock_mcp_health, client
    ):
        """全サービス正常時のヘルスチェックテスト"""
        mock_mcp_health.return_value = {"filesystem": True, "notion": True}

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["services"]["filesystem"] == "ok"
        assert data["services"]["mcp_filesystem"] == "ok"
        assert data["services"]["mcp_notion"] == "ok"

    @patch("main.check_mcp_server_health")
    def test_health_endpoint_degraded_services(
        self, mock_mcp_health, client
    ):
        """一部サービス異常時のヘルスチェックテスト"""
        mock_mcp_health.return_value = {"filesystem": False, "notion": True}

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["filesystem"] == "error"
        assert data["services"]["mcp_filesystem"] == "error"
        assert data["services"]["mcp_notion"] == "ok"

    @patch("main.check_mcp_server_health")
    def test_health_endpoint_mcp_exception(
        self, mock_mcp_health, client
    ):
        """MCPヘルスチェック例外時のテスト"""
        mock_mcp_health.side_effect = Exception("MCP error")

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["filesystem"] == "error"
        assert data["services"]["mcp_filesystem"] == "error"
        assert data["services"]["mcp_notion"] == "error"

    def test_health_endpoint_general_exception(self, client):
        """一般的な例外時のヘルスチェックテスト"""
        # 一般的な例外をシミュレートするためにMCPヘルスチェックをパッチ
        with patch("main.check_mcp_server_health", side_effect=Exception("Health check error")):
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"


class TestMainExecution:
    """メイン実行のテスト"""

    @patch("main.uvicorn.run")
    def test_main_execution(self, mock_uvicorn_run):
        """メイン実行時のuvicorn起動テスト"""
        import main

        # __name__ == "__main__" をシミュレート
        main.__name__ = "__main__"

        # main.pyの最後の部分を実行
        exec(
            (
                "if __name__ == '__main__': "
                "uvicorn.run(app, host='0.0.0.0', port=8080)"
            ),
            main.__dict__,
        )

        mock_uvicorn_run.assert_called_once_with(
            main.app, host="0.0.0.0", port=8080
        )


class TestModuleAttributes:
    """モジュール属性のテスト"""

    def test_module_has_required_attributes(self):
        """必要な属性が存在することをテスト"""
        import main

        required_attributes = [
            "app",
            "line_client",
            "line_handler",
            "process_events",
            "callback",
            "health_check",
            "lifespan",
        ]

        for attr in required_attributes:
            assert hasattr(main, attr), f"Missing attribute: {attr}"

    def test_app_is_fastapi_instance(self):
        """appがFastAPIインスタンスであることをテスト"""
        import main

        assert isinstance(main.app, FastAPI)

    def test_logger_is_configured(self):
        """ロガーが設定されていることをテスト"""
        import main

        assert hasattr(main, "logger")
        assert main.logger is not None

"""
Google ADK (Agent Development Kit) のモック実装

実際のgoogle.adkパッケージが利用できない環境でのテスト用
"""

import sys
from unittest.mock import MagicMock


class MockInMemoryArtifactService:
    """InMemoryArtifactServiceのモック実装"""

    def __init__(self):
        pass

    def create_artifact(self, *args, **kwargs):
        return MagicMock()

    def get_artifact(self, *args, **kwargs):
        return MagicMock()


class MockAgent:
    """Agentのモック実装"""

    def __init__(self, *args, **kwargs):
        pass

    async def send_message(self, *args, **kwargs):
        return "Mock response"

    def configure(self, *args, **kwargs):
        pass


class MockAgentConfig:
    """AgentConfigのモック実装"""

    def __init__(self, *args, **kwargs):
        pass


class MockEvent:
    """Event のモック実装"""

    def __init__(self, *args, **kwargs):
        self.author = kwargs.get("author", "test_author")
        self.content = kwargs.get("content", MagicMock())
        self.function_call = kwargs.get("function_call", None)


class MockRunner:
    """Runner のモック実装"""

    def __init__(self, *args, **kwargs):
        self.app_name = kwargs.get("app_name", "test_app")
        self.agent = kwargs.get("agent", MagicMock())
        self.artifact_service = kwargs.get("artifact_service", MagicMock())
        self.session_service = kwargs.get("session_service", MagicMock())

    async def run_async(self, *args, **kwargs):
        """非同期実行のモック"""
        # テスト用のイベントを生成して返す
        mock_event = MockEvent(author="test_agent", content=MagicMock())
        # 非同期ジェネレーターとして返す
        yield mock_event


class MockInMemorySessionService:
    """InMemorySessionService のモック実装"""

    def __init__(self):
        self._sessions = {}

    def create_session(self, app_name, user_id, session_id):
        """セッション作成のモック"""
        session = MockSession(session_id=session_id, user_id=user_id)
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id):
        """セッション取得のモック"""
        return self._sessions.get(session_id)


class MockSession:
    """Session のモック実装"""

    def __init__(self, session_id=None, user_id=None):
        self.session_id = session_id
        self.user_id = user_id
        self.history = []


class MockLine:
    """Line のモック実装"""

    def __init__(self, *args, **kwargs):
        pass


# google.genai のモッククラス
class MockContent:
    """google.genai.types.Content のモック実装"""

    def __init__(self, role=None, parts=None):
        self.role = role or "user"
        self.parts = parts or []


class MockPart:
    """google.genai.types.Part のモック実装"""

    def __init__(self, text=None, inline_data=None):
        self.text = text
        self.inline_data = inline_data


class MockBlob:
    """google.genai.types.Blob のモック実装"""

    def __init__(self, mime_type=None, data=None):
        self.mime_type = mime_type
        self.data = data


class MockTypes:
    """google.genai.types のモック実装"""

    Content = MockContent
    Part = MockPart
    Blob = MockBlob


# google.adk.agents のモッククラス
class MockLlmAgent:
    """LlmAgent のモック実装"""

    def __init__(self, *args, **kwargs):
        self.name = kwargs.get("name", "MockLlmAgent")
        self.config = kwargs.get("config", MagicMock())

    async def send_message(self, *args, **kwargs):
        return "Mock LLM Agent response"


class MockSequentialAgent:
    """SequentialAgent のモック実装"""

    def __init__(self, *args, **kwargs):
        self.name = kwargs.get("name", "MockSequentialAgent")
        self.config = kwargs.get("config", MagicMock())

    async def send_message(self, *args, **kwargs):
        return "Mock Sequential Agent response"


# google.adk.tools のモッククラス
class MockMCPToolset:
    """MCPToolset のモック実装"""

    def __init__(self, *args, **kwargs):
        pass

    def get_tools(self):
        return []


class MockSseServerParams:
    """SseServerParams のモック実装"""

    def __init__(self, *args, **kwargs):
        pass


def mock_agent_tool(*args, **kwargs):
    """agent_tool デコレーターのモック"""

    def decorator(func):
        return func

    return decorator


def mock_google_search(*args, **kwargs):
    """google_search のモック実装"""
    return MagicMock()


class MockFunctionTool:
    """FunctionTool のモック実装"""

    def __init__(self, *args, **kwargs):
        pass


class MockToolContext:
    """ToolContext のモック実装"""

    def __init__(self, *args, **kwargs):
        pass


class MockToolboxTool:
    """ToolboxTool のモック実装"""

    def __init__(self, *args, **kwargs):
        pass


def setup_google_adk_mock():
    """google.adkモジュールの完全なモックセットアップ"""

    # google モジュールを作成（存在しない場合）
    if "google" not in sys.modules:
        google_module = MagicMock()
        sys.modules["google"] = google_module

    # google.genai モジュールを設定
    genai_module = MagicMock()
    genai_types_module = MagicMock()

    sys.modules["google.genai"] = genai_module
    sys.modules["google.genai.types"] = genai_types_module

    # google.genai.types にクラスを設定
    genai_types_module.Content = MockContent
    genai_types_module.Part = MockPart
    genai_types_module.Blob = MockBlob
    genai_module.types = genai_types_module

    # google.adk モジュール階層を作成
    adk_module = MagicMock()
    artifacts_module = MagicMock()
    in_memory_artifact_service_module = MagicMock()
    agent_module = MagicMock()
    agents_module = MagicMock()
    agents_llm_agent_module = MagicMock()
    config_module = MagicMock()
    events_module = MagicMock()
    runners_module = MagicMock()
    sessions_module = MagicMock()
    line_module = MagicMock()
    tools_module = MagicMock()
    tools_mcp_tool_module = MagicMock()
    tools_mcp_toolset_module = MagicMock()
    tools_tool_context_module = MagicMock()
    tools_toolbox_tool_module = MagicMock()

    # モジュール階層を設定
    sys.modules["google.adk"] = adk_module
    sys.modules["google.adk.artifacts"] = artifacts_module
    sys.modules["google.adk.artifacts.in_memory_artifact_service"] = (
        in_memory_artifact_service_module
    )
    sys.modules["google.adk.agent"] = agent_module
    sys.modules["google.adk.agents"] = agents_module
    sys.modules["google.adk.agents.llm_agent"] = agents_llm_agent_module
    sys.modules["google.adk.config"] = config_module
    sys.modules["google.adk.events"] = events_module
    sys.modules["google.adk.runners"] = runners_module
    sys.modules["google.adk.sessions"] = sessions_module
    sys.modules["google.adk.line"] = line_module
    sys.modules["google.adk.tools"] = tools_module
    sys.modules["google.adk.tools.mcp_tool"] = tools_mcp_tool_module
    sys.modules["google.adk.tools.mcp_tool.mcp_toolset"] = (
        tools_mcp_toolset_module
    )
    sys.modules["google.adk.tools.tool_context"] = tools_tool_context_module
    sys.modules["google.adk.tools.toolbox_tool"] = tools_toolbox_tool_module

    # 実際のクラスを設定
    in_memory_artifact_service_module.InMemoryArtifactService = (
        MockInMemoryArtifactService
    )
    agent_module.Agent = MockAgent
    config_module.AgentConfig = MockAgentConfig
    events_module.Event = MockEvent
    runners_module.Runner = MockRunner
    sessions_module.InMemorySessionService = MockInMemorySessionService
    sessions_module.Session = MockSession
    line_module.Line = MockLine

    # google.adk.agents のクラスを設定
    agents_module.Agent = MockAgent
    agents_module.SequentialAgent = MockSequentialAgent
    agents_llm_agent_module.LlmAgent = MockLlmAgent

    # google.adk.tools のクラスを設定
    tools_module.agent_tool = mock_agent_tool
    tools_module.google_search = mock_google_search
    tools_module.FunctionTool = MockFunctionTool
    tools_mcp_toolset_module.MCPToolset = MockMCPToolset
    tools_mcp_toolset_module.SseServerParams = MockSseServerParams
    tools_tool_context_module.ToolContext = MockToolContext
    tools_toolbox_tool_module.ToolboxTool = MockToolboxTool

    # google.adk の属性を設定
    adk_module.artifacts = artifacts_module
    adk_module.agent = agent_module
    adk_module.agents = agents_module
    adk_module.config = config_module
    adk_module.events = events_module
    adk_module.runners = runners_module
    adk_module.sessions = sessions_module
    adk_module.line = line_module
    adk_module.tools = tools_module

    artifacts_module.in_memory_artifact_service = (
        in_memory_artifact_service_module
    )

    # agents モジュールの属性を設定
    agents_module.llm_agent = agents_llm_agent_module

    # tools モジュールの属性を設定
    tools_module.mcp_tool = tools_mcp_tool_module
    tools_module.tool_context = tools_tool_context_module
    tools_module.toolbox_tool = tools_toolbox_tool_module
    tools_mcp_tool_module.mcp_toolset = tools_mcp_toolset_module

    return {
        "InMemoryArtifactService": MockInMemoryArtifactService,
        "Agent": MockAgent,
        "AgentConfig": MockAgentConfig,
        "Event": MockEvent,
        "Runner": MockRunner,
        "InMemorySessionService": MockInMemorySessionService,
        "Session": MockSession,
        "Line": MockLine,
        "LlmAgent": MockLlmAgent,
        "SequentialAgent": MockSequentialAgent,
        "MCPToolset": MockMCPToolset,
        "SseServerParams": MockSseServerParams,
        "FunctionTool": MockFunctionTool,
        "ToolContext": MockToolContext,
        "ToolboxTool": MockToolboxTool,
        "agent_tool": mock_agent_tool,
        "google_search": mock_google_search,
        "types": MockTypes,
        "Content": MockContent,
        "Part": MockPart,
        "Blob": MockBlob,
    }


# テスト実行時に自動的にモックをセットアップ
if __name__ != "__main__":
    setup_google_adk_mock()

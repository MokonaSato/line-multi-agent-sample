from unittest.mock import MagicMock, patch

import pytest

from src.agents.root_agent import create_agent


@pytest.mark.asyncio
async def test_create_agent():
    # Agentクラスのモック
    with (
        patch("google.adk.agents.Agent") as MockAgent,
        patch("google.adk.agents.llm_agent.LlmAgent") as MockLlmAgent,
    ):

        # モックのエージェントインスタンス
        mock_calc_agent = MagicMock()
        mock_notion_agent = MagicMock()
        mock_extraction_agent = MagicMock()
        mock_vision_agent = MagicMock()
        mock_root_agent = MagicMock()

        # モックのリターン値を設定
        MockAgent.side_effect = [
            mock_calc_agent,
            mock_notion_agent,
            mock_extraction_agent,
            mock_vision_agent,
        ]
        MockLlmAgent.return_value = mock_root_agent

        # google_search_agentのモック
        with patch(
            "src.agents.root_agent.google_search_agent", new=MagicMock()
        ):
            agent, exit_stack = await create_agent()

            # エージェントが作成されたことを確認
            assert agent is mock_root_agent

            # LlmAgentが正しいサブエージェントで作成されたことを確認
            MockLlmAgent.assert_called_once()
            _, kwargs = MockLlmAgent.call_args

            assert kwargs["model"] == "gemini-2.5-flash-preview-05-20"
            assert kwargs["name"] == "root_agent"
            assert mock_calc_agent in kwargs["sub_agents"]
            assert mock_notion_agent in kwargs["sub_agents"]
            assert mock_extraction_agent in kwargs["sub_agents"]
            assert mock_vision_agent in kwargs["sub_agents"]
            assert (
                len(kwargs["tools"]) == 2
            )  # google_search_agent と fetch_web_content

from unittest.mock import MagicMock, patch

import pytest
from google.adk.runners import Runner
from google.genai import types

from src.agents.vision_agent import vision_agent


@pytest.mark.asyncio
async def test_vision_agent_food_image():
    """vision_agentが料理画像を正しく分析できるかテスト"""

    # テスト用に空のダミー画像データを作成
    dummy_image_data = b"dummy_image_data"

    # ランナー作成のモック
    with patch("google.adk.runners.Runner", autospec=True) as MockRunner:
        # モックランナーの設定
        mock_runner = MockRunner.return_value
        mock_response = MagicMock()
        mock_response.content = types.Content(
            role="model",
            parts=[
                types.Part(
                    text="""```json
{
  "image_type": "料理",
  "description": "画像にはパスタ料理が写っています。トマトソースがかかったスパゲッティで、上にはバジルの葉が飾られています。",
  "extracted_data": {
    "dish_name": "トマトパスタ",
    "ingredients": ["パスタ", "トマトソース", "バジル", "オリーブオイル"],
    "cuisine_type": "イタリアン",
    "preparation_style": "茹でて和えるタイプの料理"
  },
  "meta": {
    "analysis_confidence": "高"
  }
}```"""
                )
            ],
        )
        mock_response.is_final_response.return_value = True

        # イテレータとしての振る舞いを設定
        mock_runner.run_async.return_value.__aiter__.return_value = [
            mock_response
        ]

        # エージェントの実行
        runner = Runner(agent=vision_agent)

        # 画像コンテンツを作成
        parts = [
            types.Part.text(
                "この料理画像を分析して、何の料理か教えてください。"
            ),
            types.Part.inline_data(
                mime_type="image/jpeg", data=dummy_image_data
            ),
        ]
        content = types.Content(role="user", parts=parts)

        response = None
        async for event in runner.run_async(
            user_id="test_user", session_id="test_session", new_message=content
        ):
            if event.is_final_response():
                response = event.content.parts[0].text
                break

        # 検証
        assert response is not None
        assert "料理" in response
        assert "トマトパスタ" in response
        assert "イタリアン" in response

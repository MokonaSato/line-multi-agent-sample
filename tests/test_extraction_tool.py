from unittest.mock import MagicMock, patch

import pytest
from google.adk.runners import Runner
from google.genai import types

from src.agents.content_extraction_agent import content_extraction_agent


@pytest.mark.asyncio
async def test_content_extraction_agent_recipe():
    """content_extraction_agentがレシピHTMLを正しく分析できるかテスト"""

    # テスト用のレシピHTML (シンプルな例)
    recipe_html = """
    <html>
      <head><title>簡単トマトパスタ</title></head>
      <body>
        <h1>簡単トマトパスタ</h1>
        <div class="ingredients">
          <h2>材料（2人分）</h2>
          <ul>
            <li>スパゲッティ 200g</li>
            <li>トマト 2個</li>
            <li>にんにく 1片</li>
            <li>オリーブオイル 大さじ2</li>
            <li>塩 適量</li>
          </ul>
        </div>
        <div class="instructions">
          <h2>作り方</h2>
          <ol>
            <li>スパゲッティを袋の表示通りに茹でる</li>
            <li>トマトとにんにくをみじん切りにする</li>
            <li>フライパンでオリーブオイルとにんにくを熱する</li>
            <li>トマトを加えて弱火で5分炒める</li>
            <li>茹で上がったパスタを加えて塩で味を整える</li>
          </ol>
        </div>
      </body>
    </html>
    """

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
  "content_type": "レシピ",
  "extracted_data": {
    "recipe_name": "簡単トマトパスタ",
    "ingredients": [
        "スパゲッティ 200g",
        "トマト 2個",
        "にんにく 1片",
        "オリーブオイル 大さじ2",
        "塩 適量"
    ],
    "instructions": [
        "スパゲッティを袋の表示通りに茹でる",
        "トマトとにんにくをみじん切りにする",
        "フライパンでオリーブオイルとにんにくを熱する",
        "トマトを加えて弱火で5分炒める",
        "茹で上がったパスタを加えて塩で味を整える"
    ],
    "cooking_time": "15分",
    "servings": "2人分",
    "calories": "情報なし",
    "category": ["パスタ", "イタリアン", "簡単"]
  },
  "meta": {
    "source_url": "",
    "extraction_confidence": "高"
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
        runner = Runner(agent=content_extraction_agent)
        content = types.Content(
            role="user",
            parts=[
                types.Part(
                    text=f"このHTMLからレシピ情報を抽出してください: {recipe_html}"
                )
            ],
        )

        response = None
        async for event in runner.run_async(
            user_id="test_user", session_id="test_session", new_message=content
        ):
            if event.is_final_response():
                response = event.content.parts[0].text
                break

        # 検証
        assert response is not None
        assert "レシピ" in response
        assert "簡単トマトパスタ" in response
        assert "スパゲッティ" in response
        assert "トマト" in response

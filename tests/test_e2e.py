from unittest.mock import MagicMock, patch

import pytest

from src.services.agent_service import call_agent_async


@pytest.mark.asyncio
@patch("src.services.agent_service._runner")
async def test_url_to_notion_workflow(mock_runner):
    """URLから情報を取得し、抽出して処理するワークフローをテスト"""

    # モックレスポンスの設定
    mock_event = MagicMock()
    mock_event.is_final_response.return_value = True
    mock_event.content.parts = [
        MagicMock(
            text=(
                "レシピ「トマトパスタ」を取得しました。材料は「パスタ、トマト、"
                "オリーブオイル、塩」です。調理手順は「1. パスタを茹でる、"
                "2. トマトソースを作る、3. 和える」です。Notionに保存しました。"
            )
        )
    ]

    # モックランナーの設定
    mock_runner.run_async.return_value.__aiter__.return_value = [mock_event]

    # エージェント呼び出し
    response = await call_agent_async(
        "https://example.com/recipe からトマトパスタのレシピを取得してNotionに保存して",
        user_id="test_user",
    )

    # 検証
    assert "レシピ" in response
    assert "トマトパスタ" in response
    assert "材料" in response
    assert "調理手順" in response
    assert "Notionに保存" in response


@pytest.mark.asyncio
@patch("src.services.agent_service._runner")
async def test_image_to_notion_workflow(mock_runner):
    """画像から情報を抽出して処理するワークフローをテスト"""

    # モックレスポンスの設定
    mock_event = MagicMock()
    mock_event.is_final_response.return_value = True
    mock_event.content.parts = [
        MagicMock(
            text=(
                "画像からレシピ「トマトパスタ」を認識しました。主な材料は「パスタ、"
                "トマト、オリーブオイル」と推測されます。イタリアン料理のカテゴリに"
                "分類されます。この情報をNotionに保存しました。"
            )
        )
    ]

    # モックランナーの設定
    mock_runner.run_async.return_value.__aiter__.return_value = [mock_event]

    # 画像認識エージェント呼び出しをシミュレート
    response = await call_agent_async(
        "私が送った料理の画像から情報を抽出してNotionに保存して",
        user_id="test_user",
    )

    # 検証
    assert "画像" in response
    assert "レシピ" in response
    assert "材料" in response
    assert "イタリアン" in response
    assert "Notionに保存" in response

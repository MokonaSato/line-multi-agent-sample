from unittest.mock import MagicMock, patch

from src.tools.web_tools import fetch_web_content


def test_fetch_web_content():
    # モックのレスポンスを作成
    mock_response = MagicMock()
    mock_response.text = (
        "<html><head><title>テストページ</title></head><body><h1>テストページ</h1>"
        "<p>テストコンテンツ</p></body></html>"
    )
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "text/html"}

    # requestsのgetメソッドをモック化
    with patch("requests.get", return_value=mock_response):
        # BeautifulSoupのモックも追加
        with patch("src.agents.tools.web_tools.BeautifulSoup") as mock_soup:
            # BeautifulSoupのモックを設定
            mock_bs_instance = MagicMock()
            mock_soup.return_value = mock_bs_instance

            # タイトル属性のモック
            mock_title = MagicMock()
            mock_title.string = "テストページ"
            # title属性を設定
            mock_bs_instance.title = mock_title

            # metaタグの設定（descriptionメタタグ）
            mock_meta_tag = MagicMock()
            mock_meta_tag.get.return_value = "テスト説明文"
            # find メソッドのモック設定
            mock_bs_instance.find.return_value = mock_meta_tag

            # 関数実行
            result = fetch_web_content("https://example.com")

            # 結果を検証 - 辞書の中の値を確認
            assert result["success"]
            assert result["title"] == "テストページ"
            assert "テストコンテンツ" in result["html"]
            assert result["url"] == "https://example.com"
            assert result["status_code"] == 200
            assert result["description"] == "テスト説明文"


def test_fetch_web_content_error():
    # 失敗するケース
    with patch("requests.get", side_effect=Exception("接続エラー")):
        result = fetch_web_content("https://example.com")

        # エラーメッセージが辞書の中に含まれていることを確認
        assert not result["success"]
        assert "接続エラー" in result["error"]
        assert result["url"] == "https://example.com"

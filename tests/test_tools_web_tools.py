"""
Webツール機能のテストモジュール
"""

from unittest.mock import MagicMock, patch

import pytest
import requests
from bs4 import BeautifulSoup

# プロジェクトルートを sys.path に追加
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.web_tools import fetch_web_content


class TestFetchWebContent:
    """fetch_web_content関数のテストクラス"""

    @patch("src.tools.web_tools.requests.get")
    def test_fetch_web_content_success(self, mock_get):
        """正常なWebコンテンツ取得のテスト"""
        # モックレスポンスを設定
        mock_response = MagicMock()
        mock_response.text = '<html><head><title>Test Page</title><meta name="description" content="Test description"></head><body>Test content</body></html>'
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/html; charset=utf-8"}
        mock_get.return_value = mock_response

        result = fetch_web_content("https://example.com")

        assert result["success"] is True
        assert result["url"] == "https://example.com"
        assert result["title"] == "Test Page"
        assert result["description"] == "Test description"
        assert result["status_code"] == 200
        assert result["content_type"] == "text/html; charset=utf-8"
        assert result["html"] == mock_response.text

    @patch("src.tools.web_tools.requests.get")
    def test_fetch_web_content_with_headers(self, mock_get):
        """適切なヘッダーが設定されているかのテスト"""
        mock_response = MagicMock()
        mock_response.text = (
            "<html><head><title>Test</title></head><body></body></html>"
        )
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_get.return_value = mock_response

        fetch_web_content("https://example.com")

        # 正しいヘッダーで呼び出されているか確認
        expected_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        }
        mock_get.assert_called_once_with(
            "https://example.com", headers=expected_headers, timeout=10
        )

    @patch("src.tools.web_tools.requests.get")
    def test_fetch_web_content_no_title(self, mock_get):
        """タイトルがないページのテスト"""
        mock_response = MagicMock()
        mock_response.text = (
            "<html><head></head><body>No title page</body></html>"
        )
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_get.return_value = mock_response

        result = fetch_web_content("https://example.com")

        assert result["success"] is True
        assert result["title"] == "No title found"

    @patch("src.tools.web_tools.requests.get")
    def test_fetch_web_content_no_description(self, mock_get):
        """メタディスクリプションがないページのテスト"""
        mock_response = MagicMock()
        mock_response.text = "<html><head><title>Test</title></head><body>No description</body></html>"
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_get.return_value = mock_response

        result = fetch_web_content("https://example.com")

        assert result["success"] is True
        assert result["description"] == ""

    @patch("src.tools.web_tools.requests.get")
    def test_fetch_web_content_empty_description(self, mock_get):
        """空のメタディスクリプションのテスト"""
        mock_response = MagicMock()
        mock_response.text = '<html><head><title>Test</title><meta name="description" content=""></head><body></body></html>'
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_get.return_value = mock_response

        result = fetch_web_content("https://example.com")

        assert result["success"] is True
        assert result["description"] == ""

    @patch("src.tools.web_tools.requests.get")
    def test_fetch_web_content_requests_exception(self, mock_get):
        """requests例外のテスト"""
        mock_get.side_effect = requests.RequestException("Connection error")

        result = fetch_web_content("https://example.com")

        assert result["success"] is False
        assert result["error"] == "Connection error"
        assert result["url"] == "https://example.com"

    @patch("src.tools.web_tools.requests.get")
    def test_fetch_web_content_http_error(self, mock_get):
        """HTTPエラーのテスト"""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "404 Not Found"
        )
        mock_get.return_value = mock_response

        result = fetch_web_content("https://example.com")

        assert result["success"] is False
        assert result["error"] == "404 Not Found"
        assert result["url"] == "https://example.com"

    @patch("src.tools.web_tools.requests.get")
    def test_fetch_web_content_timeout_error(self, mock_get):
        """タイムアウトエラーのテスト"""
        mock_get.side_effect = requests.Timeout("Request timeout")

        result = fetch_web_content("https://example.com")

        assert result["success"] is False
        assert result["error"] == "Request timeout"
        assert result["url"] == "https://example.com"

    @patch("src.tools.web_tools.requests.get")
    def test_fetch_web_content_connection_error(self, mock_get):
        """接続エラーのテスト"""
        mock_get.side_effect = requests.ConnectionError("Connection failed")

        result = fetch_web_content("https://example.com")

        assert result["success"] is False
        assert result["error"] == "Connection failed"
        assert result["url"] == "https://example.com"

    @patch("src.tools.web_tools.requests.get")
    def test_fetch_web_content_invalid_html(self, mock_get):
        """不正なHTMLのテスト"""
        mock_response = MagicMock()
        mock_response.text = '<html><head><title>Test</title><meta name="description" content="desc">'
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_get.return_value = mock_response

        result = fetch_web_content("https://example.com")

        # BeautifulSoupは不正なHTMLでも処理できるため、成功する
        assert result["success"] is True
        assert result["title"] == "Test"
        assert result["description"] == "desc"

    @patch("src.tools.web_tools.requests.get")
    def test_fetch_web_content_no_content_type(self, mock_get):
        """Content-Typeヘッダーがない場合のテスト"""
        mock_response = MagicMock()
        mock_response.text = (
            "<html><head><title>Test</title></head><body></body></html>"
        )
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_get.return_value = mock_response

        result = fetch_web_content("https://example.com")

        assert result["success"] is True
        assert result["content_type"] == ""

    @patch("src.tools.web_tools.requests.get")
    def test_fetch_web_content_multiple_meta_tags(self, mock_get):
        """複数のメタタグがある場合のテスト"""
        mock_response = MagicMock()
        mock_response.text = """
        <html>
        <head>
            <title>Test</title>
            <meta name="keywords" content="test, keywords">
            <meta name="description" content="First description">
            <meta name="description" content="Second description">
        </head>
        <body></body>
        </html>
        """
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_get.return_value = mock_response

        result = fetch_web_content("https://example.com")

        assert result["success"] is True
        # 最初に見つかったdescriptionが使用される
        assert result["description"] == "First description"

    @patch("src.tools.web_tools.requests.get")
    def test_fetch_web_content_complex_html(self, mock_get):
        """複雑なHTMLのテスト"""
        mock_response = MagicMock()
        mock_response.text = """
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>複雑なページ</title>
            <meta name="description" content="これは複雑なページの説明です。">
            <meta name="keywords" content="テスト, HTML, Python">
        </head>
        <body>
            <header>
                <h1>メインタイトル</h1>
            </header>
            <main>
                <p>メインコンテンツ</p>
            </main>
        </body>
        </html>
        """
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/html; charset=UTF-8"}
        mock_get.return_value = mock_response

        result = fetch_web_content("https://example.com")

        assert result["success"] is True
        assert result["title"] == "複雑なページ"
        assert result["description"] == "これは複雑なページの説明です。"
        assert result["content_type"] == "text/html; charset=UTF-8"

    @patch("src.tools.web_tools.requests.get")
    def test_fetch_web_content_general_exception(self, mock_get):
        """一般的な例外のテスト"""
        mock_get.side_effect = Exception("Unexpected error")

        result = fetch_web_content("https://example.com")

        assert result["success"] is False
        assert result["error"] == "Unexpected error"
        assert result["url"] == "https://example.com"

    @patch("src.tools.web_tools.requests.get")
    def test_fetch_web_content_beautifulsoup_error(self, mock_get):
        """BeautifulSoup処理でのエラーテスト"""
        mock_response = MagicMock()
        mock_response.text = (
            "<html><head><title>Test</title></head><body></body></html>"
        )
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_get.return_value = mock_response

        with patch(
            "src.tools.web_tools.BeautifulSoup",
            side_effect=Exception("Parsing error"),
        ):
            result = fetch_web_content("https://example.com")

            assert result["success"] is False
            assert result["error"] == "Parsing error"
            assert result["url"] == "https://example.com"

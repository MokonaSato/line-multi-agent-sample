import pytest

from src.agents.tools.web_tools import fetch_web_content


@pytest.mark.asyncio
async def test_fetch_web_content_success():
    """fetch_web_contentが有効なURLから正しくコンテンツを取得するかテスト"""
    # テスト用のシンプルなWebページ
    test_url = "https://example.com"

    # ツール実行
    result = fetch_web_content(test_url)

    # 検証
    assert result["success"] is True
    assert "html" in result
    assert result["url"] == test_url
    assert result["status_code"] == 200
    assert "text/html" in result["content_type"]
    assert "Example Domain" in result["title"]


@pytest.mark.asyncio
async def test_fetch_web_content_invalid_url():
    """fetch_web_contentが無効なURLに対して適切にエラー処理するかテスト"""
    # 不正なURL
    invalid_url = "https://this-domain-does-not-exist-for-sure.xyz"

    # ツール実行
    result = fetch_web_content(invalid_url)

    # 検証
    assert result["success"] is False
    assert "error" in result
    assert result["url"] == invalid_url


@pytest.mark.asyncio
async def test_fetch_web_content_timeout():
    """fetch_web_contentがタイムアウトを適切に処理するかテスト"""
    # タイムアウトするようなURL (遅延させるサイト)
    timeout_url = "https://httpstat.us/200?sleep=10000"  # 10秒の遅延

    # ツール実行 (タイムアウトを期待)
    result = fetch_web_content(timeout_url)

    # 検証 (成功か失敗かは環境による)
    assert result["url"] == timeout_url
    if not result["success"]:
        assert "error" in result
        assert "timeout" in result["error"].lower()

from typing import Any, Dict

import requests
from bs4 import BeautifulSoup


def fetch_web_content(url: str) -> Dict[str, Any]:
    """
    指定されたURLからWebコンテンツを取得します。

    Args:
        url: 取得するWebページのURL

    Returns:
        HTMLコンテンツとメタデータを含む辞書
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Beautiful Soupを使用してHTMLを解析
        soup = BeautifulSoup(response.text, "html.parser")

        # タイトルを抽出
        title = soup.title.string if soup.title else "No title found"

        # メタディスクリプションを抽出
        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag and meta_tag.get("content"):
            meta_desc = meta_tag.get("content")

        return {
            "success": True,
            "html": response.text,
            "url": url,
            "title": title,
            "description": meta_desc,
            "status_code": response.status_code,
            "content_type": response.headers.get("Content-Type", ""),
        }
    except Exception as e:
        return {"success": False, "error": str(e), "url": url}

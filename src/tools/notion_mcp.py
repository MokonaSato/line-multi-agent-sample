"""Notion MCP Server連携モジュール

このモジュールはNotionMCPサーバーとの通信を担当し、
HTTP API経由でMCPサーバーにリクエストを送信します。
"""

import os
import time
from typing import Any, Dict, List, Optional

import httpx

from src.utils.logger import setup_logger

logger = setup_logger("notion_mcp")

# Notion MCP ServerのURL（環境変数から取得）
NOTION_MCP_URL = os.getenv("NOTION_MCP_URL", "http://localhost:3001")


def initialize_notion_mcp() -> None:
    """Notion MCP Serverを初期化する（同期版）"""
    try:
        logger.info(
            f"Initializing Notion MCP client with URL: {NOTION_MCP_URL}"
        )

        # MCPサーバーが起動するまで最大60秒待機
        max_wait_time = 60
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            if check_notion_mcp_health_sync():
                logger.info("✅ Notion MCP client initialized successfully")
                return

            logger.info("Waiting for Notion MCP Server to start...")
            time.sleep(5)

        logger.warning(
            f"⚠️ Notion MCP Server not available after {max_wait_time}s, "
            "using fallback mode"
        )

    except Exception as e:
        logger.error(f"Failed to initialize Notion MCP client: {e}")
        logger.warning("Running without Notion MCP Server")


def cleanup_notion_mcp() -> None:
    """Notion MCP Serverのクリーンアップ（同期版）"""
    try:
        logger.info("✅ Notion MCP cleanup completed")
    except Exception as e:
        logger.error(f"Error during Notion MCP cleanup: {e}")


def check_notion_mcp_health_sync() -> bool:
    """Notion MCP Serverのヘルスチェック（同期版）"""
    try:
        with httpx.Client(timeout=5.0) as client:
            # まずヘルスチェックエンドポイントを試す
            try:
                response = client.get(f"{NOTION_MCP_URL}/health")
                return response.status_code == 200
            except Exception:
                # ヘルスエンドポイントがない場合は基本的なステータスを確認
                try:
                    response = client.get(f"{NOTION_MCP_URL}/")
                    return response.status_code in [
                        200,
                        404,
                    ]  # サーバーが応答すれば OK
                except Exception:
                    return False
    except Exception as e:
        logger.warning(f"Notion MCP health check failed: {e}")
        return False


async def check_notion_mcp_health() -> bool:
    """Notion MCP Serverのヘルスチェック（非同期版）"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # まずヘルスチェックエンドポイントを試す
            try:
                response = await client.get(f"{NOTION_MCP_URL}/health")
                return response.status_code == 200
            except Exception:
                # ヘルスエンドポイントがない場合は基本的なステータスを確認
                try:
                    response = await client.get(f"{NOTION_MCP_URL}/")
                    return response.status_code in [
                        200,
                        404,
                    ]  # サーバーが応答すれば OK
                except Exception:
                    return False
    except Exception as e:
        logger.warning(f"Notion MCP health check failed: {e}")
        return False


def create_notion_page(
    parent_database_id: str,
    properties: Dict[str, Any],
    children: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Notion MCP Serverを通じてページを作成する（同期版）

    Args:
        parent_database_id: 親データベースID
        properties: ページプロパティ
        children: 子コンテンツ（オプション）

    Returns:
        作成されたページの情報
    """
    try:
        # MCP Server APIエンドポイントに接続
        payload = {
            "method": "notion_create_page",
            "params": {
                "parent": {"database_id": parent_database_id},
                "properties": properties,
                "children": children or [],
            },
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{NOTION_MCP_URL}/api/call",
                json=payload,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(
                    f"✅ Successfully created Notion page: {result.get('id')}"
                )
                return {
                    "success": True,
                    "id": result.get("id"),
                    "url": result.get("url"),
                    "properties": result.get("properties", {}),
                }
            else:
                error_text = response.text
                logger.error(
                    f"Failed to create Notion page: {response.status_code} - "
                    f"{error_text}"
                )
                return {
                    "success": False,
                    "error": f"API call failed: {response.status_code}",
                    "id": None,
                    "url": None,
                }

    except Exception as e:
        logger.error(f"Error creating Notion page via MCP: {e}")
        return {
            "success": False,
            "error": f"MCP Server通信エラー: {str(e)}",
            "id": None,
            "url": None,
        }


def query_notion_database(
    database_id: str,
    filter_conditions: Optional[Dict[str, Any]] = None,
    sorts: Optional[List[Dict[str, Any]]] = None,
    page_size: int = 100,
) -> Dict[str, Any]:
    """Notion MCP Serverを通じてデータベースをクエリする（同期版）

    Args:
        database_id: データベースID
        filter_conditions: フィルター条件
        sorts: ソート条件
        page_size: ページサイズ

    Returns:
        クエリ結果
    """
    try:
        payload = {
            "method": "notion_query_database",
            "params": {
                "database_id": database_id,
                "filter": filter_conditions,
                "sorts": sorts,
                "page_size": page_size,
            },
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{NOTION_MCP_URL}/api/call",
                json=payload,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(
                    "✅ Successfully queried Notion database: %d items",
                    len(result.get("results", [])),
                )
                return {
                    "success": True,
                    "results": result.get("results", []),
                    "has_more": result.get("has_more", False),
                    "next_cursor": result.get("next_cursor"),
                }
            else:
                error_text = response.text
                logger.error(
                    f"Failed to query Notion database: {response.status_code}"
                    f" - {error_text}"
                )
                return {
                    "success": False,
                    "error": f"API call failed: {response.status_code}",
                    "results": [],
                    "has_more": False,
                    "next_cursor": None,
                }

    except Exception as e:
        logger.error(f"Error querying Notion database via MCP: {e}")
        return {
            "success": False,
            "error": f"MCP Server通信エラー: {str(e)}",
            "results": [],
            "has_more": False,
            "next_cursor": None,
        }


def update_notion_page(
    page_id: str,
    properties: Optional[Dict[str, Any]] = None,
    archived: Optional[bool] = None,
) -> Dict[str, Any]:
    """Notion MCP Serverを通じてページを更新する（同期版）

    Args:
        page_id: ページID
        properties: 更新するプロパティ
        archived: アーカイブ状態

    Returns:
        更新されたページの情報
    """
    try:
        payload = {
            "method": "notion_update_page",
            "params": {
                "page_id": page_id,
                "properties": properties,
                "archived": archived,
            },
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{NOTION_MCP_URL}/api/call",
                json=payload,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Successfully updated Notion page: {page_id}")
                return {
                    "success": True,
                    "id": result.get("id"),
                    "url": result.get("url"),
                    "properties": result.get("properties", {}),
                }
            else:
                error_text = response.text
                logger.error(
                    f"Failed to update Notion page: {response.status_code} - "
                    f"{error_text}"
                )
                return {
                    "success": False,
                    "error": f"API call failed: {response.status_code}",
                    "id": None,
                    "url": None,
                }

    except Exception as e:
        logger.error(f"Error updating Notion page via MCP: {e}")
        return {
            "success": False,
            "error": f"MCP Server通信エラー: {str(e)}",
            "id": None,
            "url": None,
        }


def retrieve_notion_page(page_id: str) -> Dict[str, Any]:
    """Notion MCP Serverを通じてページを取得する（同期版）

    Args:
        page_id: ページID

    Returns:
        ページの情報
    """
    try:
        payload = {
            "method": "notion_retrieve_page",
            "params": {"page_id": page_id},
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{NOTION_MCP_URL}/api/call",
                json=payload,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(
                    f"✅ Successfully retrieved Notion page: {page_id}"
                )
                return {
                    "success": True,
                    "page": result,
                    "id": result.get("id"),
                    "url": result.get("url"),
                    "properties": result.get("properties", {}),
                }
            else:
                error_text = response.text
                logger.error(
                    f"Failed to retrieve Notion page: "
                    f"{response.status_code} - {error_text}"
                )
                return {
                    "success": False,
                    "error": f"API call failed: {response.status_code}",
                    "page": None,
                }

    except Exception as e:
        logger.error(f"Error retrieving Notion page via MCP: {e}")
        return {
            "success": False,
            "error": f"MCP Server通信エラー: {str(e)}",
            "page": None,
        }

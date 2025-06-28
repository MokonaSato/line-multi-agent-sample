"""Notion API トークンの検証とテスト機能

このモジュールは、Notion API トークンが有効かどうかを検証し、
API接続の健全性をテストする機能を提供します。
"""

from typing import Dict, Any, Optional, Tuple
import httpx
from datetime import datetime

from src.utils.logger import setup_logger
from src.utils.gcp_secret_manager import get_notion_token_from_secret_manager

logger = setup_logger("notion_validator")

# Notion API の設定
NOTION_API_BASE_URL = "https://api.notion.com/v1"
NOTION_API_VERSION = "2022-06-28"
REQUEST_TIMEOUT = 10  # 秒


class NotionTokenValidator:
    """Notion API トークンの検証クラス
    
    Notion API への接続テストとトークンの有効性検証を行います。
    """

    def __init__(self, token: Optional[str] = None):
        """初期化
        
        Args:
            token: Notion API トークン。指定しない場合は Secret Manager から取得
        """
        self.token = token or get_notion_token_from_secret_manager()
        
        if not self.token:
            logger.warning("Notion API トークンが取得できませんでした")
        else:
            # トークンの最初の8文字だけログに出力（セキュリティのため）
            masked_token = f"{self.token[:8]}..." if len(self.token) > 8 else "***"
            logger.info(f"Notion API トークンを取得しました: {masked_token}")

    def _get_headers(self) -> Dict[str, str]:
        """API リクエスト用のヘッダーを構築
        
        Returns:
            HTTPヘッダーの辞書
        """
        return {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": NOTION_API_VERSION,
            "Content-Type": "application/json"
        }

    async def validate_token_async(self) -> Tuple[bool, Dict[str, Any]]:
        """Notion API トークンの有効性を非同期で検証
        
        /v1/users エンドポイントを使用してトークンの有効性をテストします。
        
        Returns:
            Tuple[bool, Dict[str, Any]]: (検証成功フラグ, 詳細情報)
        """
        if not self.token:
            return False, {
                "error": "token_missing",
                "message": "Notion API トークンが設定されていません",
                "timestamp": datetime.now().isoformat()
            }

        try:
            logger.info("Notion API への接続テストを開始します")
            
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.get(
                    f"{NOTION_API_BASE_URL}/users",
                    headers=self._get_headers()
                )
                
                # レスポンスの詳細をログに記録
                logger.info(f"Notion API レスポンス: ステータス={response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    user_count = len(data.get("results", []))
                    
                    logger.info(f"✅ Notion API トークンが有効です。ユーザー数: {user_count}")
                    
                    return True, {
                        "status": "valid",
                        "message": "Notion API トークンは有効です",
                        "user_count": user_count,
                        "timestamp": datetime.now().isoformat(),
                        "response_data": data
                    }
                
                elif response.status_code == 401:
                    logger.error("❌ Notion API トークンが無効です（認証エラー）")
                    return False, {
                        "error": "unauthorized",
                        "message": "Notion API トークンが無効または期限切れです",
                        "status_code": 401,
                        "timestamp": datetime.now().isoformat()
                    }
                
                elif response.status_code == 403:
                    logger.error("❌ Notion API へのアクセス権限がありません")
                    return False, {
                        "error": "forbidden",
                        "message": "Notion API へのアクセス権限がありません",
                        "status_code": 403,
                        "timestamp": datetime.now().isoformat()
                    }
                
                else:
                    logger.error(f"❌ Notion API から予期しないレスポンス: {response.status_code}")
                    error_text = response.text
                    
                    return False, {
                        "error": "api_error",
                        "message": f"Notion API エラー: {response.status_code}",
                        "status_code": response.status_code,
                        "response_text": error_text,
                        "timestamp": datetime.now().isoformat()
                    }
                    
        except httpx.TimeoutException:
            logger.error("❌ Notion API への接続がタイムアウトしました")
            return False, {
                "error": "timeout",
                "message": f"Notion API への接続がタイムアウトしました（{REQUEST_TIMEOUT}秒）",
                "timestamp": datetime.now().isoformat()
            }
            
        except httpx.RequestError as e:
            logger.error(f"❌ Notion API への接続中にネットワークエラーが発生: {e}")
            return False, {
                "error": "network_error",
                "message": f"ネットワークエラー: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Notion API 検証中に予期しないエラーが発生: {e}")
            return False, {
                "error": "unexpected_error",
                "message": f"予期しないエラー: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    def validate_token_sync(self) -> Tuple[bool, Dict[str, Any]]:
        """Notion API トークンの有効性を同期的に検証
        
        Returns:
            Tuple[bool, Dict[str, Any]]: (検証成功フラグ, 詳細情報)
        """
        if not self.token:
            return False, {
                "error": "token_missing",
                "message": "Notion API トークンが設定されていません",
                "timestamp": datetime.now().isoformat()
            }

        try:
            logger.info("Notion API への同期接続テストを開始します")
            
            with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
                response = client.get(
                    f"{NOTION_API_BASE_URL}/users",
                    headers=self._get_headers()
                )
                
                logger.info(f"Notion API レスポンス: ステータス={response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    user_count = len(data.get("results", []))
                    
                    logger.info(f"✅ Notion API トークンが有効です。ユーザー数: {user_count}")
                    
                    return True, {
                        "status": "valid",
                        "message": "Notion API トークンは有効です",
                        "user_count": user_count,
                        "timestamp": datetime.now().isoformat(),
                        "response_data": data
                    }
                
                else:
                    logger.error(f"❌ Notion API エラー: {response.status_code}")
                    return False, {
                        "error": "api_error",
                        "message": f"Notion API エラー: {response.status_code}",
                        "status_code": response.status_code,
                        "timestamp": datetime.now().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"❌ Notion API 検証中にエラーが発生: {e}")
            return False, {
                "error": "unexpected_error",
                "message": f"エラー: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }


# 便利関数
async def validate_notion_token_async(token: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
    """Notion API トークンを非同期で検証する便利関数
    
    Args:
        token: 検証するトークン。指定しない場合は Secret Manager から取得
        
    Returns:
        Tuple[bool, Dict[str, Any]]: (検証成功フラグ, 詳細情報)
    """
    validator = NotionTokenValidator(token)
    return await validator.validate_token_async()


def validate_notion_token_sync(token: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
    """Notion API トークンを同期的に検証する便利関数
    
    Args:
        token: 検証するトークン。指定しない場合は Secret Manager から取得
        
    Returns:
        Tuple[bool, Dict[str, Any]]: (検証成功フラグ, 詳細情報)
    """
    validator = NotionTokenValidator(token)
    return validator.validate_token_sync()
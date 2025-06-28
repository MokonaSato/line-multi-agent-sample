"""GCP Secret Manager からシークレットを取得するユーティリティモジュール

このモジュールは、Google Cloud Secret Manager からシークレット（APIキーやトークン）を
安全に取得する機能を提供します。
"""

import os
from typing import Optional

from google.cloud import secretmanager
from google.cloud.exceptions import NotFound, PermissionDenied

from src.utils.logger import setup_logger

logger = setup_logger("gcp_secret_manager")


class SecretManagerClient:
    """GCP Secret Manager クライアント
    
    Google Cloud Secret Manager からシークレットを取得するためのクライアントクラス。
    """

    def __init__(self):
        """初期化
        
        環境変数からGCPプロジェクトIDを取得し、Secret Managerクライアントを初期化します。
        """
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not self.project_id:
            logger.warning("GOOGLE_CLOUD_PROJECT環境変数が設定されていません")
        
        try:
            self.client = secretmanager.SecretManagerServiceClient()
            logger.info("Secret Manager クライアントを初期化しました")
        except Exception as e:
            logger.error(f"Secret Manager クライアントの初期化に失敗: {e}")
            self.client = None

    def get_secret(self, secret_name: str, version: str = "latest") -> Optional[str]:
        """指定されたシークレットを取得
        
        Args:
            secret_name: Secret Manager でのシークレット名
            version: シークレットのバージョン（デフォルト: "latest"）
        
        Returns:
            シークレットの値（文字列）、または取得に失敗した場合は None
        """
        if not self.client:
            logger.error("Secret Manager クライアントが初期化されていません")
            return None
        
        if not self.project_id:
            logger.error("プロジェクトIDが設定されていません")
            return None

        try:
            # シークレットのフルパスを構築
            secret_path = f"projects/{self.project_id}/secrets/{secret_name}/versions/{version}"
            logger.info(f"シークレットを取得中: {secret_path}")
            
            # シークレットを取得
            response = self.client.access_secret_version(request={"name": secret_path})
            secret_value = response.payload.data.decode("UTF-8")
            
            logger.info(f"シークレット '{secret_name}' を正常に取得しました")
            return secret_value
            
        except NotFound:
            logger.error(f"シークレット '{secret_name}' が見つかりません")
            return None
        except PermissionDenied:
            logger.error(f"シークレット '{secret_name}' にアクセスする権限がありません")
            return None
        except Exception as e:
            logger.error(f"シークレット '{secret_name}' の取得中にエラーが発生: {e}")
            return None

    def get_notion_token(self) -> Optional[str]:
        """Notion API トークンを取得
        
        Secret Manager から 'notion-token' という名前のシークレットを取得します。
        
        Returns:
            Notion API トークン、または取得に失敗した場合は None
        """
        return self.get_secret("notion-token")


# グローバルインスタンス
_secret_client: Optional[SecretManagerClient] = None


def get_secret_manager_client() -> SecretManagerClient:
    """Secret Manager クライアントのシングルトンインスタンスを取得
    
    Returns:
        SecretManagerClient インスタンス
    """
    global _secret_client
    if _secret_client is None:
        _secret_client = SecretManagerClient()
    return _secret_client


def get_notion_token_from_secret_manager() -> Optional[str]:
    """Secret Manager から Notion トークンを取得する便利関数
    
    Returns:
        Notion API トークン、または取得に失敗した場合は None
    """
    client = get_secret_manager_client()
    return client.get_notion_token()
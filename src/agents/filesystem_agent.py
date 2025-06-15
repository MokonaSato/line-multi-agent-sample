# src/agents/filesystem_agent.py
"""ファイルシステムエージェントモジュール

このモジュールは、filesystem MCP serverを使用してファイルシステム操作を行う
エージェントを提供します。
"""

from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams

from src.utils.logger import setup_logger

logger = setup_logger("filesystem_agent")


class FilesystemAgentManager:
    """ファイルシステムエージェント管理クラス"""

    def __init__(self):
        self.filesystem_tools = None
        self.exit_stack = None
        self.agent = None

    async def get_filesystem_tools(self):
        """Filesystem MCP serverからツールを取得"""
        try:
            logger.info("Attempting to connect to MCP Filesystem server...")

            # Filesystem MCP (localhost:8000) へSSEで接続
            self.filesystem_tools, self.exit_stack = (
                await MCPToolset.from_server(
                    connection_params=SseServerParams(
                        url="http://localhost:8000/sse"
                    )
                )
            )

            logger.info("Filesystem MCP Toolset created successfully.")
            return self.filesystem_tools, self.exit_stack

        except Exception as e:
            logger.error(f"Failed to connect to Filesystem MCP server: {e}")
            # フォールバック: 空のツールセット
            self.filesystem_tools = []
            return self.filesystem_tools, None

    async def create_filesystem_agent(
        self, model: str = "gemini-2.5-flash-preview-05-20"
    ) -> LlmAgent:
        """ファイルシステムエージェントを作成"""
        if self.filesystem_tools is None:
            await self.get_filesystem_tools()

        # プロンプトファイルから指示書を読み込み
        try:
            from src.utils.prompt_manager import PromptManager

            prompt_manager = PromptManager()
            instruction = prompt_manager.get_prompt("agents.filesystem.main")
        except Exception as e:
            logger.warning(f"プロンプトファイルの読み込みに失敗: {e}")
            # デフォルトの指示書を使用
            instruction = self._get_default_instruction()

        self.agent = LlmAgent(
            name="filesystem_agent",
            model=model,
            description=(
                "ファイルシステム操作を実行するエージェントです。"
                "ファイルの読み書き、ディレクトリ操作、ファイル検索、"
                "ファイル情報の取得などを行います。"
            ),
            instruction=instruction,
            tools=self.filesystem_tools or [],
        )

        logger.info("Filesystem agent created successfully.")
        return self.agent

    def _get_default_instruction(self) -> str:
        """デフォルトの指示書を返す"""
        return """あなたはファイルシステム操作を行う専門エージェントです。

## 基本動作方針
- ユーザーのファイル操作リクエストを理解し、適切なツールを選択して実行してください
- ファイルパスの指定やディレクトリ構造を正確に把握してください
- ファイル操作の結果を明確に報告してください
- エラーが発生した場合は、分かりやすく説明し、対処法を提示してください

## 対応可能な操作
- ファイルの読み取り（read_file, read_multiple_files）
- ファイルの作成・書き込み（write_file）
- ファイルの編集（edit_file）
- ディレクトリの作成（create_directory）
- ファイル・ディレクトリの一覧表示（list_directory, directory_tree）
- ファイル・ディレクトリの移動・リネーム（move_file）
- ファイル検索（search_files）
- ファイル情報取得（get_file_info）
- 許可ディレクトリの確認（list_allowed_directories）

## 安全性の考慮
- 許可されたディレクトリ内でのみ操作を実行してください
- 重要なファイルの上書きや削除には注意を払ってください
- ファイル操作前に確認が必要な場合は、ユーザーに確認を求めてください

## 応答方法
- 操作結果を具体的に報告してください
- ファイルパスや操作内容を明確に示してください
- エラーの場合は、原因と対処法を分かりやすく説明してください

常にユーザーの意図を正確に理解し、安全で効率的なファイル操作を心がけてください。"""

    async def cleanup(self):
        """リソースをクリーンアップ"""
        if self.exit_stack:
            try:
                await self.exit_stack.aclose()
                logger.info(
                    "Filesystem agent resources cleaned up successfully."
                )
            except Exception as e:
                logger.error(f"Error during filesystem agent cleanup: {e}")


# グローバルインスタンス
_filesystem_manager = FilesystemAgentManager()


async def create_filesystem_agent(
    model: str = "gemini-2.5-flash-preview-05-20",
) -> LlmAgent:
    """ファイルシステムエージェントを作成（外部インターフェース）"""
    return await _filesystem_manager.create_filesystem_agent(model)


async def cleanup_filesystem_agent():
    """ファイルシステムエージェントのリソースをクリーンアップ"""
    await _filesystem_manager.cleanup()


def get_filesystem_manager():
    """ファイルシステムマネージャーのインスタンスを取得"""
    return _filesystem_manager

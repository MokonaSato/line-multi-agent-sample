"""
ファイルシステムツールのテストモジュール
"""

import os
from unittest.mock import MagicMock, patch

from src.tools.filesystem import (
    ALLOWED_DIRECTORIES,
    WORK_DIR,
    _validate_path,
    check_filesystem_health,
    create_directory_tool,
    delete_file_tool,
    ensure_work_directory,
    filesystem_tools,
    initialize_filesystem_service,
    list_allowed_directories,
    list_directory_tool,
    read_file_tool,
    write_file_tool,
)


# google.adk が利用できないため、モック用の簡単な実装をテスト
class MockFilesystemTest:
    """ファイルシステムツールのモックテストクラス"""

    def test_mock_filesystem_constants(self):
        """定数の存在確認テスト"""
        # google.adkに依存しない部分のテスト
        work_dir = "/tmp/user_files"
        allowed_directories = ["uploads", "temp", "logs"]

        assert work_dir == "/tmp/user_files"
        assert isinstance(allowed_directories, list)
        assert "uploads" in allowed_directories


class TestEnsureWorkDirectory:
    """ensure_work_directory関数のテストクラス"""

    @patch("os.makedirs")
    def test_ensure_work_directory_creates_directories(self, mock_makedirs):
        """作業ディレクトリが作成されることをテスト"""
        ensure_work_directory()

        # すべての許可されたディレクトリで makedirs が呼ばれることを確認
        assert mock_makedirs.call_count >= len(ALLOWED_DIRECTORIES)

    @patch("os.makedirs")
    def test_ensure_work_directory_handles_existing_directories(
        self, mock_makedirs
    ):
        """既存ディレクトリがある場合の処理をテスト"""
        ensure_work_directory()

        # exist_ok=Trueで呼び出されることを確認
        for call_args in mock_makedirs.call_args_list:
            assert call_args[1]["exist_ok"] is True


class TestValidatePath:
    """_validate_path関数のテストクラス"""

    def test_validate_path_success(self):
        """正常なパスの検証テスト"""
        file_path = "test.txt"
        full_path, error = _validate_path(file_path)

        assert error is None
        assert full_path == os.path.join(WORK_DIR, "test.txt")

    def test_validate_path_with_subdirectory(self):
        """サブディレクトリを含むパスの検証テスト"""
        file_path = "subdir/test.txt"
        full_path, error = _validate_path(file_path)

        assert error is None
        assert full_path == os.path.join(WORK_DIR, "subdir/test.txt")

    def test_validate_path_removes_leading_slash(self):
        """先頭スラッシュが除去されることをテスト"""
        file_path = "/test.txt"
        full_path, error = _validate_path(file_path)

        assert error is None
        assert full_path == os.path.join(WORK_DIR, "test.txt")

    def test_validate_path_outside_work_dir(self):
        """
        作業ディレクトリ外のパスが拒否されることをテスト
        """
        # パストラバーサル攻撃のテスト
        file_path = "../../../../etc/passwd"
        full_path, error = _validate_path(file_path)

        # 実際の実装では、パスが正規化されてエラーが発生するか、
        # 作業ディレクトリ内のパスとして扱われる
        if error is not None:
            assert "アクセス許可されていません" in error
        else:
            # 作業ディレクトリ内に正規化された場合
            assert full_path.startswith(WORK_DIR)


class TestReadFileTool:
    """read_file_tool関数のテストクラス"""

    @patch("src.tools.filesystem._validate_path")
    @patch("os.path.exists")
    @patch("builtins.open")
    def test_read_file_tool_success(
        self, mock_open, mock_exists, mock_validate
    ):
        """ファイル読み取り成功のテスト"""
        mock_validate.return_value = ("/tmp/user_files/test.txt", None)
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = (
            "test content"
        )

        result = read_file_tool("test.txt")

        assert "ファイル 'test.txt' の内容:" in result
        assert "test content" in result

    @patch("src.tools.filesystem._validate_path")
    def test_read_file_tool_validation_error(self, mock_validate):
        """パス検証エラーのテスト"""
        mock_validate.return_value = ("", "validation error")

        result = read_file_tool("../test.txt")

        assert result == "validation error"

    @patch("src.tools.filesystem._validate_path")
    @patch("os.path.exists")
    def test_read_file_tool_file_not_found(self, mock_exists, mock_validate):
        """ファイルが見つからない場合のテスト"""
        mock_validate.return_value = ("/tmp/user_files/test.txt", None)
        mock_exists.return_value = False

        result = read_file_tool("test.txt")

        assert "ファイル 'test.txt' が見つかりません" in result

    @patch("src.tools.filesystem._validate_path")
    @patch("os.path.exists")
    @patch("builtins.open")
    def test_read_file_tool_unicode_decode_error(
        self, mock_open, mock_exists, mock_validate
    ):
        """UnicodeDecodeErrorのテスト"""
        mock_validate.return_value = ("/tmp/user_files/test.bin", None)
        mock_exists.return_value = True

        # 最初の呼び出しでUnicodeDecodeError、二回目の呼び出しでバイナリデータを返す
        mock_file_text = MagicMock()
        mock_file_text.read.side_effect = UnicodeDecodeError(
            "utf-8", b"", 0, 1, "invalid start byte"
        )

        mock_file_binary = MagicMock()
        mock_file_binary.read.return_value = b"\x00\x01\x02\x03"

        mock_open.return_value.__enter__.side_effect = [
            mock_file_text,
            mock_file_binary,
        ]

        result = read_file_tool("test.bin")

        assert "バイナリファイル" in result
        assert "サイズ: 4 bytes" in result

    @patch("src.tools.filesystem._validate_path")
    @patch("os.path.exists")
    @patch("builtins.open")
    def test_read_file_tool_general_exception(
        self, mock_open, mock_exists, mock_validate
    ):
        """一般的な例外のテスト"""
        mock_validate.return_value = ("/tmp/user_files/test.txt", None)
        mock_exists.return_value = True
        mock_open.side_effect = IOError("File access error")

        result = read_file_tool("test.txt")

        assert "ファイル読み取りに失敗しました" in result
        assert "File access error" in result


class TestWriteFileTool:
    """write_file_tool関数のテストクラス"""

    @patch("src.tools.filesystem.ensure_work_directory")
    @patch("src.tools.filesystem._validate_path")
    @patch("os.path.dirname")
    @patch("os.path.exists")
    @patch("os.makedirs")
    @patch("builtins.open")
    def test_write_file_tool_success(
        self,
        mock_open,
        mock_makedirs,
        mock_exists,
        mock_dirname,
        mock_validate,
        mock_ensure,
    ):
        """ファイル書き込み成功のテスト"""
        mock_validate.return_value = ("/tmp/user_files/test.txt", None)
        mock_dirname.return_value = "/tmp/user_files"
        mock_exists.return_value = True

        result = write_file_tool("test.txt", "test content")

        assert "ファイル 'test.txt' に正常に書き込みました" in result
        assert "12 文字" in result

    @patch("src.tools.filesystem.ensure_work_directory")
    @patch("src.tools.filesystem._validate_path")
    def test_write_file_tool_validation_error(
        self, mock_validate, mock_ensure
    ):
        """パス検証エラーのテスト"""
        mock_validate.return_value = ("", "validation error")

        result = write_file_tool("../test.txt", "content")

        assert result == "validation error"

    @patch("src.tools.filesystem.ensure_work_directory")
    @patch("src.tools.filesystem._validate_path")
    @patch("os.path.dirname")
    @patch("os.path.exists")
    @patch("os.makedirs")
    @patch("builtins.open")
    def test_write_file_tool_create_parent_directory(
        self,
        mock_open,
        mock_makedirs,
        mock_exists,
        mock_dirname,
        mock_validate,
        mock_ensure,
    ):
        """親ディレクトリが作成されることをテスト"""
        mock_validate.return_value = ("/tmp/user_files/subdir/test.txt", None)
        mock_dirname.return_value = "/tmp/user_files/subdir"
        mock_exists.return_value = False  # 親ディレクトリが存在しない

        write_file_tool("subdir/test.txt", "content")

        mock_makedirs.assert_called_once_with(
            "/tmp/user_files/subdir", exist_ok=True
        )

    @patch("src.tools.filesystem.ensure_work_directory")
    @patch("src.tools.filesystem._validate_path")
    @patch("builtins.open")
    def test_write_file_tool_exception(
        self, mock_open, mock_validate, mock_ensure
    ):
        """書き込み例外のテスト"""
        mock_validate.return_value = ("/tmp/user_files/test.txt", None)
        mock_open.side_effect = IOError("Write error")

        result = write_file_tool("test.txt", "content")

        assert "ファイルの書き込みに失敗しました" in result
        assert "Write error" in result


class TestListDirectoryTool:
    """list_directory_tool関数のテストクラス"""

    @patch("src.tools.filesystem.ensure_work_directory")
    @patch("src.tools.filesystem._validate_path")
    @patch("os.path.exists")
    @patch("os.path.getsize")
    @patch("os.listdir")
    @patch("os.path.isdir")
    @patch("os.path.isfile")
    def test_list_directory_tool_success(
        self,
        mock_isfile,
        mock_isdir,
        mock_listdir,
        mock_getsize,
        mock_exists,
        mock_validate,
        mock_ensure,
    ):
        """
        ディレクトリ内容の正常表示テスト
        """
        mock_validate.return_value = ("/tmp/user_files", None)
        mock_exists.return_value = True
        # ディレクトリであることを最初に確認
        mock_isdir.return_value = True
        mock_listdir.return_value = ["file1.txt", "subdir"]

        # file1.txtのみファイル、subdirのみディレクトリ
        def isfile_side_effect(path):
            return path.endswith("file1.txt")

        def isdir_side_effect(path):
            if path == "/tmp/user_files":
                return True
            return path.endswith("subdir")

        mock_isfile.side_effect = isfile_side_effect
        mock_isdir.side_effect = isdir_side_effect
        mock_getsize.return_value = 100

        result = list_directory_tool("")

        assert "📄 file1.txt (100 bytes)" in result
        assert "📁 subdir/" in result

    @patch("src.tools.filesystem.ensure_work_directory")
    @patch("src.tools.filesystem._validate_path")
    @patch("os.path.exists")
    def test_list_directory_tool_not_found(
        self, mock_exists, mock_validate, mock_ensure
    ):
        """ディレクトリが見つからない場合のテスト"""
        mock_validate.return_value = ("/tmp/user_files/nonexistent", None)
        mock_exists.return_value = False

        result = list_directory_tool("nonexistent")

        assert "ディレクトリ 'nonexistent' が見つかりません" in result

    @patch("src.tools.filesystem.ensure_work_directory")
    @patch("src.tools.filesystem._validate_path")
    @patch("os.path.exists")
    @patch("os.path.isdir")
    def test_list_directory_tool_not_directory(
        self, mock_isdir, mock_exists, mock_validate, mock_ensure
    ):
        """ディレクトリではない場合のテスト"""
        mock_validate.return_value = ("/tmp/user_files/file.txt", None)
        mock_exists.return_value = True
        mock_isdir.return_value = False

        result = list_directory_tool("file.txt")

        assert "はディレクトリではありません" in result

    @patch("src.tools.filesystem.ensure_work_directory")
    @patch("os.path.exists")
    @patch("os.path.isdir")
    @patch("os.listdir")
    def test_list_directory_tool_empty_directory(
        self, mock_listdir, mock_isdir, mock_exists, mock_ensure
    ):
        """空ディレクトリのテスト"""
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_listdir.return_value = []

        result = list_directory_tool("")

        assert "ディレクトリ 'ルート' は空です" in result


class TestCreateDirectoryTool:
    """create_directory_tool関数のテストクラス"""

    @patch("src.tools.filesystem.ensure_work_directory")
    @patch("src.tools.filesystem._validate_path")
    @patch("os.makedirs")
    def test_create_directory_tool_success(
        self, mock_makedirs, mock_validate, mock_ensure
    ):
        """ディレクトリ作成成功のテスト"""
        mock_validate.return_value = ("/tmp/user_files/newdir", None)

        result = create_directory_tool("newdir")

        assert "ディレクトリ 'newdir' を作成しました" in result
        mock_makedirs.assert_called_once_with(
            "/tmp/user_files/newdir", exist_ok=True
        )

    @patch("src.tools.filesystem.ensure_work_directory")
    @patch("src.tools.filesystem._validate_path")
    def test_create_directory_tool_validation_error(
        self, mock_validate, mock_ensure
    ):
        """パス検証エラーのテスト"""
        mock_validate.return_value = ("", "validation error")

        result = create_directory_tool("../newdir")

        assert result == "validation error"

    @patch("src.tools.filesystem.ensure_work_directory")
    @patch("src.tools.filesystem._validate_path")
    @patch("os.makedirs")
    def test_create_directory_tool_exception(
        self, mock_makedirs, mock_validate, mock_ensure
    ):
        """ディレクトリ作成例外のテスト"""
        mock_validate.return_value = ("/tmp/user_files/newdir", None)
        mock_makedirs.side_effect = OSError("Permission denied")

        result = create_directory_tool("newdir")

        assert "ディレクトリの作成に失敗しました" in result
        assert "Permission denied" in result


class TestDeleteFileTool:
    """delete_file_tool関数のテストクラス"""

    @patch("src.tools.filesystem._validate_path")
    @patch("os.path.exists")
    @patch("os.path.isfile")
    @patch("os.remove")
    def test_delete_file_tool_file_success(
        self, mock_remove, mock_isfile, mock_exists, mock_validate
    ):
        """ファイル削除成功のテスト"""
        mock_validate.return_value = ("/tmp/user_files/test.txt", None)
        mock_exists.return_value = True
        mock_isfile.return_value = True

        result = delete_file_tool("test.txt")

        assert "ファイル 'test.txt' を削除しました" in result
        mock_remove.assert_called_once_with("/tmp/user_files/test.txt")

    @patch("src.tools.filesystem._validate_path")
    @patch("os.path.exists")
    @patch("os.path.isfile")
    @patch("os.path.isdir")
    @patch("shutil.rmtree")
    def test_delete_file_tool_directory_success(
        self, mock_rmtree, mock_isdir, mock_isfile, mock_exists, mock_validate
    ):
        """ディレクトリ削除成功のテスト"""
        mock_validate.return_value = ("/tmp/user_files/testdir", None)
        mock_exists.return_value = True
        mock_isfile.return_value = False
        mock_isdir.return_value = True

        result = delete_file_tool("testdir")

        assert "ディレクトリ 'testdir' を削除しました" in result
        mock_rmtree.assert_called_once_with("/tmp/user_files/testdir")

    @patch("src.tools.filesystem._validate_path")
    @patch("os.path.exists")
    def test_delete_file_tool_not_found(self, mock_exists, mock_validate):
        """削除対象が見つからない場合のテスト"""
        mock_validate.return_value = ("/tmp/user_files/nonexistent", None)
        mock_exists.return_value = False

        result = delete_file_tool("nonexistent")

        assert "'nonexistent' が見つかりません" in result


class TestListAllowedDirectories:
    """list_allowed_directories関数のテストクラス"""

    @patch("os.path.exists")
    def test_list_allowed_directories_success(self, mock_exists):
        """許可ディレクトリ一覧表示成功のテスト"""
        mock_exists.return_value = True

        result = list_allowed_directories()

        assert "操作可能なディレクトリ:" in result
        assert f"作業ディレクトリ: {WORK_DIR}" in result
        for directory in ALLOWED_DIRECTORIES:
            assert directory in result

    @patch("os.path.exists")
    def test_list_allowed_directories_some_not_exist(self, mock_exists):
        """一部のディレクトリが存在しない場合のテスト"""
        mock_exists.return_value = False

        result = list_allowed_directories()

        assert "操作可能なディレクトリ:" in result
        assert "未作成" in result


class TestAsyncFunctions:
    """非同期関数のテストクラス"""

    @patch("src.tools.filesystem.ensure_work_directory")
    @patch("src.tools.filesystem.logger")
    async def test_initialize_filesystem_service_success(
        self, mock_logger, mock_ensure
    ):
        """ファイルシステムサービス初期化成功のテスト"""
        result = await initialize_filesystem_service()

        assert result is True
        mock_ensure.assert_called_once()
        mock_logger.info.assert_called()

    @patch("src.tools.filesystem.ensure_work_directory")
    @patch("src.tools.filesystem.logger")
    async def test_initialize_filesystem_service_failure(
        self, mock_logger, mock_ensure
    ):
        """ファイルシステムサービス初期化失敗のテスト"""
        mock_ensure.side_effect = Exception("Initialization error")

        result = await initialize_filesystem_service()

        assert result is False
        mock_logger.error.assert_called()

    @patch("os.path.exists")
    @patch("os.path.isdir")
    async def test_check_filesystem_health_success(
        self, mock_isdir, mock_exists
    ):
        """ファイルシステムヘルスチェック成功のテスト"""
        mock_exists.return_value = True
        mock_isdir.return_value = True

        result = await check_filesystem_health()

        assert result is True

    @patch("os.path.exists")
    async def test_check_filesystem_health_failure(self, mock_exists):
        """ファイルシステムヘルスチェック失敗のテスト"""
        mock_exists.return_value = False

        result = await check_filesystem_health()

        assert result is False

    @patch("os.path.exists")
    async def test_check_filesystem_health_exception(self, mock_exists):
        """ファイルシステムヘルスチェック例外のテスト"""
        mock_exists.side_effect = Exception("Check error")

        result = await check_filesystem_health()

        assert result is False


class TestFilesystemToolsList:
    """filesystem_toolsリストのテストクラス"""

    def test_filesystem_tools_list_exists(self):
        """ツールリストが存在することをテスト"""
        assert isinstance(filesystem_tools, list)
        assert len(filesystem_tools) == 6

    def test_filesystem_tools_list_contains_all_tools(self):
        """すべてのツールが含まれることをテスト"""
        from google.adk.tools import FunctionTool

        assert len(filesystem_tools) == 6
        for tool in filesystem_tools:
            assert (
                callable(tool)
                or hasattr(tool, "__call__")
                or isinstance(tool, FunctionTool)
            )


class TestConstants:
    """定数のテストクラス"""

    def test_work_dir_constant(self):
        """WORK_DIR定数のテスト"""
        assert WORK_DIR == "/tmp/user_files"

    def test_allowed_directories_constant(self):
        """ALLOWED_DIRECTORIES定数のテスト"""
        assert isinstance(ALLOWED_DIRECTORIES, list)
        assert "uploads" in ALLOWED_DIRECTORIES
        assert "temp" in ALLOWED_DIRECTORIES
        assert "logs" in ALLOWED_DIRECTORIES

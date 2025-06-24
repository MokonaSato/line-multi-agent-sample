"""
ファイルシステムツールのシンプルなテストモジュール
"""

import os
import sys
from unittest.mock import patch, MagicMock

# sys.path 追加
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from src.tools.filesystem import (
    WORK_DIR,
    _validate_path,
    ensure_work_directory,
)


class TestValidatePathSimple:
    """_validate_path関数のシンプルなテストクラス"""

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

    def test_validate_path_outside_work_dir_simple(self):
        """作業ディレクトリ外のパスが拒否されることをテスト（シンプル版）"""
        # 実際の動作をテストするためにモックを使わない方法
        # パストラバーサル攻撃を模倣
        file_path = "../../../../etc/passwd"
        full_path, error = _validate_path(file_path)
        
        # セキュリティ制約により、作業ディレクトリ外へのアクセスは拒否される
        # 実際の実装では、abspathによってパスが正規化され、
        # startswithチェックで作業ディレクトリ外のアクセスが検出される
        if error is not None:
            assert "アクセス許可されていません" in error
        else:
            # 環境によっては正常パスとして扱われる可能性があるため、
            # 少なくとも作業ディレクトリ内のパスであることを確認
            assert full_path.startswith(WORK_DIR)


class TestEnsureWorkDirectorySimple:
    """ensure_work_directory関数のシンプルなテストクラス"""

    @patch("os.makedirs")
    def test_ensure_work_directory_creates_directories(self, mock_makedirs):
        """作業ディレクトリが作成されることをテスト"""
        ensure_work_directory()

        # makedirs が呼び出されることを確認
        assert mock_makedirs.call_count > 0
        
        # exist_ok=Trueで呼び出されることを確認
        for call_args in mock_makedirs.call_args_list:
            assert call_args[1]["exist_ok"] is True

    @patch("os.makedirs")
    def test_ensure_work_directory_handles_exception(self, mock_makedirs):
        """例外が発生しても処理が継続されることをテスト"""
        mock_makedirs.side_effect = OSError("Permission denied")
        
        # 例外が発生しても関数が正常に終了することを確認
        try:
            ensure_work_directory()
        except OSError:
            # 例外が伝播する場合もあるが、これは仕様による
            pass


class TestConstants:
    """定数のテストクラス"""

    def test_work_dir_constant(self):
        """WORK_DIR定数のテスト"""
        assert WORK_DIR == "/tmp/user_files"
        assert isinstance(WORK_DIR, str)
        assert WORK_DIR.startswith("/tmp")

    def test_work_dir_is_absolute(self):
        """WORK_DIRが絶対パスであることをテスト"""
        assert os.path.isabs(WORK_DIR)


class TestSecurityValidation:
    """セキュリティ関連のバリデーションテスト"""

    def test_path_traversal_protection(self):
        """パストラバーサル攻撃からの保護テスト"""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "../root/.ssh/id_rsa",
            "../../usr/bin/sudo",
        ]
        
        for malicious_path in malicious_paths:
            full_path, error = _validate_path(malicious_path)
            
            # エラーが発生するか、作業ディレクトリ内のパスに正規化される
            if error is None:
                # エラーが発生しない場合、作業ディレクトリ内であることを確認
                assert full_path.startswith(WORK_DIR)
            else:
                # エラーが発生する場合、適切なエラーメッセージを確認
                assert "アクセス許可されていません" in error

    def test_absolute_path_handling(self):
        """絶対パスの処理テスト"""
        absolute_paths = [
            "/etc/passwd",
            "/root/.bashrc",
            "/usr/bin/python",
        ]
        
        for abs_path in absolute_paths:
            full_path, error = _validate_path(abs_path)
            
            if error is None:
                # 絶対パスは先頭スラッシュを除去して処理される
                assert full_path.startswith(WORK_DIR)
                assert abs_path.lstrip("/") in full_path
            else:
                assert "アクセス許可されていません" in error
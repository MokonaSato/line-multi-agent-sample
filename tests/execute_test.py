#!/usr/bin/env python3
import sys

import pytest

if __name__ == "__main__":
    print("============================================")
    print("| ADK Agent Tools & Agents Test Runner     |")
    print("============================================")

    # テストディレクトリを指定
    test_dir = "tests"

    # コマンドライン引数がある場合は特定のテストを実行
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
        print(f"特定のテストを実行: {test_path}")
        exit_code = pytest.main(["-xvs", test_path])
    else:
        print(f"すべてのテストを実行: {test_dir}")
        exit_code = pytest.main(["-xvs", test_dir])

    # テスト結果を表示
    if exit_code == 0:
        print("\n✅ すべてのテストが成功しました")
    else:
        print(f"\n❌ テストが失敗しました (コード: {exit_code})")

    sys.exit(exit_code)

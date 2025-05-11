import os
import subprocess
import sys


def run_test(test_file, description):
    print(f"\n{'='*50}")
    print(f"実行中: {description}")
    print(f"{'='*50}\n")

    # pythonコマンドでモジュールを呼び出す方式に変更
    result = subprocess.run(
        [sys.executable, "-m", test_file], capture_output=False
    )

    if result.returncode != 0:
        print(f"\n❌ {description}に失敗しました")
        return False
    else:
        print(f"\n✅ {description}が成功しました")
        return True


if __name__ == "__main__":
    # テストディレクトリが存在しない場合は作成
    os.makedirs("tests", exist_ok=True)

    # 実行するテストのリスト - モジュール形式に変更
    tests = [
        ("tests.test_agents", "各エージェントの単体テスト"),
        ("tests.test_integration", "エージェント間の統合テスト"),
        ("tests.simulate_line_request", "LINEボットのシミュレーションテスト"),
    ]

    # 各テストを実行
    failures = 0
    for test_file, description in tests:
        success = run_test(test_file, description)
        if not success:
            failures += 1

    # 結果の表示
    print(f"\n{'='*50}")
    print(f"テスト完了: {len(tests)-failures}/{len(tests)} 成功")
    print(f"{'='*50}\n")

    if failures > 0:
        print(
            "❌ いくつかのテストが失敗しました。詳細はログを確認してください。"
        )
        sys.exit(1)
    else:
        print("✅ すべてのテストが成功しました！")

#!/usr/bin/env python3
"""
プロンプト内容の詳細確認スクリプト
"""

import sys

sys.path.append("/Users/mokonasato/Program/line-multi-agent")

from src.agents.prompt_manager import PromptManager


def main():
    manager = PromptManager()

    print("=== プロンプト内容詳細確認 ===\n")

    try:
        # キャッシュをクリア
        manager.reload_cache()
        prompt = manager.get_prompt("image_analysis")

        print(f"プロンプト全体（{len(prompt)}文字）:")
        print("=" * 50)
        print(prompt)
        print("=" * 50)

        # 含まれる単語を検索
        if "analysis_principle" in prompt:
            print("\n✓ 'analysis_principle' が見つかりました")
        else:
            print("\n✗ 'analysis_principle' が見つかりません")

        if "{{" in prompt:
            print("✓ 変数構文 '{{' が見つかりました")
        else:
            print("✗ 変数構文 '{{' が見つかりません")

        # 変数を検索
        import re

        variables = re.findall(r"\{\{([^}]+)\}\}", prompt)
        if variables:
            print(f"\n変数が見つかりました（{len(variables)}個）:")
            for var in set(variables):
                print(f"  - {var}")
        else:
            print("\n変数が見つかりませんでした")

    except Exception as e:
        print(f"エラー: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

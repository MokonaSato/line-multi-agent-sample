#!/usr/bin/env python3
"""
プロンプトマネージャーのデバッグスクリプト
"""

import os
import sys

sys.path.append("/Users/mokonasato/Program/line-multi-agent")

from src.agents.prompt_manager import PromptManager


def main():
    print("=== PromptManager デバッグ ===")

    manager = PromptManager()

    # テスト1: image_analysis プロンプト
    print("\n1. image_analysis プロンプトのテスト")
    try:
        prompt = manager.get_prompt("image_analysis")
        print(f"✓ 読み込み成功: {len(prompt)} 文字")
        if "analysis_principle" in prompt:
            print("✓ analysis_principle変数が見つかりました")
        else:
            print("✗ analysis_principle変数が見つかりません")
    except Exception as e:
        print(f"✗ エラー: {e}")

    # テスト2: analysis.txt ファイル直接
    print("\n2. analysis.txt ファイル直接テスト")
    try:
        prompt = manager.get_prompt(
            "workflows/recipe/image_extraction/analysis"
        )
        print(f"✓ 読み込み成功: {len(prompt)} 文字")
        if "analysis_principle" in prompt:
            print("✓ analysis_principle変数が見つかりました")
        else:
            print("✗ analysis_principle変数が見つかりません")
            print("プロンプトの最初の200文字:")
            print(prompt[:200])
            print("...")
    except Exception as e:
        print(f"✗ エラー: {e}")

    # テスト3: ファイルの存在確認
    print("\n3. ファイルの存在確認")
    analysis_path = (
        "/Users/mokonasato/Program/line-multi-agent/src/prompts/"
        "workflows/recipe/image_extraction/analysis.txt"
    )
    if os.path.exists(analysis_path):
        print(f"✓ ファイルが存在します: {analysis_path}")
        with open(analysis_path, "r", encoding="utf-8") as f:
            content = f.read()
            if "analysis_principle" in content:
                print("✓ ファイル内にanalysis_principle文字列が存在します")
            else:
                print("✗ ファイル内にanalysis_principle文字列が見つかりません")
    else:
        print(f"✗ ファイルが存在しません: {analysis_path}")


if __name__ == "__main__":
    main()

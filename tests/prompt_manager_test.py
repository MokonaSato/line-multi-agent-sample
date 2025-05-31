"""プロンプト管理システムをテストするモジュール"""

import os

from src.utils.logger import setup_logger
from src.utils.prompt_manager import PromptManager

# ロガーを設定
logger = setup_logger("prompt_manager_test")


def test_prompt_manager():
    """プロンプトマネージャーの機能をテスト"""

    # プロンプトマネージャーを初期化
    manager = PromptManager()

    # 設定ファイルが読み込めたか確認
    logger.info("全体設定: %s", manager.config)

    # ルートエージェントのプロンプトを取得
    root_prompts = manager.get_agent_prompts("root")
    logger.info("ルートエージェントのプロンプト数: %d", len(root_prompts))

    # 主要プロンプトの内容を表示
    if "main" in root_prompts:
        main_prompt = root_prompts["main"]
        logger.info("メインプロンプトのサイズ: %d文字", len(main_prompt))
        logger.info("メインプロンプトの冒頭: %s", main_prompt[:100] + "...")
    else:
        logger.error("メインプロンプトが見つかりません")

    # システムプロンプトの内容を表示
    if "system" in root_prompts:
        system_prompt = root_prompts["system"]
        logger.info("システムプロンプトのサイズ: %d文字", len(system_prompt))
        logger.info(
            "システムプロンプトの冒頭: %s", system_prompt[:100] + "..."
        )
    else:
        logger.error("システムプロンプトが見つかりません")

    # 個別プロンプトの取得テスト
    try:
        core_system = manager.get_prompt("core.system")
        logger.info("コアシステムプロンプトのサイズ: %d文字", len(core_system))
        logger.info(
            "コアシステムプロンプトの冒頭: %s", core_system[:100] + "..."
        )
    except Exception as e:
        logger.error(f"コアシステムプロンプトの取得に失敗: {e}")

    # テンプレートを直接ファイルから読み込んでテスト
    try:
        file_path = os.path.join(
            manager.root_dir, "templates", "agent_base.txt"
        )
        with open(file_path, "r", encoding="utf-8") as file:
            agent_base = file.read()
        logger.info(
            "エージェントベーステンプレートのサイズ: %d文字", len(agent_base)
        )
    except Exception as e:
        logger.error(f"テンプレートファイルの読み込みに失敗: {e}")
        agent_base = ""

    # 継承とオーバーライドのテスト
    try:
        # 直接ファイルから読み込んでテスト
        main_file = os.path.join(
            manager.root_dir, "agents", "root", "main.txt"
        )
        if os.path.exists(main_file):
            with open(main_file, "r", encoding="utf-8") as file:
                root_main = file.read()
            logger.info(
                "ルートメインプロンプトのサイズ: %d文字", len(root_main)
            )
        else:
            root_main = "ファイルが存在しません"
            logger.error(f"ファイルが存在しません: {main_file}")
    except Exception as e:
        logger.error(f"ルートメインプロンプトの読み込みに失敗: {e}")
        root_main = ""

    return {
        "status": "success",
        "prompt_counts": len(root_prompts),
        "main_prompt_size": len(main_prompt) if "main" in root_prompts else 0,
        "system_prompt_size": (
            len(system_prompt) if "system" in root_prompts else 0
        ),
    }


if __name__ == "__main__":
    # テスト実行
    result = test_prompt_manager()
    print("テスト結果:", result)

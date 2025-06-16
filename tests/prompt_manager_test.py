"""プロンプト管理システムをテストするモジュール"""

from src.agents.prompt_manager import PromptManager
from src.utils.logger import setup_logger

# ロガーを設定
logger = setup_logger("prompt_manager_test")


def test_prompt_manager():
    """プロンプトマネージャーの機能をテスト"""

    # プロンプトマネージャーを初期化
    manager = PromptManager()

    # すべてのプロンプトを取得
    prompts = manager.get_all_prompts()
    logger.info("読み込まれたプロンプト数: %d", len(prompts))

    # 主要プロンプトの確認
    main_prompt = ""
    system_prompt = ""

    if "main" in prompts:
        main_prompt = prompts["main"]
        logger.info("メインプロンプトのサイズ: %d文字", len(main_prompt))
        logger.info("メインプロンプトの冒頭: %s", main_prompt[:100] + "...")
    else:
        logger.error("メインプロンプトが見つかりません")

    # システムプロンプトの内容を表示
    if "system" in prompts:
        system_prompt = prompts["system"]
        logger.info("システムプロンプトのサイズ: %d文字", len(system_prompt))
        logger.info(
            "システムプロンプトの冒頭: %s", system_prompt[:100] + "..."
        )
    else:
        logger.error("システムプロンプトが見つかりません")

    # 個別プロンプトの取得テスト
    try:
        test_prompt = manager.get_prompt("main")
        logger.info("個別取得テスト成功: %d文字", len(test_prompt))
    except Exception as e:
        logger.error(f"個別プロンプトの取得に失敗: {e}")

    return {
        "status": "success",
        "prompt_counts": len(prompts),
        "main_prompt_size": len(main_prompt),
        "system_prompt_size": len(system_prompt),
    }


if __name__ == "__main__":
    # テスト実行
    result = test_prompt_manager()
    print("テスト結果:", result)

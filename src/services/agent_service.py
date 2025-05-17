# import re

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from config import GOOGLE_API_KEY  # noqa: F401
from src.agents.calc_agent import calculator_agent
from src.utils.logger import setup_logger

# グローバル変数
session_service = None
runner = None
APP_NAME = "calculator_app"
USER_ID = "user_1"
SESSION_ID = "session_1"

# ロガーの設定
logger = setup_logger("agent_service")


def setup_agent_runner():
    """Agent Runnerを初期化"""
    global session_service, runner

    # セッションサービスの設定
    session_service = InMemorySessionService()

    # Runnerの設定
    runner = Runner(
        agent=calculator_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    return runner


# def extract_numbers_from_text(text):
#     """テキストから数値を抽出する関数
#     複数の形式に対応:
#     - 「10と20」のような日本語表現
#     - 「10 20」のようなスペース区切り
#     - 「10,20」のようなカンマ区切り
#     """
#     # 空白またはカンマで区切られた数字を抽出
#     space_numbers = [int(s) for s in text.split() if s.isdigit()]

#     # 「数字」と「数字」の形式を検出する正規表現
#     ja_pattern = r"(\d+)\s*と\s*(\d+)"
#     ja_matches = re.findall(ja_pattern, text)

#     # 結果をマージ
#     numbers = space_numbers
#     for match in ja_matches:
#         numbers.extend([int(n) for n in match])

#     return numbers


async def call_agent_async(query: str, user_id: str):
    """エージェントにクエリを送信し、レスポンスを返す"""
    global session_service, runner, APP_NAME

    if not runner or not session_service:
        setup_agent_runner()

    # セッションIDをユーザーIDから生成（簡易的な実装）
    session_id = f"session_{user_id}"

    # ユーザーのメッセージをADK形式で準備
    content = types.Content(role="user", parts=[types.Part(text=query)])

    final_response_text = (
        "エージェントは最終応答を生成しませんでした。"  # デフォルト
    )

    # イベントを反復処理して最終応答を見つけます。
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):

        if event.is_final_response():
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate:
                final_response_text = (
                    f"エージェントがエスカレートしました: "
                    f"{event.error_message or '特定のメッセージはありません。'}"
                )
            break
    return final_response_text

    # try:
    #     # メッセージをADK形式に変換
    #     content = types.Content(role="user", parts=[types.Part(text=query)])
    #     final_response_text = "エージェントからの応答がありませんでした。"

    # 簡易的な自然言語解析：入力から数値を抽出
    # extracted_numbers = extract_numbers_from_text(query)

    # 数値が2つ以上あれば、直接計算処理を実行
    #     if len(extracted_numbers) >= 2:
    #         try:
    #             num1, num2 = extracted_numbers[:2]  # 最初の2つの数値を使用
    #             result = add_numbers(num1, num2)
    #             if result["status"] == "success":
    #                 return f"{result['expression']}です。"
    #         except Exception as calc_error:
    #             logger.error(f"数値計算でエラー: {str(calc_error)}")
    #             # 計算エラーの場合はGoogle ADKでの処理に進む

    #     # セッション管理の問題を回避するため、内部変数に直接アクセス
    #     try:
    #         session_service._sessions = {}  # セッションをクリア
    #         session_service._sessions[(APP_NAME, user_id, session_id)] = []
    #         session_service._sessions = {
    #             (APP_NAME, user_id, session_id): []
    #         }  # より直接的なアプローチ
    #         logger.debug(f"セッション作成: {(APP_NAME, user_id, session_id)}")
    #     except Exception as e:
    #         logger.warning(f"セッション作成エラー: {str(e)}")

    #     # Google ADK Runnerを使用した実行を試みる
    #     try:
    #         async for event in runner.run_async(
    #             user_id=user_id, session_id=session_id, new_message=content
    #         ):
    #             if event.is_final_response():
    #                 if event.content and event.content.parts:
    #                     final_response_text = event.content.parts[0].text
    #                     return final_response_text

    #         # イベントループが完了したがfinal_responseがない場合
    #         return final_response_text

    #     except Exception as runner_error:
    #         logger.error(f"Runnerエラー: {str(runner_error)}")
    #         # Runnerがエラーの場合、フォールバックに進む

    #     # ここまで来た場合は、すべての方法が失敗しているので、
    #     # 最終手段として基本的な計算機能を提供
    #     try:
    #         # 数字が見つからない場合や、既に処理済みの場合は説明を返す
    #         if not extracted_numbers or len(extracted_numbers) < 2:
    #             final_response_text = (
    #                 "2つの数字をスペース区切りで送信してください。例: 10 20"
    #             )
    #         else:
    #             # 2つの数字が見つかった場合
    #             num1, num2 = extracted_numbers[:2]
    #             final_response_text = f"{num1} + {num2} = {num1 + num2}です。"
    #     except Exception as fallback_error:
    #         logger.error(f"最終フォールバックエラー: {str(fallback_error)}")
    #         final_response_text = "計算処理中にエラーが発生しました。正しい形式で数字を入力してください。"

    #     return final_response_text

    # except Exception as e:
    #     import traceback

    #     error_details = traceback.format_exc()
    #     logger.error(f"処理エラー: {str(e)}\n{error_details}")
    #     return f"エラーが発生しました: {str(e)}"

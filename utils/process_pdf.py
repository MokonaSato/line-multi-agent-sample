from agents.notion_agent import create_notion_agent
from agents.ocr_agent import create_ocr_agent
from agents.translation_agent import create_translation_agent
from utils.mcp_client import setup_mcp_client


async def process_pdf_url(
    mistral_client,
    notion_client,
    notion_database_id,
    pdf_url: str,
    title: str = "無題の論文",
):
    import logging

    logger = logging.getLogger("main")

    try:
        ocr_agent = create_ocr_agent(mistral_client)
        translation_agent = create_translation_agent(mistral_client)
        notion_agent = create_notion_agent(notion_client, notion_database_id)

        tools, exit_stack = await setup_mcp_client()
        try:
            # ここにコードを追加: toolsがNoneの場合のエラーハンドリング
            if tools is None:
                logger.warning(
                    "MCPツールの初期化に失敗しました。代替手段で処理します。"
                )

            # Step 1: OCRで論文PDFをテキスト抽出
            extracted_text = ""

            # OCRを実行：ツールを直接実行
            for tool in ocr_agent.tools:
                if (
                    hasattr(tool, "function")
                    and tool.function.__name__ == "extract_text_from_pdf"
                ):
                    extracted_text = await tool.function(pdf_url=pdf_url)
                    break

            if not extracted_text:
                return {
                    "status": "error",
                    "message": "テキスト抽出に失敗しました",
                    "notion_url": None,
                }

            # Step 2: 抽出されたテキストを翻訳
            translated_text = ""

            # 翻訳を実行：ツールを直接実行
            for tool in translation_agent.tools:
                if (
                    hasattr(tool, "function")
                    and tool.function.__name__ == "translate_to_japanese"
                ):
                    translated_text = await tool.function(text=extracted_text)
                    break

            if not translated_text:
                return {
                    "status": "error",
                    "message": "翻訳に失敗しました",
                    "notion_url": None,
                }

            # Step 3: 翻訳結果をNotionに保存
            notion_url = ""

            # Notionに保存：ツールを直接実行
            for tool in notion_agent.tools:
                if (
                    hasattr(tool, "function")
                    and tool.function.__name__ == "save_to_notion"
                ):
                    result = await tool.function(
                        title=title,
                        original_text=extracted_text,
                        japanese_text=translated_text,
                        pdf_url=pdf_url,
                    )
                    if isinstance(result, dict) and "notion_url" in result:
                        notion_url = result["notion_url"]
                    break

            if not notion_url:
                return {
                    "status": "error",
                    "message": "Notionへの保存に失敗しました",
                    "notion_url": None,
                }

            return {
                "status": "success",
                "message": "PDF処理が完了しました",
                "notion_url": notion_url,
            }

        finally:
            exit_stack.close()

    except Exception as e:
        logger.error(f"PDF処理中に例外発生: {str(e)}")
        return {
            "status": "error",
            "message": f"処理中にエラーが発生しました: {str(e)}",
            "notion_url": None,
        }

from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool


def create_ocr_agent(mistral_client):
    async def extract_text_from_pdf(pdf_url: str) -> str:
        """PDFからテキストを抽出する"""
        try:
            # 古いAPIを使用（v0.4.2に対応）
            ocr_response = await mistral_client.ocr(
                model="mistral-ocr-latest",
                document_url=pdf_url,
            )

            # レスポンス形式に応じて適切に処理
            extracted_text = ""
            if hasattr(ocr_response, "pages"):
                extracted_text = "\n\n".join(
                    page.markdown for page in ocr_response.pages
                )
            else:
                # 古いバージョンのレスポンス形式に対応
                extracted_text = (
                    ocr_response.text if hasattr(ocr_response, "text") else ""
                )

            return extracted_text
        except Exception as e:
            return f"エラーが発生しました: {str(e)}"

    extract_text_tool = FunctionTool(extract_text_from_pdf)
    return Agent(
        name="OCRエージェント",
        description="PDFからテキストを抽出するエージェント",
        tools=[extract_text_tool],
    )

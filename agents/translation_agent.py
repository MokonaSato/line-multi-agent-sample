from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool


def create_translation_agent(mistral_client):
    async def translate_to_japanese(text: str) -> str:
        """英語テキストを日本語に翻訳する"""
        try:
            content = (
                "あなたは優秀な学術論文翻訳者です。与えられた英語の学術論文を正確に"
                "日本語に翻訳してください。専門用語は適切に翻訳し、必要に応じて英語の"
                "原語も括弧内に残してください。"
            )

            # v0.4.2に対応したAPIを使用
            response = await mistral_client.chat(
                model="mistral-large-latest",
                messages=[
                    {"role": "system", "content": content},
                    {
                        "role": "user",
                        "content": f"以下の論文テキストを日本語に翻訳してください:\n\n{text}",
                    },
                ],
            )

            # レスポンス形式に応じて処理
            if hasattr(response, "choices") and len(response.choices) > 0:
                return response.choices[0].message.content
            else:
                # 古いバージョンのレスポンス形式に対応
                return response.message if hasattr(response, "message") else ""

        except Exception as e:
            return f"翻訳エラーが発生しました: {str(e)}"

    translate_tool = FunctionTool(translate_to_japanese)
    return Agent(
        name="翻訳エージェント",
        description="英語テキストを日本語に翻訳するエージェント",
        tools=[translate_tool],
    )

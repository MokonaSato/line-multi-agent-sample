from typing import List, Optional

from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool


def create_notion_agent(notion_client, notion_database_id):
    async def save_to_notion(
        title: str,
        authors: List[str],
        publication_date: str,
        tags: Optional[List[str]] = None,
        pdf_title: Optional[str] = None,
        pdf_url: Optional[str] = None,
        japanese_text: Optional[str] = None,
        english_text: Optional[str] = None,
    ) -> dict:
        """生成AI関連論文データベースに新しいレコードを保存する

        Args:
            title: 論文のタイトル
            authors: 著者リスト
            publication_date: 発行日 (YYYY-MM-DD形式)
            tags: タグのリスト（「RAG」や「Agent」など）
            pdf_title: PDFファイルの名前
            pdf_url: PDFファイルのURL
            japanese_text: 日本語のマークダウンテキスト
            english_text: 英語のマークダウンテキスト

        Returns:
            保存結果を含む辞書
        """
        try:
            # ページプロパティを作成
            properties = {
                "タイトル": {"title": [{"text": {"content": title}}]},
                "著者": {
                    "rich_text": [{"text": {"content": ", ".join(authors)}}]
                },
                "発行日": {"date": {"start": publication_date}},
                "読了": {"checkbox": False},
            }

            # タグが指定されている場合は追加
            if tags and len(tags) > 0:
                properties["タグ"] = {
                    "multi_select": [{"name": tag} for tag in tags]
                }

            # PDFファイルが指定されている場合は追加
            if pdf_title and pdf_url:
                properties["PDFファイル"] = {
                    "files": [
                        {
                            "name": pdf_title,
                            "type": "external",
                            "external": {"url": pdf_url},
                        }
                    ]
                }

            # 新しいページを作成
            new_page = notion_client.pages.create(
                parent={"database_id": notion_database_id},
                properties=properties,
            )

            # ページIDを取得
            page_id = new_page["id"]

            # 子ブロックの準備
            children = []

            # 日本語テキストがある場合、日本語セクションを追加
            if japanese_text:
                # 見出し追加
                children.append(
                    {
                        "object": "block",
                        "type": "heading_1",
                        "heading_1": {
                            "rich_text": [
                                {"type": "text", "text": {"content": "日本語"}}
                            ]
                        },
                    }
                )

                # 日本語テキストを適切なサイズのチャンクに分割
                japanese_chunks = split_text_into_chunks(
                    japanese_text, max_length=1900
                )

                # 各チャンクをマークダウンコードブロックとして追加
                for chunk in japanese_chunks:
                    children.append(
                        {
                            "object": "block",
                            "type": "code",
                            "code": {
                                "language": "markdown",
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {"content": chunk},
                                    }
                                ],
                            },
                        }
                    )

            # 英語テキストがある場合、英語セクションを追加
            if english_text:
                # 見出し追加
                children.append(
                    {
                        "object": "block",
                        "type": "heading_1",
                        "heading_1": {
                            "rich_text": [
                                {"type": "text", "text": {"content": "英文"}}
                            ]
                        },
                    }
                )

                # 英語テキストを適切なサイズのチャンクに分割
                english_chunks = split_text_into_chunks(
                    english_text, max_length=1900
                )

                # 各チャンクをマークダウンコードブロックとして追加
                for chunk in english_chunks:
                    children.append(
                        {
                            "object": "block",
                            "type": "code",
                            "code": {
                                "language": "markdown",
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {"content": chunk},
                                    }
                                ],
                            },
                        }
                    )

            # 子ブロックがある場合は追加
            if children:
                # 子ブロックの数によってはAPIリクエストを分割する必要がある
                # Notion APIのリクエストサイズ制限に対応するため、分割して追加
                block_chunks = chunk_blocks(children, chunk_size=25)

                # 各チャンクを順番に追加
                for i, block_chunk in enumerate(block_chunks):
                    notion_client.blocks.children.append(
                        block_id=page_id,
                        children=block_chunk,
                    )

            # 成功レスポンスを返す
            page_url = f"https://notion.so/{page_id.replace('-', '')}"
            return {
                "status": "success",
                "message": "Notionデータベースに論文情報を保存しました",
                "notion_url": page_url,
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Notionへの保存に失敗しました: {str(e)}",
                "notion_url": None,
            }

    async def update_notion_page(
        page_id: str,
        title: Optional[str] = None,
        authors: Optional[List[str]] = None,
        publication_date: Optional[str] = None,
        tags: Optional[List[str]] = None,
        read_status: Optional[bool] = None,
        pdf_title: Optional[str] = None,
        pdf_url: Optional[str] = None,
    ) -> dict:
        """既存のNotionページのプロパティを更新する

        Args:
            page_id: 更新するページのID
            title: 新しいタイトル（省略可）
            authors: 新しい著者リスト（省略可）
            publication_date: 新しい発行日（省略可、YYYY-MM-DD形式）
            tags: 新しいタグリスト（省略可）
            read_status: 読了ステータス（省略可）
            pdf_title: 新しいPDFファイル名（省略可）
            pdf_url: 新しいPDF URL（省略可）

        Returns:
            更新結果を含む辞書
        """
        try:
            properties = {}

            if title:
                properties["タイトル"] = {
                    "title": [{"text": {"content": title}}]
                }

            if authors:
                properties["著者"] = {
                    "rich_text": [{"text": {"content": ", ".join(authors)}}]
                }

            if publication_date:
                properties["発行日"] = {"date": {"start": publication_date}}

            if tags is not None:
                properties["タグ"] = {
                    "multi_select": [{"name": tag} for tag in tags]
                }

            if read_status is not None:
                properties["読了"] = {"checkbox": read_status}

            if pdf_title and pdf_url:
                properties["PDFファイル"] = {
                    "files": [
                        {
                            "name": pdf_title,
                            "type": "external",
                            "external": {"url": pdf_url},
                        }
                    ]
                }

            # プロパティを更新
            notion_client.pages.update(
                page_id=page_id,
                properties=properties,
            )

            page_url = f"https://notion.so/{page_id.replace('-', '')}"
            return {
                "status": "success",
                "message": "Notionページを更新しました",
                "notion_url": page_url,
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Notionページの更新に失敗しました: {str(e)}",
                "notion_url": None,
            }

    async def add_markdown_to_page(
        page_id: str,
        japanese_text: Optional[str] = None,
        english_text: Optional[str] = None,
    ) -> dict:
        """既存のNotionページにマークダウンテキストを追加する

        Args:
            page_id: 更新するページのID
            japanese_text: 追加する日本語マークダウンテキスト（省略可）
            english_text: 追加する英語マークダウンテキスト（省略可）

        Returns:
            更新結果を含む辞書
        """
        try:
            children = []

            # 日本語テキストがある場合
            if japanese_text:
                # 見出し追加
                children.append(
                    {
                        "object": "block",
                        "type": "heading_1",
                        "heading_1": {
                            "rich_text": [
                                {"type": "text", "text": {"content": "日本語"}}
                            ]
                        },
                    }
                )

                # 日本語テキストを適切なサイズのチャンクに分割
                japanese_chunks = split_text_into_chunks(
                    japanese_text, max_length=1900
                )

                # 各チャンクをマークダウンコードブロックとして追加
                for chunk in japanese_chunks:
                    children.append(
                        {
                            "object": "block",
                            "type": "code",
                            "code": {
                                "language": "markdown",
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {"content": chunk},
                                    }
                                ],
                            },
                        }
                    )

            # 英語テキストがある場合
            if english_text:
                # 見出し追加
                children.append(
                    {
                        "object": "block",
                        "type": "heading_1",
                        "heading_1": {
                            "rich_text": [
                                {"type": "text", "text": {"content": "英文"}}
                            ]
                        },
                    }
                )

                # 英語テキストを適切なサイズのチャンクに分割
                english_chunks = split_text_into_chunks(
                    english_text, max_length=1900
                )

                # 各チャンクをマークダウンコードブロックとして追加
                for chunk in english_chunks:
                    children.append(
                        {
                            "object": "block",
                            "type": "code",
                            "code": {
                                "language": "markdown",
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {"content": chunk},
                                    }
                                ],
                            },
                        }
                    )

            # 子ブロックがある場合は追加
            if children:
                # 子ブロックの数によってはAPIリクエストを分割する必要がある
                block_chunks = chunk_blocks(children, chunk_size=25)

                # 各チャンクを順番に追加
                for block_chunk in block_chunks:
                    notion_client.blocks.children.append(
                        block_id=page_id,
                        children=block_chunk,
                    )

            page_url = f"https://notion.so/{page_id.replace('-', '')}"
            return {
                "status": "success",
                "message": "マークダウンテキストをNotionページに追加しました",
                "notion_url": page_url,
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"マークダウンテキストの追加に失敗しました: {str(e)}",
                "notion_url": None,
            }

    # テキストを指定の長さで分割するユーティリティ関数
    def split_text_into_chunks(text, max_length=1900):
        """長いテキストを指定の最大長で分割する

        Args:
            text: 分割するテキスト
            max_length: 各チャンクの最大長

        Returns:
            分割されたテキストのリスト
        """
        chunks = []
        # 段落で分割する（改行で区切る）
        paragraphs = text.split("\n\n")

        current_chunk = ""
        for paragraph in paragraphs:
            # この段落を追加すると最大長を超える場合
            if len(current_chunk) + len(paragraph) + 2 > max_length:
                # 現在のチャンクがすでに長い場合
                if len(current_chunk) > 0:
                    chunks.append(current_chunk)
                    current_chunk = ""

                # 単一の段落が最大長を超える場合は、さらに分割
                if len(paragraph) > max_length:
                    # 文で分割
                    sentences = paragraph.replace(". ", ".|").split("|")

                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) + 2 > max_length:
                            if len(current_chunk) > 0:
                                chunks.append(current_chunk)
                                current_chunk = ""

                            # 単一の文が長すぎる場合は、文字数で強制的に分割
                            if len(sentence) > max_length:
                                for i in range(0, len(sentence), max_length):
                                    chunks.append(sentence[i: i + max_length])
                            else:
                                current_chunk = sentence
                        else:
                            if current_chunk:
                                current_chunk += ". " + sentence
                            else:
                                current_chunk = sentence
                else:
                    current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph

        # 最後のチャンクを追加
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    # ブロックを指定のチャンクサイズで分割するユーティリティ関数
    def chunk_blocks(blocks, chunk_size=25):
        """ブロックリストを指定のチャンクサイズで分割する

        Args:
            blocks: ブロックのリスト
            chunk_size: 各チャンクの最大ブロック数

        Returns:
            分割されたブロックのリストのリスト
        """
        return [
            blocks[i: i + chunk_size]
            for i in range(0, len(blocks), chunk_size)
        ]

    # ツールを作成
    save_notion_tool = FunctionTool(save_to_notion)
    update_notion_tool = FunctionTool(update_notion_page)
    add_markdown_tool = FunctionTool(add_markdown_to_page)

    # エージェントを作成して返す
    return Agent(
        name="Notionエージェント",
        description="生成AI関連論文データベースにデータを保存・更新するエージェント",
        tools=[save_notion_tool, update_notion_tool, add_markdown_tool],
    )

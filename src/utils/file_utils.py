def read_prompt_file(file_path):
    """
    プロンプトファイルを読み込む関数

    Args:
        file_path (str): 読み込むファイルのパス

    Returns:
        str: ファイルの内容、エラーの場合は空文字列
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        print(f"プロンプトファイルの読み込みエラー: {e}")
        return ""

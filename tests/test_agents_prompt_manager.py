"""
プロンプトマネージャーのテストモジュール
"""

import os
from unittest.mock import patch

import pytest

from src.agents.prompt_manager import (
    DEFAULT_VARIABLES,
    DEFAULT_VISION_PROMPT,
    PROMPT_FILE_MAPPING,
    PromptManager,
)


class TestPromptManager:
    """PromptManagerクラスのテストクラス"""

    def setup_method(self):
        """各テストメソッドの前に実行される設定"""
        self.prompt_manager = PromptManager()

    def test_init(self):
        """初期化のテスト"""
        assert hasattr(self.prompt_manager, "prompts_dir")
        assert hasattr(self.prompt_manager, "_cache")
        assert isinstance(self.prompt_manager._cache, dict)
        assert len(self.prompt_manager._cache) == 0

    def test_prompts_dir_path(self):
        """プロンプトディレクトリのパスが正しいことをテスト"""
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "src",
            "prompts",
        )
        assert self.prompt_manager.prompts_dir.endswith("prompts")

    def test_extract_yaml_variables_with_yaml(self):
        """YAMLメタデータからの変数抽出テスト"""
        content = """---
variables:
  test_var: test_value
  number_var: 123
  bool_var: true
---
This is the prompt content with {{test_var}}."""

        variables = self.prompt_manager._extract_yaml_variables(content)

        assert variables["test_var"] == "test_value"
        assert variables["number_var"] == 123
        assert variables["bool_var"] == True

    def test_extract_yaml_variables_no_yaml(self):
        """YAMLメタデータがない場合のテスト"""
        content = "This is a simple prompt without YAML metadata."

        variables = self.prompt_manager._extract_yaml_variables(content)

        assert variables == {}

    def test_extract_yaml_variables_invalid_yaml(self):
        """不正なYAMLの場合のテスト"""
        content = """---
invalid: yaml: content: [
---
Prompt content"""

        with patch("src.agents.prompt_manager.logger") as mock_logger:
            variables = self.prompt_manager._extract_yaml_variables(content)

            assert variables == {}
            mock_logger.warning.assert_called_once()

    def test_extract_yaml_variables_no_variables_section(self):
        """variablesセクションがないYAMLのテスト"""
        content = """---
title: Test Prompt
description: This is a test
---
Prompt content"""

        variables = self.prompt_manager._extract_yaml_variables(content)

        assert variables == {}

    def test_replace_simple_variables_simple(self):
        """基本的な変数置換のテスト"""
        prompt = "Hello {{name}}, welcome to {{place}}!"
        variables = {"name": "Alice", "place": "Tokyo"}

        result = self.prompt_manager._replace_simple_variables(
            prompt, variables
        )

        assert result == "Hello Alice, welcome to Tokyo!"

    def test_replace_simple_variables_nested_dict(self):
        """ネストされた辞書変数の置換テスト"""
        prompt = "Config: {{config.host}}:{{config.port}}"
        variables = {"config": {"host": "localhost", "port": "8080"}}

        result = self.prompt_manager._replace_simple_variables(
            prompt, variables
        )

        assert result == "Config: localhost:8080"

    def test_replace_simple_variables_list_converted(self):
        """リスト変数が文字列として変換されることのテスト"""
        prompt = "Items: {{items}}"
        variables = {"items": ["item1", "item2", "item3"]}

        result = self.prompt_manager._replace_simple_variables(
            prompt, variables
        )

        # リストは文字列として変換される
        assert result == "Items: ['item1', 'item2', 'item3']"

    def test_get_prompt_unresolved_warning(self):
        """未解決変数の警告テスト（get_promptレベルでのテスト）"""
        with patch("src.agents.prompt_manager.read_prompt_file") as mock_read_file:
            mock_read_file.return_value = "Hello {{name}}, {{unresolved}} variable here"
            
            with patch("src.agents.prompt_manager.logger") as mock_logger:
                result = self.prompt_manager.get_prompt("root", {"name": "Alice"})
                
                assert "Hello Alice, {{unresolved}} variable here" in result
                mock_logger.warning.assert_called_once()
                args = mock_logger.warning.call_args[0][0]
                assert "未置換の変数が残っています" in args
                assert "unresolved" in args


    def test_clean_content_override(self):
        """overrideブロックの処理テスト"""
        prompt = (
            "Before {{override: test}}Content inside override"
            "{{/override}} After"
        )

        result = self.prompt_manager._clean_content(prompt)

        assert result == "Before Content inside override After"

    def test_clean_content_block(self):
        """blockブロックの処理テスト"""
        prompt = "Before {{block: test}}Content inside block{{/block}} After"

        result = self.prompt_manager._clean_content(prompt)

        assert result == "Before Content inside block After"

    def test_clean_content_yaml_removal(self):
        """YAMLメタデータ削除のテスト"""
        prompt = """---
title: Test
variables:
  test: value
---
This is the actual prompt content."""

        result = self.prompt_manager._clean_content(prompt)

        assert result == "This is the actual prompt content."
        assert "---" not in result
        assert "title:" not in result

    def test_clean_content_multiline_content(self):
        """複数行のブロック処理テスト"""
        prompt = """{{override: test}}
Multi-line
content inside
override block
{{/override}}"""

        result = self.prompt_manager._clean_content(prompt)

        expected = """Multi-line
content inside
override block"""
        assert result.strip() == expected


    @patch("src.agents.prompt_manager.read_prompt_file")
    def test_get_prompt_success(self, mock_read_file):
        """プロンプト取得成功のテスト"""
        mock_read_file.return_value = "Hello {{agent_name}}!"

        result = self.prompt_manager.get_prompt("root")

        assert "Hello root_agent!" == result
        assert "root" in self.prompt_manager._cache

    @patch("src.agents.prompt_manager.read_prompt_file")
    def test_get_prompt_with_custom_variables(self, mock_read_file):
        """カスタム変数を使ったプロンプト取得のテスト"""
        mock_read_file.return_value = "Hello {{custom_name}}!"
        custom_vars = {"custom_name": "Custom Agent"}

        result = self.prompt_manager.get_prompt("root", custom_vars)

        assert "Hello Custom Agent!" == result

    def test_get_prompt_unknown_key(self):
        """未知のキーでのプロンプト取得テスト"""
        with pytest.raises(ValueError) as exc_info:
            self.prompt_manager.get_prompt("unknown_key")

        assert "未知のプロンプトキー: unknown_key" in str(exc_info.value)

    @patch("src.agents.prompt_manager.read_prompt_file")
    def test_get_prompt_file_not_found(self, mock_read_file):
        """ファイルが見つからない場合のテスト"""
        mock_read_file.side_effect = FileNotFoundError("File not found")

        with patch("src.agents.prompt_manager.logger") as mock_logger:
            result = self.prompt_manager.get_prompt("root")

            assert (
                "Error: プロンプトファイル 'root' が見つかりません" in result
            )
            mock_logger.error.assert_called_once()

    @patch("src.agents.prompt_manager.read_prompt_file")
    def test_get_prompt_vision_fallback(self, mock_read_file):
        """visionプロンプトのフォールバックテスト"""
        mock_read_file.side_effect = FileNotFoundError("File not found")

        result = self.prompt_manager.get_prompt("vision")

        assert result == DEFAULT_VISION_PROMPT
        assert "vision" in self.prompt_manager._cache

    @patch("src.agents.prompt_manager.read_prompt_file")
    def test_get_prompt_general_exception(self, mock_read_file):
        """一般的な例外のテスト"""
        mock_read_file.side_effect = Exception("General error")

        with patch("src.agents.prompt_manager.logger") as mock_logger:
            result = self.prompt_manager.get_prompt("root")

            assert "Error loading prompt: General error" in result
            mock_logger.error.assert_called_once()

    @patch("src.agents.prompt_manager.read_prompt_file")
    def test_get_prompt_caching(self, mock_read_file):
        """キャッシュ機能のテスト"""
        mock_read_file.return_value = "Cached prompt"

        # 最初の呼び出し
        result1 = self.prompt_manager.get_prompt("root")
        # 2回目の呼び出し
        result2 = self.prompt_manager.get_prompt("root")

        assert result1 == result2
        assert mock_read_file.call_count == 1  # ファイル読み込みは1回だけ

    @patch("src.agents.prompt_manager.read_prompt_file")
    def test_get_prompt_custom_variables_cache_key(self, mock_read_file):
        """カスタム変数使用時のキャッシュキー生成テスト"""
        mock_read_file.return_value = "Hello {{name}}!"

        # 異なるカスタム変数で2回呼び出し
        result1 = self.prompt_manager.get_prompt("root", {"name": "Alice"})
        result2 = self.prompt_manager.get_prompt("root", {"name": "Bob"})

        assert "Alice" in result1
        assert "Bob" in result2
        assert (
            mock_read_file.call_count == 2
        )  # 異なるキャッシュキーなので2回読み込み

    @patch("src.agents.prompt_manager.read_prompt_file")
    def test_get_all_prompts(self, mock_read_file):
        """全プロンプト取得のテスト"""
        mock_read_file.return_value = "Test prompt"

        result = self.prompt_manager.get_all_prompts()

        assert isinstance(result, dict)
        assert len(result) == len(PROMPT_FILE_MAPPING)
        for key in PROMPT_FILE_MAPPING.keys():
            assert key in result

    @patch("src.agents.prompt_manager.read_prompt_file")
    def test_get_all_prompts_with_errors(self, mock_read_file):
        """エラーを含む全プロンプト取得のテスト"""

        def side_effect(path):
            if "root" in path:
                raise Exception("Test error")
            return "Test prompt"

        mock_read_file.side_effect = side_effect

        with patch("src.agents.prompt_manager.logger") as mock_logger:
            result = self.prompt_manager.get_all_prompts()

            assert isinstance(result, dict)
            # 実装のエラーメッセージに合わせて修正
            assert "Error loading prompt: Test error" in result["root"]
            mock_logger.error.assert_called()

    def test_clear_cache(self):
        """キャッシュクリアのテスト"""
        # キャッシュに何かを追加
        self.prompt_manager._cache["test"] = "cached_value"
        assert len(self.prompt_manager._cache) == 1

        with patch("src.agents.prompt_manager.logger") as mock_logger:
            self.prompt_manager.clear_cache()

            assert len(self.prompt_manager._cache) == 0
            mock_logger.info.assert_called_once_with(
                "プロンプトキャッシュをクリアしました"
            )


    def test_yaml_metadata_with_variables(self):
        """YAMLメタデータを含むプロンプトのテスト"""
        content = """---
title: Test Prompt
variables:
  custom_greeting: "こんにちは"
  custom_name: "テストユーザー"
---
{{custom_greeting}}、{{custom_name}}さん！"""

        with patch(
            "src.agents.prompt_manager.read_prompt_file"
        ) as mock_read_file:
            mock_read_file.return_value = content

            result = self.prompt_manager.get_prompt("root")

            assert "こんにちは、テストユーザーさん！" == result.strip()

    def test_complex_nested_variables(self):
        """複雑なネスト変数のテスト（1階層のみサポート）"""
        prompt = (
            "Server: {{config.host}}:{{config.port}}, "
            "Database: {{db.name}}"
        )
        variables = {
            "config": {"host": "api.example.com", "port": "8080"},
            "db": {"name": "production_db"},
        }

        result = self.prompt_manager._replace_simple_variables(
            prompt, variables
        )

        assert (
            "Server: api.example.com:8080, Database: production_db" == result
        )


class TestPromptManagerConstants:
    """定数のテストクラス"""

    def test_prompt_file_mapping_exists(self):
        """PROMPT_FILE_MAPPINGが存在することをテスト"""
        assert isinstance(PROMPT_FILE_MAPPING, dict)
        assert len(PROMPT_FILE_MAPPING) > 0

    def test_prompt_file_mapping_keys(self):
        """期待されるキーが存在することをテスト"""
        expected_keys = [
            "root",
            "calculator",
            "filesystem",
            "notion",
            "vision",
            "recipe_extraction",
            "data_transformation",
            "recipe_notion",
        ]

        for key in expected_keys:
            assert key in PROMPT_FILE_MAPPING

    def test_default_variables_exists(self):
        """DEFAULT_VARIABLESが存在することをテスト"""
        assert isinstance(DEFAULT_VARIABLES, dict)
        assert len(DEFAULT_VARIABLES) > 0

    def test_default_variables_basic_keys(self):
        """基本的な変数キーが存在することをテスト"""
        expected_keys = [
            "agent_name",
            "basic_principles",
            "available_tools",
            "recipe_database_id",
            "required_tools",
        ]

        for key in expected_keys:
            assert key in DEFAULT_VARIABLES

    def test_default_vision_prompt_exists(self):
        """DEFAULT_VISION_PROMPTが存在することをテスト"""
        assert isinstance(DEFAULT_VISION_PROMPT, str)
        assert len(DEFAULT_VISION_PROMPT.strip()) > 0
        assert "画像認識の専門家" in DEFAULT_VISION_PROMPT

    def test_get_all_prompts_with_read_error(self):
        """get_all_prompts でファイル読み込みエラーが発生した場合のテスト"""
        
        prompt_manager = PromptManager()
        
        # PROMPT_FILE_MAPPINGに存在しないプロンプトキーを一時的に追加
        original_mapping = dict(PROMPT_FILE_MAPPING)
        PROMPT_FILE_MAPPING['error_test'] = 'nonexistent.path'
        
        try:
            with patch('src.agents.prompt_manager.read_prompt_file') as mock_read_file:
                def side_effect(path):
                    if 'nonexistent.path' in path:
                        raise Exception("File read error")
                    return "valid content"
                
                mock_read_file.side_effect = side_effect
                
                prompts = prompt_manager.get_all_prompts()
                
                # エラーが発生したプロンプトはError loading prompt:で始まる
                assert 'error_test' in prompts
                assert prompts['error_test'].startswith("Error loading prompt:")
                assert "File read error" in prompts['error_test']
        finally:
            # 元の状態に戻す
            PROMPT_FILE_MAPPING.clear()
            PROMPT_FILE_MAPPING.update(original_mapping)

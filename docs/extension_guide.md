# 拡張ガイド：エージェントとツールの追加方法

このドキュメントでは、プロジェクトに新しいエージェントやツールを追加する方法について説明します。このプロジェクトでは、ルートエージェント（Root Agent）が中心となり、様々なサブエージェントを管理・調整する階層的なアーキテクチャを採用しています。

## 目次

1. [エージェント追加の基本手順](#エージェント追加の基本手順)
2. [ツール追加の基本手順](#ツール追加の基本手順)
3. [プロンプトの管理と追加](#プロンプトの管理と追加)
4. [新機能のテスト方法](#新機能のテスト方法)
5. [実装例](#実装例)

## エージェント追加の基本手順

新しいエージェントをルートエージェントのサブエージェントとして追加するには、以下の手順に従ってください。

### 1. エージェント生成メソッドの追加

`google.adk.agents`を使用して新しいサブエージェントを作成します。具体的には、`AgentFactory`クラスに新しいエージェント生成メソッドを追加します。

```python
# src/agents/agent_factory.py に追加
from google.adk.agents import Agent
from src.tools.custom_tools import custom_tools_list  # 作成したツールをインポート

def create_custom_agent(self) -> Agent:
    """カスタムエージェントを作成"""
    # 設定を取得
    cfg = self.config["custom"]

    # エージェントを作成して返す
    return Agent(
        name=cfg["name"],
        model=cfg["model"],
        description=cfg["description"],
        instruction=self.prompts[cfg["prompt_key"]],
        tools=custom_tools_list,  # 専用ツールリスト
    )
```

### 2. エージェント設定の追加

`src/agents/config.py` の `AGENT_CONFIG` ディクショナリにエージェント設定を追加します。

```python
# src/agents/config.py のAGENT_CONFIGディクショナリに追加
AGENT_CONFIG = {
    # 既存の設定...

    # カスタムエージェント設定
    "custom": {
        "name": "custom_agent",
        "model": DEFAULT_MODEL,  # もしくは特定のモデルを指定
        "prompt_key": "custom",
        "description": "特定の機能に特化したカスタムエージェント",
    },

    # 既存の設定...
}
```

### 3. create_all_standard_agents メソッドの更新

`AgentFactory`クラスの`create_all_standard_agents`メソッドを更新して、新しいエージェントを登録します。このメソッドはルートエージェントが使用するすべてのサブエージェントを生成します。

```python
# src/agents/agent_factory.py の create_all_standard_agents メソッドを更新
def create_all_standard_agents(self) -> Dict[str, Agent]:
    """すべての標準エージェントを一括で作成"""
    logger.info("すべての標準エージェントを作成します")

    # 既存のエージェント生成...
    calc_agent = self.create_calculator_agent()
    google_search_agent = self.create_google_search_agent()

    # カスタムエージェントを追加
    custom_agent = self.create_custom_agent()

    # エージェントをディクショナリにまとめて返却
    return {
        "calc_agent": calc_agent,
        "google_search_agent": google_search_agent,
        "custom_agent": custom_agent,
        # 他のエージェント...
    }
```

### 4. プロンプトテンプレートの追加

新しいエージェント用のプロンプトテンプレートを `src/prompts/agents/custom/` ディレクトリに作成し、`src/prompts/config.yaml` に登録します。

```
# src/prompts/agents/custom/system.txt の例
あなたは特定の機能に特化したカスタムエージェントです。
与えられた情報に基づいて、[機能の詳細な説明]を行います。
```

```yaml
# src/prompts/config.yaml に追加
prompts:
  # 既存の定義...

  # カスタムエージェント用プロンプト
  custom: agents/custom/system.txt

  # 既存の定義...
```

## ツール追加の基本手順

プロジェクトに新しいツールを追加するには、以下の手順に従ってください：

### 1. ツール関数の作成

`src/tools/` ディレクトリに新しいツールを定義するファイルを作成します。
このプロジェクトでは、`google.adk.tools`の`tool`デコレータを使用してツールを実装します。

```python
# src/tools/custom_tools.py
from google.adk.tools import tool
from typing import Dict, Any

@tool("custom_search", description="特定のキーワードで情報を検索するツール")
async def custom_search(query: str) -> Dict[str, Any]:
    """カスタム検索を実行する

    Args:
        query: 検索クエリ文字列

    Returns:
        検索結果の辞書
    """
    # ツールの機能実装
    # 例: APIリクエスト、データベース検索など

    # サンプル結果
    result = {
        "query": query,
        "results": [
            {"title": "結果1", "content": "内容1"},
            {"title": "結果2", "content": "内容2"}
        ]
    }
    return result

# 複数のツールをリストに登録
custom_tools_list = [custom_search]
```

### 2. ツールの統合方法

作成したツールをシステムに統合するには、以下の 2 つの方法があります：

#### 方法 1: ルートエージェントに直接ツールを登録

ルートエージェントが直接使用できるように、`create_root_agent`メソッドでツールを登録します。

```python
# src/agents/agent_factory.py の create_root_agent メソッドを更新
from src.tools.custom_tools import custom_search  # または custom_tools_list

def create_root_agent(self, sub_agents: Dict[str, Agent]) -> LlmAgent:
    """ルートエージェントを作成"""
    cfg = self.config["root"]

    return LlmAgent(
        model=cfg["model"],
        name=cfg["name"],
        instruction=self.prompts[cfg["prompt_key"]],
        description=cfg["description"],
        tools=[
            agent_tool.AgentTool(agent=sub_agents["google_search_agent"]),
            # 新しいツールを追加
            custom_search,  # 単一のツールを追加
            # または
            # *custom_tools_list,  # ツールリスト全体を追加
        ],
        sub_agents=[
            sub_agents["calc_agent"],
            # 他のサブエージェント
        ],
    )
```

#### 方法 2: 専用のサブエージェントを作成してツールを追加

特定の機能に特化したサブエージェントを作成し、そのエージェントにツールを追加する方法です。これは機能を論理的に分離する場合に適しています。

```python
# src/agents/agent_factory.py に追加
from google.adk.agents import Agent
from src.tools.custom_tools import custom_tools_list

def create_custom_agent(self) -> Agent:
    """カスタム機能エージェントを作成"""
    cfg = self.config["custom"]

    return Agent(
        name=cfg["name"],
        model=cfg["model"],
        description=cfg["description"],
        instruction=self.prompts[cfg["prompt_key"]],
        tools=custom_tools_list,  # 専用ツールリスト
    )
```

## プロンプトの管理と追加

新しいエージェントやツール用のプロンプトを追加するには：

1. `src/prompts/agents/[agent_name]/` ディレクトリを作成します
2. 必要なプロンプトテンプレートを YAML または JSON ファイルとして追加します
3. `src/agents/prompt_manager.py` を使用してプロンプトをロードします

```python
# プロンプトのロード例
from src.utils.prompt_manager import PromptManager

prompt_manager = PromptManager()
prompt_template = prompt_manager.get_prompt("agents/custom/main_prompt.yaml")
```

## 新機能のテスト方法

新しく追加したエージェントやツールをテストするには：

1. `tests/agents/` または `tests/tools/` ディレクトリにテストファイルを作成します
2. pytest を使用してテストを実行します

```python
# tests/agents/test_custom_agent.py
import pytest
from src.agents.custom_agent import CustomAgent

async def test_custom_agent_action():
    agent = CustomAgent()
    result = await agent.act({}, {})
    assert result is not None
    # 他のアサーション...
```

## 実装例

以下では、より詳細なエージェントとツールの実装例を紹介します。

### 天気情報エージェントの基本実装例

以下に、ルートエージェントのサブエージェントとして天気情報を提供するエージェントの実装例を示します。

#### 1. 天気情報ツールの実装

まず、天気情報を取得するツールを実装します：

```python
# src/tools/weather_tools.py
from google.adk.tools import tool
from typing import Dict, Any

@tool("get_weather", description="指定された都市の天気情報を取得")
async def get_weather(city: str) -> Dict[str, Any]:
    """都市の天気情報を取得

    Args:
        city: 都市名

    Returns:
        天気情報を含む辞書
    """
    # 実際には外部APIを呼び出す処理を実装
    # この例ではダミーデータを返します
    weather_data = {
        "city": city,
        "temperature": 25.5,
        "condition": "晴れ",
        "humidity": 60,
        "wind_speed": 5.2
    }
    return weather_data

@tool("get_forecast", description="天気予報を取得")
async def get_forecast(city: str, days: int = 3) -> Dict[str, Any]:
    """都市の天気予報を取得

    Args:
        city: 都市名
        days: 予報日数（デフォルト: 3）

    Returns:
        天気予報を含む辞書
    """
    # 実装例（ダミーデータ）
    return {
        "city": city,
        "forecast": [
            {"date": "2025-06-01", "condition": "晴れ", "max_temp": 28, "min_temp": 18},
            {"date": "2025-06-02", "condition": "曇り", "max_temp": 25, "min_temp": 17},
            {"date": "2025-06-03", "condition": "雨", "max_temp": 22, "min_temp": 16}
        ]
    }

# ツールをリストとして登録
weather_tools_list = [get_weather, get_forecast]
```

#### 2. エージェントファクトリーに天気エージェント生成メソッドを追加

```python
# src/agents/agent_factory.py に追加
from google.adk.agents import Agent
from src.tools.weather_tools import weather_tools_list

def create_weather_agent(self) -> Agent:
    """天気情報エージェントを作成"""
    # 設定を取得
    cfg = self.config["weather"]

    # エージェントを作成して返す
    return Agent(
        name=cfg["name"],
        model=cfg["model"],
        description=cfg["description"],
        instruction=self.prompts[cfg["prompt_key"]],
        tools=weather_tools_list,
    )
```

#### 3. 天気エージェント用の設定を追加

```python
# src/agents/config.py のAGENT_CONFIGに追加
AGENT_CONFIG = {
    # 既存の設定...

    # 天気エージェント設定
    "weather": {
        "name": "weather_agent",
        "model": DEFAULT_MODEL,
        "prompt_key": "weather",
        "description": "現在の天気情報と天気予報を提供する天気エージェント",
    },

    # 既存の設定...
}
```

#### 4. 天気エージェントをサブエージェントとして登録

```python
# src/agents/agent_factory.py の create_all_standard_agents メソッドを更新
def create_all_standard_agents(self) -> Dict[str, Agent]:
    """すべての標準エージェントを一括で作成"""
    logger.info("すべての標準エージェントを作成します")

    # 各エージェントを作成
    calc_agent = self.create_calculator_agent()
    google_search_agent = self.create_google_search_agent()
    # 天気エージェントを作成
    weather_agent = self.create_weather_agent()

    # 他の既存エージェント...

    # エージェントをディクショナリにまとめて返却
    return {
        "calc_agent": calc_agent,
        "google_search_agent": google_search_agent,
        "weather_agent": weather_agent,
        # 他のエージェント...
    }
```

#### 5. 天気エージェント用のプロンプトを作成

```
# src/prompts/agents/weather/system.txt
あなたは天気情報を提供する専門エージェントです。
ユーザーからの質問に基づいて、都市の現在の天気情報や天気予報を提供してください。
常に簡潔で正確な情報を提供し、必要に応じて適切なアドバイスを加えてください。

あなたが使えるツール:
- get_weather: 指定された都市の現在の天気情報を取得
- get_forecast: 指定された都市の天気予報を取得（デフォルト3日間）
```

#### 6. プロンプト設定に天気エージェント用のプロンプトを登録

```yaml
# src/prompts/config.yaml に追加
prompts:
  # 既存のプロンプト設定...

  # 天気エージェント用プロンプト
  weather: agents/weather/system.txt

  # 他のプロンプト設定...
```

#### 7. テストの作成

```python
# tests/agents/test_weather_agent.py
import pytest
from unittest.mock import patch, AsyncMock
from src.agents.agent_factory import AgentFactory

@pytest.mark.asyncio
async def test_weather_agent():
    """天気エージェントのテスト"""
    # モック準備
    mock_weather_data = {
        "city": "東京",
        "temperature": 25.5,
        "condition": "晴れ",
        "humidity": 60,
        "wind_speed": 5.2
    }

    # AgentFactoryを初期化（実際のテストではより適切に初期化）
    factory = AgentFactory({}, {
        "weather": {"name": "weather_agent", "model": "test-model", "prompt_key": "weather", "description": "test"}
    })

    # ツールをモック化
    with patch("google.adk.agents.Agent", autospec=True) as MockAgent:
        # AgentインスタンスのモックとActの設定
        mock_agent = MockAgent.return_value
        mock_agent.act = AsyncMock(return_value="東京の天気: 晴れ、気温25.5°C")

        # エージェントを作成（実装に合わせて調整）
        agent = factory.create_weather_agent()

        # 呼び出しをテスト
        result = await agent.act({"input": "東京の天気は？"}, {})

        # 検証
        assert "東京の天気" in result
        assert "25.5°C" in result
```

### 外部 API と連携するサブエージェントのより高度な実装例

ここでは、外部 API を利用したより実践的な天気情報サブエージェントの実装例を紹介します。

#### 1. 外部 API と連携するツールの実装

```python
# src/tools/advanced_weather_tools.py
from google.adk.tools import tool
import aiohttp
import os
from typing import Dict, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)

# APIキーを環境変数から取得
API_KEY = os.environ.get("WEATHER_API_KEY", "")
BASE_URL = "https://api.weatherapi.com/v1"

@tool("advanced_weather", description="指定された場所の詳細な天気情報を取得")
async def get_advanced_weather(location: str) -> Dict[str, Any]:
    """詳細な天気情報を取得するツール

    Args:
        location: 場所（都市名など）

    Returns:
        詳細な天気情報
    """
    if not API_KEY:
        logger.warning("WEATHER_API_KEY環境変数が設定されていません")
        return {"error": "APIキーが設定されていません"}

    url = f"{BASE_URL}/current.json"
    params = {
        "key": API_KEY,
        "q": location,
        "lang": "ja"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "location": data["location"]["name"],
                        "region": data["location"]["region"],
                        "country": data["location"]["country"],
                        "temperature": data["current"]["temp_c"],
                        "condition": data["current"]["condition"]["text"],
                        "humidity": data["current"]["humidity"],
                        "wind_speed": data["current"]["wind_kph"],
                        "wind_direction": data["current"]["wind_dir"],
                        "pressure": data["current"]["pressure_mb"],
                        "precipitation": data["current"]["precip_mm"],
                        "cloud": data["current"]["cloud"],
                        "uv": data["current"]["uv"],
                        "last_updated": data["current"]["last_updated"]
                    }
                else:
                    error_data = await response.text()
                    logger.error(f"Weather API error: {response.status}, {error_data}")
                    return {"error": f"API error: {response.status}"}
    except Exception as e:
        logger.error(f"天気情報取得エラー: {str(e)}")
        return {"error": f"天気情報を取得できませんでした: {str(e)}"}

@tool("advanced_forecast", description="指定された場所の天気予報を取得")
async def get_advanced_forecast(location: str, days: int = 3) -> Dict[str, Any]:
    """詳細な天気予報を取得するツール

    Args:
        location: 場所（都市名など）
        days: 予報日数（1-10）

    Returns:
        天気予報データ
    """
    if not API_KEY:
        logger.warning("WEATHER_API_KEY環境変数が設定されていません")
        return {"error": "APIキーが設定されていません"}

    url = f"{BASE_URL}/forecast.json"
    params = {
        "key": API_KEY,
        "q": location,
        "days": min(days, 10),  # APIの制限内に収める
        "lang": "ja"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    forecast_days = []
                    for day_data in data["forecast"]["forecastday"]:
                        forecast_days.append({
                            "date": day_data["date"],
                            "max_temp": day_data["day"]["maxtemp_c"],
                            "min_temp": day_data["day"]["mintemp_c"],
                            "condition": day_data["day"]["condition"]["text"],
                            "chance_of_rain": day_data["day"]["daily_chance_of_rain"],
                            "sunrise": day_data["astro"]["sunrise"],
                            "sunset": day_data["astro"]["sunset"]
                        })

                    return {
                        "location": data["location"]["name"],
                        "country": data["location"]["country"],
                        "forecast": forecast_days
                    }
                else:
                    error_data = await response.text()
                    logger.error(f"Weather API error: {response.status}, {error_data}")
                    return {"error": f"API error: {response.status}"}
    except Exception as e:
        logger.error(f"天気予報取得エラー: {str(e)}")
        return {"error": f"天気予報を取得できませんでした: {str(e)}"}

# ツールリストにまとめる
advanced_weather_tools = [get_advanced_weather, get_advanced_forecast]
```

#### 2. エージェントファクトリーに高度な天気エージェント生成メソッドを追加

```python
# src/agents/agent_factory.py に追加
from google.adk.agents import LlmAgent
from src.tools.advanced_weather_tools import advanced_weather_tools

def create_advanced_weather_agent(self) -> LlmAgent:
    """高度な天気情報エージェントを作成"""
    # 設定を取得
    cfg = self.config["advanced_weather"]

    # エージェントを作成して返す
    return LlmAgent(
        name=cfg["name"],
        model=cfg["model"],
        instruction=self.prompts[cfg["prompt_key"]],
        description=cfg["description"],
        tools=advanced_weather_tools,
    )
```

#### 3. 高度な天気エージェントの設定を追加

```python
# src/agents/config.py の AGENT_CONFIG に追加
AGENT_CONFIG = {
    # 既存の設定...

    # 高度な天気エージェント設定
    "advanced_weather": {
        "name": "advanced_weather_agent",
        "model": DEFAULT_MODEL,  # またはより高性能なモデル
        "prompt_key": "advanced_weather",
        "description": "詳細な天気情報と予報を提供する高度な天気情報エージェント",
    },

    # 既存の設定...
}
```

#### 4. プロンプトファイルの作成

```
# src/prompts/agents/advanced_weather/system.txt
あなたは高度な天気情報を提供する専門エージェントです。
ユーザーの質問に応じて、現在の天気情報や天気予報を提供し、役立つアドバイスを提供してください。

使用できるツール:
- advanced_weather: 指定した場所の現在の天気情報を取得します。詳細なデータが含まれます。
- advanced_forecast: 指定した場所の天気予報を取得します。日数を指定できます。

ユーザーの質問から場所や日数を抽出し、適切なツールを使用して情報を提供してください。
データに基づいたアドバイス（暑さ対策、寒さ対策、雨への準備など）も含めると良いでしょう。
常に簡潔で正確な情報を提供し、視覚的に見やすいフォーマットで回答を整形してください。
```

#### 5. プロンプト設定ファイルを更新

```yaml
# src/prompts/config.yaml に追加
prompts:
  # 既存のプロンプト...

  # 高度な天気エージェント用プロンプト
  advanced_weather: agents/advanced_weather/system.txt

  # 既存のプロンプト...
```

#### 6. create_all_standard_agents メソッドを更新して高度な天気エージェントを登録

```python
# src/agents/agent_factory.py の create_all_standard_agents メソッドを更新
def create_all_standard_agents(self) -> Dict[str, Agent]:
    """すべての標準エージェントを一括で作成"""
    logger.info("すべての標準エージェントを作成します")

    # 各エージェントを作成
    calc_agent = self.create_calculator_agent()
    url_workflow_agent = self.create_url_recipe_workflow_agent()
    google_search_agent = self.create_google_search_agent()

    # 高度な天気エージェントを追加
    advanced_weather_agent = self.create_advanced_weather_agent()

    # エージェントをディクショナリにまとめて返却
    return {
        "calc_agent": calc_agent,
        "url_recipe_workflow_agent": url_workflow_agent,
        "google_search_agent": google_search_agent,
        "advanced_weather_agent": advanced_weather_agent,
        # 他のエージェント...
    }
```

#### 6. 複雑なテスト例

```python
# tests/agents/test_advanced_weather_agent.py
import pytest
from unittest.mock import patch, AsyncMock
from src.agents.agent_factory import AgentFactory
from src.tools.advanced_weather_tools import get_advanced_weather, get_advanced_forecast
from google.adk.agents import LlmAgent

class TestAdvancedWeatherAgent:
    """高度な天気エージェントのテスト"""

    @pytest.fixture
    def mock_factory(self):
        """AgentFactoryのモック"""
        # 設定とプロンプトを準備
        prompts = {
            "advanced_weather": "天気情報を提供するエージェントです。"
        }
        config = {
            "advanced_weather": {
                "name": "test_weather_agent",
                "model": "test-model",
                "prompt_key": "advanced_weather",
                "description": "テスト用天気エージェント"
            }
        }
        return AgentFactory(prompts, config)

    @pytest.fixture
    def mock_weather_data(self):
        """天気データのモック"""
        return {
            "location": "東京",
            "region": "東京都",
            "country": "日本",
            "temperature": 22.5,
            "condition": "晴れ",
            "humidity": 65,
            "wind_speed": 12.5,
            "wind_direction": "北東",
            "pressure": 1012,
            "precipitation": 0.0,
            "cloud": 15,
            "uv": 4,
            "last_updated": "2025-05-30 14:30"
        }

    @pytest.fixture
    def mock_forecast_data(self):
        """天気予報データのモック"""
        return {
            "location": "大阪",
            "country": "日本",
            "forecast": [
                {
                    "date": "2025-05-31",
                    "max_temp": 24.5,
                    "min_temp": 18.2,
                    "condition": "晴れ",
                    "chance_of_rain": 10,
                    "sunrise": "05:32 AM",
                    "sunset": "18:15 PM"
                },
                {
                    "date": "2025-06-01",
                    "max_temp": 26.0,
                    "min_temp": 19.5,
                    "condition": "晴れ時々曇り",
                    "chance_of_rain": 20,
                    "sunrise": "05:31 AM",
                    "sunset": "18:16 PM"
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_agent_creation(self, mock_factory):
        """エージェント作成のテスト"""
        with patch('google.adk.agents.LlmAgent', autospec=True) as MockAgent:
            # エージェント作成
            mock_factory.create_advanced_weather_agent()

            # 検証
            MockAgent.assert_called_once()
            args, kwargs = MockAgent.call_args
            assert kwargs["name"] == "test_weather_agent"
            assert kwargs["model"] == "test-model"
            assert kwargs["description"] == "テスト用天気エージェント"

    @pytest.mark.asyncio
    async def test_agent_tools(self, mock_factory, mock_weather_data, mock_forecast_data):
        """エージェントのツール機能テスト"""
        # ツールをモック化
        with patch('src.tools.advanced_weather_tools.get_advanced_weather',
                  AsyncMock(return_value=mock_weather_data)) as mock_current:
            with patch('src.tools.advanced_weather_tools.get_advanced_forecast',
                      AsyncMock(return_value=mock_forecast_data)) as mock_forecast:

                # LLMAgentをモック（実際の動作に合わせて調整）
                with patch('google.adk.agents.LlmAgent', autospec=True) as MockAgent:
                    mock_agent = MockAgent.return_value
                    mock_agent.generate_response = AsyncMock(return_value={
                        "output": "東京の天気は晴れ、気温は22.5°Cです。"
                    })

                    # エージェント作成
                    agent = mock_factory.create_advanced_weather_agent()

                    # 現在の天気を確認
                    context = {"input": "東京の天気は？"}
                    response = await agent.generate_response(context)

                    # 検証
                    assert isinstance(response, dict)
                    assert "output" in response
                    assert "東京" in response["output"]
```

### ルートエージェントとサブエージェントの連携と統合例

このプロジェクトのアーキテクチャでは、ルートエージェントがすべてのサブエージェントを管理し、ユーザーの質問に応じて適切なサブエージェントに処理を委任します。以下は FastAPI との統合例です。

#### 1. ルートエージェントの役割と動作

ルートエージェントは、サブエージェントの集合を管理し、ユーザーからの入力に基づいて最適なサブエージェントに処理を委任します：

```python
# src/agents/agent_factory.py のルートエージェント作成部分（抜粋）
def create_root_agent(self, sub_agents: Dict[str, Agent]) -> LlmAgent:
    """ルートエージェントを作成"""
    cfg = self.config["root"]

    return LlmAgent(
        model=cfg["model"],
        name=cfg["name"],
        instruction=self.prompts[cfg["prompt_key"]],
        description=cfg["description"],
        tools=[
            # ツールとして直接アクセスできるエージェント
            agent_tool.AgentTool(agent=sub_agents["google_search_agent"]),
        ],
        sub_agents=[
            # サブエージェントとして管理されるエージェント
            sub_agents["calc_agent"],
            sub_agents["url_recipe_workflow_agent"],
            sub_agents["image_recipe_workflow_agent"],
            sub_agents["notion_agent"],
            sub_agents["vision_agent"],
            # 新しく追加したエージェント
            sub_agents["weather_agent"],  # 追加した天気エージェント
        ],
    )
```

#### 2. FastAPI を使ったエージェントの統合例

```python
# src/services/agent_service/executor.py
from src.agents.root_agent import create_agent
from src.services.agent_service.session_manager import SessionManager
from src.utils.logger import get_logger

logger = get_logger(__name__)
session_manager = SessionManager()

async def process_user_message(user_input: str, session_id: str = None):
    """ユーザーメッセージを処理し、適切なエージェントの応答を返す

    Args:
        user_input: ユーザー入力
        session_id: セッションID（存在しない場合は新規作成）

    Returns:
        エージェントの応答
    """
    try:
        # セッション管理
        if not session_id:
            session_id = session_manager.create_session()
        elif not session_manager.session_exists(session_id):
            session_id = session_manager.create_session()
            logger.warning(f"不明なセッション{session_id}が要求されました。新規セッションを作成します。")

        # ルートエージェントを取得
        root_agent, exit_stack = await create_agent()

        # コンテキスト準備（セッション履歴を含める）
        history = session_manager.get_history(session_id)
        context = {"history": history, "session_id": session_id}

        # エージェント実行
        logger.info(f"セッション {session_id}: メッセージ処理 - '{user_input}'")
        response = await root_agent.generate_response({
            "input": user_input,
            "context": context
        })

        # 履歴更新
        session_manager.add_to_history(session_id, "user", user_input)
        session_manager.add_to_history(session_id, "agent", response["output"])

        return {
            "response": response["output"],
            "session_id": session_id,
            "context": {
                "selected_agent": response.get("selected_agent", "root"),
                "tools_used": response.get("tools_used", [])
            }
        }

    except Exception as e:
        logger.error(f"メッセージ処理エラー: {str(e)}")
        return {
            "error": f"メッセージの処理中にエラーが発生しました: {str(e)}",
            "session_id": session_id
        }
```

#### 3. FastAPI エンドポイントの作成

```python
# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from src.services.agent_service.executor import process_user_message

app = FastAPI()

class UserMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

@app.post("/api/chat")
async def chat_endpoint(request: UserMessage):
    """チャットAPIエンドポイント"""
    try:
        result = await process_user_message(request.message, request.session_id)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"処理エラー: {str(e)}")
```

#### 4. サブエージェント間の連携と処理の流れ

1. ユーザーが質問を送信します（例：「東京の天気は？」）
2. FastAPI エンドポイントがリクエストを受け取ります
3. `process_user_message`関数がルートエージェントを呼び出します
4. ルートエージェントはプロンプトに基づいて質問を分析し、天気に関する質問だと判断します
5. ルートエージェントは天気サブエージェントに処理を委任します
6. 天気サブエージェントは専用ツールを使って天気情報を取得します
7. 取得した情報をもとに回答を生成し、ルートエージェントに返します
8. ルートエージェントは必要に応じて回答を調整し、ユーザーに返信します

このような階層的なアーキテクチャにより、各サブエージェントは特定の機能に特化し、ルートエージェントは全体の調整を担当します。新しい機能を追加する場合は、専用のサブエージェントとツールを実装し、ルートエージェントに登録するだけで、システム全体に機能を追加できます。

このアーキテクチャの利点は、モジュール性の高さ、再利用性、保守性の良さにあります。それぞれのエージェントとツールは独立して開発・テストでき、システム全体の複雑性を管理しやすくなります。

# LINE Multi-Agent Function Call Flow

このドキュメントは、LINE Multi-Agentアプリケーションにおける関数呼び出し関係をMermaidフローチャートで可視化したものです。

## 全体アーキテクチャ フロー

```mermaid
flowchart TD
    subgraph "main.py - FastAPI Application"
        callback[callback/1] --> process_events[process_events/1]
        lifespan[lifespan/1] --> init_agent[init_agent/1]
        lifespan --> init_filesystem[initialize_filesystem_service/1]
        lifespan --> check_mcp[check_mcp_server_health/1]
        health_check[health_check/1] --> check_fs_health[check_filesystem_health/1]
        health_check --> check_mcp_health[check_mcp_server_health/1]
    end

    subgraph "agent_service_impl.py - Agent Service Layer"
        init_agent --> as_init[AgentService.init_agent/1]
        as_init --> create_agent[create_agent/1]
        call_agent_async[call_agent_async/1] --> execute_response[execute_and_get_response/1]
        call_agent_with_image[call_agent_with_image_async/1] --> execute_response
        execute_response --> execute_attempt[_execute_single_attempt/1]
        execute_attempt --> token_limit_handler[_handle_token_limit_error/1]
        cleanup_resources[cleanup_resources/1] --> cleanup_exit[cleanup_exit_stack/1]
    end

    subgraph "line_service/handler.py - LINE Event Handler"
        process_events --> handle_event[handle_event/1]
        handle_event --> handle_text[handle_text_message/1]
        handle_event --> handle_image[handle_image_message/1]
        handle_text --> call_agent_async
        handle_image --> call_agent_with_image
        handle_text --> reply_text[reply_text/1]
        handle_image --> reply_text
    end

    subgraph "line_service/client.py - LINE Client"
        process_events --> parse_events[parse_webhook_events/1]
        reply_text --> create_api[create_api_client/1]
        handle_image --> get_content[get_message_content/1]
    end

    subgraph "agents/root_agent.py - Root Agent"
        create_agent --> create_prompt_mgr[PromptManager/1]
        create_agent --> create_factory[AgentFactory/1]
        create_agent --> create_all_agents[create_all_standard_agents/1]
        create_agent --> create_root[create_root_agent/1]
    end

    subgraph "agents/agent_factory.py - Agent Factory"
        create_factory --> get_mcp_tools[get_tools_async/1]
        create_all_agents --> create_calc[create_calculator_agent/1]
        create_all_agents --> create_search[create_google_search_agent/1]
        create_all_agents --> create_notion[create_notion_agent/1]
        create_all_agents --> create_vision[create_vision_agent/1]
        create_all_agents --> create_fs[create_filesystem_agent/1]
        create_all_agents --> create_url_pipeline[create_url_recipe_pipeline/1]
        create_all_agents --> create_image_pipeline[create_image_recipe_pipeline/1]
        create_all_agents --> create_url_workflow[create_url_recipe_workflow_agent/1]
        create_all_agents --> create_image_workflow[create_image_recipe_workflow_agent/1]
        create_root --> get_prompt[get_prompt/1]
    end

    subgraph "agents/prompt_manager.py - Prompt Manager"
        create_prompt_mgr --> get_all_prompts[get_all_prompts/1]
        get_prompt --> read_prompt[read_prompt_file/1]
        get_prompt --> substitute_vars[_replace_variables_with_dict/1]
        get_prompt --> process_template[_process_template_blocks/1]
    end

    subgraph "tools/mcp_integration.py - MCP Integration"
        get_mcp_tools --> check_mcp_enabled[MCP_ENABLED/1]
        check_mcp --> get_available_tools[get_available_mcp_tools/1]
        get_mcp_tools --> create_toolset[MCPToolset.from_server/1]
        check_mcp_health --> notion_health[check_notion_mcp_health/1]
        check_mcp_health --> fs_health[check_filesystem_mcp_health/1]
    end

    subgraph "tools/calculator_tools.py - Calculator Tools"
        create_calc --> calc_tools[calculator_tools/1]
        calc_tools --> add_nums[add_numbers/1]
        calc_tools --> subtract_nums[subtract_numbers/1]
        calc_tools --> multiply_nums[multiply_nums/1]
        calc_tools --> divide_nums[divide_numbers/1]
    end

    subgraph "tools/web_tools.py - Web Tools"
        create_search --> fetch_web[fetch_web_content/1]
        fetch_web --> http_get[requests.get/1]
        fetch_web --> parse_html[BeautifulSoup/1]
    end

    subgraph "tools/mcp_servers - MCP Only"
        create_notion --> notion_mcp[MCPToolset Notion/1]
        create_fs --> filesystem_mcp[MCPToolset Filesystem/1]
        notion_mcp --> mcp_create_page[notion_create_page_mcp/1]
        notion_mcp --> mcp_query_db[notion_query_database_mcp/1]
        filesystem_mcp --> mcp_read_file[filesystem_read_file_mcp/1]
        filesystem_mcp --> mcp_write_file[filesystem_write_file_mcp/1]
    end

    subgraph "tools/filesystem.py - Filesystem Tools"
        init_filesystem --> ensure_work_dir[ensure_work_directory/1]
        check_fs_health --> validate_work_dir[validate work directory/1]
        create_fs --> fs_tools[filesystem_tools/1]
        fs_tools --> read_file[read_file_tool/1]
        fs_tools --> write_file[write_file_tool/1]
        fs_tools --> list_dir[list_directory_tool/1]
    end

    subgraph "utils/logger.py - Logging"
        setup_logger[setup_logger/1] --> configure_log[configure logging/1]
    end

    subgraph "utils/file_utils.py - File Utils"
        read_prompt --> read_file_util[read_prompt_file/1]
    end

    %% Style the subgraphs
    classDef mainApp fill:#e1f5fe
    classDef service fill:#f3e5f5
    classDef agent fill:#e8f5e8
    classDef tool fill:#fff3e0
    classDef mcp fill:#e8f0fe
    classDef util fill:#fafafa

    class callback,process_events,lifespan,health_check mainApp
    class init_agent,call_agent_async,call_agent_with_image,execute_attempt,cleanup_resources service
    class create_agent,create_factory,create_all_agents,get_prompt,create_prompt_mgr agent
    class calc_tools,fetch_web,fs_tools tool
    class notion_mcp,filesystem_mcp,mcp_create_page,mcp_query_db,mcp_read_file,mcp_write_file mcp
    class setup_logger,read_prompt util
```

## 主要な処理フロー

### 1. LINE メッセージ処理フロー

```mermaid
sequenceDiagram
    participant LINE as LINE Platform
    participant Main as main.py
    participant Handler as line_service/handler.py
    participant Client as line_service/client.py
    participant Service as agent_service_impl.py
    participant Agent as Root Agent

    LINE->>Main: POST /callback
    Main->>Main: process_events()
    Main->>Client: parse_webhook_events()
    Client-->>Main: parsed events
    Main->>Handler: handle_event()
    
    alt Text Message
        Handler->>Service: call_agent_async()
    else Image Message
        Handler->>Service: call_agent_with_image_async()
    end
    
    Service->>Service: execute_and_get_response()
    Service->>Service: _execute_single_attempt()
    
    alt Token Limit Error
        Service->>Service: _handle_token_limit_error()
        Service->>Service: retry with reduced content
    end
    
    Service->>Agent: execute via Google ADK
    Agent-->>Service: response
    Service-->>Handler: response
    Handler->>Client: reply_text()
    Client->>LINE: send reply
```

### 2. エージェント初期化フロー

```mermaid
sequenceDiagram
    participant Main as main.py
    participant Service as agent_service_impl.py
    participant Root as root_agent.py
    participant Factory as agent_factory.py
    participant PromptMgr as prompt_manager.py
    participant MCP as mcp_integration.py

    Main->>Service: init_agent()
    Service->>Root: create_agent()
    Root->>PromptMgr: PromptManager()
    PromptMgr->>PromptMgr: get_all_prompts()
    Root->>Factory: AgentFactory()
    Factory->>MCP: get_tools_async()
    MCP->>MCP: check_mcp_server_health()
    MCP-->>Factory: MCP tools
    Factory->>Factory: create_all_standard_agents()
    Factory->>Root: create_root_agent()
    Root-->>Service: agent + exit_stack
    Service-->>Main: initialization complete
```

### 3. プロンプト処理フロー

```mermaid
flowchart LR
    subgraph "agents/prompt_manager.py"
        A[get_prompt] --> B[check_cache]
        B --> C[read_prompt_file]
        C --> D[extract_file_variables]
        D --> E[_replace_variables_with_dict]
        E --> F[_process_template_blocks]
        F --> G[cache_result]
        G --> H[return processed prompt]
    end
    
    subgraph "utils/file_utils.py"
        C --> I[read_prompt_file]
    end
```

### 4. エラーハンドリングと再試行フロー

```mermaid
flowchart TD
    A[execute_and_get_response] --> B[_execute_single_attempt]
    B --> C{Success?}
    C -->|Yes| D[Return response]
    C -->|No| E{Token limit error?}
    E -->|Yes| F[_handle_token_limit_error]
    F --> G[Reduce message size]
    G --> H{Retry count < MAX?}
    H -->|Yes| B
    H -->|No| I[Return shortened response]
    E -->|No| J{Other error?}
    J -->|Yes| K[Log error]
    K --> L[Return error response]
    J -->|No| B
```

### 5. MCP ツール統合フロー

```mermaid
flowchart TD
    subgraph "MCP Integration"
        A[get_tools_async] --> B{MCP_ENABLED?}
        B -->|Yes| C[get_available_mcp_tools]
        C --> D[notion MCP server]
        C --> E[filesystem MCP server]
        D --> F[check_notion_mcp_health]
        E --> G[check_filesystem_mcp_health]
        F --> H[MCPToolset.from_server]
        G --> H
        H --> I[integrate into agents]
        B -->|No| J[skip MCP integration]
    end
```

## ファイル別主要関数一覧

### main.py
- `lifespan()` - FastAPIライフサイクル管理
- `process_events()` - LINEイベント処理
- `callback()` - LINE Webhookエンドポイント
- `health_check()` - ヘルスチェック

### agent_service_impl.py
- `init_agent()` - エージェント初期化
- `call_agent_async()` - テキストメッセージ処理
- `call_agent_with_image_async()` - 画像メッセージ処理
- `execute_and_get_response()` - メイン実行ロジック（リトライ付き）
- `_execute_single_attempt()` - 単一実行試行
- `_handle_token_limit_error()` - トークン制限エラー処理
- `cleanup_resources()` - リソースクリーンアップ

### line_service/handler.py
- `handle_event()` - LINEイベントハンドラー
- `handle_text_message()` - テキストメッセージ処理
- `handle_image_message()` - 画像メッセージ処理

### line_service/client.py
- `parse_webhook_events()` - Webhookイベント解析
- `reply_text()` - テキスト返信
- `get_message_content()` - メッセージ内容取得

### agents/root_agent.py
- `create_agent()` - ルートエージェント作成

### agents/agent_factory.py
- `create_all_standard_agents()` - 全エージェント作成
- `create_calculator_agent()` - 計算エージェント作成
- `create_notion_agent()` - Notionエージェント作成（MCP必須）
- `create_vision_agent()` - ビジョンエージェント作成
- `create_filesystem_agent()` - ファイルシステムエージェント作成（MCP必須）
- `create_url_recipe_pipeline()` - URLレシピパイプライン作成（MCP必須）
- `create_image_recipe_pipeline()` - 画像レシピパイプライン作成（MCP必須）
- `create_url_recipe_workflow_agent()` - URLレシピワークフローエージェント作成
- `create_image_recipe_workflow_agent()` - 画像レシピワークフローエージェント作成

### agents/prompt_manager.py
- `get_prompt()` - プロンプト取得（キャッシュ付き）
- `get_all_prompts()` - 全プロンプト読み込み
- `_replace_variables_with_dict()` - 変数置換
- `_process_template_blocks()` - テンプレートブロック処理

### tools/mcp_integration.py
- `get_tools_async()` - MCPツール取得
- `check_mcp_server_health()` - MCPサーバーヘルスチェック
- `get_available_mcp_tools()` - 利用可能MCPツール取得

### tools/mcp_integration.py
- **get_tools_async()**: MCPサーバーからのツール取得
- **check_mcp_server_health()**: MCPサーバーヘルスチェック  
- **MCPToolset.from_server()**: MCP接続とツールセット作成

### tools/filesystem.py
- `initialize_filesystem_service()` - ファイルシステム初期化
- `check_filesystem_health()` - ファイルシステムヘルスチェック
- `filesystem_tools` - ファイル操作ツール群

## アーキテクチャの特徴

### 1. MCP完全統合
- Notion操作はMCPサーバー経由のみ（フォールバック廃止）
- Filesystem操作もMCP統合
- 従来のNotion APIツールは完全削除

### 2. エラー耐性
- トークン制限エラーの自動処理
- リトライメカニズム
- 堅牢なエラーハンドリング
- MCP接続必須による一貫性保証

### 3. モジュラー設計
- 各エージェントが独立したツールセットを持つ
- MCP統合による外部サービス連携
- プロンプト管理の集約化

### 4. スケーラビリティ
- エージェントファクトリーパターン
- 設定駆動のエージェント作成
- ツールの動的統合

### 5. 運用の簡素化
- APIキー管理不要（MCPサーバー経由）
- 統一されたツールインターフェース
- メンテナンス性の向上

このフローチャートは、LINE Multi-Agentアプリケーションの最新のアーキテクチャと関数呼び出し関係を表しており、システム全体の理解とメンテナンスに役立ちます。
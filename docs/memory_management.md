# LINE Multi-Agent メモリ管理システム

## 概要

このドキュメントは、LINE Multi-Agentプロジェクトにおけるメモリ管理システムの現在の実装、制約、および改善案について説明します。

## 現在のメモリ管理アーキテクチャ

### システム構成

LINE Multi-Agentは**完全にインメモリベース**のセッション管理を採用しており、永続的な会話履歴の保存は行っていません。

```
[LINE Webhook] → [FastAPI] → [AgentService] → [InMemorySessionService] → [Google ADK Session]
                                                     ↓
                                            [最大3会話ターンのメモリ内保存]
```

### 主要コンポーネント

#### 1. セッション管理 (`src/services/agent_service_impl.py`)

**実装詳細:**
```python
# Google ADKのインメモリセッションサービスを使用
self.session_service = InMemorySessionService()

# セッション作成パターン
session_id = f"session_{user_id}"

# 制約設定
MAX_SESSION_HISTORY_SIZE = 3  # 最大3会話ターンまで保持
```

**主な機能:**
- ユーザーごとの独立したセッション作成
- 会話履歴の自動切り詰め（3ターン超過時）
- アプリケーション再起動時の完全リセット

#### 2. 履歴制限メカニズム

```python
def _limit_session_history(self, session: Session) -> None:
    """セッション履歴を最大サイズに制限"""
    if session.history and len(session.history) > MAX_SESSION_HISTORY_SIZE:
        session.history = session.history[-MAX_SESSION_HISTORY_SIZE:]
```

**動作原理:**
- 新しい会話が追加されるたびに履歴サイズをチェック
- 3ターンを超えた場合、古い履歴から自動削除
- FIFO（First In, First Out）方式で履歴管理

#### 3. トークン制限対応

```python
# トークン制限時の履歴削減設定
TOKEN_LIMIT_REDUCTION_RATIO = 0.8  # 80%に削減
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 2
```

**エラー処理フロー:**
1. API呼び出しでトークン制限エラー検出
2. セッション履歴を80%に削減
3. 最大3回まで再試行
4. 失敗時は短縮レスポンスを生成

## 会話履歴が保存されない原因

### 根本原因

**InMemorySessionService の使用:**
- Google ADKの `InMemorySessionService()` は一時的なメモリ内保存のみ
- アプリケーション再起動やコンテナの停止で全データ消失
- Cloud Run環境では特に影響が大きい

### 具体的な制約

1. **再起動時のデータ消失**
   - Cloud Runの自動スケーリングでコンテナが停止
   - サーバーメンテナンス時の全履歴消失
   - 開発時の再起動での履歴リセット

2. **会話ターン制限**
   - 最大3ターンまでの履歴保持
   - 長期的なコンテキスト追跡不可
   - 複雑なタスクでの文脈喪失

3. **マルチインスタンス問題**
   - Cloud Runの複数インスタンス間でセッション共有不可
   - ロードバランシング時の会話継続性問題

## 現在のメモリ使用パターン

### ファイル別実装状況

| ファイル | 役割 | メモリ関連機能 |
|---------|------|---------------|
| `agent_service_impl.py` | メインセッション管理 | InMemorySessionService, 履歴制限 |
| `line_service/handler.py` | LINE Webhook処理 | ユーザーID抽出, メッセージ転送 |
| `root_agent.py` | エージェント調整 | セッション状態参照 |
| `mcp_integration.py` | 外部サービス連携 | Notion接続（会話履歴には非使用） |

### メモリ関連定数

```python
# セッション設定
MAX_SESSION_HISTORY_SIZE = 3
MIN_FINAL_RESPONSE_LENGTH = 50

# エラー処理設定
TOKEN_LIMIT_REDUCTION_RATIO = 0.8
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 2

# 環境変数
MCP_ENABLED = True  # MCPサーバー使用（Notion等）
```

## 現在のアーキテクチャの利点と欠点

### 利点

1. **シンプルな実装**
   - 外部データベース不要
   - 設定が最小限
   - 高速な読み書き

2. **Cloud Run適合性**
   - ステートレス設計
   - 自動スケーリング対応
   - リソース効率性

3. **メモリ効率**
   - 履歴サイズ制限によるメモリ保護
   - 自動ガベージコレクション

### 欠点

1. **永続性の欠如**
   - 再起動時の全データ消失
   - 長期的なユーザー履歴なし
   - 学習データの蓄積不可

2. **コンテキスト制限**
   - 3ターンのみの短期記憶
   - 複雑なタスクでの文脈喪失
   - ユーザーの好み学習不可

3. **分析・改善の困難**
   - 会話データの分析不可
   - システム改善のためのデータ不足
   - ユーザー行動パターン把握不可

## 改善提案

### 短期改善案（即座に実装可能）

#### 1. メモリサイズ調整
```python
# config.py に追加
MAX_SESSION_HISTORY_SIZE = int(os.getenv("MAX_SESSION_HISTORY", "5"))
```

#### 2. セッション情報のログ出力
```python
# 会話終了時にセッション情報をログに記録
logger.info(f"Session ended: user={user_id}, turns={len(session.history)}")
```

### 中期改善案（開発工数: 1-2週間）

#### 1. Redis によるセッション永続化

**実装概要:**
```python
# requirements.txt に追加
redis==4.5.4

# 新しいセッションサービス実装
class RedisSessionService:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.ttl = 86400 * 7  # 7日間保持
    
    def get_session(self, session_id: str) -> Session:
        data = self.redis.get(f"session:{session_id}")
        return Session.from_json(data) if data else Session()
    
    def save_session(self, session_id: str, session: Session):
        self.redis.setex(
            f"session:{session_id}", 
            self.ttl, 
            session.to_json()
        )
```

**メリット:**
- アプリケーション再起動での履歴保持
- 複数インスタンス間でのセッション共有
- TTL（Time To Live）による自動削除

#### 2. 環境変数による切り替え機能

```python
# config.py
MEMORY_BACKEND = os.getenv("MEMORY_BACKEND", "inmemory")  # "inmemory" or "redis"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# agent_service_impl.py
def create_session_service():
    if MEMORY_BACKEND == "redis":
        return RedisSessionService(REDIS_URL)
    return InMemorySessionService()
```

### 長期改善案（開発工数: 3-4週間）

#### 1. データベースによる完全な履歴管理

**アーキテクチャ:**
```sql
-- 会話履歴テーブル設計
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    session_id VARCHAR(100) NOT NULL,
    message_type ENUM('user', 'assistant') NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX idx_conversations_user_session ON conversations(user_id, session_id);
CREATE INDEX idx_conversations_timestamp ON conversations(timestamp);
```

**実装例:**
```python
# models/conversation.py
class ConversationStore:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
    
    def save_message(self, user_id: str, session_id: str, 
                    message_type: str, content: str, metadata: dict = None):
        # データベースに会話履歴を永続保存
        pass
    
    def get_recent_messages(self, user_id: str, limit: int = 10):
        # 最近の会話履歴を取得
        pass
    
    def get_user_summary(self, user_id: str):
        # ユーザーの会話パターン分析
        pass
```

#### 2. 分析・監視機能

```python
# analytics/conversation_analytics.py
class ConversationAnalytics:
    def generate_usage_report(self, start_date: date, end_date: date):
        # 期間別使用統計
        pass
    
    def identify_common_queries(self):
        # よくある質問の特定
        pass
    
    def measure_agent_performance(self):
        # エージェントの性能分析
        pass
```

## 実装優先度

### Phase 1: 緊急対応（1週間以内）
- [ ] セッション履歴サイズの環境変数化
- [ ] セッション情報のログ出力強化
- [ ] メモリ使用量監視の追加

### Phase 2: 基本的な永続化（2-3週間）
- [ ] Redis セッションサービスの実装
- [ ] 環境変数による backends 切り替え
- [ ] Cloud Run での Redis 接続設定

### Phase 3: 完全な履歴管理（1-2ヶ月）
- [ ] PostgreSQL データベース設計
- [ ] 会話履歴の完全永続化
- [ ] ユーザー分析機能の実装
- [ ] データ移行ツールの開発

## Cloud Run での考慮事項

### Redis 使用時の設定

```yaml
# cloudbuild.yaml への追加
env:
  - name: MEMORY_BACKEND
    value: "redis"
  - name: REDIS_URL
    value: "redis://[REDIS_INSTANCE_IP]:6379"
```

### データベース使用時の設定

```yaml
# Cloud SQL 接続設定
env:
  - name: DB_URL
    value: "postgresql://user:pass@[CLOUD_SQL_IP]/dbname"
  - name: CLOUD_SQL_CONNECTION_NAME
    value: "[PROJECT_ID]:[REGION]:[INSTANCE_NAME]"
```

## モニタリング指標

### 現在追跡すべき指標

1. **メモリ使用量**
   - セッション数
   - 履歴ターン数
   - メモリ消費量

2. **性能指標**
   - 応答時間
   - セッション作成頻度
   - 履歴切り詰め発生回数

3. **エラー指標**
   - トークン制限エラー頻度
   - セッション作成失敗率
   - 履歴取得エラー

### Redis 導入後の追加指標

1. **Redis 接続状況**
   - 接続エラー率
   - レスポンス時間
   - キー数と使用メモリ

2. **セッション永続性**
   - TTL 期限切れ率
   - セッション復元成功率

## 結論

現在のシステムは**完全にインメモリベース**であり、会話履歴の永続保存は行われていません。これは設計上の選択であり、Cloud Run の stateless な特性に適合していますが、ユーザー体験の向上には改善が必要です。

**即座に対応すべき課題:**
1. 3ターン制限の緩和（環境変数化）
2. セッション情報の可視化
3. メモリ使用量の監視

**長期的な改善方向:**
1. Redis による中間的な永続化
2. データベースによる完全な履歴管理
3. ユーザー行動分析機能の追加

これらの改善により、より良いユーザー体験と運用性を実現できます。
#!/bin/bash
# deploy.sh - Cloud Run MCP Sidecar デプロイメントスクリプト

set -e

# 設定値
PROJECT_ID=${PROJECT_ID:-"gen-lang-client-0075173573"}
REGION=${REGION:-"asia-northeast1"}
SERVICE_NAME=${SERVICE_NAME:-"line-multi-agent"}

# 色付きログ出力
log_info() {
    echo -e "\033[36m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[32m[SUCCESS]\033[0m $1"
}

log_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

# プロジェクトIDの確認
if [ "$PROJECT_ID" = "your-project-id" ]; then
    log_error "PROJECT_ID を設定してください"
    echo "例: export PROJECT_ID=my-project-123"
    exit 1
fi

log_info "デプロイメント開始"
log_info "Project ID: $PROJECT_ID"
log_info "Region: $REGION"
log_info "Service Name: $SERVICE_NAME"

# 1. gcloud の設定確認
log_info "Google Cloud 設定を確認中..."
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION

# 2. 必要なAPIの有効化
log_info "必要なAPIを有効化中..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# 3. Cloud Build の実行権限確認
log_info "Cloud Build の権限を確認中..."
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

# Cloud Build サービスアカウントに必要な権限を付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/run.admin" \
    --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/iam.serviceAccountUser" \
    --quiet

log_success "Cloud Build 権限設定完了"

# 4. Cloud Run サービスアカウントの確認
log_info "Cloud Run サービスアカウントを確認中..."
SA_NAME="line-multi-agent-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# サービスアカウントが存在しない場合は作成
if ! gcloud iam service-accounts describe $SA_EMAIL --quiet 2>/dev/null; then
    gcloud iam service-accounts create $SA_NAME \
        --display-name="Line Multi Agent Service Account" \
        --description="Service account for Line Multi Agent with MCP support"
    
    log_success "サービスアカウント作成完了: $SA_EMAIL"
else
    log_info "サービスアカウント既存: $SA_EMAIL"
fi

# 5. 環境変数の設定
log_info "環境変数を設定中..."
if [ ! -f ".env" ]; then
    log_error ".env ファイルが見つかりません"
    log_info "以下の形式で .env ファイルを作成してください："
    echo "GOOGLE_API_KEY=your-google-api-key"
    echo "NOTION_TOKEN=your-notion-token"
    echo "LINE_CHANNEL_ACCESS_TOKEN=your-line-channel-access-token"
    echo "LINE_CHANNEL_SECRET=your-line-channel-secret"
    exit 1
fi

# .env ファイルを読み込み（Cloud Build で使用）
source .env
log_success "環境変数読み込み完了"

# 6. Cloud Build のトリガー
log_info "Cloud Build を実行中..."
if [ -f "cloudbuild.yaml" ] && [ -f ".env" ]; then
    # 環境変数を Cloud Build に渡す（substitutions形式）
    source .env
    gcloud builds submit \
        --config=cloudbuild.yaml \
        --substitutions="_REGION=$REGION,_SERVICE_NAME=$SERVICE_NAME,_GOOGLE_API_KEY=$GOOGLE_API_KEY,_NOTION_TOKEN=$NOTION_TOKEN,_LINE_CHANNEL_ACCESS_TOKEN=$LINE_CHANNEL_ACCESS_TOKEN,_LINE_CHANNEL_SECRET=$LINE_CHANNEL_SECRET" \
        .
    
    if [ $? -eq 0 ]; then
        log_success "Cloud Build 完了"
    else
        log_error "Cloud Build 失敗"
        exit 1
    fi
else
    log_error "cloudbuild.yaml または .env が見つかりません"
    exit 1
fi

# 7. デプロイメント状態の確認
log_info "デプロイメント状態を確認中..."
sleep 10

# サービスの状態確認
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --format="value(status.url)")

if [ -n "$SERVICE_URL" ]; then
    log_success "Cloud Run サービス デプロイ完了"
    log_success "サービス URL: $SERVICE_URL"
    
    # ヘルスチェック
    log_info "ヘルスチェック実行中..."
    if curl -f "${SERVICE_URL}/health" -s > /dev/null; then
        log_success "ヘルスチェック成功"
        
        # MCP ステータス確認
        log_info "MCP ステータス確認中..."
        if curl -f "${SERVICE_URL}/mcp/status" -s > /dev/null; then
            log_success "MCP サイドカー正常動作中"
        else
            log_error "MCP サイドカーに問題があります"
        fi
    else
        log_error "ヘルスチェック失敗 - サービスの起動を待っています..."
    fi
else
    log_error "サービス URL を取得できませんでした"
    exit 1
fi

# 8. IAM の最終設定
log_info "IAM 設定を完了中..."
gcloud run services add-iam-policy-binding $SERVICE_NAME \
    --region=$REGION \
    --member="allUsers" \
    --role="roles/run.invoker" \
    --quiet

log_success "すべてのデプロイメント処理が完了しました"
log_info "サービス URL: $SERVICE_URL"
log_info "ヘルスチェック: ${SERVICE_URL}/health"
log_info "MCP ステータス: ${SERVICE_URL}/mcp/status"

echo ""
log_info "次のステップ:"
echo "1. LINE Webhook URL を設定: ${SERVICE_URL}/callback"
echo "2. 動作確認: ${SERVICE_URL}/health にアクセス"
echo "3. MCP 機能テスト: curl ${SERVICE_URL}/mcp/status"
#!/bin/bash
# monitor.sh - Cloud Run MCP Sidecar 監視スクリプト

set -e

# 設定値
PROJECT_ID=${PROJECT_ID:-"your-project-id"}
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

# サービス URL を取得
get_service_url() {
    gcloud run services describe $SERVICE_NAME \
        --region=$REGION \
        --format="value(status.url)" 2>/dev/null
}

# ヘルスチェック実行
health_check() {
    local service_url=$(get_service_url)
    if [ -z "$service_url" ]; then
        log_error "サービス URL を取得できません"
        return 1
    fi
    
    log_info "ヘルスチェック実行中: ${service_url}/health"
    
    local response
    response=$(curl -s -w "%{http_code}" "${service_url}/health" --max-time 10)
    local http_code="${response: -3}"
    local body="${response%???}"
    
    if [ "$http_code" = "200" ]; then
        log_success "メインアプリケーション: 正常"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
        return 0
    else
        log_error "メインアプリケーション: 異常 (HTTP $http_code)"
        echo "$body"
        return 1
    fi
}

# MCP ステータス確認
mcp_status_check() {
    local service_url=$(get_service_url)
    if [ -z "$service_url" ]; then
        log_error "サービス URL を取得できません"
        return 1
    fi
    
    log_info "MCP ステータス確認中: ${service_url}/mcp/status"
    
    local response
    response=$(curl -s -w "%{http_code}" "${service_url}/mcp/status" --max-time 10)
    local http_code="${response: -3}"
    local body="${response%???}"
    
    if [ "$http_code" = "200" ]; then
        log_success "MCP サイドカー: 正常"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
        return 0
    else
        log_error "MCP サイドカー: 異常 (HTTP $http_code)"
        echo "$body"
        return 1
    fi
}

# Cloud Run サービス情報表示
service_info() {
    log_info "Cloud Run サービス情報:"
    gcloud run services describe $SERVICE_NAME \
        --region=$REGION \
        --format="table(
            metadata.name,
            status.url,
            status.conditions[0].type,
            status.conditions[0].status,
            spec.template.metadata.annotations.'run.googleapis.com/cpu',
            spec.template.metadata.annotations.'run.googleapis.com/memory'
        )"
}

# ログ表示
show_logs() {
    local lines=${1:-50}
    log_info "最新 $lines 行のログを表示:"
    
    gcloud logging read "
        resource.type=cloud_run_revision 
        AND resource.labels.service_name=$SERVICE_NAME 
        AND resource.labels.location=$REGION
    " \
        --limit=$lines \
        --format="table(
            timestamp,
            resource.labels.revision_name,
            severity,
            textPayload
        )" \
        --order=desc
}

# 使用方法表示
usage() {
    echo "使用方法: $0 [コマンド]"
    echo ""
    echo "利用可能なコマンド:"
    echo "  health              - ヘルスチェック実行"
    echo "  mcp-status          - MCP ステータス確認"
    echo "  info                - サービス情報表示"
    echo "  logs [行数]         - ログ表示（デフォルト: 50行）"
    echo "  monitor             - 継続監視（5分間隔）"
    echo ""
    echo "例:"
    echo "  $0 health"
    echo "  $0 logs 100"
    echo "  $0 monitor"
}

# 継続監視
continuous_monitor() {
    log_info "継続監視を開始します (Ctrl+C で停止)"
    
    while true; do
        echo ""
        echo "========================================="
        echo "監視実行時刻: $(date)"
        echo "========================================="
        
        health_check
        echo ""
        mcp_status_check
        
        echo ""
        log_info "次の監視まで 5分間 待機中..."
        sleep 300
    done
}

# メイン処理
main() {
    case "${1:-health}" in
        "health")
            health_check
            ;;
        "mcp-status")
            mcp_status_check
            ;;
        "info")
            service_info
            ;;
        "logs")
            show_logs "${2:-50}"
            ;;
        "monitor")
            continuous_monitor
            ;;
        "help"|"-h"|"--help")
            usage
            ;;
        *)
            log_error "不明なコマンド: $1"
            usage
            exit 1
            ;;
    esac
}

# プロジェクト ID の確認
if [ "$PROJECT_ID" = "your-project-id" ]; then
    log_error "PROJECT_ID を設定してください"
    echo "例: export PROJECT_ID=my-project-123"
    exit 1
fi

main "$@"
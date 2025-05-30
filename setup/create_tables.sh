#!/bin/bash
# Create DynamoDB tables from SAM template in local DynamoDB

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE_FILE="$PROJECT_ROOT/template.yaml"

# Check if DynamoDB Local is running
check_dynamodb_running() {
    if ! curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo "❌ DynamoDB Local is not running on port 8000"
        echo "Start it with: make dynamodb-local-start"
        exit 1
    fi
    echo "✅ DynamoDB Local is running"
}

# Create tables using AWS CLI and yq
create_tables() {
    echo "🚀 Creating tables from SAM template..."

    cd "$PROJECT_ROOT"

    # Create Users table
    echo "Creating Users table..."
    aws dynamodb create-table \
        --cli-input-yaml "$(cat template.yaml | yq 'del(.Resources.UsersTable.Properties.PointInTimeRecoverySpecification) | .Resources.UsersTable.Properties')" \
        --no-cli-pager \
        --endpoint-url http://localhost:8000 > /dev/null

    # Create Chats table
    echo "Creating Chats table..."
    aws dynamodb create-table \
        --cli-input-yaml "$(cat template.yaml | yq 'del(.Resources.ChatsTable.Properties.PointInTimeRecoverySpecification) | .Resources.ChatsTable.Properties')" \
        --no-cli-pager \
        --endpoint-url http://localhost:8000 > /dev/null

    echo "✅ Tables created successfully"
}

# List tables to verify creation
verify_tables() {
    echo "📋 Verifying table creation..."

    # Use AWS CLI to list tables
    aws dynamodb list-tables \
        --endpoint-url http://localhost:8000 \
        --region us-east-1 \
        --no-cli-pager

    # echo ""
    # echo "📊 Describing Users table..."
    # aws dynamodb describe-table \
    #     --table-name Users \
    #     --endpoint-url http://localhost:8000 \
    #     --region us-east-1 \
    #     --no-cli-pager \
    #     --query 'Table.{TableName:TableName,KeySchema:KeySchema,AttributeDefinitions:AttributeDefinitions,GlobalSecondaryIndexes:GlobalSecondaryIndexes}'

    # echo ""
    # echo "📊 Describing Chats table..."
    # aws dynamodb describe-table \
    #     --table-name Chats \
    #     --endpoint-url http://localhost:8000 \
    #     --region us-east-1 \
    #     --no-cli-pager \
    #     --query 'Table.{TableName:TableName,KeySchema:KeySchema,AttributeDefinitions:AttributeDefinitions,GlobalSecondaryIndexes:GlobalSecondaryIndexes}'
}

main() {
    echo "🔧 Setting up DynamoDB Local tables from SAM template"
    check_dynamodb_running
    create_tables
    verify_tables
    echo "✅ Schema synchronization complete!"
}

case "${1:-}" in
    verify)
        verify_tables
        ;;
    *)
        main
        ;;
esac

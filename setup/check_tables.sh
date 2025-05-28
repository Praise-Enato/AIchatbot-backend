#!/bin/bash
# Check if DynamoDB tables exist

set -e

# Check if specific tables exist
check_tables_exist() {
    local tables=$(aws dynamodb list-tables --endpoint-url http://localhost:8000 --region us-east-1 --no-cli-pager --output json 2>/dev/null || echo '{"TableNames":[]}')

    # Check for both Users and Chats tables
    if echo "$tables" | grep -q '"Users"' && echo "$tables" | grep -q '"Chats"'; then
        return 0  # Tables exist
    else
        return 1  # Tables don't exist
    fi
}

# Main check
if check_tables_exist; then
    echo "✅ Tables already exist"
    exit 0
else
    echo "❌ Tables do not exist"
    exit 1
fi

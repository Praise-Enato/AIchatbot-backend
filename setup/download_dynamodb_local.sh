#!/bin/bash
# Download DynamoDB Local JAR from AWS

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DYNAMODB_DIR="$SCRIPT_DIR/../dynamodb-local"
JAR_PATH="$DYNAMODB_DIR/DynamoDBLocal.jar"

# Check if JAR already exists
if [ -f "$JAR_PATH" ]; then
    echo "DynamoDB Local JAR already exists at $JAR_PATH"
    exit 0
fi

echo "Downloading DynamoDB Local..."
mkdir -p "$DYNAMODB_DIR"
cd "$DYNAMODB_DIR"

# Download and extract DynamoDB Local
curl -L -o dynamodb_local_latest.tar.gz https://d1ni2b6xgvw0s0.cloudfront.net/v2.x/dynamodb_local_latest.tar.gz
tar -xzf dynamodb_local_latest.tar.gz
rm dynamodb_local_latest.tar.gz

# Verify the JAR was extracted
if [ -f "$JAR_PATH" ]; then
    echo "✅ DynamoDB Local ready at $JAR_PATH"
else
    echo "❌ Error: DynamoDBLocal.jar not found after extraction"
    exit 1
fi

#!/bin/bash
# Start/stop DynamoDB Local instance

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DYNAMODB_DIR="$SCRIPT_DIR/../tests/dynamodb-local"
JAR_PATH="$DYNAMODB_DIR/DynamoDBLocal.jar"
PID_FILE="$DYNAMODB_DIR/dynamodb-local.pid"
LOG_FILE="$DYNAMODB_DIR/dynamodb-local.log"
DATA_DIR="$DYNAMODB_DIR/data"

start_dynamodb() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "DynamoDB Local is already running (PID: $pid)"
            return 0
        else
            rm -f "$PID_FILE"
        fi
    fi

    # Ensure JAR exists
    if [ ! -f "$JAR_PATH" ]; then
        echo "DynamoDB Local JAR not found. Running download script..."
        "$SCRIPT_DIR/download_dynamodb_local.sh"
    fi

    # Create data directory
    mkdir -p "$DATA_DIR"

    echo "Starting DynamoDB Local on port 8000..."

    # Start DynamoDB Local in the background
    java -Djava.library.path="$DYNAMODB_DIR/DynamoDBLocal_lib" \
         -jar "$JAR_PATH" \
         -port 8000 \
         -inMemory \
         > "$LOG_FILE" 2>&1 &

    local pid=$!
    echo $pid > "$PID_FILE"

    # Wait a moment for startup
    sleep 3

    # Check if process is still running
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "✅ DynamoDB Local started successfully (PID: $pid)"
        echo "📄 Logs: $LOG_FILE"
    else
        echo "❌ Failed to start DynamoDB Local"
        cat "$LOG_FILE"
        rm -f "$PID_FILE"
        exit 1
    fi
}

stop_dynamodb() {
    if [ ! -f "$PID_FILE" ]; then
        echo "DynamoDB Local is not running (no PID file)"
        return 0
    fi

    local pid=$(cat "$PID_FILE")
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "Stopping DynamoDB Local (PID: $pid)..."
        kill "$pid"
        rm -f "$PID_FILE"
        echo "✅ DynamoDB Local stopped"
    else
        echo "DynamoDB Local is not running (stale PID file)"
        rm -f "$PID_FILE"
    fi
}

status_dynamodb() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "✅ DynamoDB Local is running (PID: $pid)"
            return 0
        else
            echo "❌ DynamoDB Local is not running (stale PID file)"
            rm -f "$PID_FILE"
            return 1
        fi
    else
        echo "❌ DynamoDB Local is not running"
        return 1
    fi
}

case "${1:-}" in
    start)
        start_dynamodb
        ;;
    stop)
        stop_dynamodb
        ;;
    restart)
        stop_dynamodb
        start_dynamodb
        ;;
    status)
        status_dynamodb
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        echo "  start   - Start DynamoDB Local"
        echo "  stop    - Stop DynamoDB Local"
        echo "  restart - Restart DynamoDB Local"
        echo "  status  - Check DynamoDB Local status"
        exit 1
        ;;
esac

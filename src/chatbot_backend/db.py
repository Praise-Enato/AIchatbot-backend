import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import boto3
from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError

from chatbot_backend.custom_logger import get_logger
from chatbot_backend.models.chat import Chat, ChatListResponse, Message, Stream, Vote
from chatbot_backend.models.user import User

# Configure logging
logger = get_logger("db")

# Initialize DynamoDB resource and tables
# Use local DynamoDB when DYNAMODB_URL is set
dynamodb_url = os.environ.get("DYNAMODB_URL")
dynamodb = boto3.resource("dynamodb", endpoint_url=dynamodb_url) if dynamodb_url else boto3.resource("dynamodb")
# Get table names from environment variables with defaults
users_table = dynamodb.Table(os.environ.get("USERS_TABLE", "Users"))
chats_table = dynamodb.Table(os.environ.get("CHATS_TABLE", "Chats"))

# Users
# - PK=user_id
#   - created_at = ISO-8601 string
#   - stripe_customer_id = nullable string
#   - active_subscription_id = nullable string
#   - subscription_status = nullable active | canceled
#   - plan_id = nullable string
#   - current_period_start = nullable ISO-8601 string
#   - current_period_end = nullable ISO-8601 string
#   - cancel_at_period_end = bool
# GSI1-Email: email -> user_id, password_hash, created_at
# GSI2-UsersByType: Type + CreatedAt -> user_id
# GSI3-StripeCustomer: stripe_customer_id -> user_id, active_subscription_id, subscription_status
# GSI4-Subscription: active_subscription_id -> user_id, stripe_customer_id, subscription_status

# Chats
# - PK=chat_id
# - Attributes
#   - sK= META | MSG#CreatedAt#MessageId | VOTE#MessageId | STR#CreatedAt#StreamId
#   - type = CHAT | MESSAGE | VOTE | STREAM
#   - user_id = in CHAT + MESSAGE
#   - chat_created_at = ISO-8601 in CHAT
#   - created_at = ISO-8601 in MESSAGE + STREAM
#   - title = CHAT title
#   - visibility = public | private in CHAT
#   - role = user | assistant in MESSAGE
#   - parts = JSON blob in MESSAGE
#   - attachments = JSON blob in MESSAGE
#   - message_id = UUID in MESSAGE + VOTE
#   - is_upvoted = bool in VOTE
#   - stream_id = UUID in STREAM
# GSI1-ChatsByUser: user_id + chat_created_at -> chat_id, title, visibility, chat_created_at
# GSI2-MessageById: message_id + created_at -> all MESSAGE attrs
# GSI3-MsgsByUser: user_id + created_at -> message_id, role


def get_user(email: str) -> User | None:
    """Fetch user by email."""
    resp = users_table.query(IndexName="GSI1-Email", KeyConditionExpression=Key("email").eq(email))
    logger.info(f"User response: {resp}")
    items = resp.get("Items", [])
    return User.model_validate(items[0]) if items else None


def create_user(email: str, password_hash: str) -> User:
    """Create a new email user."""
    user_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    item = {
        "user_id": user_id,
        "email": email,
        "source": "email",
        "password_hash": password_hash,
        "created_at": now,
        "cancel_at_period_end": False,
    }
    try:
        users_table.put_item(Item=item)
        return User.model_validate(item)
    except ClientError as err:
        logger.error("Failed to create user %s: %s", email, err)
        raise RuntimeError("Could not write new user to database") from err


def create_guest_user() -> User:
    """Create a new guest user."""
    user_id = str(uuid.uuid4())
    now = datetime.now(UTC)
    now_iso = now.isoformat()
    email = f"guest-{int(now.timestamp() * 1000)}"
    item = {
        "user_id": user_id,
        "email": email,
        "source": "guest",
        "created_at": now_iso,
        "cancel_at_period_end": False,
    }
    try:
        users_table.put_item(Item=item)
        return User.model_validate(item)
    except ClientError as err:
        logger.error("Failed to create user %s: %s", email, err)
        raise RuntimeError("Could not write new user to database") from err


def get_or_create_user_from_oauth(email: str | None, provider: str, provider_account_id: str) -> User:
    """Fetch or create a user via OAuth."""
    email = email or f"{provider}-{provider_account_id}@oauth.local"
    user = get_user(email)
    if user:
        return user
    # No existing user, create new
    user_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    item = {
        "user_id": user_id,
        "email": email,
        "source": "oauth",
        "provider": provider,
        "provider_account_id": provider_account_id,
        "created_at": now,
        "cancel_at_period_end": False,
    }
    try:
        users_table.put_item(Item=item, ConditionExpression="attribute_not_exists(email)")
        return User.model_validate(item)
    except users_table.meta.client.exceptions.ConditionalCheckFailedException:
        # race: someone else just created it
        user = get_user(email)
        if not user:
            raise RuntimeError("User creation race condition: user not found after creation") from None
        return user
    except ClientError as err:
        logger.error("Failed to create user %s: %s", email, err)
        raise RuntimeError("Could not write new user to database") from err


def save_chat(chat_id: str, user_id: str, title: str, visibility: str) -> Chat:
    """Save a new chat."""
    now = datetime.now(UTC).isoformat()
    item = {
        "chat_id": chat_id,
        "sk": "META",
        "type": "CHAT",
        "user_id": user_id,
        "chat_created_at": now,
        "title": title,
        "visibility": visibility,
    }
    try:
        chats_table.put_item(Item=item)
        return Chat.model_validate(item)
    except ClientError as err:
        logger.error("Failed to create chat %s: %s", chat_id, err)
        raise RuntimeError("Could not write new chat to database") from err


def delete_chat_by_id(chat_id: str) -> None:
    """Delete a chat and all its related items."""
    try:
        resp = chats_table.query(KeyConditionExpression=Key("chat_id").eq(chat_id))
        with chats_table.batch_writer() as batch:
            for item in resp.get("Items", []):
                batch.delete_item(Key={"chat_id": item["chat_id"], "sk": item["sk"]})
    except ClientError as err:
        logger.error("Failed to delete chat %s: %s", chat_id, err)
        raise RuntimeError("Could not delete chat from database") from err


def get_chats_by_user_id(
    user_id: str, limit: int, starting_after: str | None = None, ending_before: str | None = None
) -> ChatListResponse:
    """Paginate chats for a user."""
    idx = "GSI1-ChatsByUser"
    extended_limit = limit + 1

    try:

        def query_chat(cond: Any) -> dict[str, Any]:
            params = {
                "IndexName": idx,
                "KeyConditionExpression": Key("user_id").eq(user_id) & cond,
                "ScanIndexForward": False,
                "Limit": extended_limit,
            }
            return chats_table.query(**params)

        if starting_after:
            chat = get_chat_by_id(starting_after)
            if not chat:
                raise ValueError(f"Chat with id {starting_after} not found")
            cutoff = chat.chat_created_at
            resp = query_chat(Key("chat_created_at").gt(cutoff))

        elif ending_before:
            chat = get_chat_by_id(ending_before)
            if not chat:
                raise ValueError(f"Chat with id {ending_before} not found")
            cutoff = chat.chat_created_at
            resp = query_chat(Key("chat_created_at").lt(cutoff))

        else:
            # no cursor → fetch newest first
            resp = query_chat(Key("chat_created_at").gt("1970-01-01T00:00:00+00:00"))

        items = resp.get("Items", [])
        has_more = len(items) > limit
        chats = [Chat.model_validate(item) for item in items[:limit]]
        return ChatListResponse(chats=chats, has_more=has_more)
    except ClientError as err:
        logger.error("Failed to get chats for user %s: %s", user_id, err)
        raise RuntimeError("Could not get chats from database") from err


def get_chat_by_id(chat_id: str) -> Chat | None:
    """Get chat metadata by id."""
    pk = chat_id
    try:
        resp = chats_table.get_item(Key={"chat_id": pk, "sk": "META"})
        item = resp.get("Item")
        return Chat.model_validate(item) if item else None
    except ClientError as err:
        logger.error("Failed to get chat %s: %s", chat_id, err)
        raise RuntimeError("Could not get chat from database") from err


def save_messages(user_id: str, messages: list[Message]) -> None:
    """Batch write messages."""
    try:
        with chats_table.batch_writer() as batch:
            for m in messages:
                pk = m.chat_id
                sk = f"MSG#{m.created_at}#{m.message_id}"
                item = {
                    "chat_id": pk,
                    "sk": sk,
                    "type": "MESSAGE",
                    "user_id": user_id,
                    "created_at": m.created_at,
                    "role": m.role,
                    "parts": m.parts,
                    "attachments": m.attachments,
                    "message_id": m.message_id,
                }
                batch.put_item(Item=item)
    except ClientError as err:
        logger.error("Failed to save messages: %s", err)
        raise RuntimeError("Could not save messages to database") from err


def get_messages_by_chat_id(chat_id: str) -> list[Message]:
    """Fetch all messages for a chat in ascending order."""
    pk = chat_id
    try:
        resp = chats_table.query(
            KeyConditionExpression=Key("chat_id").eq(pk) & Key("sk").begins_with("MSG#"), ScanIndexForward=True
        )
        items = resp.get("Items", [])
        return [Message.model_validate(item) for item in items]
    except ClientError as err:
        logger.error("Failed to get messages for chat %s: %s", chat_id, err)
        raise RuntimeError("Could not get messages from database") from err


def vote_message(chat_id: str, message_id: str, vote_type: str) -> None:
    """Upsert a vote record."""
    pk = chat_id
    sk = f"VOTE#{message_id}"
    try:
        chats_table.put_item(
            Item={"chat_id": pk, "sk": sk, "type": "VOTE", "message_id": message_id, "is_upvoted": (vote_type == "up")}
        )
    except ClientError as err:
        logger.error("Failed to vote message: %s", err)
        raise RuntimeError("Could not vote message in database") from err


def get_votes_by_chat_id(chat_id: str) -> list[Vote]:
    """Get all votes for a chat."""
    pk = chat_id
    try:
        resp = chats_table.query(KeyConditionExpression=Key("chat_id").eq(pk) & Key("sk").begins_with("VOTE#"))
        items = resp.get("Items", [])
        return [Vote.model_validate(item) for item in items]
    except ClientError as err:
        logger.error("Failed to get votes for chat %s: %s", chat_id, err)
        raise RuntimeError("Could not get votes from database") from err


def get_message_by_id(message_id: str) -> Message | None:
    """Fetch message by its ID (rare)."""
    try:
        resp = chats_table.query(IndexName="GSI2-MessageById", KeyConditionExpression=Key("message_id").eq(message_id))
        items = resp.get("Items", [])
        if not items:
            return None
        # retrieve full item using projected table keys - this is a rare operation
        rec = items[0]
        get_resp = chats_table.get_item(Key={"chat_id": rec["chat_id"], "sk": rec["sk"]})
        item = get_resp.get("Item")
        return Message.model_validate(item) if item else None
    except ClientError as err:
        logger.error("Failed to get message by id %s: %s", message_id, err)
        raise RuntimeError("Could not get message from database") from err


def delete_messages_by_chat_id_after_timestamp(chat_id: str, timestamp: str) -> None:
    """Delete messages and their votes after a given timestamp."""
    pk = chat_id
    start = timestamp
    end = "\uffff"
    try:
        resp = chats_table.query(
            KeyConditionExpression=Key("chat_id").eq(pk) & Key("sk").between(f"MSG#{start}", f"MSG#{end}")
        )
        items = resp.get("Items", [])
        with chats_table.batch_writer() as batch:
            for m in items:
                # delete message record
                batch.delete_item(Key={"chat_id": m["chat_id"], "sk": m["sk"]})
                # delete vote record
                batch.delete_item(Key={"chat_id": m["chat_id"], "sk": f"VOTE#{m['message_id']}"})
    except ClientError as err:
        logger.error("Failed to delete messages by chat id after timestamp %s: %s", chat_id, err)
        raise RuntimeError("Could not delete messages from database") from err


def update_chat_visibility_by_id(chat_id: str, visibility: str) -> None:
    """Update a chat's visibility."""
    pk = chat_id
    try:
        chats_table.update_item(
            Key={"chat_id": pk, "sk": "META"},
            UpdateExpression="SET visibility = :v",
            ExpressionAttributeValues={":v": visibility},
        )
    except ClientError as err:
        logger.error("Failed to update chat visibility: %s", err)
        raise RuntimeError("Could not update chat visibility in database") from err


def get_message_count_by_user_id(user_id: str, difference_in_hours: int) -> int:
    """Count 'user' messages by a user in the last N hours."""
    cutoff = (datetime.now(UTC) - timedelta(hours=difference_in_hours)).isoformat()
    try:
        resp = chats_table.query(
            IndexName="GSI3-MsgsByUser",
            KeyConditionExpression=Key("user_id").eq(user_id) & Key("created_at").gte(cutoff),
            FilterExpression=Attr("role").eq("user"),
            Select="COUNT",
        )
        return resp.get("Count", 0)
    except ClientError as err:
        logger.error("Failed to get message count by user id: %s", err)
        raise RuntimeError("Could not get message count from database") from err


def create_stream_id(stream_id: str, chat_id: str) -> Stream:
    """Record a new stream ID."""
    pk = chat_id
    now = datetime.now(UTC).isoformat()
    try:
        item = {
            "chat_id": pk,
            "sk": f"STR#{now}#{stream_id}",
            "type": "STREAM",
            "created_at": now,
            "stream_id": stream_id,
        }
        chats_table.put_item(Item=item)
        return Stream.model_validate(item)
    except ClientError as err:
        logger.error("Failed to create stream id: %s", err)
        raise RuntimeError("Could not create stream id in database") from err


def get_stream_ids_by_chat_id(chat_id: str) -> list[str]:
    """Fetch all stream IDs for a chat."""
    pk = chat_id
    try:
        resp = chats_table.query(
            KeyConditionExpression=Key("chat_id").eq(pk) & Key("sk").begins_with("STR#"), ScanIndexForward=True
        )
        return [item["stream_id"] for item in resp.get("Items", [])]
    except ClientError as err:
        logger.error("Failed to get stream ids by chat id: %s", err)
        raise RuntimeError("Could not get stream ids from database") from err

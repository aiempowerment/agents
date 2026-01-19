from typing import Any, Dict, Optional
import os
import json
import base64
import time
import hmac
import hashlib
from datetime import datetime, timezone

import boto3
import yaml

from core.event_processor import EventProcessor
from core.task_publisher import TaskPublisher


_sqs = None
_processor: Optional[EventProcessor] = None
_queue_url = None

SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]


def _init() -> None:
    global _sqs, _processor, _queue_url

    if _processor is not None:
        return

    with open("tenant_config.yaml", "r", encoding="utf-8") as f:
        tenant_config: Dict[str, Any] = yaml.safe_load(f)

    dynamodb_config = tenant_config.get("dynamodb", {}) or {}
    dynamodb = boto3.resource("dynamodb", region_name=dynamodb_config.get("region"))
    processes_table = dynamodb.Table(dynamodb_config["processes_table"])

    sqs_config = tenant_config.get("sqs", {}) or {}
    _sqs = boto3.client("sqs", region_name=sqs_config.get("region"))
    _queue_url = sqs_config.get("tasks_url")

    _processor = EventProcessor(
        processes_table=processes_table,
        task_publisher=TaskPublisher(_sqs, _queue_url),
    )

    print("INIT: processor ready")


def _extract_raw_body(event: Dict[str, Any]) -> str:
    body = event.get("body") or ""
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")
    return body


def _is_valid_slack_request(headers: Dict[str, Any], raw_body: str) -> bool:
    timestamp = headers.get("x-slack-request-timestamp")
    signature = headers.get("x-slack-signature")

    if not timestamp or not signature:
        return False

    try:
        ts = int(timestamp)
    except ValueError:
        return False

    if abs(int(time.time()) - ts) > 60 * 5:
        return False

    base_string = f"v0:{timestamp}:{raw_body}".encode("utf-8")
    computed = "v0=" + hmac.new(
        SLACK_SIGNING_SECRET.encode("utf-8"),
        base_string,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(computed, signature)


def _slack_ts_to_iso_and_epoch(ts: Optional[str]) -> tuple[Optional[str], Optional[int]]:
    if not ts:
        return None, None

    try:
        epoch_float = float(ts)
        epoch_int = int(epoch_float)
        dt = datetime.fromtimestamp(epoch_float, tz=timezone.utc)
        iso = dt.isoformat().replace("+00:00", "Z")
        return iso, epoch_int
    except Exception:
        return None, None


def lambda_handler(event, context):
    _init()

    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    raw_body = _extract_raw_body(event)

    if not _is_valid_slack_request(headers, raw_body):
        return {"statusCode": 401, "body": "invalid signature"}

    payload = json.loads(raw_body) if raw_body else {}

    if payload.get("type") == "url_verification":
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"challenge": payload.get("challenge", "")}),
        }

    if payload.get("type") != "event_callback":
        return {"statusCode": 200, "body": ""}

    slack_event = payload.get("event", {}) or {}

    if slack_event.get("subtype") == "bot_message" or slack_event.get("bot_id"):
        return {"statusCode": 200, "body": ""}

    if slack_event.get("type") != "app_mention":
        return {"statusCode": 200, "body": ""}

    identity = slack_event.get("user")
    content = slack_event.get("text")
    channel = slack_event.get("channel")
    thread_ts = slack_event.get("thread_ts") or slack_event.get("ts")

    timestamp_iso, timestamp_epoch = _slack_ts_to_iso_and_epoch(slack_event.get("ts"))

    _processor.process(
        process_type="SLACK_CONVERSATION",
        event="SLACK_MENTION_RECEIVED",
        context={"identity": identity},
        payload={
            "user": identity,
            "channel": channel,
            "thread_ts": thread_ts,
            "content": content,
            "timestamp_iso": timestamp_iso,
            "timestamp_epoch": timestamp_epoch,
            "slack_event_id": payload.get("event_id"),
        },
    )

    return {"statusCode": 200, "body": ""}
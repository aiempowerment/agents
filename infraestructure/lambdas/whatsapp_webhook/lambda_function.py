from typing import Any, Dict

import boto3
import yaml
import json

import handler

from core.event_processor import EventProcessor
from core.task_publisher import TaskPublisher

from services.messages_dynamodb import MessagesDynamodbService
from services.messages_whatsapp import MessagesWhatsappService
from integrations.messages import MessagesIntegration


_sqs = None
_processor = None
_queue_url = None

_s3 = None
_bucket = None
_verify_token = None

_history_service = None
_whatsapp_service = None
_messages_integration = None


def _init() -> None:
    global _sqs, _processor, _queue_url
    global _s3, _bucket, _verify_token
    global _history_service, _whatsapp_service, _messages_integration

    if _processor is not None:
        return

    with open("tenant_config.yaml", "r", encoding="utf-8") as f:
        tenant_config: Dict[str, Any] = yaml.safe_load(f)

    dynamodb_config = tenant_config.get("dynamodb", {}) or {}
    dynamodb = boto3.resource( "dynamodb", region_name=dynamodb_config.get("region"))

    messages_table = dynamodb.Table(dynamodb_config["messages_table"])
    processes_table = dynamodb.Table(dynamodb_config["processes_table"])

    sqs_config = tenant_config.get("sqs", {}) or {}
    _sqs = boto3.client("sqs", region_name=sqs_config.get("region"))

    _queue_url = (sqs_config.get("tasks_url"))

    _processor = EventProcessor(
        processes_table=processes_table,
        task_publisher=TaskPublisher(_sqs, _queue_url),
    )

    print("INIT: processor ready")

    whatsapp_config = tenant_config.get("whatsapp", {}) or {}
    _verify_token = whatsapp_config.get("verify_token")

    s3_config = tenant_config.get("s3", {}) or {}
    _bucket = s3_config.get("bucket")
    _s3 = boto3.client("s3", region_name=s3_config.get("region"))

    _history_service = MessagesDynamodbService(messages_table)
    _whatsapp_service = MessagesWhatsappService(tenant_config=tenant_config)
    _messages_integration = MessagesIntegration(_history_service, _whatsapp_service)



def lambda_handler(event, context):
    _init()
    
    print("INCOMING_HTTP_BODY:", event.get("body"))

    method = (
        event.get("requestContext", {})
        .get("http", {})
        .get("method")
        or event.get("httpMethod", "GET")
    )

    if method == "GET":
        return handle_verification(event)
    if method == "POST":
        return handle_webhook(event)

    return {"statusCode": 405, "body": "Method not allowed"}


def handle_verification(event):
    params = event.get("queryStringParameters") or {}
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == _verify_token and challenge:
        return {"statusCode": 200, "body": challenge}

    return {"statusCode": 403, "body": "Forbidden"}


def handle_webhook(event):
    body_raw = event.get("body")

    try:
        payload = json.loads(body_raw)
    except json.JSONDecodeError:
        print("INVALID_JSON:", body_raw)
        return {"statusCode": 400, "body": "Invalid JSON"}

    events = _messages_integration.parse_incoming_payload(payload)

    for ev in events:
        identity = ev.get("identity") or ""
        identity_part = identity.split(":", 1)[-1] if ":" in identity else identity
        content = dict(ev.get("content") or {})
        msg_id = ev.get("msg_id")
        message_type = ev.get("message_type")
        ext = "bin"

        if message_type in ["image", "video", "audio", "document"]:
            media_id = content.get("media_id")
            if media_id:
                meta_result = _whatsapp_service.get_media_metadata(media_id)
                if meta_result.get("status") == "ok":
                    meta = meta_result.get("data") or {}
                    download_url = meta.get("url")
                    mime_type = meta.get("mime_type") or content.get("mime_type")
                    filename = content.get("filename")

                    if filename and "." in filename:
                        ext = filename.rsplit(".", 1)[-1].lower()
                    elif mime_type and "/" in mime_type:
                        ext = mime_type.split("/")[-1].lower()

                    if download_url:
                        download_result = _whatsapp_service.download_media(download_url)
                        if download_result.get("status") == "ok":
                            media_bytes = download_result.get("content") or b""

                            media_key = f"whatsapp_media/{identity_part}/{msg_id}_{media_id}.{ext}"

                            _s3.put_object(
                                Bucket=_bucket,
                                Key=media_key,
                                Body=media_bytes,
                            )

                            content["media_s3_key"] = media_key
                            if mime_type:
                                content["mime_type"] = mime_type
                            if filename:
                                content["filename"] = filename
                        else:
                            print("MEDIA_DOWNLOAD_ERROR", media_id, download_result)
                else:
                    print("MEDIA_META_ERROR", media_id, meta_result)

        _history_service.save_message(
            identity=identity,
            direction="in",
            channel="whatsapp",
            message_type=message_type,
            timestamp_iso=ev.get("timestamp_iso"),
            timestamp_epoch=ev.get("timestamp_epoch"),
            content=content,
            payload=ev.get("raw_payload"),
            msg_id=ev.get("msg_id")
        )

        try:
            handler.handler(_processor, ev)
        except Exception as e:
            print("HANDLER_RUNTIME_ERROR:", str(e))

    return {"statusCode": 200, "body": "EVENT_RECEIVED"}
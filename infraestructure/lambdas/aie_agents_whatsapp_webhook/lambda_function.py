import json
import os
from datetime import datetime, timezone

import boto3

from services.messages_dynamodb import MessagesDynamodbService
from services.messages_whatsapp import MessagesWhatsappService
from integrations.messages import MessagesIntegration


dynamodb = boto3.resource("dynamodb")
messages_table = dynamodb.Table(os.environ["MESSAGES_TABLE"])
s3 = boto3.client("s3")

BUCKET = os.environ["WHATSAPP_BUCKET"]
VERIFY_TOKEN = os.environ["WHATSAPP_VERIFY_TOKEN"]

tenant_id = "alfa"
tenant_config = {
    "whatsapp": {
        "token": os.environ["WHATSAPP_TOKEN"],
        "number": os.environ.get("WHATSAPP_NUMBER", ""),
    }
}

history_service = MessagesDynamodbService(messages_table)
whatsapp_service = MessagesWhatsappService(tenant_config=tenant_config)
messages_integration = MessagesIntegration(history_service, whatsapp_service)


def lambda_handler(event, context):
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

    if mode == "subscribe" and token == VERIFY_TOKEN and challenge:
        return {"statusCode": 200, "body": challenge}

    return {"statusCode": 403, "body": "Forbidden"}


def handle_webhook(event):
    body_raw = event.get("body") or "{}"

    try:
        payload = json.loads(body_raw)
    except json.JSONDecodeError:
        print("INVALID_JSON:", body_raw)
        return {"statusCode": 400, "body": "Invalid JSON"}

    events = messages_integration.parse_incoming_payload(payload)

    for ev in events:
        content = dict(ev.get("content") or {})

        if ev.get("message_type") in ["image", "video", "audio", "document"]:
            media_id = content.get("media_id")
            if media_id:
                meta_result = whatsapp_service.get_media_metadata(media_id)
                if meta_result.get("status") == "ok":
                    meta = meta_result.get("data") or {}
                    download_url = meta.get("url")
                    mime_type = meta.get("mime_type") or content.get("mime_type")
                    filename = content.get("filename")

                    ext = "bin"
                    if filename and "." in filename:
                        ext = filename.rsplit(".", 1)[-1].lower()
                    elif mime_type and "/" in mime_type:
                        ext = mime_type.split("/")[-1].lower()

                    if download_url:
                        download_result = whatsapp_service.download_media(download_url)
                        if download_result.get("status") == "ok":
                            media_bytes = download_result.get("content") or b""
                            epoch = ev.get("timestamp_epoch")
                            if epoch is None:
                                epoch = int(datetime.now(timezone.utc).timestamp())

                            identity = ev.get("identity") or ""
                            identity_part = identity.split(":", 1)[-1] if ":" in identity else identity

                            media_key = f"whatsapp_media/{identity_part}/{epoch}_{media_id}.{ext}"

                            s3.put_object(
                                Bucket=BUCKET,
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

        ts_iso = ev.get("timestamp_iso")
        ts_dt = None
        if ts_iso:
            try:
                ts_dt = datetime.fromisoformat(ts_iso)
            except Exception:
                ts_dt = None
        if ts_dt is None:
            ts_dt = datetime.now(timezone.utc)

        history_service.save_message(
            identity=ev.get("identity"),
            direction="in",
            channel="whatsapp",
            message_type=ev.get("message_type"),
            content=content,
            payload=ev.get("raw_payload"),
            msg_id=ev.get("msg_id"),
            timestamp=ts_dt,
        )

    return {"statusCode": 200, "body": "EVENT_RECEIVED"}
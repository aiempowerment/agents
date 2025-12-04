import json
import os
from datetime import datetime, timezone
import boto3
import urllib3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["MESSAGES_TABLE"])
s3 = boto3.client("s3")
BUCKET = os.environ["WHATSAPP_BUCKET"]
WHATSAPP_TOKEN = os.environ["WHATSAPP_TOKEN"]
VERIFY_TOKEN = os.environ["WHATSAPP_VERIFY_TOKEN"]

http = urllib3.PoolManager()


def to_iso_timestamp(ts_str: str) -> str:
    if not ts_str:
        return datetime.now(timezone.utc).isoformat()
    try:
        ts_int = int(ts_str)
        return datetime.fromtimestamp(ts_int, tz=timezone.utc).isoformat()
    except ValueError:
        return datetime.now(timezone.utc).isoformat()


def to_epoch(ts_str: str | None) -> int | None:
    if not ts_str:
        return None
    try:
        return int(ts_str)
    except ValueError:
        return None


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
    elif method == "POST":
        return handle_webhook(event)
    else:
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

    entries = payload.get("entry", [])

    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            messages = value.get("messages", [])
            contacts = value.get("contacts", [])

            contact_wa = None
            if contacts:
                contact_wa = contacts[0].get("wa_id")

            for msg in messages:
                save_incoming_message(payload, value, msg, contact_wa)

    return {"statusCode": 200, "body": "EVENT_RECEIVED"}


def normalize_phone(phone: str) -> str:
    phone = phone.replace("+", "").strip()
    if phone.startswith("521") and len(phone) == 13:
        return "52" + phone[3:]
    return phone
    
def save_incoming_message(payload, value, msg, contact_wa):
    from_id = msg.get("from") or contact_wa
    if not from_id:
        print("MISSING_FROM_FIELD:", msg)
        return

    from_id_normalized = normalize_phone(from_id)
    identity = f"whatsapp:{from_id_normalized}"

    metadata = value.get("metadata", {}) or {}
    to_number = metadata.get("display_phone_number")
    to_identity = f"whatsapp:{to_number}" if to_number else None

    ts_raw = msg.get("timestamp") or value.get("timestamp")
    iso_ts = to_iso_timestamp(ts_raw)
    epoch_ts = to_epoch(ts_raw)

    msg_id = msg.get("id", "")
    direction = "in"
    message_key = f"{iso_ts}#{direction}#{msg_id}"

    msg_type = msg.get("type", "unknown")
    content = {}

    if msg_type in ["image", "video", "audio", "document"]:
        media_info = msg.get(msg_type) or {}
        media_id = media_info.get("id")

        if media_id:
            meta_url = f"https://graph.facebook.com/v20.0/{media_id}"
            meta_resp = http.request(
                "GET",
                meta_url,
                headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"},
            )

            if meta_resp.status != 200:
                print("MEDIA_META_ERROR", meta_resp.status, media_id, meta_resp.data)
            else:
                try:
                    meta = json.loads(meta_resp.data.decode("utf-8"))
                except Exception as e:
                    print("MEDIA_META_PARSE_ERROR", media_id, e, meta_resp.data)
                    meta = {}

                download_url = meta.get("url")

                mime_type = meta.get("mime_type") or media_info.get("mime_type")
                filename = media_info.get("filename")

                ext = "bin"
                if filename and "." in filename:
                    ext = filename.rsplit(".", 1)[-1].lower()
                elif mime_type and "/" in mime_type:
                    ext = mime_type.split("/")[-1].lower()

                if download_url:
                    file_resp = http.request(
                        "GET",
                        download_url,
                        headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"},
                    )

                    if file_resp.status == 200:
                        media_key = (
                            f"whatsapp_media/{from_id_normalized}/"
                            f"{epoch_ts}_{media_id}.{ext}"
                        )

                        s3.put_object(
                            Bucket=BUCKET,
                            Key=media_key,
                            Body=file_resp.data,
                        )

                        content["media_id"] = media_id
                        content["media_s3_key"] = media_key
                        content["media_type"] = msg_type
                        if mime_type:
                            content["mime_type"] = mime_type
                        if filename:
                            content["filename"] = filename
                    else:
                        print(
                            "MEDIA_DOWNLOAD_ERROR",
                            file_resp.status,
                            media_id,
                            file_resp.data,
                        )

    elif msg_type == "text":
        content["text"] = (msg.get("text") or {}).get("body")

    item = {
        "identity": identity,
        "message_key": message_key,
        "channel": "whatsapp",
        "direction": direction,
        "message_type": msg_type,
        "timestamp_iso": iso_ts,
        "timestamp_epoch": epoch_ts,
        "content": content,
        "payload": payload,
    }

    table.put_item(Item=item)
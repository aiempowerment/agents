def handler(processor, event):
    identity = event.get("identity") or ""
    identity_part = identity.split(":", 1)[-1] if ":" in identity else identity

    content = dict(event.get("content") or {})
    message_type = event.get("message_type")

    msg_id = event.get("msg_id")
    timestamp_iso = event.get("timestamp_iso")
    timestamp_epoch = event.get("timestamp_epoch")

    if message_type == "document":
        media_id = content.get("media_id")
        if media_id:
            processor.process(
                process_type="WHATSAPP_DOCUMENT_PIPELINE",
                event="DOCUMENT_RECEIVED",
                context={"identity": identity, "msg_id": msg_id, "media_id": media_id},
                payload={
                    "identity": identity,
                    "phone": identity_part,
                    "msg_id": msg_id,
                    "media_id": media_id,
                    "timestamp_iso": timestamp_iso,
                    "timestamp_epoch": timestamp_epoch,
                    "document": content,
                },
            )
    else:
        processor.process(
            process_type="WHATSAPP_CONVERSATION",
            event="WHATSAPP_MESSAGE_RECEIVED",
            context={"identity": identity},
            payload={
                "identity": identity,
                "phone": identity_part,
                "msg_id": msg_id,
                "message_type": message_type,
                "content": content,
                "timestamp_iso": timestamp_iso,
                "timestamp_epoch": timestamp_epoch,
            },
        )
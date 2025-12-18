def handler(processor, event):
    
    identity = event.get("identity") or ""
    identity_part = identity.split(":", 1)[-1] if ":" in identity else identity
    content = dict(event.get("content") or {})
    timestamp_iso = event.get("timestamp_iso")
    timestamp_epoch = event.get("timestamp_epoch")
    message_type = event.get("message_type")

    context_key = {
        "identity": identity,
        "msg_id": event.get("msg_id")
    }

    if message_type in ["document"]:
        payload = {
            "phone": identity_part,
            "timestamp_epoch": timestamp_epoch,
            "media_id": content.get("media_id"),
        }
        processor.process(
            process_type="PROCESS_INCOMING_WHATSAPP_DOCUMENT",
            event="DOCUMENT_RECEIVED",
            context=context_key
        )

    processor.process(
        process_type="READ_INCOMING_WHATSAPP_MESSAGE",
        event="MESSAGE_RECEIVED",
        context=context_key
    )
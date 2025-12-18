from models.task import Task

def handler(task_publisher, event):
    
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
        media_id = content.get("media_id")
        task = Task(
            task_type="PROCESS_INCOMING_WHATSAPP_DOCUMENT",
            agent_type="ACCOUNTING_ASSISTANT",
            process_type="READ_INCOMING_WHATSAPP_MESSAGE",
            context_key=context_key,
            payload={
                "phone": identity_part,
                "timestamp_epoch": timestamp_epoch,
                "media_id": media_id,
            },
            timestamp_iso=timestamp_iso,
            timestamp_epoch=timestamp_epoch
        )
        task_publisher.publish(task)

    debounce_policy = {
        "type": "messages_idle",
        "min_idle_seconds": 60,
    }
    task = Task(
        task_type="ANSWER_INCOMING_WHATSAPP_MESSAGE",
        agent_type="ACCOUNTING_ASSISTANT",
        process_type="READ_INCOMING_WHATSAPP_MESSAGE",
        context_key=context_key,
        payload=content,
        debounce_policy=debounce_policy,
        timestamp_iso=timestamp_iso,
        timestamp_epoch=timestamp_epoch
    )
    task_publisher.publish(task)
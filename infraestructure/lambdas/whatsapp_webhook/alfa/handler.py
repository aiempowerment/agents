from models.task import Task

def handler(task_publisher, identity, content, timestamp_iso, timestamp_epoch):
    debounce_policy = {
        "type": "messages_idle",
        "min_idle_seconds": 60,
    }
    task = Task(
        task_type="READ_INCOMING_WHATSAPP_MESSAGE",
        agent_type="ACCOUNTING_ASSISTANT",
        process_type="READ_INCOMING_WHATSAPP_MESSAGE",
        context_key=identity,
        payload=content,
        debounce_policy=debounce_policy,
        timestamp_iso=timestamp_iso,
        timestamp_epoch=timestamp_epoch
    )
    task_publisher.publish(task)
    pass
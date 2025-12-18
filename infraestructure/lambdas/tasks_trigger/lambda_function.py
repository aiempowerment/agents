from typing import Any, Dict, List

import boto3
import yaml

from core.task_processor import TaskProcessor
from core.task_publisher import TaskPublisher


_sqs = None
_processor = None
_queue_url = None


def _init() -> None:
    global _sqs, _processor, _queue_url

    if _processor is not None:
        return

    print("INIT: loading tenant_config.yaml")

    with open("tenant_config.yaml", "r", encoding="utf-8") as f:
        tenant_config: Dict[str, Any] = yaml.safe_load(f)

    dynamodb_config = tenant_config.get("dynamodb", {}) or {}
    dynamodb = boto3.resource("dynamodb", region_name=dynamodb_config.get("region"))
    messages_table = dynamodb.Table(dynamodb_config.get("messages_table"))
    processes_table = dynamodb.Table(dynamodb_config.get("processes_table"))
    contacts_table = dynamodb.Table(dynamodb_config.get("contacts_table"))
    tasks_table = dynamodb.Table(dynamodb_config.get("tasks_table"))

    sqs_config = tenant_config.get("sqs", {}) or {}
    _sqs = boto3.client("sqs", region_name=sqs_config.get("region"))

    _queue_url = (
        sqs_config.get("tasks_url")
        or sqs_config.get("url")
        or sqs_config.get("queue_url")
    )
    if not _queue_url:
        raise RuntimeError("Missing SQS queue url in tenant config.")

    print(f"INIT: queue_url={_queue_url}")

    task_publisher = TaskPublisher(_sqs, _queue_url)

    _processor = TaskProcessor(
        tenant_config=tenant_config,
        messages_table=messages_table,
        processes_table=processes_table,
        contacts_table=contacts_table,
        tasks_table=tasks_table,
        task_publisher=task_publisher,
    )

    print("INIT: processor ready")


def lambda_handler(event, context):
    _init()

    records = event.get("Records", []) or []
    print(f"EVENT: records={len(records)} request_id={getattr(context, 'aws_request_id', None)}")

    failures: List[Dict[str, str]] = []

    for i, record in enumerate(records):
        message_id = record.get("messageId")
        receipt = record.get("receiptHandle")
        body = record.get("body", "")

        print(f"RECORD[{i}]: messageId={message_id} body_len={len(body)}")
    
        print("BODY:", body)

        try:
            processed, remaining = _processor.process(body)
            print(f"PROCESS: messageId={message_id} processed={processed} remaining={remaining}")

            if processed:
                continue

            if remaining < 0:
                print(f"DROP: messageId={message_id} stale")
                continue

            delay = max(0, min(int(remaining), 43200))
            _sqs.change_message_visibility(
                QueueUrl=_queue_url,
                ReceiptHandle=receipt,
                VisibilityTimeout=delay,
            )
            print(f"DEFER: messageId={message_id} delay={delay}s")

            failures.append({"itemIdentifier": message_id})

        except Exception as e:
            print(f"ERROR: messageId={message_id} err={repr(e)}")
            failures.append({"itemIdentifier": message_id})

    print(f"RETURN: failures={len(failures)}")
    return {"batchItemFailures": failures}
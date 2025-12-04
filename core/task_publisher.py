import json
from typing import Any, Dict
from dataclasses import asdict


class TaskPublisher:
    def __init__(self, client, queue_url: str):
        self._client = client
        self._queue_url = queue_url

    def publish(self, task: Any) -> None:
        """Acepta dataclass Task o un dict."""
        if not isinstance(task, dict):
            task = asdict(task)

        body = json.dumps(task)

        self._client.send_message(
            QueueUrl=self._queue_url,
            MessageBody=body,
        )
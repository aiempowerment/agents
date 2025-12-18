import json
from typing import Any
from dataclasses import asdict


class TaskPublisher:
    def __init__(self, client, queue_url: str):
        self._client = client
        self._queue_url = queue_url

    def publish(self, task: Any) -> None:
        if not isinstance(task, dict):
            task = asdict(task)

        policy = task.get("debounce_policy")
        if policy:
            delay = int(policy.get("min_idle_seconds", 0))
            delay = max(0, min(delay, 900))
        else:
            delay = 0

        body = json.dumps(task)

        print(f"📤 Publishing task {task['task_id']} → {task['task_type']} delay={delay}s")

        self._client.send_message(
            QueueUrl=self._queue_url,
            MessageBody=body,
            DelaySeconds=delay,
        )
# core/task_processor.py
import json
from datetime import datetime
from typing import Any, Dict, Tuple

from models.task import Task
from core.process_engine import ProcessEngine
from core.process_registry import ProcessRegistry
from services.messages_dynamodb import MessagesDynamodbService

from agents.accounting_assistant.agent_factory import AccountingAssistantAgentFactory
from agents.hello_world.agent_factory import HelloWorldAgentFactory


class TaskProcessor:
    def __init__(
        self,
        tenant_config: Dict[str, Any],
        messages_table,
        processes_table,
        task_publisher: Any | None = None,
    ):
        process_definitions = ProcessRegistry.all()

        self._engine = ProcessEngine(
            processes_table=processes_table,
            task_publisher=task_publisher,
            process_definitions=process_definitions,
        )

        self._tenant_config = tenant_config
        self._messages_table = messages_table
        self._messages_service = MessagesDynamodbService(messages_table)

        self._agent_factories: Dict[str, Any] = {
            "ACCOUNTING_ASSISTANT": AccountingAssistantAgentFactory,
            "HELLO_WORLD": HelloWorldAgentFactory,
        }

    def _build_agent(self, task: Task):
        factory = self._agent_factories.get(task.agent_type)
        if not factory:
            raise RuntimeError(f"Unknown agent_type: {task.agent_type}")

        return factory.build(
            tenant_config=self._tenant_config,
            messages_table=self._messages_table,
            process_engine=self._engine,
        )

    def _evaluate_debounce(self, task: Task) -> int:
        policy = getattr(task, "debounce_policy", None)
        if not policy or policy.get("type") != "messages_idle":
            return 0

        min_idle = int(policy.get("min_idle_seconds", 0))
        if min_idle <= 0:
            return 0

        identity = task.context_key
        if not identity:
            return 0

        history = self._messages_service.get_history(identity, limit=1)
        if not history:
            return 0

        last_msg = history[-1]
        last_ts = (
            last_msg.get("timestamp_epoch")
            if isinstance(last_msg, dict)
            else getattr(last_msg, "timestamp_epoch", None)
        )

        if last_ts is None:
            return 0

        task_ts = getattr(task, "timestamp_epoch", None)
        if task_ts is None:
            return 0

        if int(task_ts) < int(last_ts):
            return -1

        now_ts = int(datetime.utcnow().timestamp())
        idle = now_ts - int(last_ts)
        remaining = min_idle - idle

        if remaining <= 0:
            return 0

        return remaining

    def process(self, body: str) -> Tuple[bool, int]:
        data = json.loads(body)

        context_key = data.get("context_key") or ""
        if isinstance(context_key, dict):
            context_key = context_key.get("identity") or ""

        task = Task(
            task_type=data["task_type"],
            agent_type=data["agent_type"],
            process_type=data["process_type"],
            context_key=context_key,
            payload=data.get("payload", {}),
            debounce_policy=data.get("debounce_policy"),
            timestamp_iso=data.get("timestamp_iso"),
            timestamp_epoch=data.get("timestamp_epoch"),
        )

        remaining = self._evaluate_debounce(task)
        if remaining < 0:
            return False, remaining
        if remaining > 0:
            return False, remaining

        agent = self._build_agent(task)
        agent.handle(task)

        return True, 0
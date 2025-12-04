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
            "ACCOUNTING_JUNIOR": AccountingAssistantAgentFactory,
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
        """
        Devuelve segundos restantes según debounce_policy.
        <= 0 -> se puede ejecutar ahora.
        >  0 -> conviene re-encolar con ese delay.
        """
        policy = getattr(task, "debounce_policy", None)
        if not policy:
            return 0

        policy_type = policy.get("type")
        if policy_type != "messages_idle":
            return 0

        min_idle = int(policy.get("min_idle_seconds", 0))
        if min_idle <= 0:
            return 0

        identity = task.context_key.get("identity")
        if not identity:
            return 0

        history = self._messages_service.get_history(identity, limit=1)
        if not history:
            return 0

        last = history[-1]

        if isinstance(last, dict):
            last_ts = last.get("timestamp_epoch")
        else:
            last_ts = getattr(last, "timestamp_epoch", None)

        if not last_ts:
            return 0

        now_ts = int(datetime.utcnow().timestamp())
        idle = now_ts - int(last_ts)
        remaining = min_idle - idle

        return remaining

    def process_raw_body(self, body: str) -> Tuple[bool, int]:
        """
        Procesa el body de una task serializada.

        Devuelve:
        - processed: True si se ejecutó la task, False si debe re-encolarse.
        - remaining_seconds: segundos a esperar si processed es False.
        """
        data = json.loads(body)

        task = Task(
            task_type=data["task_type"],
            agent_type=data["agent_type"],
            process_type=data["process_type"],
            context_key=data.get("context_key", {}),
            payload=data.get("payload", {}),
            debounce_policy=data.get("debounce_policy"),
        )

        remaining = self._evaluate_debounce(task)
        if remaining > 0:
            return False, remaining

        agent = self._build_agent(task)
        agent.handle(task)

        return True, 0
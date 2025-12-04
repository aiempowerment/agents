# core/task_processor.py
import json
from typing import Any, Dict

from models.task import Task
from core.process_engine import ProcessEngine
from core.process_registry import ProcessRegistry

from agents.accounting_assistant.agent_factory import AccountingAssistantAgentFactory
from agents.hello_world.agent_factory import HelloWorldAgentFactory


class TaskProcessor:
    def __init__(self, tenant_config, messages_table, processes_table, task_publisher=None):
        process_definitions = ProcessRegistry.all()

        self._engine = ProcessEngine(
            processes_table=processes_table,
            task_publisher=task_publisher,
            process_definitions=process_definitions,
        )

        self._tenant_config = tenant_config
        self._messages_table = messages_table

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

    def process_raw_body(self, body: str) -> None:
        data = json.loads(body)

        task = Task(
            task_type=data["task_type"],
            agent_type=data["agent_type"],
            process_type=data["process_type"],
            context_key=data.get("context_key", {}),
            payload=data.get("payload", {}),
        )

        agent = self._build_agent(task)
        agent.handle(task)
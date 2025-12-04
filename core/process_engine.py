import uuid
from datetime import datetime
from typing import Any, Dict, List

from models.task import Task


class ProcessEngine:
    def __init__(self, processes_table, task_publisher, process_definitions: Dict[str, Any]):
        """
        processes_table: instancia de DynamoDB.Table
        task_publisher: clase responsable de publicar tasks (ej: SQS, EventBridge, etc.)
        process_definitions: dict { process_type: ProcessClass }
        """
        self._table = processes_table
        self._task_publisher = task_publisher
        self._definitions = process_definitions

    # ---------------- Internal helpers ---------------- #

    def _get_definition(self, process_type: str):
        process_def = self._definitions.get(process_type)
        if process_def is None:
            raise RuntimeError(f"Unknown process_type: {process_type}")
        return process_def

    def _make_process_key(self, tenant_id: str, process_type: str, business_key: str) -> str:
        """Clave única del proceso en Dynamo."""
        return f"{tenant_id}#{process_type}#{business_key}"

    def _publish_tasks(
        self,
        *,
        task_defs: List[Dict[str, Any]],
        process_type: str,
        context: Dict[str, Any],
    ) -> List[Task]:
        """Convierte task_defs en Tasks y los publica."""
        tasks: List[Task] = []

        for t in task_defs:
            task = Task(
                task_type=t["task_type"],
                agent_type=t["agent_type"],
                process_type=process_type,
                context_key=context,
                payload=t.get("payload", {}),
            )

            tasks.append(task)

            # Si tu publisher espera dict:
            # self._task_publisher.publish(task.__dict__)
            self._task_publisher.publish(task)

        return tasks

    # ---------------- Public method: create or update process ---------------- #

    def run(
        self,
        *,
        tenant_id: str,
        process_type: str,
        event: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:

        # Obtener definición del proceso
        process_def = self._get_definition(process_type)

        # Cada proceso define su business_key
        if hasattr(process_def, "build_business_key"):
            business_key = process_def.build_business_key(context)
        else:
            raise RuntimeError(f"Process {process_type} must define build_business_key(context)")

        # Clave de Dynamo
        process_key = self._make_process_key(tenant_id, process_type, business_key)

        # Buscar proceso existente
        resp = self._table.get_item(
            Key={
                "process_key": process_key,
                "state_key": "CURRENT",
            }
        )
        item = resp.get("Item")

        # Si no existe → estado inicial
        if item is None:
            current_state = "INIT"
            stored_context: Dict[str, Any] = {}
            created_at = None
        else:
            current_state = item["state"]
            stored_context = item.get("context", {}) or {}
            created_at = item.get("created_at")

        # Merge del context nuevo con el existente
        merged_context = {**stored_context, **context}

        # Ejecutar transición
        next_state, task_defs = process_def.apply_transition(current_state, event, merged_context)

        # Persistir nuevo estado del proceso
        now = datetime.utcnow().isoformat()

        self._table.put_item(
            Item={
                "process_key": process_key,
                "state_key": "CURRENT",
                "tenant_id": tenant_id,
                "process_type": process_type,
                "business_key": business_key,
                "state": next_state,
                "context": merged_context,
                "created_at": created_at or now,
                "updated_at": now,
            }
        )

        # Publicar tareas generadas
        tasks = self._publish_tasks(
            task_defs=task_defs,
            process_type=process_type,
            context=merged_context,
        )

        return {
            "process_key": process_key,
            "state": next_state,
            "tasks": tasks,
        }
from typing import Dict, Any, Tuple

from core.process_engine import ProcessEngine
from core.process_registry import ProcessRegistry

from core.processes.whatspp_document_pipeline import WhatsappDocumentPipelineProcess
from core.processes.whatsapp_conversation import WhatsappConversationProcess

class EventProcessor:
    def __init__(
        self,
        processes_table,
        task_publisher: Any | None = None,
    ):
        ProcessRegistry.register(WhatsappDocumentPipelineProcess)
        ProcessRegistry.register(WhatsappConversationProcess)
        process_definitions = ProcessRegistry.all()

        self._engine = ProcessEngine(
            processes_table=processes_table,
            task_publisher=task_publisher,
            process_definitions=process_definitions,
        )

    def process(self, process_type: str, event: str, context: Dict[str, Any], payload: Dict[str, Any]) -> Tuple[bool, int]:

        self._engine.run(
            process_type=process_type,
            event=event,
            task_type=None,
            context=context,
            payload=payload
        )
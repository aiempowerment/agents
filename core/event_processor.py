from typing import Any, Tuple

from core.process_engine import ProcessEngine
from core.process_registry import ProcessRegistry

from core.processes.process_incoming_whatspp_document import ProcessIncomingWhatsappDocumentProcess
from core.processes.read_incoming_whatsapp_message import ReadIncomingWhatsappMessageProcess

class EventProcessor:
    def __init__(
        self,
        processes_table,
        task_publisher: Any | None = None,
    ):
        ProcessRegistry.register(ProcessIncomingWhatsappDocumentProcess)
        ProcessRegistry.register(ReadIncomingWhatsappMessageProcess)
        process_definitions = ProcessRegistry.all()

        self._engine = ProcessEngine(
            processes_table=processes_table,
            task_publisher=task_publisher,
            process_definitions=process_definitions,
        )

    def process(self, process_type: str, event: str, context: Any) -> Tuple[bool, int]:

        self._engine.run(
            process_type=process_type,
            event=event,
            context=context
        )
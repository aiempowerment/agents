from core.process_registry import ProcessRegistry


class ProcessIncomingWhatsappDocumentProcess:
    PROCESS_TYPE = "PROCESS_INCOMING_WHATSAPP_DOCUMENT"

    def build_business_key(ctx: dict) -> str:
        msg_id = ctx["msg_id"]

        return f"{msg_id}"

    def apply_transition(state: str, event: str, data: dict) -> tuple[str, list[dict]]:

        if state == "INIT" and event == "DOCUMENT_RECEIVED":
            task = {
                "task_type": "VALIDATE_INCOMING_WHATSAPP_DOCUMENT",
                "agent_type": "ACCOUNTING_ASSISTANT",
            }
            return "DOCUMENT_RECEIVED", [task]

        if state == "INIT" and event == "TASK_SUCCEEDED":
            task = {
                "task_type": "DETECT_PDF_ENCRYPTION",
                "agent_type": "ACCOUNTING_ASSISTANT",
            }
            return "DOCUMENT_VALIDATED", [task]

        if state == "DOCUMENT_VALIDATED" and event == "TASK_SUCCEEDED":
            task = {
                "task_type": "EXTRACT DATA",
                "agent_type": "ACCOUNTING_ASSISTANT",
            }
            return "DOCUMENT_OPEN", [task]
        


ProcessRegistry.register(ProcessIncomingWhatsappDocumentProcess)
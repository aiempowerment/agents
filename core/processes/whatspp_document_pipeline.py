from core.process_registry import ProcessRegistry


class WhatsappDocumentPipelineProcess:
    PROCESS_TYPE = "WHATSAPP_DOCUMENT_PIPELINE"

    @staticmethod
    def build_business_key(context: dict) -> str:
        return f"{context['msg_id']}#{context['document_id']}"

    @staticmethod
    def apply_transition(state: str, event: str, data: dict) -> tuple[str, list[dict]]:
        task_type = data.get("task_type")

        if state == "INIT" and event == "DOCUMENT_RECEIVED":
            return "VALIDATING", [
                {
                    "task_type": "VALIDATE_DOCUMENT",
                    "agent_type": "ACCOUNTING_ASSISTANT",
                }
            ]

        if task_type == "VALIDATE_DOCUMENT" and event == "TASK_SUCCEEDED":
            return "DETECTING_PDF_ENCRYPTION", [
                {
                    "task_type": "DETECT_PDF_ENCRYPTION",
                    "agent_type": "ACCOUNTING_ASSISTANT",
                }
            ]

        if task_type == "DETECT_PDF_ENCRYPTION" and event == "TASK_SUCCEEDED":
            return "EXTRACTION_DATA", [
                {
                    "task_type": "EXTRACT_DATA",
                    "agent_type": "ACCOUNTING_ASSISTANT",
                }
            ]

        if event == "TASK_FAILED":
            return "FAILED", []

        return state, []


ProcessRegistry.register(WhatsappDocumentPipelineProcess)
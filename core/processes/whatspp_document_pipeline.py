from core.process_registry import ProcessRegistry


class WhatsappDocumentPipelineProcess:
    PROCESS_TYPE = "WHATSAPP_DOCUMENT_PIPELINE"

    @staticmethod
    def build_business_key(context: dict) -> str:
        return f"{context['msg_id']}#{context['media_id']}"

    @staticmethod
    def apply_transition(state: str, event: str, task_type: str, payload: dict) -> tuple[str, list[dict]]:

        if state == "INIT" and event == "DOCUMENT_RECEIVED":
            return "VALIDATING", [
                {
                    "task_type": "VALIDATE_DOCUMENT",
                    "agent_type": "ACCOUNTING_ASSISTANT",
                    "payload": payload
                }
            ]
        if state == "WAITING_PASSWORD" and event == "PASSWORD_CHANGED":
            
            return "EXTRACTION_DATA", [
                    {
                        "task_type": "EXTRACT_DATA",
                        "agent_type": "ACCOUNTING_ASSISTANT",
                        "payload": payload
                    }
                ]
        
        if task_type:

            if task_type == "VALIDATE_DOCUMENT" and event == "TASK_SUCCEEDED":
                return "EXTRACTION_DATA", [
                    {
                        "task_type": "EXTRACT_DATA",
                        "agent_type": "ACCOUNTING_ASSISTANT",
                        "payload": payload
                    }
                ]

            if task_type == "EXTRACT_DATA" and event == "TASK_FAILED":
                error_type = payload["error_type"]

                if error_type=="PDF_PROTECTED":
                    return "PDF_UNLOCKING", [
                        {
                            "task_type": "PDF_UNLOCK",
                            "agent_type": "ACCOUNTING_ASSISTANT",
                            "payload": payload
                        }
                    ]

            if task_type == "PDF_UNLOCK" and event == "TASK_SUCCEEDED":

                return "EXTRACTION_DATA", [
                    {
                        "task_type": "EXTRACT_DATA",
                        "agent_type": "ACCOUNTING_ASSISTANT",
                        "payload": payload
                    }
                ]

            if task_type == "PDF_UNLOCK" and event == "TASK_FAILED":

                error_type = payload["error_type"]

                if error_type=="PASSWORD_NOT_FOUND":

                    payload["message"] = "No cuento con la contraseña. Cual es?"
                    return "WAITING_PASSWORD", [
                        {
                            "task_type": "SEND_WHATSAPP_MESSAGE",
                            "agent_type": "ACCOUNTING_ASSISTANT",
                            "payload": payload
                        }
                    ]
                if error_type=="WRONG_PASSWORD":

                    payload["message"] = "La contraseña que tengo es incorrecta. Cual es la correcta?"
                    return "WAITING_PASSWORD", [
                        {
                            "task_type": "SEND_WHATSAPP_MESSAGE",
                            "agent_type": "ACCOUNTING_ASSISTANT",
                            "payload": payload
                        }
                    ]

            if event == "TASK_FAILED":
                return "FAILED", []

        return state, []


ProcessRegistry.register(WhatsappDocumentPipelineProcess)
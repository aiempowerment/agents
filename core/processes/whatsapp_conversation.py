from core.process_registry import ProcessRegistry


class WhatsappConversationProcess:
    PROCESS_TYPE = "WHATSAPP_CONVERSATION"

    @staticmethod
    def build_business_key(context: dict) -> str:
        identity = context["identity"]
        return identity.split(":", 1)[-1]

    @staticmethod
    def apply_transition(state: str, event: str, task_type: str, payload: dict) -> tuple[str, list[dict]]:

        if event == "WHATSAPP_MESSAGE_RECEIVED":
            return "WAITING_IDLE", [
                {
                    "task_type": "ANSWER_INCOMING_WHATSAPP_MESSAGE",
                    "agent_type": "ACCOUNTING_ASSISTANT",
                    "debounce_policy": {"type": "messages_idle", "min_idle_seconds": 60},
                }
            ]

        if event == "LLM_ACTION_REQUESTED":
            return "WAITING_ACTION", [
                {
                    "task_type": payload["action"],
                    "agent_type": "ACCOUNTING_ASSISTANT",
                    "payload": payload
                }
            ]

        if event == "TASK_FAILED" and state == "WAITING_IDLE":
            return "FAILED", []
        
        if event == "TASK_SUCCEEDED" and state == "WAITING_IDLE":
            return "ANSWERED", []
        
        if event == "TASK_SUCCEEDED" and state == "WAITING_ACTION" and task_type == "SET_PASSWORD":
            return "ANSWERED", [
                {
                    "task_type": "REPROCESS_PENDING_FILES",
                    "agent_type": "ACCOUNTING_ASSISTANT"
                }
            ]

        return state, []


ProcessRegistry.register(WhatsappConversationProcess)
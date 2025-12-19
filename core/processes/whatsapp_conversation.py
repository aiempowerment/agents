from core.process_registry import ProcessRegistry


class WhatsappConversationProcess:
    PROCESS_TYPE = "WHATSAPP_CONVERSATION"

    @staticmethod
    def build_business_key(context: dict) -> str:
        identity = context["identity"]
        return identity.split(":", 1)[-1]

    @staticmethod
    def apply_transition(state: str, event: str, data: dict) -> tuple[str, list[dict]]:

        if event == "WHATSAPP_MESSAGE_RECEIVED":
            task = {
                "task_type": "ANSWER_INCOMING_WHATSAPP_MESSAGE",
                "agent_type": "ACCOUNTING_ASSISTANT",
                "debounce_policy": {"type": "messages_idle", "min_idle_seconds": 60},
            }
            return "WAITING_IDLE", [task]

        if state == "WAITING_IDLE" and event == "TASK_SUCCEEDED":
            return "ANSWERED", []

        if state == "WAITING_IDLE" and event == "TASK_FAILED":
            return "FAILED", []

        return state, []


ProcessRegistry.register(WhatsappConversationProcess)
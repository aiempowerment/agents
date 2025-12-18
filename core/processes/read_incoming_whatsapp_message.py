from core.process_registry import ProcessRegistry


class ReadIncomingWhatsappMessageProcess:
    PROCESS_TYPE = "READ_INCOMING_WHATSAPP_MESSAGE"

    def build_business_key(ctx: dict) -> str:
        identity = ctx["identity"]
        msg_id = ctx["msg_id"]

        return f"{identity}#{msg_id}"

    def apply_transition(state: str, event: str, data: dict) -> tuple[str, list[dict]]:
        if state == "INIT" and event == "WHATSAPP_MESSAGE_RECEIVED":
            return "MESSAGE_RECEIVED", [
                {
                    "task_type": "READ_INCOMING_WHATSAPP_MESSAGE",
                    "agent_type": "ACCOUNTING_ASSISTANT",
                    "payload": data,
                }
            ]

        return state, []


ProcessRegistry.register(ReadIncomingWhatsappMessageProcess)
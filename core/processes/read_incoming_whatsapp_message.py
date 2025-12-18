from core.process_registry import ProcessRegistry


class ReadIncomingWhatsappMessageProcess:
    PROCESS_TYPE = "READ_INCOMING_WHATSAPP_MESSAGE"

    def build_business_key(ctx: dict) -> str:
        identity = ctx["identity"]
        msg_id = ctx["msg_id"]

        return f"{identity}#{msg_id}"

    def apply_transition(state: str, event: str, data: dict) -> tuple[str, list[dict]]:

        if state == "INIT" and event == "MESSAGE_RECEIVED":
            debounce_policy = {
                "type": "messages_idle",
                "min_idle_seconds": 60,
            }
            task = {
                "task_type": "ANSWER_INCOMING_WHATSAPP_MESSAGE",
                "agent_type": "ACCOUNTING_ASSISTANT",
                "process_type": "READ_INCOMING_WHATSAPP_MESSAGE",
                # context_key=context_key,
                # payload=content,
                "debounce_policy": debounce_policy,
                # timestamp_iso=timestamp_iso,
                # timestamp_epoch=timestamp_epoch
            }

            return "MESSAGE_READING", [task]

        if state == "INIT" and event == "TASK_SUCCEEDED":

            return "FINISHED", []
        


ProcessRegistry.register(ReadIncomingWhatsappMessageProcess)
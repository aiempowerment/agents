from core.process_registry import ProcessRegistry


class SlackConversationProcess:
    PROCESS_TYPE = "SLACK_CONVERSATION"

    @staticmethod
    def build_business_key(context: dict) -> str:
        identity = context["identity"]
        return identity

    @staticmethod
    def apply_transition(state: str, event: str, task_type: str, payload: dict) -> tuple[str, list[dict]]:

        if event == "SLACK_MENTION_RECEIVED":
            return "WAITING_IDLE", [
                {
                    "task_type": "ANSWER_INCOMING_SLACK_MENTION",
                    "agent_type": "ACCOUNTING_ASSISTANT",
                    "payload": payload
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

        return state, []


ProcessRegistry.register(SlackConversationProcess)
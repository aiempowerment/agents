from typing import List, Dict


class ConversationContextBuilder:
    def __init__(self, max_messages: int = 20):
        self._max_messages = max_messages

    def build(self, history: List[Dict]) -> str:
        history_lines: List[str] = []

        for msg in history:
            timestamp = msg.get("timestamp")
            direction = msg.get("direction")
            text = msg.get("text", "")

            if direction == "in":
                speaker = "Cliente"
            elif direction == "out":
                speaker = "Agente"
            else:
                speaker = "Otro"

            history_lines.append(f"{speaker}({timestamp}): {text}")

        return "\n".join(history_lines[-self._max_messages:])
class ReadMessagesCapability:
    def __init__(self, messages_integration):
        self.messages_integration = messages_integration

    def __call__(self, identity: str):
        raw_history = self.messages_integration.get_history(identity)
        formatted = []

        for msg in raw_history:
            timestamp = msg.timestamp_iso.split("+")[0]
            direction = msg.direction

            content = msg.content or {}
            text = content.get("text")

            if isinstance(text, dict):
                text = text.get("body") or None

            if not text:
                text = "<non-text message>"

            formatted.append({
                "timestamp": timestamp,
                "direction": direction,
                "text": text,
            })

        return formatted
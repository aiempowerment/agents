class ReadMessagesCapability:
    def __init__(self, messages_integration):
        self.messages_integration = messages_integration

    def __call__(self, identity: str):
        raw_history = self.messages_integration.get_history(identity)
        formatted = []

        for msg in raw_history:
            timestamp = (msg.timestamp_iso or "").split("+")[0]
            direction = msg.direction

            content = msg.content or {}
            message_type = getattr(msg, "message_type", None) or content.get("media_type") or "text"

            text = content.get("text", "")

            if not text:
                if message_type == "document":
                    filename = content.get("filename") or "archivo"
                    mime_type = content.get("mime_type") or content.get("mimeType") or ""
                    text = f"[document] {filename} {mime_type}".strip()
                else:
                    text = "<non-text message>"

            formatted.append(
                {
                    "timestamp": timestamp,
                    "direction": direction,
                    "message_type": message_type,
                    "text": text,
                    "content": content,
                }
            )

        return formatted
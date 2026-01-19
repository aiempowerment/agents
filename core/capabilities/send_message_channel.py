class SendMessageChannelCapability:
    def __init__(self, slack_integration):
        self.slack_integration = slack_integration

    def __call__(self, channel_id: str, text: str, thread_ts: str | None = None):
        return self.slack_integration.send_message(
            channel_id=channel_id,
            text=text,
            thread_ts=thread_ts,
        )
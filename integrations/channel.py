class ChannelIntegration:
    def __init__(self, channel_service):
        self.channel_service = channel_service

    def send_message(self, channel_id: str, text: str, thread_ts: str | None = None):
        return self.channel_service.post_message(channel_id, text, thread_ts)
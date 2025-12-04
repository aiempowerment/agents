class SendMessageCapability:
    def __init__(self, messages_integration):
        self.messages_integration = messages_integration

    def __call__(self, phone_number: str, message: str) -> dict:
        return self.messages_integration.send_text(phone_number, message)
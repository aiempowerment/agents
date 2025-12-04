from datetime import datetime


class MessagesIntegration:
    def __init__(self, history_service, message_service):
        self.history_service = history_service
        self.message_service = message_service

    def get_history(self, identity: str):
        return self.history_service.get_history(identity)

    def send_text(self, phone_number: str, message: str) -> dict:
        result = self.message_service.send_text(phone_number, message)
        self._save_outgoing_text(phone_number, message, result)
        return result
    

    def _normalize_phone(self, phone: str) -> str:
        phone = phone.replace("+", "").strip()
        if phone.startswith("521") and len(phone) == 13:
            return "52" + phone[3:]
        return phone

    def _save_outgoing_text(self, phone_number: str, message: str, send_result: dict):
        msg_id = ""
        if isinstance(send_result, dict):
            response = send_result.get("response")
            if isinstance(response, dict):
                messages = response.get("messages") or []
                if messages:
                    msg_id = messages[0].get("id", "") or ""

        phone_number_normalized = self._normalize_phone(phone_number)
        identity = f"whatsapp:{phone_number_normalized}"

        self.history_service.save_message(
            identity=identity,
            direction="out",
            channel="whatsapp",
            message_type="text",
            content={"text": message},
            payload=send_result,
            msg_id=msg_id,
            timestamp=datetime.utcnow(),
        )
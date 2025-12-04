import requests
from datetime import datetime


class MessagesWhatsappService:
    name = "whatsapp"

    def __init__(self, tenant_config):
        self._config = tenant_config.get("whatsapp", {})
        self._token = self._config.get("token")
        self._number = self._config.get("number")
        self._url = f"https://graph.facebook.com/v21.0/{self._number}/messages"

    def send_template(self, phone: str, template_name: str, language_code: str = "en_US") -> dict:
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code}
            }
        }
        try:
            resp = requests.post(self._url, headers=headers, json=payload)
            resp.raise_for_status()
            return {
                "status": "sent",
                "service": self.name,
                "sent_at": datetime.utcnow().isoformat(),
                "response": resp.json(),
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "service": self.name,
                "sent_at": datetime.utcnow().isoformat(),
                "error": str(e),
            }

    def send_text(self, phone: str, message: str) -> dict:
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {
                "body": message
            }
        }
        try:
            resp = requests.post(self._url, headers=headers, json=payload)
            resp.raise_for_status()
            return {
                "status": "sent",
                "service": self.name,
                "sent_at": datetime.utcnow().isoformat(),
                "response": resp.json(),
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "service": self.name,
                "sent_at": datetime.utcnow().isoformat(),
                "error": str(e),
            }
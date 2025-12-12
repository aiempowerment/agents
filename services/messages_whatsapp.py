import json
from datetime import datetime
import urllib3


class MessagesWhatsappService:
    name = "whatsapp"

    def __init__(self, tenant_config):
        cfg = tenant_config.get("whatsapp", {})
        self._token = cfg.get("token")
        self._number = cfg.get("number")
        self._url = f"https://graph.facebook.com/v21.0/{self._number}/messages"
        self._http = urllib3.PoolManager()

    def _headers(self):
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    def _wrap_sent_response(self, data):
        return {
            "status": "sent",
            "service": self.name,
            "sent_at": datetime.utcnow().isoformat(),
            "response": data,
        }

    def _wrap_sent_error(self, err):
        return {
            "status": "error",
            "service": self.name,
            "sent_at": datetime.utcnow().isoformat(),
            "error": err,
        }

    def _wrap_fetched_response(self, data):
        return {
            "status": "ok",
            "service": self.name,
            "fetched_at": datetime.utcnow().isoformat(),
            "data": data,
        }

    def _wrap_fetched_error(self, err):
        return {
            "status": "error",
            "service": self.name,
            "fetched_at": datetime.utcnow().isoformat(),
            "error": err,
        }

    def _wrap_download_response(self, content: bytes):
        return {
            "status": "ok",
            "service": self.name,
            "fetched_at": datetime.utcnow().isoformat(),
            "content": content,
        }

    def _json_or_none(self, raw):
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return None

    def send_template(self, phone: str, template_name: str, language_code: str = "en_US") -> dict:
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
            },
        }

        resp = self._http.request(
            "POST",
            self._url,
            headers=self._headers(),
            body=json.dumps(payload),
        )

        if resp.status >= 200 and resp.status < 300:
            return self._wrap_sent_response(self._json_or_none(resp.data))

        return self._wrap_sent_error(f"{resp.status}: {resp.data}")

    def send_text(self, phone: str, message: str) -> dict:
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {"body": message},
        }

        resp = self._http.request(
            "POST",
            self._url,
            headers=self._headers(),
            body=json.dumps(payload),
        )

        if resp.status >= 200 and resp.status < 300:
            return self._wrap_sent_response(self._json_or_none(resp.data))

        return self._wrap_sent_error(f"{resp.status}: {resp.data}")

    def get_media_metadata(self, media_id: str) -> dict:
        url = f"https://graph.facebook.com/v21.0/{media_id}"

        resp = self._http.request(
            "GET",
            url,
            headers=self._headers(),
        )

        if resp.status >= 200 and resp.status < 300:
            return self._wrap_fetched_response(self._json_or_none(resp.data))

        return self._wrap_fetched_error(f"{resp.status}: {resp.data}")

    def download_media(self, download_url: str) -> dict:
        resp = self._http.request(
            "GET",
            download_url,
            headers=self._headers(),
        )

        if resp.status >= 200 and resp.status < 300:
            return self._wrap_download_response(resp.data)

        return self._wrap_fetched_error(f"{resp.status}: {resp.data}")
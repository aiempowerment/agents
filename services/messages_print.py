from datetime import datetime


class MessagesPrintService:
    name = "print"

    def __init__(self, tenant_config):
        config = {}

    def send_text(self, phone, message: str) -> dict:
        print(f"[PrintService to:{phone}] {message}")
        return {
            "status": "printed",
            "service": self.name,
            "sent_at": datetime.utcnow().isoformat(),
        }

    def send_template(self, phone: str, template_name: str, language_code: str = "en_US") -> dict:
        print(f"[MessagesPrintService to:{phone} template:{template_name}]")
        return {
            "status": "printed",
            "service": self.name,
            "sent_at": datetime.utcnow().isoformat(),
        }
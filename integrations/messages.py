from datetime import datetime
from typing import Optional, Dict, Any, List


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

    def parse_incoming_payload(self, payload: dict) -> List[dict]:
        events = []
        entries = payload.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                contacts = value.get("contacts", [])
                contact_wa = None
                if contacts:
                    contact_wa = contacts[0].get("wa_id")
                for msg in messages:
                    parsed = self._parse_single_incoming_message(payload, value, msg, contact_wa)
                    if parsed:
                        events.append(parsed)
        return events

    def _normalize_phone(self, phone: str) -> str:
        phone = phone.replace("+", "").strip()
        if phone.startswith("521") and len(phone) == 13:
            return "52" + phone[3:]
        return phone

    def _parse_single_incoming_message(
        self,
        payload: Dict[str, Any],
        value: Dict[str, Any],
        msg: Dict[str, Any],
        contact_wa: Optional[str],
    ) -> Optional[dict]:
        from_id = msg.get("from") or contact_wa
        if not from_id:
            return None

        identity = f"whatsapp:{self._normalize_phone(from_id)}"
        ts_raw = msg.get("timestamp") or value.get("timestamp")
        ts_epoch = self._to_epoch(ts_raw)
        ts_iso = self._to_iso(ts_raw)
        msg_id = msg.get("id", "") or ""
        msg_type = msg.get("type", "unknown")
        content = self._extract_content(msg)

        return {
            "identity": identity,
            "msg_id": msg_id,
            "message_type": msg_type,
            "timestamp_iso": ts_iso,
            "timestamp_epoch": ts_epoch,
            "content": content,
            "raw_msg": msg,
            "raw_value": value,
            "raw_payload": payload,
        }

    def _extract_content(self, msg: dict) -> dict:
        msg_type = msg.get("type")
        if msg_type == "text":
            return {"text": (msg.get("text") or {}).get("body")}
        if msg_type in ["image", "video", "audio", "document"]:
            media_info = msg.get(msg_type) or {}
            return {
                "media_id": media_info.get("id"),
                "media_type": msg_type,
                "mime_type": media_info.get("mime_type"),
                "filename": media_info.get("filename"),
            }
        return {}

    def _to_epoch(self, ts: Optional[str]) -> Optional[int]:
        if not ts:
            return None
        try:
            return int(ts)
        except ValueError:
            return None

    def _to_iso(self, ts: Optional[str]) -> str:
        try:
            return datetime.utcfromtimestamp(int(ts)).isoformat()
        except:
            return datetime.utcnow().isoformat()

    def _extract_msg(self, send_result: dict) -> dict:
        response = send_result.get("response")
        if not isinstance(response, dict):
            return {}
        messages = response.get("messages") or []
        if not messages:
            return {}
        return messages[0] or {}

    def _save_outgoing_text(self, phone_number: str, message: str, send_result: dict):
        msg = self._extract_msg(send_result)
        msg_id = msg.get("id", "")
        ts_raw = msg.get("timestamp")
        ts_epoch = self._to_epoch(ts_raw)
        ts_iso = self._to_iso(ts_raw)
        identity = f"whatsapp:{self._normalize_phone(phone_number)}"
        self.history_service.save_message(
            identity=identity,
            direction="out",
            channel="whatsapp",
            message_type="text",
            timestamp_iso=ts_iso,
            timestamp_epoch=ts_epoch,
            content={"text": message},
            payload=send_result,
            msg_id=msg_id,
        )
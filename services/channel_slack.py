import requests


class ChannelSlackService:
    def __init__(self, tenant_config):
        slack_config = (tenant_config.get("slack") or {})
        self._token = slack_config.get("token")
        if not self._token:
            raise ValueError("SLACK_TOKEN_MISSING")

    def post_message(self, channel_id, text, thread_ts=None):
        url = "https://slack.com/api/chat.postMessage"
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json; charset=utf-8",
        }
        payload = {
            "channel": channel_id,
            "text": text,
        }
        if thread_ts:
            payload["thread_ts"] = thread_ts

        r = requests.post(url, headers=headers, json=payload, timeout=10)
        data = r.json()
        if not data.get("ok"):
            raise RuntimeError(f"SLACK_API_ERROR: {data}")
        return data
from typing import Optional, List, Dict
import json


class LlmChatCapability:
    def __init__(self, llm_integration):
        self.llm_integration = llm_integration

    def __call__(
        self,
        prompt: str,
        system: Optional[str] = None,
        context_messages: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
    ) -> str:
        response = self.llm_integration.chat(
            prompt=prompt,
            system=system,
            context_messages=context_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        response_json = json.loads(response)

        response_format = {}

        if "action_payload" in response_json and isinstance(response_json.get("action_payload"), dict):
            response_format.update(response_json["action_payload"])

        if "reply_text" in response_json:
            response_format["reply_text"] = response_json["reply_text"]

        if "action" in response_json:
            response_format["action"] = response_json["action"]

        return response_format if response_format else response_json
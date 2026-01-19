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
        response_mode: str = "whatsapp",
    ):
        response = self.llm_integration.chat(
            prompt=prompt,
            system=system,
            context_messages=context_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        response_json = json.loads(response)

        if response_mode == "slack":
            reply_text = response_json.get("reply_text")
            ops = response_json.get("ops")

            if reply_text is None or not isinstance(reply_text, str):
                raise ValueError("LLM_RESPONSE_INVALID_REPLY_TEXT")

            if ops is None:
                raise ValueError("LLM_RESPONSE_OPS_MISSING")

            if not isinstance(ops, list):
                raise ValueError("LLM_RESPONSE_OPS_INVALID")

            normalized_ops = []
            for op_item in ops:
                if not isinstance(op_item, dict):
                    raise ValueError("LLM_RESPONSE_OP_ITEM_INVALID")

                op_name = op_item.get("op")
                data = op_item.get("data", {})

                if not op_name or not isinstance(op_name, str):
                    raise ValueError("LLM_RESPONSE_OP_NAME_MISSING")

                if data is None:
                    data = {}

                if not isinstance(data, dict):
                    raise ValueError("LLM_RESPONSE_OP_DATA_INVALID")

                normalized_ops.append(
                    {
                        "op": op_name,
                        "data": data,
                    }
                )

            return {
                "reply_text": reply_text,
                "ops": normalized_ops,
            }

        if response_mode == "whatsapp":
            response_format = {}

            if "action_payload" in response_json and isinstance(response_json.get("action_payload"), dict):
                response_format.update(response_json["action_payload"])

            if "reply_text" in response_json:
                response_format["reply_text"] = response_json["reply_text"]

            if "action" in response_json:
                response_format["action"] = response_json["action"]

            return response_format if response_format else response_json

        raise ValueError("LLM_RESPONSE_MODE_INVALID")
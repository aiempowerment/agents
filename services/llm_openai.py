from typing import Any, Dict, List, Optional
from openai import OpenAI


class LlmOpenaiService:
    def __init__(self, tenant_config: Dict[str, Any]):
        config = tenant_config.get("llm", {})
        self._config = config.get("openai", {})
        self._model = self._config.get("model")
        self._api_key = self._config.get("api_key")
        self._client: Optional[OpenAI] = None

    def _get_client(self) -> OpenAI:
        if self._client:
            return self._client

        if not self._api_key:
            raise RuntimeError(f"Missing API key in env var {self._api_key}")

        self._client = OpenAI(api_key=self._api_key)
        return self._client

    def ask(
        self,
        user_content: str,
        system_content: Optional[str] = None,
        extra_messages: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
    ) -> str:
        client = self._get_client()

        messages: List[Dict[str, str]] = []

        if system_content:
            messages.append({"role": "system", "content": system_content})

        if extra_messages:
            messages.extend(extra_messages)

        messages.append({"role": "user", "content": user_content})

        kwargs: Dict[str, Any] = {"temperature": temperature}
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        response = client.chat.completions.create(
            model=self._model,
            messages=messages,
            **kwargs,
        )

        return response.choices[0].message.content
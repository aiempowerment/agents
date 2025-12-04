from typing import Optional, List, Dict


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
        return self.llm_integration.chat(
            prompt=prompt,
            system=system,
            context_messages=context_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
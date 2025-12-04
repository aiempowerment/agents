from typing import Optional, List, Dict


class LlmIntegration:
    def __init__(self, llm_service):
        self.llm_service = llm_service

    def chat(
        self,
        prompt: str,
        system: Optional[str] = None,
        context_messages: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
    ) -> str:
        return self.llm_service.ask(
            user_content=prompt,
            system_content=system,
            extra_messages=context_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
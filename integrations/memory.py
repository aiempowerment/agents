from typing import Optional, Dict, Any


class MemoryIntegration:
    def __init__(self, memory_service):
        self.memory_service = memory_service

    def get_state(
        self,
        *,
        channel_id: str,
    ) -> Dict[str, Any]:
        return self.memory_service.get_state(
            channel_id=channel_id,
        )

    def update_state(
        self,
        *,
        channel_id: str,
        op: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        return self.memory_service.update_state(
            channel_id=channel_id,
            op=op,
            payload=payload,
        )
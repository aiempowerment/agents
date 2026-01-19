from typing import Dict, Any


class UpdateMemoryStateCapability:
    def __init__(self, memory_integration):
        self.memory_integration = memory_integration

    def __call__(
        self,
        *,
        channel_id: str,
        op: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:

        state = self.memory_integration.update_state(
            channel_id=channel_id,
            op=op,
            payload=payload,
        )

        return {
            "channel_id": channel_id,
            "op": op,
            "state": state,
        }
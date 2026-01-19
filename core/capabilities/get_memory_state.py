from typing import Dict, Any


class GetMemoryStateCapability:
    def __init__(self, memory_integration):
        self.memory_integration = memory_integration

    def __call__(
        self,
        channel_id: str,
    ) -> Dict[str, Any]:

        state = self.memory_integration.get_state(
            channel_id=channel_id,
        )

        if not state:
            return {
                "channel_id": channel_id,
                "state": None,
            }

        return {
            "channel_id": channel_id,
            "state": state,
        }
from typing import Dict, Any


class GetProcessStateCapability:
    def __init__(self, processes_integration):
        self.processes_integration = processes_integration

    def __call__(
        self,
        process_type: str,
        business_key: str,
    ) -> Dict[str, Any]:

        item = self.processes_integration.get_current(
            process_type=process_type,
            business_key=business_key,
        )

        if not item:
            return {
                "process_type": process_type,
                "business_key": business_key,
                "state": None,
            }

        return {
            "process_type": process_type,
            "business_key": business_key,
            "state": item.get("state"),
        }
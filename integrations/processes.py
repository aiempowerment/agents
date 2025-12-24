from typing import Optional, Dict, Any


class ProcessesIntegration:
    def __init__(self, processes_service):
        self.processes_service = processes_service

    def get_current(self, process_type: str, business_key: str) -> Optional[Dict[str, Any]]:
        return self.processes_service.get_current(
            process_type=process_type,
            business_key=business_key,
        )
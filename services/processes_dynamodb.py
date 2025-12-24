from typing import Dict, Any, Optional


class ProcessesDynamodbService:
    def __init__(self, processes_table):
        self._table = processes_table

    def get_current(
        self,
        *,
        process_type: str,
        business_key: str,
    ) -> Optional[Dict[str, Any]]:
        if not process_type:
            raise ValueError("PROCESS_TYPE_MISSING")
        if not business_key:
            raise ValueError("BUSINESS_KEY_MISSING")

        process_key = f"{process_type}#{business_key}"

        resp = self._table.get_item(
            Key={
                "process_key": process_key,
                "state_key": "CURRENT",
            }
        )

        return resp.get("Item")
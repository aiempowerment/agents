from typing import Dict, List


class MemoryOpsExecutor:
    def __init__(self, update_memory_capability):
        self.update_memory_capability = update_memory_capability

    def execute(
        self,
        *,
        channel_id: str,
        llm_output: Dict,
    ) -> Dict:
        if not isinstance(llm_output, dict):
            raise ValueError("LLM_OUTPUT_INVALID")

        reply_text = llm_output.get("reply_text", "")
        ops: List[Dict] = llm_output.get("ops", [])

        if ops is None:
            raise ValueError("LLM_OPS_MISSING")

        if not isinstance(ops, list):
            raise ValueError("LLM_OPS_INVALID")

        for idx, op_item in enumerate(ops):
            if not isinstance(op_item, dict):
                raise ValueError("LLM_OP_ITEM_INVALID")

            op = op_item.get("op")
            data = op_item.get("data", {})

            if not op:
                raise ValueError("LLM_OP_NAME_MISSING")

            if data is None:
                data = {}

            if not isinstance(data, dict):
                raise ValueError("LLM_OP_DATA_INVALID")

            self.update_memory_capability(
                channel_id=channel_id,
                op=op,
                payload=data,
            )

        return {
            "reply_text": reply_text,
            "executed_ops": [op["op"] for op in ops],
        }
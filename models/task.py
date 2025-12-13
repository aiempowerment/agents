from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Task:
    task_type: str
    agent_type: str
    process_type: str
    context_key: Dict[str, Any] = field(default_factory=dict)
    payload: Dict[str, Any] = field(default_factory=dict)
    debounce_policy: Optional[Dict[str, Any]] = None
    timestamp_iso: Optional[str] = None
    timestamp_epoch: Optional[int] = None
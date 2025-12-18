from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import uuid
from datetime import datetime, timezone
import time


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_epoch() -> int:
    return int(time.time())


@dataclass
class Task:
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    task_type: str = ""
    agent_type: str = ""
    process_type: str = ""
    context_key: Dict[str, Any] = field(default_factory=dict)
    payload: Dict[str, Any] = field(default_factory=dict)
    debounce_policy: Optional[Dict[str, Any]] = None

    timestamp_iso: str = field(default_factory=_now_iso)
    timestamp_epoch: int = field(default_factory=_now_epoch)
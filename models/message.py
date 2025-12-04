from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Message:
    identity: str
    message_key: str

    channel: str
    direction: str
    message_type: Optional[str] = ""

    timestamp_iso: Optional[str] = None
    timestamp_epoch: Optional[int] = None

    content: Dict[str, Any] = field(default_factory=dict)
    payload: Dict[str, Any] = field(default_factory=dict)
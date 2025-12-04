from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from models.task import Task

class Agent(ABC):
    required_capabilities = []

    def __init__(self, capabilities, process_engine):
        for cap in self.required_capabilities:
            if cap not in capabilities:
                raise ValueError(
                    f"{self.__class__.__name__} missing capability '{cap}'"
                )

        self.capabilities = capabilities
        self.process_engine = process_engine

    @abstractmethod
    def handle(self, task: Task) -> Dict[str, Any]:
        ...
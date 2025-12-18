from typing import Any, Dict, Type, Optional


class ProcessRegistry:
    _registry: Dict[str, Type[Any]] = {}

    @classmethod
    def register(cls, process_cls: Type[Any]) -> None:
        process_type = getattr(process_cls, "PROCESS_TYPE", None)
        if not process_type:
            raise RuntimeError(f"Process class {process_cls.__name__} must define PROCESS_TYPE")
        cls._registry[process_type] = process_cls

    @classmethod
    def get(cls, process_type: str) -> Optional[Type[Any]]:
        return cls._registry.get(process_type)

    @classmethod
    def all(cls) -> Dict[str, Type[Any]]:
        return dict(cls._registry)
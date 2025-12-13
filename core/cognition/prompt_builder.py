from pathlib import Path
from typing import Dict, Any, Union


class PromptBuilder:
    def __init__(self, base_dir: Union[str, Path]):
        self._base_dir = Path(base_dir)

    def load(self, name: str) -> str:
        path = self._base_dir / name
        return path.read_text(encoding="utf-8")

    def build(self, name: str, variables: Dict[str, Any]) -> str:
        template = self.load(name)

        for key, value in variables.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))

        return template
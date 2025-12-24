from typing import Iterable, Optional, List


class ListFilesCapability:
    def __init__(self, files_integration):
        self.files_integration = files_integration

    def __call__(
        self,
        directory: str,
        extensions: Optional[Iterable[str]] = None,
    ) -> List[str]:
        return self.files_integration.list_files(
            directory=directory,
            extensions=extensions,
        )
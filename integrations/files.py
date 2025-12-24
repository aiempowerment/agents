from typing import Iterable, Optional, List


class FilesIntegration:
    def __init__(self, files_service):
        self.files_service = files_service

    def list_files(
        self,
        directory: str,
        extensions: Optional[Iterable[str]] = None,
    ) -> List[str]:
        return self.files_service.list_files(
            directory=directory,
            extensions=extensions,
        )
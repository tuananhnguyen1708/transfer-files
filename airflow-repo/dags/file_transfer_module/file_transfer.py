from abc import ABC, abstractmethod


class FileTransfer(ABC):
    def __init__(self):
        # default temp folder in local
        self.local_temp_dir: str = '/tmp/transfer_files'
        # File list needs to be transferred
        self.process_files: list[str] = []

    @abstractmethod
    def list_all_files(self) -> list[str]:
        pass

    @abstractmethod
    def download_files(self) -> None:
        pass

    @abstractmethod
    def put_files(self) -> None:
        pass

    @abstractmethod
    def detect_new_files(self, file_list: list[str]) -> list[str]:
        pass

    @abstractmethod
    def close(self) -> None:
        pass

from typing import Optional, List


class ValidationService:
    def __init__(self):
        pass

    def validate_file(self, repository_key: str, file_path: str) -> dict:
        pass

    def validate_entity(self, repository_key: str, file_path: str, new_entity: dict, old_entity: dict):
        pass

    def validate_all_files(self, repository_key: str, file_paths: Optional[List[str]] = None):
        pass

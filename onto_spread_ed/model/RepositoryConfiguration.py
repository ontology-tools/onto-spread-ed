from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class SubOntologyConfiguration:
    release_file: str
    excel_file: str


DEFAULT = object()


@dataclass
class RepositoryConfiguration:
    short_name: str
    full_name: str

    id_digits: int = 6
    indexed_files: List[str] = field(default_factory=lambda: [r".*\.xlsx"])
    main_branch: str = "main"
    prefixes: Dict[str, str] = field(default_factory=lambda: {})
    release_file: str = field(default=DEFAULT)
    release_script_path: str = ".onto-ed/release_script.json"
    subontologies: Dict[str, SubOntologyConfiguration] = field(default_factory=lambda: {})

    def __post_init__(self):
        if self.release_file == DEFAULT:
            self.release_file = self.short_name.lower() + ".owl"

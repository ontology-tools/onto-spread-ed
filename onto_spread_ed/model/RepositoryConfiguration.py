from dataclasses import dataclass
from typing import Dict, List


@dataclass
class SubOntologyConfiguration:
    release_file: str
    excel_file: str


@dataclass
class RepositoryConfiguration:
    short_name: str
    full_name: str
    main_branch: str
    prefixes: Dict[str, str]
    indexed_files: List[str]

    release_file: str
    subontologies: Dict[str, SubOntologyConfiguration]

    id_digits: int

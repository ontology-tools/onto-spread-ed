import os
from typing import List, Optional

from .ColumnMapping import ColumnMappingFactory, ColumnMapping
from .SchemaLoader import SchemaLoader


class Schema:
    _mapping_factories: List[ColumnMappingFactory]

    def __init__(self, mapping_factories: List[ColumnMappingFactory],
                 ignored_fields: Optional[List[str]] = None) -> None:
        if ignored_fields is None:
            ignored_fields = []

        self._mapping_factories = mapping_factories
        self._ignored_fields = ignored_fields

    def is_ignored(self, header_name: str) -> bool:
        return header_name in self._ignored_fields

    def get_mapping(self, origin: str, header_name: str) -> Optional[ColumnMapping]:
        if self.is_ignored(header_name):
            return None

        return next(
            iter(m.create_mapping(origin, header_name) for m in self._mapping_factories if m.maps(header_name)), None)


_SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")

DEFAULT_SCHEMA = SchemaLoader.load(os.path.join(_SCHEMA_DIR, "default_entity_schema.yaml"))
DEFAULT_SCHEMA_DEFINITION = SchemaLoader.load_definition(os.path.join(_SCHEMA_DIR, "default_entity_schema.yaml"))
DEFAULT_IMPORT_SCHEMA = SchemaLoader.load(os.path.join(_SCHEMA_DIR, "default_import_schema.yaml"))

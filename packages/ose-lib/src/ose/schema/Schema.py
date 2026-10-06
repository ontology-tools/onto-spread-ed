from importlib.resources import files

from pydantic import BaseModel

from ose.schema.ColumnMapping import AnyColumnMapping, ColumnMapping


class Schema(BaseModel):
    extends: str | None = None
    ignored: list[str] = []
    mappings: list[AnyColumnMapping] = []

    def is_ignored(self, header_name: str) -> bool:
        return header_name in self.ignored

    def get_mapping(self, origin: str, header_name: str) -> ColumnMapping | None:
        if self.is_ignored(header_name):
            return None

        for mapping in self.mappings:
            if match := mapping.match(header_name):
                return mapping.for_column(origin, header_name, match)

        return None

    def extending(self, parent: "Schema") -> "Schema":
        return Schema(
            ignored=[
                *self.ignored,
                *(
                    i
                    for i in parent.ignored
                    if not any(m.match(i) for m in self.mappings)
                ),
            ],
            mappings=[*self.mappings, *parent.mappings],
        )


def resolve_schema(
    name: str, schemas: dict[str, Schema], _seen: tuple[str, ...] = ()
) -> Schema:
    if name in _seen:
        raise ValueError(
            f"Cyclic spreadsheet schema inheritance: {' -> '.join([*_seen, name])}"
        )
    if name not in schemas:
        raise ValueError(f"Unknown spreadsheet schema '{name}'")

    schema = schemas[name]
    if schema.extends is None:
        return schema

    return schema.extending(resolve_schema(schema.extends, schemas, (*_seen, name)))


def _load_builtin(file: str) -> Schema:
    return Schema.model_validate_json(files(__package__).joinpath(file).read_text())


DEFAULT_SCHEMA = _load_builtin("default.json")
DEFAULT_IMPORT_SCHEMA = _load_builtin("default_import.json")
BUILTIN_SCHEMAS: dict[str, Schema] = {
    "default": DEFAULT_SCHEMA,
    "import": DEFAULT_IMPORT_SCHEMA,
}

from whoosh.fields import Schema, TEXT, KEYWORD, ID, SchemaClass
from whoosh.formats import Existence, Positions, Frequency


class OntologyContentSchema(SchemaClass):
    repo = ID(stored=True)
    spreadsheet = ID(stored=True)
    class_id = ID(stored=True)
    label = TEXT(stored=True)
    definition = TEXT(stored=True)
    parent = KEYWORD(stored=True)
    tobereviewedby = TEXT(stored=True)


schema = OntologyContentSchema()

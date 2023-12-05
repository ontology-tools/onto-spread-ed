import unittest

from onto_spread_ed.model.ExcelOntology import ExcelOntology


class Roundtrip(unittest.TestCase):
    def test_something(self):
        o = ExcelOntology("https://example.com/")
        o.import_excel_ontology("bcio_upper", "/Users/bgehrk/development/ontologies/Upper Level BCIO/inputs/BCIO_Upper_Defs.xlsx")
        o.add_terms_from_excel("bcio", "/Users/bgehrk/development/ontologies/Behaviour/BCIO_behaviour.xlsx")
        o.add_imported_terms("bcio_external", "/Users/bgehrk/development/ontologies/Upper Level BCIO/inputs/BCIO_External_Imports.xlsx")
        o.resolve()
        result = o.verify()
        self.assertEqual(result.ok(), True)  # add assertion here


if __name__ == '__main__':
    unittest.main()

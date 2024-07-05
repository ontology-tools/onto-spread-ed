import csv
import hashlib
import logging
import os
import subprocess
from functools import reduce
from multiprocessing import Pool
from typing import Optional, Any, Dict, List, Union, Tuple

from .OntoloyBuildService import OntologyBuildService
from ..model.ExcelOntology import ExcelOntology, OntologyImport
from ..model.Relation import OWLPropertyType
from ..model.Result import Result
from ..model.TermIdentifier import TermIdentifier

ROBOT = os.environ.get("ROBOT", "robot")


def _import_id(imp: OntologyImport):
    h = hashlib.sha256()
    h.update(imp.purl.encode())
    return h.hexdigest()


class RobotOntologyBuildService(OntologyBuildService):
    _logger = logging.getLogger(__name__)

    def merge_imports(self,
                      imports: List[OntologyImport],
                      outfile: str,
                      iri: str,
                      main_ontology_name: str,
                      tmp_dir: str,
                      renamings: List[Tuple[str, str]],
                      new_parents: List[Tuple[str, str]]) -> Result[str]:

        download_path = os.path.join("/", "tmp", "onto-ed-release", "robot-download-cache")
        # download_path = os.path.join(tmp_dir, "robot-download-cache")
        os.makedirs(download_path, exist_ok=True)
        result = Result()
        with Pool(4) as p:
            results = p.starmap(self._download_ontology, {(x.purl, _import_id(x), download_path) for x in imports})
            result = reduce(lambda a, b: a + b, results, result)

            if result.has_errors():
                return result

            for imp in imports:
                src = os.path.join(download_path, _import_id(imp) + ".owl")
                dst = os.path.join(download_path, imp.id + ".owl")
                if os.path.exists(dst):
                    os.unlink(dst)

                os.link(src, dst)

            results = p.starmap(self._extract_slim_ontology, [(x, download_path) for x in imports])
            result = reduce(lambda a, b: a + b, results, result)

            if result.has_errors():
                return result

        result += self._merge_imported_ontologies(iri, outfile, main_ontology_name, download_path, imports, renamings,
                                                  new_parents)

        return result

    def _download_ontology(self, purl: str, name: str, download_path: str) -> Result[Union[str, Tuple]]:
        out = os.path.join(download_path, name + ".owl")
        if not os.path.exists(out):
            get_ontology_cmd = f'curl -L "{purl}" > {out}'
            return self._execute_command(get_ontology_cmd, shell_flag=True)

        return Result(())

    def _extract_slim_ontology(self, imp: OntologyImport, download_path: str) -> Result[Union[str, Tuple]]:
        filename = os.path.join(download_path, imp.id + ".slim.owl")
        slim_cmd = [ROBOT, 'merge',
                    '--input', f'"{os.path.join(download_path, imp.id + ".owl")}"',
                    'extract', '--method', 'MIREOT',
                    '--annotate-with-source', 'true',
                    '--upper-term', imp.root_id.id,
                    '--intermediates', imp.intermediates,
                    '--output', filename]
        for prefix, definition in imp.prefixes:
            slim_cmd.append('--prefix')
            slim_cmd.append(f'"{prefix}: {definition}"')

        for term in imp.imported_terms:
            slim_cmd.append('--lower-term')
            slim_cmd.append(term.id)

        slim_cmd = " ".join(slim_cmd)

        if os.path.exists(filename) and os.path.exists(filename + ".cache"):
            with open(filename + ".cache", "r") as f:
                c = f.readlines()
                if c is not None and len(c) >= 1:
                    cache = c[0]
                    if cache.strip() == slim_cmd.strip():
                        return Result(())

        result = self._execute_command(slim_cmd, shell_flag=True)
        if result.ok():
            with open(filename + ".cache", "w") as f:
                f.writelines([slim_cmd])
        return result

    def _merge_imported_ontologies(self, merged_iri: str, merged_file: str, main_ontology_name: str, download_path: str,
                                   imports: List[OntologyImport],
                                   renamings: List[Tuple[str, str]],
                                   new_parents: List[Tuple[str, str]]) -> Result[str]:
        """
        Merges previously added, downloaded, and extracted ontology terms into one merged ontology

        :param merged_iri: IRI of the new, merged ontology
        :param merged_file: Output filename
        :param main_ontology_name: Name of the main ontology to be included in an annotation
        :param download_path: Path where the imported ontologies were downloaded
        :return:
        """
        # Now merge all the imports into a single file
        cmd = [ROBOT]

        if len(renamings) + len(new_parents) > 0:
            modifications_file = os.path.join(download_path, "external_modifications.csv")
            with open(modifications_file, "w") as f:
                csv_writer = csv.DictWriter(f, ["ID", "Parent", "Label"])
                csv_writer.writeheader()
                csv_writer.writerow({"ID": "ID", "Parent": "SC %", "Label": "LABEL"})

                for (id, label) in renamings:
                    csv_writer.writerow({"ID": id, "Label": label})

                for (id, parent) in new_parents:
                    csv_writer.writerow({"ID": id, "Parent": parent})

            cmd += ["template", "--template", modifications_file]
            for imp in imports:
                cmd += [
                    *[x for (prefix, definition)
                      in imp.prefixes for x
                      in ["--prefix", f'"{prefix}: {definition}"']],
                ]

        cmd += ["merge"]

        for imp in imports:
            cmd.append('--input')
            cmd.append(os.path.join(download_path, imp.id + ".slim.owl"))

        cmd.extend(
            ['annotate', '--ontology-iri', merged_iri, '--version-iri', merged_iri, '--annotation rdfs:comment ',
             '"This file contains externally imported content for the ' + main_ontology_name +
             '. It was prepared using ROBOT and a custom script from a spreadsheet of imported terms."',
             '--output', merged_file])

        cmd = " ".join(cmd)

        return self._execute_command(cmd, shell_flag=True)

    def build_ontology(self, ontology: ExcelOntology, outfile: str, prefixes: Optional[Dict[str, str]],
                       dependency_files: Optional[List[str]], tmp_dir: str):
        # with NamedTemporaryFile("w",) as f:
        with open(os.path.join(tmp_dir, os.path.basename(outfile)) + ".csv", "w") as csv_file:
            internal_relations = [r.id for r in ontology.used_relations() if
                                  r.owl_property_type == OWLPropertyType.Internal]

            header = [
                ("type", "TYPE"),
                ("id", "ID"),
                ("label", "LABEL"),
                ("parent class", "SC % SPLIT=;"),
                ("parent relation", "SP % SPLIT=;"),
                ("logical definition", "EC %"),
                ("domain", "DOMAIN"),
                ("range", "RANGE"),
                ("equivalent relationship", "EP % SPLIT=;")
            ]

            for relation in ontology.used_relations():
                if relation.owl_property_type == OWLPropertyType.AnnotationProperty:
                    header.append((f"REL '{relation.label}'", f"A {relation.id} SPLIT=;"))
                elif relation.owl_property_type in [OWLPropertyType.DataProperty, OWLPropertyType.ObjectProperty]:
                    header.append((f"REL '{relation.label}'", f"SC '{relation.label}' some % SPLIT=;"))
                else:
                    pass

            fieldnames = [k for k, _ in header]
            writer = csv.DictWriter(csv_file, fieldnames, delimiter=',', quotechar='\"', quoting=csv.QUOTE_MINIMAL)

            writer.writeheader()
            writer.writerow(dict(header))

            for term in ontology.terms():
                row = {
                    "type": "class",
                    "id": term.id,
                    "label": term.label,
                    "parent class": ";".join(t.id for t in term.sub_class_of),
                    "logical definition": ";".join(t for t in term.equivalent_to)
                }

                for relation, value in term.relations:
                    if relation.id in internal_relations:
                        continue

                    row[f"REL '{relation.label}'"] = value.id if isinstance(value, TermIdentifier) else value

                writer.writerow(row)

            for relation in ontology.relations():
                if relation.owl_property_type == OWLPropertyType.Internal:
                    continue

                typ = {
                    OWLPropertyType.AnnotationProperty: "annotation property",
                    OWLPropertyType.ObjectProperty: "object property",
                    OWLPropertyType.DataProperty: "data property"
                }[relation.owl_property_type]
                row = {
                    "type": typ,
                    "id": relation.id,
                    "label": relation.label,
                    "parent relation": ";".join(r.id for r in relation.sub_property_of),
                    "domain": relation.domain.id if relation.domain is not None else None,
                    "range": relation.range.id if relation.range is not None else None,
                    "equivalent relationship": ";".join(p.id for p in relation.equivalent_relations)
                }

                for r, value in relation.relations:
                    row[f"REL '{r.label}'"] = value

                writer.writerow(row)

            template_command: List[str] = [ROBOT, 'template', '--template', csv_file.name]
            for prefix, definition in prefixes.items():
                template_command.append('--prefix')
                template_command.append(f'"{prefix}: {definition}"')
            template_command.extend(['--ontology-iri', f'"{ontology.iri()}"',
                                     '--output', f'"{outfile}"'
                                     ])

            # A bit of hacking to deal appropriately with external dependency files:
            if dependency_files is not None:
                dependency_file_name = os.path.join(tmp_dir, "imports.owl")
                # with NamedTemporaryFile("w", suffix="import.owl") as dependency_f:
                with open(dependency_file_name, "w") as dependency_f:

                    # Allow multiple dependencies. These will become OWL imports.
                    dependency_file_names = dependency_files
                    dependency_f.write(f"""<?xml version="1.0"?>
<rdf:RDF xmlns="http://www.semanticweb.org/ontologies/temporary#"
    xml:base="{tmp_dir}/"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:obo="http://purl.obolibrary.org/obo/"
    xmlns:owl="http://www.w3.org/2002/07/owl#"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:xml="http://www.w3.org/XML/1998/namespace"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
    xmlns:foaf="http://xmlns.com/foaf/0.1/"
    xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">
    <owl:Ontology rdf:about="http://www.semanticweb.org/ontologies/temporary/{ontology.iri().split('/')[-1]}">\n""")

                    for d in dependency_file_names:
                        dependency_f.write(
                            f"<owl:imports rdf:resource=\"./{d}\"/> \n")
                    dependency_f.write(" </owl:Ontology> \n</rdf:RDF> ")

                template_command.extend(['--input', dependency_f.name,
                                         "--merge-before",
                                         "--collapse-import-closure", "false"])

        return self._execute_command(" ".join(template_command), cwd=tmp_dir)

    def merge_ontologies(self, ontologies: List[str], outfile: str, iri: str, version_iri: str,
                         annotations: Dict[str, str]) -> Result[Any]:
        command = [ROBOT, "merge"]
        command += [f'"{s}"' for o in ontologies for s in ["--input", o]]
        command += ["annotate"]
        command += [f'"{s}"' for k, v in annotations.items() for s in ["--annotation", k, v]]
        command += ["--ontology-iri", f'"{iri}"']
        command += ["--version-iri", f'"{version_iri}"']
        command += ["--output", f'"{outfile}"']

        return self._execute_command(" ".join(command))

    def _execute_command(self, command_str: str, shell_flag=True, cwd=None) -> Result[str]:
        result = Result()
        self._logger.debug(f"Executing command: {command_str}")
        output = subprocess.Popen(command_str,
                                  cwd=cwd,
                                  shell=shell_flag,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
        stdout, stderr = output.communicate()

        if output.returncode != 0:
            result.error(command=command_str,
                         out=stdout.decode() if stdout is not None else None,
                         err=stderr.decode() if stderr is not None else None,
                         code=output.returncode)

        result.value = stdout.decode()
        return result

    def collapse_imports(self, file: str) -> Result[Any]:
        return self._execute_command(f'{ROBOT} merge --input "{file}" --output "{file}" -c true')

import asyncio
import csv
from functools import reduce
import hashlib
import logging
import os
import shlex
import subprocess
from typing import Optional, Any, Dict, List, Tuple, Literal

from ose.utils.asyncio import max_concurrency

from ose.building.OntoloyBuildService import OntologyBuildService
from ose.ontology import ExcelOntology, OntologyImport
from ose.schema import OWLPropertyType, TermIdentifier
from ose.result import Log, Result, ResultContext, Success, is_successful

ROBOT = os.environ.get("ROBOT", "robot")


def _import_id(imp: OntologyImport):
    h = hashlib.sha256()
    h.update(f"{imp.version_iri}|{imp.iri}".encode())
    return h.hexdigest()


class RobotOntologyBuildService(OntologyBuildService):
    _logger = logging.getLogger(__name__)

    def _create_catalog_file(self, tmp_dir, files: List[str]):
        uris = "\n".join(
            [
                f'<uri name="{f}" uri="file:{tmp_dir}/{f.split("/")[-1]}"/>'
                for f in files
            ]
        )
        content = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<catalog prefer="public" xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
    <group id="Folder Repository, directory=, recursive=true, Auto-Update=true, version=2" prefer="public" xml:base="">
{uris}
    </group>
</catalog>
"""
        with open(os.path.join(tmp_dir, "catalog-v001.xml"), "w") as f:
            f.write(content)

    async def merge_imports(
        self,
        imports: List[OntologyImport],
        outfile: str,
        iri: str,
        main_ontology_name: str,
        tmp_dir: str,
        renamings: List[
            Tuple[str, str, Literal["class", "object property", "data_property"]]
        ],
        new_parents: List[
            Tuple[str, str, Literal["class", "object property", "data_property"]]
        ],
    ) -> Result[tuple[()]]:
        with ResultContext() as log:
            download_path = os.path.join(
                "/", "tmp", "onto-ed-release", "robot-download-cache"
            )
            # download_path = os.path.join(tmp_dir, "robot-download-cache")
            os.makedirs(download_path, exist_ok=True)
            async with asyncio.TaskGroup() as tg:
                tasks = [
                    tg.create_task(
                        self._download_ontology(
                            imp.version_iri if imp.version_iri is not None else imp.iri,
                            _import_id(imp),
                            download_path,
                        )
                    )
                    for imp in imports
                ]

            log += reduce(lambda a, b: a + b, [t.result() for t in tasks], Log())

            if log.has_errors():
                return log.fail()

            for imp in imports:
                src = os.path.join(download_path, _import_id(imp) + ".owl")
                dst = os.path.join(download_path, imp.id + ".owl")
                if os.path.exists(dst):
                    os.unlink(dst)

                os.link(src, dst)

            async with asyncio.TaskGroup() as tg:
                tasks = [
                    tg.create_task(
                        self._extract_slim_ontology(
                            main_ontology_name, imp, download_path
                        )
                    )
                    for imp in imports
                ]

            log += reduce(lambda a, b: a + b, [t.result() for t in tasks], Log())

            if log.has_errors():
                return log.fail()

            log += await self._merge_imported_ontologies(
                iri,
                outfile,
                main_ontology_name,
                download_path,
                imports,
                renamings,
                new_parents,
            )

        return log.to_result()

    @max_concurrency(2)
    async def _download_ontology(
        self, iri: str, name: str, download_path: str
    ) -> Result[tuple[()]]:
        out = os.path.join(download_path, name + ".owl")
        if not os.path.exists(out):
            result = await self._execute_command(["curl", "-L", "-o", out, iri])

            if not is_successful(result):
                self._logger.error(f"Failed to download '{name}' from '{iri}'")

            return result.void()

        return Success(())

    @max_concurrency(2)
    async def _extract_slim_ontology(
        self, main_ontology_name: str, imp: OntologyImport, download_path: str
    ) -> Result[tuple[()]]:
        with ResultContext() as log:
            root_id = None
            if (
                imp.root_id is None
                or (root_id := imp.root_id.as_resolved_identifier()) is None
            ):
                log.warning(
                    type="missing-root-id",
                    msg=f"Missing root ID for import '{imp.id}'. Assuming owl:Thing",
                )

            filename = os.path.join(
                download_path, f"{imp.id}.{main_ontology_name}.slim.owl"
            )
            slim_cmd: list[str] = [
                ROBOT,
                "merge",
                "--input",
                os.path.join(download_path, imp.id + ".owl"),
                "extract",
                "--method",
                "MIREOT",
                "--annotate-with-source",
                "true",
            ]

            if root_id is not None:
                slim_cmd += ["--upper-term", root_id.id]

            if imp.intermediates is not None:
                slim_cmd += ["--intermediates", imp.intermediates]

            for prefix, definition in imp.prefixes:
                slim_cmd += ["--prefix", f"{prefix}: {definition}"]

            for term in imp.imported_terms:
                slim_cmd += ["--lower-term", term.id]

            if len(imp.excluding) > 0:
                slim_cmd += [
                    "remove",
                    "--preserve-structure",
                    "false",
                    *[a for x in imp.excluding for a in ["--term", x.id]],
                ]

            slim_cmd += ["--output", filename]
            cmd = shlex.join(slim_cmd)

            if os.path.exists(filename) and os.path.exists(filename + ".cache"):
                with open(filename + ".cache", "r") as f:
                    c = f.readlines()
                    if c is not None and len(c) >= 1:
                        cache = c[0]
                        if cache.strip() == cmd.strip():
                            return Success(())

            result = await self._execute_command(slim_cmd)
            if result.successful:
                with open(filename + ".cache", "w") as f:
                    f.writelines([cmd])

            log += result.void()

        return log.to_result()

    async def _merge_imported_ontologies(
        self,
        merged_iri: str,
        merged_file: str,
        main_ontology_name: str,
        download_path: str,
        imports: List[OntologyImport],
        renamings: List[
            Tuple[str, str, Literal["class", "object property", "data_property"]]
        ],
        new_parents: List[
            Tuple[str, str, Literal["class", "object property", "data_property"]]
        ],
    ) -> Result[tuple[()]]:
        """
        Merges previously added, downloaded, and extracted ontology terms into one merged ontology

        :param merged_iri: IRI of the new, merged ontology
        :param merged_file: Output filename
        :param main_ontology_name: Name of the main ontology to be included in an annotation
        :param download_path: Path where the imported ontologies were downloaded
        :return:
        """
        # Now merge all the imports into a single file
        build_cmd = [ROBOT]

        if len(renamings) + len(new_parents) > 0:
            modifications_file = os.path.join(
                download_path, "external_modifications.csv"
            )
            with open(modifications_file, "w") as f:
                csv_writer = csv.DictWriter(f, ["ID", "Type", "Parent", "Label"])
                csv_writer.writeheader()
                csv_writer.writerow(
                    {"ID": "ID", "Type": "TYPE", "Parent": "SC %", "Label": "LABEL"}
                )

                for id, label, type in renamings:
                    csv_writer.writerow({"ID": id, "Type": type, "Label": label})

                for id, parent, type in new_parents:
                    csv_writer.writerow({"ID": id, "Type": type, "Parent": parent})

            build_cmd += ["template", "--template", modifications_file]
            for imp in imports:
                build_cmd += [
                    *[
                        x
                        for (prefix, definition) in imp.prefixes
                        for x in ["--prefix", f"{prefix}: {definition}"]
                    ],
                ]

        build_cmd += ["merge"]

        for imp in imports:
            build_cmd.append("--input")
            build_cmd.append(
                os.path.join(download_path, f"{imp.id}.{main_ontology_name}.slim.owl")
            )

        build_cmd += [
            "reason",
            "--reasoner",
            "elk",
            "--exclude-tautologies",
            "true",
            "reduce",
            "remove",
            "--axioms",
            "structural-tautologies",
        ]

        build_cmd += [
            "annotate",
            "--ontology-iri",
            merged_iri,
            "--version-iri",
            merged_iri,
            "--annotation",
            "rdfs:comment",
            "This file contains externally imported content for the "
            + main_ontology_name
            + ". It was prepared using ROBOT and a custom script from a spreadsheet of imported terms.",
            "--output",
            merged_file,
        ]

        return (await self._execute_command(build_cmd)).void()

    async def build_ontology(
        self,
        ontology: ExcelOntology,
        outfile: str,
        prefixes: Optional[Dict[str, str]],
        dependency_iris: Optional[List[str]],
        tmp_dir: str,
        iri_prefix: str,
    ) -> Result[tuple[()]]:
        # Remove trailing slashes
        while iri_prefix.endswith("/"):
            iri_prefix = iri_prefix[:-1]

        with open(
            os.path.join(tmp_dir, os.path.basename(outfile)) + ".csv", "w"
        ) as csv_file:
            internal_relations = [
                r.id
                for r in ontology.used_relations()
                if r.owl_property_type == OWLPropertyType.Internal
            ]

            header = [
                ("type", "TYPE"),
                ("id", "ID"),
                ("label", "LABEL"),
                ("parent class", "SC % SPLIT=;"),
                ("parent relation", "SP % SPLIT=;"),
                ("logical definition", "EC %"),
                ("domain", "DOMAIN"),
                ("range", "RANGE"),
                ("equivalent relationship", "EP % SPLIT=;"),
            ]

            for used_relation in ontology.used_relations():
                if (
                    used_relation.owl_property_type
                    == OWLPropertyType.AnnotationProperty
                ):
                    header.append(
                        (
                            f"REL '{used_relation.label}'",
                            f"A {used_relation.id} SPLIT=;",
                        )
                    )
                elif used_relation.owl_property_type in [
                    OWLPropertyType.DataProperty,
                    OWLPropertyType.ObjectProperty,
                ]:
                    header.append(
                        (
                            f"REL '{used_relation.label}'",
                            f"SC '{used_relation.label}' some % SPLIT=;",
                        )
                    )
                else:
                    pass

            fieldnames = [k for k, _ in header]
            writer = csv.DictWriter(
                csv_file,
                fieldnames,
                delimiter=",",
                quotechar='"',
                quoting=csv.QUOTE_MINIMAL,
            )

            writer.writeheader()
            writer.writerow(dict(header))

            for term in ontology.terms():
                row = {
                    "type": "class",
                    "id": term.id,
                    "label": term.label,
                    "parent class": ";".join(t.id for t in term.sub_class_of),
                    "logical definition": ";".join(t for t in term.equivalent_to),
                }

                for term_relation, value in term.relations:
                    if term_relation.id in internal_relations:
                        continue

                    row[f"REL '{term_relation.label}'"] = (
                        value.id if isinstance(value, TermIdentifier) else value
                    )

                writer.writerow(row)

            for relation in ontology.relations():
                if relation.owl_property_type == OWLPropertyType.Internal:
                    continue

                typ = {
                    OWLPropertyType.AnnotationProperty: "annotation property",
                    OWLPropertyType.ObjectProperty: "object property",
                    OWLPropertyType.DataProperty: "data property",
                }[relation.owl_property_type]
                row = {
                    "type": typ,
                    "id": relation.id,
                    "label": relation.label,
                    "parent relation": ";".join(r.id for r in relation.sub_property_of),
                    "domain": (
                        relation.domain.id if relation.domain is not None else ""
                    ),
                    "range": relation.range.id if relation.range is not None else "",
                    "equivalent relationship": ";".join(
                        p.id for p in relation.equivalent_relations
                    ),
                }

                for term_relation, value in relation.relations:
                    row[f"REL '{term_relation.label}'"] = value

                writer.writerow(row)

            # A bit of hacking to deal appropriately with external dependency files:
            cmd: List[str] = [ROBOT]
            if dependency_iris is not None and len(dependency_iris) > 0:
                dependency_file_name = os.path.join(tmp_dir, "imports.owl")
                # with NamedTemporaryFile("w", suffix="import.owl") as dependency_f:
                with open(dependency_file_name, "w") as dependency_f:

                    # Allow multiple dependencies. These will become OWL imports.
                    dependency_file_names = [i.split("/")[-1] for i in dependency_iris]
                    dependency_f.write(f"""<?xml version="1.0"?>
<rdf:RDF xmlns="{iri_prefix}/imports.owl"
    xml:base="{iri_prefix}/imports.owl"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:obo="http://purl.obolibrary.org/obo/"
    xmlns:owl="http://www.w3.org/2002/07/owl#"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:xml="http://www.w3.org/XML/1998/namespace"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
    xmlns:foaf="http://xmlns.com/foaf/0.1/"
    xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">
    <owl:Ontology rdf:about="{iri_prefix}/imports.owl">\n""")

                    for d in dependency_iris:
                        dependency_f.write(f'<owl:imports rdf:resource="{d}"/> \n')
                    dependency_f.write(" </owl:Ontology> \n</rdf:RDF> ")

                    self._create_catalog_file(tmp_dir, dependency_iris)

                    cmd.extend(
                        [
                            "merge",
                            *[x for d in dependency_file_names for x in ["--input", d]],
                        ]
                    )

        cmd.extend(
            [
                "template",
                "--template",
                csv_file.name,
                "--collapse-import-closure",
                "false",
            ]
        )

        if prefixes is not None:
            cmd += [
                a
                for prefix, definition in prefixes.items()
                for a in ["--prefix", f"{prefix}: {definition}"]
            ]

        cmd += [
            "annotate",
            "--ontology-iri",
            str(ontology.iri()),
            "--output",
            outfile,
        ]

        result = await self._execute_command(cmd, cwd=tmp_dir)

        # Merge the import file to readd the OWL imports
        if (
            result.successful
            and dependency_iris is not None
            and len(dependency_iris) > 0
        ):
            cmd = [
                ROBOT,
                "merge",
                "--input",
                dependency_f.name,
                "--input",
                outfile,
                "--collapse-import-closure",
                "false",
                "annotate",
                "--ontology-iri",
                str(ontology.iri()),
                "reason",
                "--reasoner",
                "elk",
                "--exclude-tautologies",
                "true",
                "reduce",
                "remove",
                "--axioms",
                "structural-tautologies",
                "--output",
                outfile,
            ]

            result &= await self._execute_command(cmd, cwd=tmp_dir)

        return result.void()

    async def merge_ontologies(
        self,
        ontologies: List[str],
        outfile: str,
        iri: str,
        version_iri: str,
        annotations: Dict[str, str],
    ) -> Result[Any]:
        command = [ROBOT, "merge"]
        command += [s for o in ontologies for s in ["--input", o]]
        command += ["annotate"]
        command += [s for k, v in annotations.items() for s in ["--annotation", k, v]]
        command += ["--ontology-iri", iri]
        command += ["--version-iri", version_iri]

        command.extend(
            [
                "reason",
                "--reasoner",
                "elk",
                "--exclude-tautologies",
                "true",
                "reduce",
                "remove",
                "--axioms",
                "structural-tautologies",
            ]
        )

        command += ["--output", outfile]

        result = await self._execute_command(command)

        return result

    # def fix_iri(self, file: str, temp_dir: str, iri_prefix: str):
    #     with fileinput.FileInput(file, inplace=True, backup='.bak') as file:
    #         for line in file:
    #             print(line
    #                   .replace(temp_dir, iri_prefix)
    #                   .replace("http://www.semanticweb.org/ontologies/temporary", iri_prefix), end='')

    async def _execute_command(self, command: list[str], cwd=None) -> Result[str]:
        command_str = shlex.join(command)
        stdout = b""
        with ResultContext() as log:
            self._logger.debug(f"Executing command: {command_str}")
            proc = await asyncio.create_subprocess_exec(
                *command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                sout = stdout.decode() if stdout is not None else None
                serr = stderr.decode() if stderr is not None else None
                log.error(command=command_str, out=sout, err=serr, code=proc.returncode)
                self._logger.error(
                    f"Command exited with code {proc.returncode}: {command_str}\nSTDOUT: {sout}\nSTDERR: {serr}"
                )

        return log.to_result(stdout.decode())

    async def collapse_imports(self, file: str) -> Result[tuple[()]]:
        return (
            await self._execute_command(
                [ROBOT, "merge", "--input", file, "--output", file, "-c", "true"]
            )
        ).void()

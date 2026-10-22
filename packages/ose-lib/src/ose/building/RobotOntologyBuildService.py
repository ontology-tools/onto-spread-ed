import asyncio
import csv
import hashlib
import logging
import os
import shlex
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional, Any, Dict, List, Tuple, Literal
from uuid import uuid4
from xml.sax.saxutils import quoteattr

from ose.utils.asyncio import max_concurrency

from ose.building.OntologyBuildService import OntologyBuildService
from ose.ontology import ExcelOntology, OntologyImport
from ose.schema import OWLPropertyType, TermIdentifier
from ose.result import ResultContext, Result, with_result_context_method, is_successful

ROBOT = os.environ.get("ROBOT", "robot")

DEFAULT_CACHE_DIR = str(Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "ontospreaded")
"""Downloaded and extracted external ontologies, shared by all builds"""


def _import_id(imp: OntologyImport):
    h = hashlib.sha256()
    h.update(f"{imp.version_iri}|{imp.iri}".encode())
    return h.hexdigest()


def _partial_path(path: str) -> str:
    """
    A unique path next to `path` to write to before moving the file into place, so that readers never see it half
    written, even if several builds write it at once. It keeps the extension, from which ROBOT infers the format.
    """
    base, extension = os.path.splitext(path)
    return f"{base}.{uuid4().hex}.part{extension}"


class RobotOntologyBuildService(OntologyBuildService):
    """
    Builds ontologies with ROBOT. Every call works in a temporary directory of its own. Downloaded and extracted
    external ontologies are cached in `cache_dir`, which builds running in parallel can share.
    """

    _logger = logging.getLogger(__name__)

    def __init__(self, cache_dir: str | None = None) -> None:
        cache_dir = os.path.abspath(os.path.expanduser(
            cache_dir if cache_dir is not None else os.environ.get("OSE_ROBOT_CACHE_DIR", DEFAULT_CACHE_DIR)
        ))
        self._cache_max_age = float(os.environ.get("OSE_ROBOT_CACHE_MAX_AGE", "86400"))
        self._robot_version: str | None = None
        self._download_dir = os.path.join(cache_dir, "robot-download-cache")
        self._slim_dir = os.path.join(cache_dir, "robot-slim-cache")

    def _create_catalog_file(self, work_dir: str, files: Dict[str, str]) -> str:
        """Writes an XML catalog that resolves the IRIs in `files` to the local files they map to"""
        uris = "\n".join(
            f"        <uri name={quoteattr(iri)} uri={quoteattr(Path(file).resolve().as_uri())}/>"
            for iri, file in files.items()
        )
        content = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<catalog prefer="public" xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
    <group id="Folder Repository, directory=, recursive=true, Auto-Update=true, version=2" prefer="public" xml:base="">
{uris}
    </group>
</catalog>
"""
        catalog = os.path.join(work_dir, "catalog-v001.xml")
        with open(catalog, "w") as f:
            f.write(content)
        return catalog

    @with_result_context_method
    async def merge_imports(
        self,
        ctx: ResultContext,
        imports: List[OntologyImport],
        outfile: str,
        iri: str,
        main_ontology_name: str,
        renamings: List[
            Tuple[str, str, Literal["class", "object property", "data_property"]]
        ],
        new_parents: List[
            Tuple[str, str, Literal["class", "object property", "data_property"]]
        ],
    ) -> tuple[()]:
        os.makedirs(self._download_dir, mode=0o700, exist_ok=True)
        os.makedirs(self._slim_dir, mode=0o700, exist_ok=True)

        async with asyncio.TaskGroup() as tg:
            downloads = [
                tg.create_task(
                    self._download_ontology(
                        imp.version_iri if imp.version_iri is not None else imp.iri,
                        _import_id(imp),
                    )
                )
                for imp in imports
            ]

        for t in downloads:
            ctx.attempt(t.result())

        if ctx.log.has_errors():
            ctx.fail()

        async with asyncio.TaskGroup() as tg:
            slims = [tg.create_task(self._extract_slim_ontology(imp)) for imp in imports]

        slim_files = [ctx.attempt(t.result()) for t in slims]

        if ctx.log.has_errors():
            ctx.fail()

        with tempfile.TemporaryDirectory(prefix="ose-robot-") as work_dir:
            ctx.unwrap(
                await self._merge_imported_ontologies(
                    iri,
                    outfile,
                    main_ontology_name,
                    work_dir,
                    # Errors above abort; the filter narrows the result type.
                    [f for f in slim_files if f is not None],
                    imports,
                    renamings,
                    new_parents,
                )
            )

        return ()

    @max_concurrency(2)
    @with_result_context_method
    async def _download_ontology(self, ctx: ResultContext, iri: str, name: str) -> str:
        """Downloads the ontology unless it is cached already. Returns the path of the downloaded file."""
        out = os.path.join(self._download_dir, name + ".owl")
        if not os.path.exists(out) or time.time() - os.path.getmtime(out) >= self._cache_max_age:
            partial = _partial_path(out)
            try:
                # `--fail`: an HTTP error must not end up in the cache as the ontology
                result = await self._execute_command(["curl", "-L", "--fail", "-o", partial, iri])
                if is_successful(result):
                    os.replace(partial, out)
                else:
                    self._logger.error(f"Failed to download '{name}' from '{iri}'")
                ctx.unwrap(result)
            finally:
                Path(partial).unlink(missing_ok=True)

        return out

    @max_concurrency(2)
    @with_result_context_method
    async def _extract_slim_ontology(self, ctx: ResultContext, imp: OntologyImport) -> str:
        """
        Extracts the imported terms from the downloaded ontology. The result is cached by the ROBOT command, which
        contains everything it depends on. Returns the path of the extracted file.
        """
        root_id = None
        if (
            imp.root_id is None
            or (root_id := imp.root_id.as_resolved_identifier()) is None
        ):
            ctx.log.warning(
                type="missing-root-id",
                msg=f"Missing root ID for import '{imp.id}'. Assuming owl:Thing",
            )

        slim_cmd: list[str] = [
            ROBOT,
            "merge",
            "--input",
            os.path.join(self._download_dir, _import_id(imp) + ".owl"),
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

        # A refreshed download must invalidate an extraction even if the IRI
        # and requested terms stay the same.
        download = Path(self._download_dir) / (_import_id(imp) + ".owl")
        with download.open("rb") as downloaded:
            content_hash = hashlib.file_digest(downloaded, "sha256").hexdigest()
        if self._robot_version is None:
            self._robot_version = ctx.unwrap(await self._execute_command([ROBOT, "--version"]))
        key = hashlib.sha256((shlex.join(slim_cmd) + content_hash + self._robot_version).encode()).hexdigest()
        filename = os.path.join(self._slim_dir, f"{imp.id}.{key}.slim.owl")
        if os.path.exists(filename):
            return filename

        partial = _partial_path(filename)
        try:
            result = await self._execute_command([*slim_cmd, "--output", partial])
            if is_successful(result):
                os.replace(partial, filename)
            ctx.unwrap(result)
        finally:
            Path(partial).unlink(missing_ok=True)

        return filename

    async def _merge_imported_ontologies(
        self,
        merged_iri: str,
        merged_file: str,
        main_ontology_name: str,
        work_dir: str,
        slim_files: List[str],
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
        :param work_dir: Directory for temporary files of this build
        :param slim_files: The extracted ontologies to merge
        :return:
        """
        merged_file = os.path.abspath(merged_file)
        slim_files = [os.path.abspath(file) for file in slim_files]
        work_dir = os.path.abspath(work_dir)
        # Now merge all the imports into a single file
        build_cmd = [ROBOT]

        if len(renamings) + len(new_parents) > 0:
            modifications_file = os.path.join(work_dir, "external_modifications.csv")
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

        for slim_file in slim_files:
            build_cmd.append("--input")
            build_cmd.append(slim_file)

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

        return (await self._execute_command(build_cmd, cwd=work_dir)).void()

    @with_result_context_method
    async def build_ontology(
        self,
        ctx: ResultContext,
        ontology: ExcelOntology,
        outfile: str,
        prefixes: Optional[Dict[str, str]],
        dependency_iris: Optional[List[str]],
        local_ontologies: Dict[str, str],
        iri_prefix: str,
    ) -> tuple[()]:
        outfile = os.path.abspath(outfile)
        local_ontologies = {iri: os.path.abspath(file) for iri, file in local_ontologies.items()}
        missing = [iri for iri in dependency_iris or [] if iri not in local_ontologies]
        if missing:
            ctx.fail(type="unknown-dependency", msg=f"No local files for the dependencies {', '.join(missing)}")

        # Remove trailing slashes
        while iri_prefix.endswith("/"):
            iri_prefix = iri_prefix[:-1]

        with tempfile.TemporaryDirectory(prefix="ose-robot-") as work_dir:
            template_file = os.path.join(work_dir, os.path.basename(outfile)) + ".csv"
            self._write_template(ontology, template_file)

            # A bit of hacking to deal appropriately with external dependency files:
            cmd: List[str] = [ROBOT]
            catalog: str | None = None
            imports_file: str | None = None
            if dependency_iris:
                # Resolve the dependencies and their imports to the local files, not to the published versions
                catalog = self._create_catalog_file(work_dir, local_ontologies)
                imports_file = os.path.join(work_dir, "imports.owl")
                self._write_imports_file(imports_file, iri_prefix, dependency_iris)

                cmd.extend(
                    [
                        "merge",
                        "--catalog",
                        catalog,
                        *[x for iri in dependency_iris for x in ["--input", local_ontologies[iri]]],
                    ]
                )

            cmd.extend(
                [
                    "template",
                    "--template",
                    template_file,
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

            ctx.unwrap(await self._execute_command(cmd, cwd=work_dir))

            # Merge the import file to readd the OWL imports
            if catalog is not None and imports_file is not None:
                cmd = [
                    ROBOT,
                    "merge",
                    "--catalog",
                    catalog,
                    "--input",
                    imports_file,
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

                ctx.unwrap(await self._execute_command(cmd, cwd=work_dir))

        return ()

    @staticmethod
    def _write_imports_file(path: str, iri_prefix: str, dependency_iris: List[str]) -> None:
        """Writes an ontology that only imports the dependencies. These will become OWL imports."""
        with open(path, "w") as dependency_f:
            dependency_f.write(f"""<?xml version="1.0"?>
<rdf:RDF xmlns={quoteattr(iri_prefix + "/imports.owl")}
    xml:base={quoteattr(iri_prefix + "/imports.owl")}
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:obo="http://purl.obolibrary.org/obo/"
    xmlns:owl="http://www.w3.org/2002/07/owl#"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:xml="http://www.w3.org/XML/1998/namespace"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
    xmlns:foaf="http://xmlns.com/foaf/0.1/"
    xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">
    <owl:Ontology rdf:about={quoteattr(iri_prefix + "/imports.owl")}>\n""")

            for dependency_iri in dependency_iris:
                dependency_f.write(
                    f'<owl:imports rdf:resource={quoteattr(dependency_iri)}/> \n'
                )
            dependency_f.write(" </owl:Ontology> \n</rdf:RDF> ")

    @staticmethod
    def _write_template(ontology: ExcelOntology, path: str) -> None:
        """Writes the terms and relations of the ontology as ROBOT template"""
        with open(path, "w") as csv_file:
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

    @with_result_context_method
    async def _execute_command(
        self, ctx: ResultContext, command: list[str], cwd=None
    ) -> str:
        command_str = shlex.join(command)
        self._logger.debug(f"Executing command: {command_str}")
        try:
            proc = await asyncio.create_subprocess_exec(
                *command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except OSError as e:
            ctx.fail(type="command-failed", command=command_str, msg=str(e))

        try:
            stdout, stderr = await proc.communicate()
        except asyncio.CancelledError:
            try:
                proc.kill()
            except ProcessLookupError:
                pass  # The subprocess finished just before cancellation.
            waiter = asyncio.create_task(proc.communicate())
            while not waiter.done():
                try:
                    await asyncio.shield(waiter)
                except asyncio.CancelledError:
                    continue
            waiter.result()
            raise

        if proc.returncode != 0:
            sout = stdout.decode() if stdout is not None else None
            serr = stderr.decode() if stderr is not None else None
            ctx.log.error(
                type="command-failed",
                command=command_str,
                out=sout,
                err=serr,
                code=proc.returncode,
            )
            self._logger.error(
                f"Command exited with code {proc.returncode}: {command_str}\nSTDOUT: {sout}\nSTDERR: {serr}"
            )

        return stdout.decode()

    async def collapse_imports(self, file: str) -> Result[tuple[()]]:
        return (
            await self._execute_command(
                [ROBOT, "merge", "--input", file, "--output", file, "-c", "true"]
            )
        ).void()

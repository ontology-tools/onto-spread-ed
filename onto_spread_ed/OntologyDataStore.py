import re
from datetime import date
from urllib.request import urlopen

import networkx
import pyhornedowl
from pyhornedowl.model import SubClassOf, ObjectSomeValuesFrom, ObjectProperty, Class

from onto_spread_ed import constants
from onto_spread_ed.services.ConfigurationService import ConfigurationService


class OntologyDataStore:
    config: ConfigurationService
    node_props = {"shape": "box", "style": "rounded", "font": "helvetica"}
    rel_cols = {"has part": "blue", "part of": "blue", "contains": "green",
                "has role": "darkgreen", "is about": "darkgrey",
                "has participant": "darkblue"}

    def __init__(self, config: ConfigurationService):
        self.releases = {}
        self.releasedates = {}
        self.label_to_id = {}
        self.graphs = {}
        self.config = config

    def parseRelease(self, repo):
        config = self.config.get(repo)
        # Keep track of when you parsed this release
        self.graphs[repo] = networkx.MultiDiGraph()
        self.releasedates[repo] = date.today()
        # print("Release date ",self.releasedates[repo])

        # Get the ontology from the repository
        ontofilename = config.release_file
        full_repo_name = config.full_name
        branch = config.main_branch
        location = f"https://raw.githubusercontent.com/{full_repo_name}/{branch}/{ontofilename}"
        print("Fetching release file from", location)
        data = urlopen(location).read()  # bytes
        ontofile = data.decode('utf-8')

        # Parse it
        if ontofile:
            self.releases[repo] = pyhornedowl.open_ontology(ontofile)
            prefixes = config.prefixes
            for prefix in prefixes.items():
                self.releases[repo].add_prefix_mapping(prefix[0], prefix[1])
            for classIri in self.releases[repo].get_classes():
                classId = self.releases[repo].get_id_for_iri(classIri)
                if classId:
                    classId = classId.replace(":", "_")
                    # is it already in the graph?
                    if classId not in self.graphs[repo].nodes:
                        label = self.releases[repo].get_annotation(classIri, constants.RDFS_LABEL)
                        if label:
                            self.label_to_id[label.strip()] = classId
                            self.graphs[repo].add_node(classId,
                                                       label=label.strip().replace(" ", "\n"),
                                                       **OntologyDataStore.node_props)
                        else:
                            print("Could not determine label for IRI", classIri)
                else:
                    print("Could not determine ID for IRI", classIri)
            for classIri in self.releases[repo].get_classes():
                classId = self.releases[repo].get_id_for_iri(classIri)
                if classId:
                    parents = self.releases[repo].get_superclasses(classIri)
                    for p in parents:
                        plabel = self.releases[repo].get_annotation(p, constants.RDFS_LABEL)
                        if plabel and plabel.strip() in self.label_to_id:
                            self.graphs[repo].add_edge(self.label_to_id[plabel.strip()],
                                                       classId.replace(":", "_"), dir="back")
                    axioms = self.releases[repo].get_axioms_for_iri(classIri)  # other relationships
                    for a in axioms:
                        if isinstance(a.axiom, SubClassOf) and \
                                isinstance(a.axiom.sup, ObjectSomeValuesFrom) and \
                                isinstance(a.axiom.sup.ope, ObjectProperty) and \
                                isinstance(a.axiom.sup.bce, Class):
                            relIri = str(a.axiom.sup.ope.first)
                            targetIri = str(a.axiom.sup.bce.first)
                            rel_name = self.releases[repo].get_annotation(relIri, constants.RDFS_LABEL)
                            targetLabel = self.releases[repo].get_annotation(targetIri, constants.RDFS_LABEL)
                            if targetLabel and targetLabel.strip() in self.label_to_id:
                                if rel_name in OntologyDataStore.rel_cols:
                                    rcolour = OntologyDataStore.rel_cols[rel_name]
                                else:
                                    rcolour = "orange"
                                self.graphs[repo].add_edge(classId.replace(":", "_"),
                                                           self.label_to_id[targetLabel.strip()],
                                                           color=rcolour,
                                                           label=rel_name)

    def getReleaseLabels(self, repo):
        all_labels = set()
        for classIri in self.releases[repo].get_classes():
            all_labels.add(self.releases[repo].get_annotation(classIri, constants.RDFS_LABEL))
        return (all_labels)

    def parseSheetData(self, repo, data):
        for entry in data:
            if 'ID' in entry and \
                    'Label' in entry and \
                    'Definition' in entry and \
                    'Parent' in entry and \
                    len(entry['ID']) > 0:
                entryId = entry['ID'].replace(":", "_")
                entryLabel = entry['Label'].strip()
                self.label_to_id[entryLabel] = entryId
                self.graphs[repo].add_node(entryId, label=entryLabel.replace(" ", "\n"), **OntologyDataStore.node_props)
                if entryId in self.graphs[repo].nodes:
                    self.graphs[repo].remove_node(entryId)
                    self.graphs[repo].add_node(entryId, label=entryLabel.replace(" ", "\n"),
                                               **OntologyDataStore.node_props)
        for entry in data:
            if 'ID' in entry and \
                    'Label' in entry and \
                    'Definition' in entry and \
                    'Parent' in entry and \
                    len(entry['ID']) > 0:
                entryParent = re.sub(r"[\[].*?[\]]", "", str(entry['Parent'])).strip()
                if entryParent in self.label_to_id:  # Subclass relations
                    # Subclass relations must be reversed for layout
                    self.graphs[repo].add_edge(self.label_to_id[entryParent],
                                               entry['ID'].replace(":", "_"), dir="back")
                for header in entry.keys():  # Other relations
                    if entry[header] and str(entry[header]).strip() and "REL" in header:
                        # Get the rel name
                        rel_names = re.findall(r"'([^']+)'", header)
                        if len(rel_names) > 0:
                            rel_name = rel_names[0]
                            if rel_name in OntologyDataStore.rel_cols:
                                rcolour = OntologyDataStore.rel_cols[rel_name]
                            else:
                                rcolour = "orange"

                            relValues = entry[header].split(";")
                            for relValue in relValues:
                                if relValue.strip() in self.label_to_id:
                                    self.graphs[repo].add_edge(entry['ID'].replace(":", "_"),
                                                               self.label_to_id[relValue.strip()],
                                                               color=rcolour,
                                                               label=rel_name)

    # re-factored the following:
    # *new : getIDsFromSheetMultiSelect
    # getIDsFromSheet - related ID's from whole sheet
    # getIDsFromSelection - related ID's from selection in sheet
    # getRelatedIds - related ID's from list of ID's

    # *new: getIDSForSheetGraphMultiSelect
    # getDotForSheetGraph - graph from whole sheet
    # getDotForSelection - graph from selection in sheet
    # getDotForIDs - graph from ID list

    def getIDsFromSheetMultiSelect(self, repo, data, filter):
        ids = []
        for entry in data:
            if 'Curation status' in entry and str(entry['Curation status']) == "Obsolete":
                print("Obsolete: ", entry)
            else:
                if filter != [""] and filter != []:
                    for f in filter:
                        if str(entry['Curation status']) == f:
                            if 'ID' in entry and len(entry['ID']) > 0:
                                ids.append(entry['ID'].replace(":", "_"))
                            if 'Parent' in entry:
                                entryParent = re.sub(r"[\[].*?[\]]", "", str(entry['Parent'])).strip()
                                if entryParent in self.label_to_id:
                                    ids.append(self.label_to_id[entryParent])
                            if ":" in entry['ID'] or "_" in entry['ID']:
                                entryIri = self.releases[repo].get_iri_for_id(entry['ID'].replace("_", ":"))
                                if entryIri:
                                    descs = pyhornedowl.get_descendants(self.releases[repo], entryIri)
                                    for d in descs:
                                        ids.append(self.releases[repo].get_id_for_iri(d).replace(":", "_"))
                            if self.graphs[repo]:
                                graph_descs = None
                                try:
                                    graph_descs = networkx.algorithms.dag.descendants(self.graphs[repo],
                                                                                      entry['ID'].replace(":", "_"))
                                except networkx.exception.NetworkXError:
                                    print("NetworkXError sheet multiselect: ", entry['ID'])

                                if graph_descs is not None:
                                    for g in graph_descs:
                                        if g not in ids:
                                            ids.append(g)

        return (ids)

    def getIDsFromSheet(self, repo, data, filter):
        # list of ids from sheetExternal
        ids = []
        for entry in data:
            if 'Curation status' in entry and str(entry['Curation status']) == "Obsolete":
                print("Obsolete: ", entry)
            else:
                if filter != "":
                    if str(entry['Curation status']) == filter:
                        if 'ID' in entry and len(entry['ID']) > 0:
                            ids.append(entry['ID'].replace(":", "_"))

                        if 'Parent' in entry:
                            entryParent = re.sub(r"[\[].*?[\]]", "", str(entry['Parent'])).strip()
                            if entryParent in self.label_to_id:
                                ids.append(self.label_to_id[entryParent])

                        if ":" in entry['ID'] or "_" in entry['ID']:
                            entryIri = self.releases[repo].get_iri_for_id(entry['ID'].replace("_", ":"))
                            if entryIri:
                                descs = pyhornedowl.get_descendants(self.releases[repo], entryIri)
                                for d in descs:
                                    ids.append(self.releases[repo].get_id_for_iri(d).replace(":", "_"))
                        if self.graphs[repo]:
                            graph_descs = None
                            try:
                                graph_descs = networkx.algorithms.dag.descendants(self.graphs[repo],
                                                                                  entry['ID'].replace(":", "_"))
                            except networkx.exception.NetworkXError:
                                print("NetworkXError sheet filter: ", entry['ID'])

                            if graph_descs is not None:
                                for g in graph_descs:
                                    if g not in ids:
                                        ids.append(g)
                else:
                    if 'ID' in entry and len(entry['ID']) > 0:
                        ids.append(entry['ID'].replace(":", "_"))

                    if 'Parent' in entry:
                        entryParent = re.sub(r"[\[].*?[\]]", "", str(entry['Parent'])).strip()
                        print("found entryParent: ", entryParent)
                        if entryParent in self.label_to_id:
                            ids.append(self.label_to_id[entryParent])
                    if ":" in entry['ID'] or "_" in entry['ID']:
                        entryIri = self.releases[repo].get_iri_for_id(entry['ID'].replace("_", ":"))
                        if entryIri:
                            descs = pyhornedowl.get_descendants(self.releases[repo], entryIri)
                            for d in descs:
                                ids.append(self.releases[repo].get_id_for_iri(d).replace(":", "_"))
                    if self.graphs[repo]:
                        graph_descs = None
                        try:
                            graph_descs = networkx.algorithms.dag.descendants(self.graphs[repo],
                                                                              entry['ID'].replace(":", "_"))
                        except networkx.exception.NetworkXError:
                            print("NetworkXError Sheet: ", entry['ID'])

                        if graph_descs is not None:
                            for g in graph_descs:
                                if g not in ids:
                                    ids.append(g)
        return (ids)

    def getIDsFromSelectionMultiSelect(self, repo, data, selectedIds, filter):
        # Add all descendents of the selected IDs, the IDs and their parents.
        ids = []
        for id in selectedIds:
            entry = data[id]
            # don't visualise rows which are set to "Obsolete":
            if 'Curation status' in entry and str(entry['Curation status']) == "Obsolete":
                pass
            else:
                if filter != [""] and filter != []:
                    for f in filter:
                        if str(entry['Curation status']) == f:
                            if str(entry['ID']) and str(entry['ID']).strip():  # check for none and blank ID's
                                if 'ID' in entry and len(entry['ID']) > 0:
                                    ids.append(entry['ID'].replace(":", "_"))
                                if 'Parent' in entry:
                                    entryParent = re.sub(r"[\[].*?[\]]", "", str(entry['Parent'])).strip()
                                    if entryParent in self.label_to_id:
                                        ids.append(self.label_to_id[entryParent])
                                if ":" in entry['ID'] or "_" in entry['ID']:
                                    entryIri = self.releases[repo].get_iri_for_id(entry['ID'].replace("_", ":"))
                                    if entryIri:
                                        descs = pyhornedowl.get_descendants(self.releases[repo], entryIri)
                                        for d in descs:
                                            ids.append(self.releases[repo].get_id_for_iri(d).replace(":", "_"))
                                if self.graphs[repo]:
                                    graph_descs = None
                                    try:
                                        graph_descs = networkx.algorithms.dag.descendants(self.graphs[repo],
                                                                                          entry['ID'].replace(":", "_"))
                                    except networkx.exception.NetworkXError:
                                        print("NetworkXError selection multiselect: ", entry['ID'])

                                    if graph_descs is not None:
                                        for g in graph_descs:
                                            if g not in ids:
                                                ids.append(g)
        return (ids)

    def getIDsFromSelection(self, repo, data, selectedIds, filter):
        # Add all descendents of the selected IDs, the IDs and their parents.
        ids = []
        for id in selectedIds:
            entry = data[id]
            # don't visualise rows which are set to "Obsolete":
            if 'Curation status' in entry and str(entry['Curation status']) == "Obsolete":
                pass
            else:
                if filter != "":
                    if str(entry['Curation status']) == filter:
                        if str(entry['ID']) and str(entry['ID']).strip():  # check for none and blank ID's
                            if 'ID' in entry and len(entry['ID']) > 0:
                                ids.append(entry['ID'].replace(":", "_"))
                            if 'Parent' in entry:
                                entryParent = re.sub(r"[\[].*?[\]]", "", str(entry['Parent'])).strip()
                                if entryParent in self.label_to_id:
                                    ids.append(self.label_to_id[entryParent])
                            if ":" in entry['ID'] or "_" in entry['ID']:
                                entryIri = self.releases[repo].get_iri_for_id(entry['ID'].replace("_", ":"))
                                if entryIri:
                                    descs = pyhornedowl.get_descendants(self.releases[repo], entryIri)
                                    for d in descs:
                                        ids.append(self.releases[repo].get_id_for_iri(d).replace(":", "_"))
                            if self.graphs[repo]:
                                graph_descs = None
                                try:
                                    graph_descs = networkx.algorithms.dag.descendants(self.graphs[repo],
                                                                                      entry['ID'].replace(":", "_"))
                                except networkx.exception.NetworkXError:
                                    print("NetworkXError selection filter: ", str(entry['ID']))

                                if graph_descs is not None:
                                    for g in graph_descs:
                                        if g not in ids:
                                            ids.append(g)
                else:
                    if str(entry['ID']) and str(entry['ID']).strip():  # check for none and blank ID's
                        if 'ID' in entry and len(entry['ID']) > 0:
                            ids.append(entry['ID'].replace(":", "_"))
                        if 'Parent' in entry:
                            entryParent = re.sub(r"[\[].*?[\]]", "", str(entry['Parent'])).strip()
                            if entryParent in self.label_to_id:
                                ids.append(self.label_to_id[entryParent])
                        if ":" in entry['ID'] or "_" in entry['ID']:
                            entryIri = self.releases[repo].get_iri_for_id(entry['ID'].replace("_", ":"))
                            if entryIri:
                                descs = pyhornedowl.get_descendants(self.releases[repo], entryIri)
                                for d in descs:
                                    ids.append(self.releases[repo].get_id_for_iri(d).replace(":", "_"))
                        if self.graphs[repo]:
                            graph_descs = None
                            try:
                                graph_descs = networkx.algorithms.dag.descendants(self.graphs[repo],
                                                                                  entry['ID'].replace(":", "_"))
                            except networkx.exception.NetworkXError:
                                print("NetworkXError selection all: ", str(entry['ID']))

                            if graph_descs is not None:
                                for g in graph_descs:
                                    if g not in ids:
                                        ids.append(g)
        return (ids)

    def getRelatedIDs(self, repo, selectedIds):
        # Add all descendents of the selected IDs, the IDs and their parents.
        ids = []
        for id in selectedIds:
            ids.append(id.replace(":", "_"))
            if ":" in id or "_" in id:
                entryIri = self.releases[repo].get_iri_for_id(id.replace("_", ":"))

                if entryIri:
                    descs = pyhornedowl.get_descendants(self.releases[repo], entryIri)
                    for d in descs:
                        ids.append(self.releases[repo].get_id_for_iri(d).replace(":", "_"))

                    superclasses = self.releases[repo].get_superclasses(entryIri)
                    for s in superclasses:
                        ids.append(self.releases[repo].get_id_for_iri(s).replace(":", "_"))
            if self.graphs[repo]:
                graph_descs = None
                try:
                    graph_descs = networkx.algorithms.dag.descendants(self.graphs[repo], id.replace(":", "_"))
                except networkx.exception.NetworkXError:
                    print("NetworkXError relatedIDs: ", str(id))

                if graph_descs is not None:
                    for g in graph_descs:
                        if g not in ids:
                            ids.append(g)
        return (ids)

    def getDotForSheetGraph(self, repo, data, filter):
        # Get a list of IDs from the sheet graph
        # todo: is there a better way to do this?
        if hasattr(filter, 'lower'):  # check if filter is a string
            ids = OntologyDataStore.getIDsFromSheet(self, repo, data, filter)
        else:  # should be a list then
            ids = OntologyDataStore.getIDsFromSheetMultiSelect(self, repo, data, filter)
        subgraph = self.graphs[repo].subgraph(ids)
        P = networkx.nx_pydot.to_pydot(subgraph)
        return (P)

    def getDotForSelection(self, repo, data, selectedIds, filter):
        # Add all descendents of the selected IDs, the IDs and their parents.
        # todo: is there a better way to do this?
        if hasattr(filter, 'lower'):  # check if filter is a string
            ids = OntologyDataStore.getIDsFromSelection(self, repo, data, selectedIds, filter)
        else:  # should be a list then
            ids = OntologyDataStore.getIDsFromSelectionMultiSelect(self, repo, data, selectedIds, filter)
        # Then get the subgraph as usual
        subgraph = self.graphs[repo].subgraph(ids)
        P = networkx.nx_pydot.to_pydot(subgraph)
        return (P)

    def getDotForIDs(self, repo, selectedIds):
        # Add all descendents of the selected IDs, the IDs and their parents.
        ids = OntologyDataStore.getRelatedIDs(self, repo, selectedIds)
        # Then get the subgraph as usual
        subgraph = self.graphs[repo].subgraph(ids)
        P = networkx.nx_pydot.to_pydot(subgraph)
        return (P)

    # to create a dictionary and add all info to it, in the relevant place
    def getMetaData(self, repo, allIDS):
        DEFN = "http://purl.obolibrary.org/obo/IAO_0000115"
        SYN = "http://purl.obolibrary.org/obo/IAO_0000118"

        label = ""
        definition = ""
        synonyms = ""
        entries = []

        for classIri in self.releases[repo].get_classes():
            classId = self.releases[repo].get_id_for_iri(classIri).replace(":", "_")
            for id in allIDS:
                if id is not None:
                    if classId == id:
                        label = self.releases[repo].get_annotation(classIri, constants.RDFS_LABEL)  # yes
                        if self.releases[repo].get_annotation(classIri, DEFN) is not None:
                            definition = self.releases[repo].get_annotation(classIri, DEFN).replace(",", "").replace(
                                "'", "").replace("\"", "")
                        else:
                            definition = ""
                        if self.releases[repo].get_annotation(classIri, SYN) is not None:
                            synonyms = self.releases[repo] \
                                .get_annotation(classIri, SYN) \
                                .replace(",", "") \
                                .replace("'", "") \
                                .replace("\"", "")
                        else:
                            synonyms = ""
                        entries.append({
                            "id": id,
                            "label": label,
                            "synonyms": synonyms,
                            "definition": definition,
                        })
        return (entries)

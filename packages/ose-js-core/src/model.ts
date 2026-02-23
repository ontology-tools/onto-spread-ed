export interface ReleaseScriptFile {
    needs: string[];
    sources: {
        file: string;
        type: "classes" | "relations" | "individuals" | "owl";
    }[];
    target: {
        file: string;
        iri: string;
        ontology_annotations: { [K: string]: string };
        publish: boolean;
    };
    addParentsFile: string | null;
    renameTermFile: string | null;

}

export interface ReleaseScript {
    external: ReleaseScriptFile;
    files: { [K: string]: ReleaseScriptFile };
    full_repository_name: string;
    iri_prefix: string;
    prefixes: { [K: string]: string };
    short_repository_name: string;
    steps: {
        args: any,
        name: string
    }[];
}


export interface Release<D = Date> {
    id: number
    state: "starting" | "running" | "completed" | "canceled" | "errored" | "waiting-for-user"
    running: boolean
    step: number
    details: { [k: string]: any }
    started_by: string,
    release_script: ReleaseScript,
    start: D
    end: D
    worker_id: string,
    included_files: string[]
}

// Same as ose/model/ExcelOntology.py
export type DiagnosticKind =
    "unknown-column" |
    "incomplete-term" |
    "unknown-relation" |
    "missing-label" |
    "missing-id" |
    "inconsistent-import" |
    "missing-import" |
    "no-parent" |
    "unknown-parent" |
    "missing-parent" | "ignored-parent" |
    "unknown-disjoint" |
    "missing-disjoint" | "ignored-disjoint" |
    "unknown-relation-value" |
    "missing-relation-value" |
    "ignored-relation-value" |
    "unknown-domain" |
    "missing-domain" |
    "ignored-domain" |
    "unknown-range" |
    "missing-range" |
    "ignored-range" |
    "duplicate"

export interface Diagnostic {
    type: DiagnosticKind,

    [K: string]: any
}

export type Severity = "error" | "warning" | "info";

export interface TermIdentifier {
    id?: string
    label?: string
}

export interface Term {
    id: string
    label: string
    synonyms: string[]
    origin: [string, number]
    relations: [[TermIdentifier, any]][]
    sub_class_of: TermIdentifier[]
    equivalent_to: string[]
    disjoint_with: TermIdentifier[]
}

export type AutoFixState = "loading" | "impossible" | "fixed" | "loaded";

export interface RepositoryConfig {
    short_name: string
    full_name: string

    id_digits: number
    indexed_files: string[]
    main_branch: string
    prefixes: { [K: string]: string }
    release_file: string
    release_script_path: string
    subontologies: {
        [K: string]: {
            release_file: string
            excel_file: string
        }
    }
    readonly_files: {[K: string]: string}
    validation: ("include-external" | "include-dependencies")[]
}

interface _BaseChangeRecord {
    type: "change" | "add" | "delete",
    row: number,
}

export interface UpdateChangeRecord extends _BaseChangeRecord {
    type: "change",
    oldFields: { [k: string]: string },
    newFields: { [k: string]: string }
}

export interface AddChangeRecord extends _BaseChangeRecord {
    type: "add",
    newFields: { [k: string]: string },
    position: number,
}

export interface DeleteChangeRecord extends _BaseChangeRecord {
    type: "delete",
    oldFields: { [k: string]: string },
    position: number,
}

export type ChangeRecord = UpdateChangeRecord | AddChangeRecord | DeleteChangeRecord;

export interface MergeConflict {
    row: number,
    col: string,
    base_value: string,
    our_value: string,
    their_value: string,
}

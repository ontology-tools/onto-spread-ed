// Same as ose/project.py of ose-lib
export interface ProjectFile {
    needs: string[];
    sources: {
        file: string;
        type: "classes" | "relations" | "individuals" | "owl";
        spreadsheet_schema: string;
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

export interface BuildStep {
    name: string;
    args: { [K: string]: any };
}

export interface BuildConfiguration {
    name: string;
    description: string | null;
    stages: BuildStep[];
}

export interface Project {
    short_name: string;
    full_name: string;
    id_digits: number;
    main_branch: string;
    prefixes: { [K: string]: string };
    subontologies: {
        [K: string]: {
            release_file: string
            excel_file: string
        }
    };
    readonly_files: { [K: string]: string };
    validation: ("include-external" | "include-dependencies")[];
    iri_prefix: string;
    short_repository_name: string;
    full_repository_name: string;
    external: ProjectFile;
    files: { [K: string]: ProjectFile };
    build_configurations: BuildConfiguration[];
    spreadsheet_schemas: { [K: string]: any };
}

// Same as ose/building of ose-lib
export type BuildState = "starting" | "running" | "completed" | "cancelled" | "errored" | "paused";

export interface StageResult {
    log: { errors: Diagnostic[], warnings: Diagnostic[], infos: Diagnostic[] };
    data: { [K: string]: any };
    result: "skipped" | "cancelled" | "paused" | "failed" | "completed";
}

export interface BuildArtifact {
    id: string;
    local_path: string;
    final_path: string | null;
    kind: "source" | "intermediate" | "final";
    origin: string;
}

export interface ReleaseContext {
    build_id: string;
    project: Project;
    build_configuration: BuildConfiguration;
    current_stage: number | null;
    state: BuildState;
    stage_results: (StageResult | null)[];
    artifacts: BuildArtifact[];
}

export interface Progress {
    stage: number;
    current_item: number | null;
    total_items: number | null;
    item: string | null;
    message: string | null;
}

export interface Release<D = Date> {
    id: number
    repo: string
    state: BuildState
    started_by: string,
    start: D
    end: D | null
    worker_id: string | null,
    heartbeat_at: D | null,
    requested_action: "run" | "skip" | "rerun" | null,
    requested_by: string | null,
    context: ReleaseContext | null,
    progress: Progress | null
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

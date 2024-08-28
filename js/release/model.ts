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
        published: boolean;
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
    state: string
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

export interface Diagnostic {
  type: string,

  [K: string]: any
}

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

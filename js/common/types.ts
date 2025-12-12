
declare global {
    interface Window {
        ose?: {
            visualise?: VisualisationData;
        };
        oseDataChanged?: () => void;
    }
}


export interface Graph {
  directed: boolean
  edges: Edge[]
  multigraph: boolean
  nodes: Node[]
}

export interface Edge {
  source: string
  target: string
  type: any
  color?: string
  label?: string
}


export interface Node {
  class: string
  id: string
  label: string
  ose_curation: string
  ose_origin: string
  source: 'current' | 'dependencies' | 'derived'
  visual_depth: number
}

export interface Row {
  Label: string;
  ID: string;
  Parent: string;

  [key: string]: string;
}

export interface VisualisationData {
  sheetData: SpreadsheetData<Row>,
  selection: number[];
}

export interface SpreadsheetData<RowType = Record<string, string | null | number | boolean>> {
  header: string[],
  rows: RowType[],
  file_sha: string,
  repo_name: string,
  folder: string,
  spreadsheet_name: string,
}

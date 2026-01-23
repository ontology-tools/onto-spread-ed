
declare global {
    interface Window {
        ose?: {
            visualise?: VisualisationData;
        };
        oseDataChanged?: () => void;
    }
}

export class Graph {
  private _edges: Edge[];
  private _nodes: Map<string, Node>;

  private _successors: Map<string, Set<string>>;
  private _predecessors: Map<string, Set<string>>;

  get nodes(): ReadonlyArray<Node> {
    return Array.from(this._nodes.values())
  }

  get edges(): ReadonlyArray<Edge> {
    return this._edges
  }

  public get roots(): ReadonlyArray<Node> {
    return this.nodes.filter(n => this.predecessors(n.id).length === 0);
  }

  public get leaves(): ReadonlyArray<Node> {
    return this.nodes.filter(n => this.successors(n.id).length === 0);
  }

  constructor(nodes: Node[] = [], edges: Edge[] = []) {
    this._nodes = new Map<string, Node>();
    this._edges = [];

    this._successors = new Map<string, Set<string>>();
    this._predecessors = new Map<string, Set<string>>();

    for (const node of nodes) {
      this.addNode(node);
    }

    for (const edge of edges) {
      this.addEdge(edge);
    }
  }

  public outgoingEdges(nodeId: string): Edge[] {
    return this._edges.filter(e => e.source === nodeId)
  }

  public incomingEdges(nodeId: string): Edge[] {
    return this._edges.filter(e => e.target === nodeId)
  }

  public node(nodeId: string): Node | undefined {
    return this._nodes.get(nodeId)
  }


  public addNode(node: Node): void {
    this._nodes.set(node.id, node);
  }

  public removeNode(node: Node): void
  public removeNode(nodeId: string): void
  public removeNode(nodeOrId: Node | string): void {
    const nodeId = typeof nodeOrId === 'string' ? nodeOrId : nodeOrId.id;
    this._nodes.delete(nodeId);

    // Remove associated edges
    this._edges = this._edges.filter(e => e.source !== nodeId && e.target !== nodeId);

    this._successors.delete(nodeId);
    this._predecessors.delete(nodeId);

    for (const [_, targets] of this._successors) {
      targets.delete(nodeId);
    }

    for (const [_, sources] of this._predecessors) {
      sources.delete(nodeId);
    }
  }

  public removeEdge(edgeToRemove: Pick<Edge, 'source' | 'target'> & Partial<Pick<Edge, 'type'>>): void {
    this._edges = this._edges.filter(e => !(e.source === edgeToRemove.source && e.target === edgeToRemove.target && (!edgeToRemove.type || e.type === edgeToRemove.type)));

    this._successors.get(edgeToRemove.source)?.delete(edgeToRemove.target);
    this._predecessors.get(edgeToRemove.target)?.delete(edgeToRemove.source);
  }

  public addEdge(edge: Edge): void {
    this._edges.push(edge);

    if (!this._successors.has(edge.source)) {
      this._successors.set(edge.source, new Set<string>());
    }
    this._successors.get(edge.source)!.add(edge.target);

    if (!this._predecessors.has(edge.target)) {
      this._predecessors.set(edge.target, new Set<string>());
    }
    this._predecessors.get(edge.target)!.add(edge.source);
  }

  public successors(node: Node): Node[]
  public successors(nodeId: string): Node[]
  public successors(nodeOrId: Node | string): Node[] {
    const nodeId = typeof nodeOrId === 'string' ? nodeOrId : nodeOrId.id;
    return Array.from(this._successors.get(nodeId) || []).map(id => this._nodes.get(id)!);
  }

  public predecessors(node: Node): Node[]
  public predecessors(nodeId: string): Node[]
  public predecessors(nodeOrId: Node | string): Node[] {
    const nodeId = typeof nodeOrId === 'string' ? nodeOrId : nodeOrId.id;
    return Array.from(this._predecessors.get(nodeId) || []).map(id => this._nodes.get(id)!);
  }
  
  public reachable(nodeId: string): Set<string> {
    const visited = new Set<string>();
    const stack = [nodeId];

    while (stack.length > 0) {
      const current = stack.pop()!;
      if (!visited.has(current)) {
        visited.add(current);
        const successors = this.successors(current);
        for (const succ of successors) {
          if (!visited.has(succ.id)) {
            stack.push(succ.id);
          }
        }
      }
    }

    return visited;
  }

  public backwardReachable(nodeId: string): Set<string> {
    const visited = new Set<string>();
    const stack = [nodeId];

    while (stack.length > 0) {
      const current = stack.pop()!;
      if (!visited.has(current)) {
        visited.add(current);
        const predecessors = this.predecessors(current);
        for (const pred of predecessors) {
          if (!visited.has(pred.id)) {
            stack.push(pred.id);
          }
        }
      }
    }

    return visited;
  }

  public clone(): Graph {
    return new Graph(this.nodes.map(n => ({ ...n })), this.edges.map(e => ({ ...e })));
  }
}

export interface Edge {
  source: string
  target: string
  type: string
  color?: string
  label?: string
}


export interface Node {
  class: string
  id: string
  label: string
  curationStatus: string
  origin: string
  source: 'current' | 'dependencies' | 'derived'
  visualDepth: number
  isSelected: boolean
}

export interface Row {
  Label: string;
  ID: string;
  Parent: string;

  [key: string]: string;
}

export interface VisualisationData {
  /**
   * Data for the spreadsheet being visualised
   */
  sheetData: SpreadsheetData<Row>,

  /**
   * Indexes of selected rows in the spreadsheet that should be visualised
   */
  selection: number[] | null;
}

export interface SpreadsheetData<RowType = Record<string, string | null | number | boolean>> {
  header: string[],
  rows: RowType[],
  file_sha: string,
  repo_name: string,
  folder: string,
  spreadsheet_name: string,
}

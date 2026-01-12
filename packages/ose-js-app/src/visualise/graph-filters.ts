import { Graph, Node, Edge } from "@ose/js-core";
import { CURATION_STATUS } from "@ose/js-core";

export interface FilterOptions {
  curationFilter: string[];
  showChildrenFromOtherSheets: boolean;
  showParentsFromOtherSheets: boolean;
  numChildLevels: number | null;
  currentSheet?: string;
}

export interface FilteredGraph {
  nodes: Node[];
  hierarchyEdges: Edge[];
  relationEdges: Edge[];
}

/**
 * Apply filters to graph nodes and edges
 */
export function applyGraphFilters(graph: Graph, options: FilterOptions): FilteredGraph {
  const filteredNodeIds = new Set<string>();
  
  // Filter nodes based on criteria
  for (const node of graph.nodes) {
    const status = node.curationStatus;
    const depth = node.visualDepth;
    const isFromCurrentSheet = node.source === 'current';
    const isParentNode = depth < 0;
    const isChildNode = depth > 0;
    const isRelevantParent = depth === 0; 

    // Check each filter condition
    const passesCurationFilter = options.curationFilter.includes(status);
    const passesDepthFilter = depth <= (options.numChildLevels ?? Infinity);
    const passesSheetFilter = isFromCurrentSheet || isRelevantParent
      || (isParentNode && options.showParentsFromOtherSheets)
      || (isChildNode && options.showChildrenFromOtherSheets);

    if (passesCurationFilter && passesDepthFilter && passesSheetFilter) {
      filteredNodeIds.add(node.id);
    }
  }

  // Filter nodes and edges
  const nodes = graph.nodes.filter(n => filteredNodeIds.has(n.id));
  const allEdges = graph.edges.filter(e => 
    filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target)
  );
  
  // Separate subclass_of edges (for hierarchy) from other relation edges
  const hierarchyEdges = allEdges.filter(e => e.type === 'subclass_of');
  const relationEdges = allEdges.filter(e => e.type !== 'subclass_of');

  return { nodes, hierarchyEdges, relationEdges };
}

/**
 * Build hierarchical tree structure from filtered nodes and edges
 */
export interface HierarchyNode {
  id: string;
  label: string;
  ose_curation: string;
  ose_origin: string;
  ose_source: 'current' | 'dependencies' | 'derived';
  ose_selected: boolean;
  children: HierarchyNode[];
}

export function buildHierarchyTrees(
  nodes: Node[], 
  hierarchyEdges: Edge[]
): HierarchyNode[] {
  // Build adjacency map (parent -> children) using only subclass_of edges
  const childrenMap = new Map<string, string[]>();
  const parentMap = new Map<string, string>();
  
  for (const edge of hierarchyEdges) {
    // In a directed graph, source -> target means source is parent of target
    if (!childrenMap.has(edge.source)) {
      childrenMap.set(edge.source, []);
    }
    childrenMap.get(edge.source)!.push(edge.target);
    parentMap.set(edge.target, edge.source);
  }

  // Find root nodes (nodes with no parent)
  const roots = nodes.filter(n => !parentMap.has(n.id));

  // Create node lookup map
  const nodeMap = new Map<string, Node>();
  for (const node of nodes) {
    nodeMap.set(node.id, node);
  }

  // Recursively build hierarchy
  function buildHierarchy(nodeId: string): HierarchyNode | null {
    const node = nodeMap.get(nodeId);
    if (!node) return null;

    const children: HierarchyNode[] = [];
    const childIds = childrenMap.get(nodeId) ?? [];
    for (const childId of childIds) {
      const child = buildHierarchy(childId);
      if (child) children.push(child);
    }

    return {
      id: node.id,
      label: node.label,
      ose_curation: node.curationStatus,
      ose_origin: node.origin,
      ose_source: node.source,
      ose_selected: node.isSelected,
      children
    };
  }

  // Build tree for each root
  const trees: HierarchyNode[] = [];
  for (const root of roots) {
    const tree = buildHierarchy(root.id);
    if (tree) trees.push(tree);
  }

  return trees;
}

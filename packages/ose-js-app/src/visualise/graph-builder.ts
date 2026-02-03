import { CURATION_STATUS } from "@ose/js-core";
import { Graph, Node, Row } from "@ose/js-core";

export interface TermDataRelation {
    relation: { label: string };
    target: { label: string };
}

/**
 * Term data from backend
 */
export interface TermData<ParentId = string | undefined> {
    id: string;
    index: number;
    label: string;
    curationStatus?: string;
    origin?: string;
    subClassOf: { id: ParentId, label: string }[];
    relations: TermDataRelation[];
}

export type ResolvedTermData = TermData<string>;

/**
 * Raw data from backend API (only dependencies and derived)
 */
export interface DependencyData {
    dependencies: ResolvedTermData[];
    derived: ResolvedTermData[];
}

/**
 * Build graph from current spreadsheet data combined with dependencies
 */
export function buildGraphFromSpreadsheet(
    currentRows: Row[],
    currentHeader: string[],
    currentSpreadsheetName: string,
    dependencyData: DependencyData,
    selection?: number[]
): Graph {
    const graph: Graph = new Graph();

    const relationColumns = currentHeader.filter(h => h.startsWith("REL "));
    console.debug("Relation columns found:", relationColumns);

    // Convert current spreadsheet rows to TermData
    const currentTerms: TermData[] = currentRows.map((row, index) => {
        const id = row['ID'].trim();
        const label = row['Label'].trim();
        const curationStatus = Object.entries(row)
            .find(([k, _]) => k.toLowerCase().includes('curation status'))
            ?.[1]?.trim() || CURATION_STATUS.PRE_PROPOSED;
        const parents = [{ label: row['Parent'].trim(), id: undefined }];

        const relations: TermDataRelation[] = [];
        for (const relCol of relationColumns) {
            const value = row[relCol];
            if (value && typeof value === 'string') {
                const targets = value.split(";").map(t => t.trim()).filter(Boolean);
                for (const target of targets) {
                    relations.push({
                        relation: { label: relCol.replace(/REL '([^']+)'.*/, "$1") },
                        target: {label: target}
                    });
                }
            }
        }

        return {
            id,
            label,
            curationStatus,
            origin: currentSpreadsheetName,
            subClassOf: parents,
            relations,
            index
        };
    }).filter(term => term.id); // Filter out rows without IDs

    // Track all terms (combined from all sources)
    const termsByLabel = new Map<string, TermData & { source: 'current' | 'dependencies' | 'derived' }>();

    // Add terms from current spreadsheet
    for (const term of currentTerms) {
        termsByLabel.set(term.label, { ...term, source: 'current' });
    }

    // Add dependencies
    for (const term of dependencyData.dependencies) {
        if (!termsByLabel.has(term.label)) {
            termsByLabel.set(term.label, { ...term, source: 'dependencies' });
        }
    }

    // Add derived terms
    for (const term of dependencyData.derived) {
        if (!termsByLabel.has(term.label)) {
            termsByLabel.set(term.label, { ...term, source: 'derived' });
        }
    }


    // Resolve parent IDs
    for (const term of currentTerms) {
        for (const parent of term.subClassOf) {
            const parentTerm = termsByLabel.get(parent.label);
            if (parentTerm) {
                parent.id = parentTerm.id;
            } else if (parent.id === undefined) {
                console.warn(`Parent term with label "${parent.label}" not found for term "${term.label} [${term.id}]"`);
            }
        }
    }

    const allTerms = new Map<string, ResolvedTermData & { source: 'current' | 'dependencies' | 'derived' }>();
    for (const term of termsByLabel.values()) {
        const unresolvedParents = term.subClassOf.filter(p => p.id === undefined);
        if (unresolvedParents.length > 0) {
            console.warn(`Term "${term.label} [${term.id}]" has unresolved parents:`, unresolvedParents);
        }

        term.subClassOf = term.subClassOf.filter(p => p.id !== undefined);
        allTerms.set(term.id, term as ResolvedTermData & { source: 'current' | 'dependencies' | 'derived' });
    }


    // Create nodes for all terms
    for (const [id, term] of allTerms) {
        const nodeId = id.replace(':', '_');
        const origin = term.origin || '<unknown>';
        const curationStatus = term.curationStatus || 'External';

        const node: Node = {
            id: nodeId,
            label: term.label,
            class: `ose-curation-status-${curationStatus.toLowerCase().replace(/\s+/g, '_')}`,
            curationStatus,
            origin,
            source: term.source,
            isSelected: selection?.includes(term.index) === true,
            visualDepth: -Infinity // Will be calculated later
        };
        graph.addNode(node);
    }

    // Create edges for subclass_of relationships
    for (const [id, term] of allTerms) {
        const nodeId = id.replace(':', '_');

        for (const parent of term.subClassOf) {
            const parentNodeId = parent.id.replace(':', '_');

            // Add parent node if it doesn't exist (external reference)
            if (!allTerms.has(parent.id)) {
                console.warn(`Parent term with label "${parent.label}" not found for term "${term.label} [${term.id}]"`);
            }

            graph.addEdge({
                source: parentNodeId,
                target: nodeId,
                type: 'subclass_of'
            });
        }
    }

    // Create edges for other relations
    for (const [id, term] of allTerms) {
        const nodeId = id.replace(':', '_');

        for (const rel of term.relations) {
            const targetTerm = termsByLabel.get(rel.target.label);
            if (!targetTerm) {
                console.warn(`Relation target term with label "${rel.target.label}" not found for term "${term.label} [${term.id}]"`);
                continue;
            }

            const targetNodeId = targetTerm.id.replace(':', '_');
            const relationColor = getRelationColor(rel.relation.label);

            graph.addEdge({
                source: nodeId,
                target: targetNodeId,
                type: rel.relation.label,
                label: rel.relation.label,
                color: relationColor
            });
        }
    }

    console.debug(`Built graph with ${graph.nodes.length} nodes and ${graph.edges.length} edges from ${currentTerms.length} current terms, ${dependencyData.dependencies.length} dependencies, and ${dependencyData.derived.length} derived terms.`, { edges: graph.edges, nodes: graph.nodes, allTerms });

    // Remove dependency or derived nodes that don't have a path to current nodes
    const currentNodeIds = new Set(
        Array.from(allTerms.entries())
            .filter(([_, term]) => term.source === 'current')
            .map(([id, _]) => id.replace(':', '_'))
    );


    const derivedNodeIds = new Set(
        Array.from(allTerms.entries())
            .filter(([_, term]) => term.source === 'derived')
            .map(([id, _]) => id.replace(':', '_'))
    );

    const dependencyNodeIds = new Set(
        Array.from(allTerms.entries())
            .filter(([_, term]) => term.source === 'dependencies')
            .map(([id, _]) => id.replace(':', '_'))
    );


    function isReachableDependency(nodeId: string): boolean {
        if (currentNodeIds.has(nodeId)) {
            return true;
        }

        const children = graph.successors(nodeId);
        for (const child of children) {
            if (isReachableDependency(child.id)) {
                return true;
            }
        }
        return false;
    }

    function isReachableDerived(nodeId: string): boolean {
        if (currentNodeIds.has(nodeId)) {
            return true;
        }

        const parents = graph.predecessors(nodeId);
        for (const parent of parents) {
            if (isReachableDerived(parent.id)) {
                return true;
            }
        }
        return false;
    }

    function isReachable(nodeId: string): boolean {
        if (currentNodeIds.has(nodeId)) {
            return true;
        }
        if (derivedNodeIds.has(nodeId)) {
            return isReachableDerived(nodeId);
        }
        if (dependencyNodeIds.has(nodeId)) {
            return isReachableDependency(nodeId);
        }
        return false;
    }

    for (const node of graph.nodes) {
        if (!isReachable(node.id)) {
            graph.removeNode(node.id);
        }
    }

    // Calculate visual depth for all nodes
    calculateVisualDepth(graph);

    console.log({ graph: graph.clone() })

    // Calculate which nodes are visible for the current selection
    if (selection && selection.length > 0) {
        const visibleNodes = new Set(graph.nodes.filter(node => node.isSelected).map(node => node.id));
        calculateVisibleNodes(graph, visibleNodes);

        for (const node of graph.nodes) {
            if (!visibleNodes.has(node.id)) {
                graph.removeNode(node.id);
            }
        }
    }

    return graph;
}

/**
 * Get color for relation type
 */
function getRelationColor(label?: string): string {
    const colorMap: Record<string, string> = {
        "has part": "blue",
        "part of": "blue",
        "contains": "green",
        "has role": "darkgreen",
        "is about": "darkgrey",
        "has participant": "darkblue",
    };

    return (label ? colorMap[label] : null) ?? "orange";
}

/**
 * Calculate visual depth for all nodes in the graph
 * 
 * Visual depth rules:
 * - -1 for parent nodes that are no immediate parents of any current sheet nodes
 * - 0 for nodes that are parents of current sheet nodes but not from current sheet
 * - 1..n for current sheet and derived nodes based on distance from closest parent with depth 0 (see above)
 */
function calculateVisualDepth(graph: Graph) {
    // Memoization for depth calculation
    const depthCache = new Map<string, number>();

    function getVisualDepth(node: Node): number {
        if (depthCache.has(node.id)) {
            return depthCache.get(node.id)!;
        }

        if (!node) {
            console.error("Node not found for ID:", node);
            return -Infinity;
        }

        const pred = graph.predecessors(node);
        const succ = graph.successors(node);
        const isFromCurrentSheet = node.source !== 'dependencies';

        let depth: number;

        if (!isFromCurrentSheet && succ.find(s => s.source !== 'dependencies')) {
            depth = 0;
        } else {
            const maxParentDepth = pred.reduce((d, p) => Math.max(d, getVisualDepth(p)), -1);

            if (isFromCurrentSheet) {
                depth = maxParentDepth + 1;
            } else {
                depth = maxParentDepth;
            }
        }

        depthCache.set(node.id, depth);
        return depth;
    }


    // Calculate depth for all nodes
    for (const node of graph.nodes) {
        node.visualDepth = getVisualDepth(node);
    }
}

function calculateVisibleNodes(graph: Graph, visibleNodes: Set<string>): void {
    const isVisible = (node: Node, direction: 'up' | 'down'): boolean => {
        if (visibleNodes.has(node.id)) {
            return true;
        }
        
        const fn = direction === 'up' ? graph.predecessors.bind(graph) : graph.successors.bind(graph);
        
        const visible = fn(node.id).reduce((acc, n) => isVisible(n, direction) || acc, false)

        if (visible) {
            visibleNodes.add(node.id);
        }

        return visible;
    }

    for (const node of graph.leaves) {
        isVisible(node, 'up');
    }

    for (const node of graph.roots) {
        isVisible(node, 'down');
    }
}

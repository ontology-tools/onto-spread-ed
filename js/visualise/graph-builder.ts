import { CURATION_STATUS } from '../common/constants';
import { Graph, Node, Row } from '../common/types';

/**
 * Term data from backend
 */
export interface TermData<ParentId = string | undefined> {
    id: string;
    label: string;
    curation_status?: string;
    origin?: string;
    sub_class_of: { id: ParentId, label: string }[];
    relations: {
        relation: { label: string };
        target: string;
    }[];
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
    dependencyData: DependencyData
): Graph {
    const graph: Graph = {
        directed: true,
        multigraph: true,
        nodes: [],
        edges: []
    };

    const relationColumns = currentHeader.filter(h => h.startsWith("REL "));
    console.debug("Relation columns found:", relationColumns);

    // Convert current spreadsheet rows to TermData
    const currentTerms: TermData[] = currentRows.map(row => {
        const getId = (row: Row) => row['ID'].trim();
        const getLabel = (row: Row) => row['Label'].trim();


        const getCurationStatus = (row: Row) => Object.entries(row)
            .find(([k, _]) => k.toLowerCase().includes('curation status'))
            ?.[1].trim() || CURATION_STATUS.PRE_PROPOSED;
        const getParents = (row: Row) => [{ label: row['Parent'].trim(), id: undefined }];

        const relations: Array<{ relation: { label: string }; target: string }> = [];
        for (const relCol of relationColumns) {
            const value = row[relCol];
            if (value && typeof value === 'string') {
                const targets = value.split(";").map(t => t.trim()).filter(Boolean);
                for (const target of targets) {
                    relations.push({
                        relation: { label: relCol.replace(/REL '([^']+)'.*/, "$1") },
                        target: target
                    });
                }
            }
        }

        return {
            id: getId(row),
            label: getLabel(row),
            curation_status: getCurationStatus(row),
            origin: currentSpreadsheetName,
            sub_class_of: getParents(row),
            relations: relations
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
        for (const parent of term.sub_class_of) {
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
        const unresolvedParents = term.sub_class_of.filter(p => p.id === undefined);
        if (unresolvedParents.length > 0) {
            console.warn(`Term "${term.label} [${term.id}]" has unresolved parents:`, unresolvedParents);
        }

        term.sub_class_of = term.sub_class_of.filter(p => p.id !== undefined);
        allTerms.set(term.id, term as ResolvedTermData & { source: 'current' | 'dependencies' | 'derived' });
    }


    // Create nodes for all terms
    for (const [id, term] of allTerms) {
        const nodeId = id.replace(':', '_');
        const origin = term.origin || '<unknown>';
        const curationStatus = term.curation_status || 'External';

        graph.nodes.push({
            id: nodeId,
            label: term.label,
            class: `ose-curation-status-${curationStatus.toLowerCase().replace(/\s+/g, '_')}`,
            ose_curation: curationStatus,
            ose_origin: origin,
            source: term.source,
            visual_depth: -Infinity // Will be calculated later
        });
    }

    // Create edges for subclass_of relationships
    for (const [id, term] of allTerms) {
        const nodeId = id.replace(':', '_');

        for (const parent of term.sub_class_of) {
            const parentNodeId = parent.id.replace(':', '_');

            // Add parent node if it doesn't exist (external reference)
            if (!allTerms.has(parent.id)) {
                console.warn(`Parent term with label "${parent.label}" not found for term "${term.label} [${term.id}]"`);
            }

            graph.edges.push({
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
            const targetTerm = termsByLabel.get(rel.target);
            if (!targetTerm) {
                console.warn(`Relation target term with label "${rel.target}" not found for term "${term.label} [${term.id}]"`);
                continue;
            }

            const targetNodeId = targetTerm.id.replace(':', '_');
            const relationColor = getRelationColor(rel.relation.label);

            graph.edges.push({
                source: nodeId,
                target: targetNodeId,
                type: rel.relation,
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

    const successors = new Map<string, Set<string>>();
    const predecessors = new Map<string, Set<string>>();
    for (const edge of graph.edges) {
        if (!successors.has(edge.source)) {
            successors.set(edge.source, new Set());
        }
        successors.get(edge.source)!.add(edge.target);

        if (!predecessors.has(edge.target)) {
            predecessors.set(edge.target, new Set());
        }
        predecessors.get(edge.target)!.add(edge.source);
    }

    function isReachableDependency(nodeId: string): boolean {
        if (currentNodeIds.has(nodeId)) {
            return true;
        }

        const children = successors.get(nodeId) ?? new Set();
        for (const childId of children) {
            if (isReachableDependency(childId)) {
                return true;
            }
        }
        return false;
    }

    function isReachableDerived(nodeId: string): boolean {
        if (currentNodeIds.has(nodeId)) {
            return true;
        }

        const parents = predecessors.get(nodeId) ?? new Set();
        for (const parentId of parents) {
            if (isReachableDerived(parentId)) {
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

    graph.nodes = graph.nodes.filter(n => isReachable(n.id));
    graph.edges = graph.edges.filter(e => isReachable(e.source) && isReachable(e.target));

    // Calculate visual depth for all nodes
    calculateVisualDepth(graph);

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
    // Build adjacency maps
    const predecessors = new Map<string, string[]>();
    const successors = new Map<string, string[]>();

    for (const edge of graph.edges) {
        if (edge.type === 'subclass_of') {
            if (!predecessors.has(edge.target)) {
                predecessors.set(edge.target, []);
            }
            predecessors.get(edge.target)!.push(edge.source);

            if (!successors.has(edge.source)) {
                successors.set(edge.source, []);
            }
            successors.get(edge.source)!.push(edge.target);
        }
    }

    // Create node lookup map
    const nodeMap = new Map<string, Node>();
    for (const node of graph.nodes) {
        nodeMap.set(node.id, node);
    }

    // Memoization for depth calculation
    const depthCache = new Map<string, number>();

    function getVisualDepth(nodeId: string): number {
        if (depthCache.has(nodeId)) {
            return depthCache.get(nodeId)!;
        }

        const node = nodeMap.get(nodeId);
        if (!node) {
            console.error("Node not found for ID:", nodeId);
            return -Infinity;
        }

        const pred = predecessors.get(nodeId) ?? [];
        const succ = successors.get(nodeId) ?? [];
        const isFromCurrentSheet = node.source === 'current';

        let depth: number;

        if (!isFromCurrentSheet && succ.find(s => nodeMap.get(s)?.source !== 'dependencies')) {
            depth = 0;
        } else {
            const maxParentDepth = pred.reduce((d, p) => Math.max(d, getVisualDepth(p)), -1);

            if (isFromCurrentSheet) {
                depth = maxParentDepth + 1;
            } else {
                depth = maxParentDepth;
            }
        }

        depthCache.set(nodeId, depth);
        return depth;
    }


    // Calculate depth for all nodes
    for (const node of graph.nodes) {
        node.visual_depth = getVisualDepth(node.id);
    }
}

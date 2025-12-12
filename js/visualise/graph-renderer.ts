import * as d3 from 'd3';
import svgPanZoom from 'svg-pan-zoom';
import { Edge } from '../common/types';
import { HierarchyNode } from './graph-filters';
import { CURATION_STATUS } from '../common/constants';

// Relation color map (matching RELATION_COLOR_MAP in visualise.py)
export const RELATION_COLOR_MAP: Record<string, string> = {
  "has part": "blue",
  "part of": "blue",
  "contains": "green",
  "has role": "darkgreen",
  "is about": "darkgrey",
  "has participant": "darkblue",
};

// Layout constants
const FONT_SIZE = 11;
const LINE_HEIGHT = 14;
const MAX_LINE_WIDTH = 120;
const NODE_PADDING = 12;
const HORIZONTAL_SPACING = 40;
const VERTICAL_SPACING = 40;

export interface NodeDimensions {
  width: number;
  height: number;
  lines: string[];
}

export interface TreeLayoutData {
  root: d3.HierarchyPointNode<HierarchyNode>;
  offsetX: number;
  offsetY: number;
  treeWidth: number;
}

export interface PanZoomState {
  zoom: number;
  pan: { x: number; y: number };
}

/**
 * Text wrapping helper
 */
function wrapText(svg: d3.Selection<SVGSVGElement, unknown, null, undefined>, text: string, maxWidth: number): string[] {
  const words = text.split(/\s+/);
  const lines: string[] = [];
  let currentLine = '';

  const tempText = svg.append('text')
    .style('font-size', `${FONT_SIZE}px`)
    .style('visibility', 'hidden');

  for (const word of words) {
    const testLine = currentLine ? `${currentLine} ${word}` : word;
    tempText.text(testLine);
    const testWidth = (tempText.node() as SVGTextElement).getComputedTextLength();

    if (testWidth > maxWidth && currentLine) {
      lines.push(currentLine);
      currentLine = word;
    } else {
      currentLine = testLine;
    }
  }
  if (currentLine) {
    lines.push(currentLine);
  }

  tempText.remove();
  return lines;
}

/**
 * Text measurement helper
 */
function measureText(svg: d3.Selection<SVGSVGElement, unknown, null, undefined>, text: string): number {
  const tempText = svg.append('text')
    .style('font-size', `${FONT_SIZE}px`)
    .style('visibility', 'hidden')
    .text(text);
  const width = (tempText.node() as SVGTextElement).getComputedTextLength();
  tempText.remove();
  return width;
}

/**
 * Calculate dimensions for all nodes
 */
export function calculateNodeDimensions(
  svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
  trees: HierarchyNode[]
): Map<string, NodeDimensions> {
  const nodeDimensionsMap = new Map<string, NodeDimensions>();

  for (const tree of trees) {
    const stack = [tree];
    while (stack.length > 0) {
      const node = stack.pop()!;
      const label = node.label || node.id;
      const lines = wrapText(svg, label, MAX_LINE_WIDTH);
      const maxLineWidthActual = Math.max(...lines.map(line => measureText(svg, line)));
      const nodeWidth = Math.max(80, maxLineWidthActual + NODE_PADDING * 2);
      const nodeHeight = Math.max(24, lines.length * LINE_HEIGHT + NODE_PADDING);
      nodeDimensionsMap.set(node.id, { width: nodeWidth, height: nodeHeight, lines });
      stack.push(...node.children);
    }
  }

  return nodeDimensionsMap;
}

/**
 * Calculate tree layouts and positions
 */
export function calculateTreeLayouts(
  trees: HierarchyNode[],
  nodeDimensionsMap: Map<string, NodeDimensions>
): { 
  treeLayouts: TreeLayoutData[];
  nodePositions: Map<string, { x: number; y: number }>;
  maxNodeWidth: number;
  maxNodeHeight: number;
} {
  // Find max node dimensions for layout spacing
  let maxNodeWidth = 0;
  let maxNodeHeight = 0;
  nodeDimensionsMap.forEach(dims => {
    maxNodeWidth = Math.max(maxNodeWidth, dims.width);
    maxNodeHeight = Math.max(maxNodeHeight, dims.height);
  });

  let currentX = 20;
  const nodePositions = new Map<string, { x: number; y: number }>();
  const treeLayouts: TreeLayoutData[] = [];

  // First pass: calculate all layouts and store node positions
  for (const tree of trees) {
    const root = d3.hierarchy(tree);
    
    // Calculate tree dimensions - use nodeSize with [horizontal spacing, vertical spacing]
    const treeLayout = d3.tree<HierarchyNode>()
      .nodeSize([maxNodeWidth + HORIZONTAL_SPACING, maxNodeHeight + VERTICAL_SPACING])
      .separation((a, b) => a.parent === b.parent ? 1 : 1.2);

    treeLayout(root);

    // Find bounds of this tree (x is now horizontal, y is vertical)
    let minX = Infinity, maxX = -Infinity;
    root.each(d => {
      minX = Math.min(minX, d.x!);
      maxX = Math.max(maxX, d.x!);
    });

    const treeWidth = maxX - minX + maxNodeWidth + 20;
    const offsetX = currentX - minX + maxNodeWidth / 2;
    const offsetY = 50;

    // Store layout data for second pass
    treeLayouts.push({ 
      root: root as d3.HierarchyPointNode<HierarchyNode>, 
      offsetX, 
      offsetY, 
      treeWidth 
    });

    // Store node positions
    root.each(d => {
      nodePositions.set(d.data.id, { 
        x: d.x! + offsetX, 
        y: d.y! + offsetY 
      });
    });

    currentX += treeWidth + 40;
  }

  return { treeLayouts, nodePositions, maxNodeWidth, maxNodeHeight };
}

/**
 * Create arrow markers for edges
 */
export function createArrowMarkers(
  defs: d3.Selection<SVGDefsElement, unknown, null, undefined>,
  relationEdges: Edge[]
) {
  // Hierarchy arrow marker (gray)
  defs.append('marker')
    .attr('id', 'arrow-hierarchy')
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', 8)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5')
    .attr('fill', '#999');

  // Create arrow markers for each relation color
  const usedColors = new Set<string>();
  for (const edge of relationEdges) {
    const edgeLabel = edge.label || edge.type || '';
    const edgeColor = RELATION_COLOR_MAP[edgeLabel] || edge.color || 'orange';
    usedColors.add(edgeColor);
  }
  
  usedColors.forEach(color => {
    const colorId = color.replace(/[^a-zA-Z0-9]/g, '_');
    defs.append('marker')
      .attr('id', `arrow-${colorId}`)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 8)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', color);
  });
}

/**
 * Draw hierarchy edges
 */
export function drawHierarchyEdges(
  edgesLayer: d3.Selection<SVGGElement, unknown, null, undefined>,
  treeLayouts: TreeLayoutData[],
  nodeDimensionsMap: Map<string, NodeDimensions>,
  onEdgeInteraction: (sourceId: string, targetId: string, element: SVGElement, action: 'enter' | 'leave' | 'click') => void
) {
  for (const { root, offsetX, offsetY } of treeLayouts) {
    const treeEdgesGroup = edgesLayer.append('g')
      .attr('class', 'tree-edges')
      .attr('transform', `translate(${offsetX}, ${offsetY})`);

    treeEdgesGroup.selectAll('.link')
      .data(root.links())
      .enter()
      .append('path')
      .attr('class', 'link')
      .attr('data-source', d => d.source.data.id)
      .attr('data-target', d => d.target.data.id)
      .attr('d', d => {
        const source = d.source as d3.HierarchyPointNode<HierarchyNode>;
        const target = d.target as d3.HierarchyPointNode<HierarchyNode>;
        const targetDims = nodeDimensionsMap.get(target.data.id);
        const targetHeight = targetDims ? targetDims.height / 2 : 12;
        const adjustedTargetY = target.y! - targetHeight;
        return `M${source.x},${source.y}C${source.x},${(source.y + adjustedTargetY) / 2} ${target.x},${(source.y + adjustedTargetY) / 2} ${target.x},${adjustedTargetY}`;
      })
      .attr('marker-end', 'url(#arrow-hierarchy)')
      .on('mouseenter', function(_event, d) {
        onEdgeInteraction(d.source.data.id, d.target.data.id, this, 'enter');
      })
      .on('mouseleave', function(_event, d) {
        onEdgeInteraction(d.source.data.id, d.target.data.id, this, 'leave');
      })
      .on('click', function(_event, d) {
        onEdgeInteraction(d.source.data.id, d.target.data.id, this, 'click');
      })
      .each(function(_d) {
        d3.select(this).append('title').text('subclass of');
      });
  }
}

/**
 * Draw relation edges
 */
export function drawRelationEdges(
  edgesLayer: d3.Selection<SVGGElement, unknown, null, undefined>,
  relationEdges: Edge[],
  nodePositions: Map<string, { x: number; y: number }>,
  nodeDimensionsMap: Map<string, NodeDimensions>,
  nodeIdLabelMap: Record<string, string>,
  onEdgeInteraction: (sourceId: string, targetId: string, element: SVGElement, action: 'enter' | 'leave' | 'click') => void
) {
  for (const edge of relationEdges) {
    const sourcePos = nodePositions.get(edge.source);
    const targetPos = nodePositions.get(edge.target);
    
    if (!sourcePos || !targetPos) continue;

    const edgeLabel = edge.label || edge.type || '';
    const edgeColor = RELATION_COLOR_MAP[edgeLabel] || edge.color || 'orange';
    const colorId = edgeColor.replace(/[^a-zA-Z0-9]/g, '_');

    // Get target node dimensions to adjust endpoint
    const targetDims = nodeDimensionsMap.get(edge.target);
    const targetHeight = targetDims ? targetDims.height / 2 : 12;

    // Draw curved path for relation edge
    const midX = (sourcePos.x + targetPos.x) / 2;
    const midY = (sourcePos.y + targetPos.y) / 2;
    const dx = targetPos.x - sourcePos.x;
    const dy = targetPos.y - sourcePos.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const offsetAmount = Math.min(30, dist * 0.2);
    const curveOffsetX = dist > 0 ? (-dy / dist) * offsetAmount : 0;
    const curveOffsetY = dist > 0 ? (dx / dist) * offsetAmount : 0;

    // Adjust target position to stop at node edge
    const angle = Math.atan2(targetPos.y - (midY + curveOffsetY), targetPos.x - (midX + curveOffsetX));
    const adjustedTargetX = targetPos.x - Math.cos(angle) * 10;
    const adjustedTargetY = targetPos.y - Math.sin(angle) * targetHeight;

    const pathData = `M${sourcePos.x},${sourcePos.y} Q${midX + curveOffsetX},${midY + curveOffsetY} ${adjustedTargetX},${adjustedTargetY}`;

    const sourceId = edge.source;
    const targetId = edge.target;
    
    edgesLayer.append('path')
      .attr('class', 'relation-link')
      .attr('data-source', sourceId)
      .attr('data-target', targetId)
      .attr('d', pathData)
      .style('fill', 'none')
      .style('stroke', edgeColor)
      .style('stroke-width', '1.5px')
      .style('stroke-dasharray', '4,2')
      .style('stroke-opacity', 0.8)
      .attr('marker-end', `url(#arrow-${colorId})`)
      .on('mouseenter', function() {
        onEdgeInteraction(sourceId, targetId, this, 'enter');
      })
      .on('mouseleave', function() {
        onEdgeInteraction(sourceId, targetId, this, 'leave');
      })
      .on('click', function() {
        onEdgeInteraction(sourceId, targetId, this, 'click');
      })
      .append('title')
      .text(`'${nodeIdLabelMap[edge.source]}' ${edgeLabel} '${nodeIdLabelMap[edge.target]}'` || 'relation');

    // Draw label on the edge
    if (edgeLabel) {
      edgesLayer.append('text')
        .attr('x', midX + curveOffsetX)
        .attr('y', midY + curveOffsetY - 4)
        .attr('text-anchor', 'middle')
        .style('font-size', '9px')
        .style('fill', edgeColor)
        .style('font-style', 'italic')
        .text(edgeLabel);
    }
  }
}

/**
 * Draw nodes
 */
export function drawNodes(
  nodesLayer: d3.Selection<SVGGElement, unknown, null, undefined>,
  treeLayouts: TreeLayoutData[],
  nodeDimensionsMap: Map<string, NodeDimensions>
) {
  for (const { root, offsetX, offsetY } of treeLayouts) {
    const treeNodesGroup = nodesLayer.append('g')
      .attr('class', 'tree-nodes')
      .attr('transform', `translate(${offsetX}, ${offsetY})`);

    const nodeGroups = treeNodesGroup.selectAll('.node')
      .data(root.descendants())
      .enter()
      .append('g')
      .attr('class', d => `node ose-curation-status-${(d.data.ose_curation || CURATION_STATUS.EXTERNAL).toLowerCase().replace(/\s+/g, '_')}`)
      .attr('data-node-id', d => d.data.id)
      .attr('transform', d => `translate(${d.x},${d.y})`);

    // Node background rectangle with dynamic dimensions
    nodeGroups.append('rect')
      .attr('x', d => {
        const dims = nodeDimensionsMap.get(d.data.id);
        return dims ? -dims.width / 2 : -40;
      })
      .attr('y', d => {
        const dims = nodeDimensionsMap.get(d.data.id);
        return dims ? -dims.height / 2 : -12;
      })
      .attr('width', d => {
        const dims = nodeDimensionsMap.get(d.data.id);
        return dims ? dims.width : 80;
      })
      .attr('height', d => {
        const dims = nodeDimensionsMap.get(d.data.id);
        return dims ? dims.height : 24;
      })
      .attr('rx', 4)
      .attr('ry', 4)
      .style('fill', '#fff')
      .style('stroke', '#999')
      .style('stroke-width', '1px');

    // Node label with multi-line support
    nodeGroups.each(function(d) {
      const dims = nodeDimensionsMap.get(d.data.id);
      if (!dims) return;

      const textGroup = d3.select(this).append('text')
        .attr('text-anchor', 'middle')
        .style('font-size', `${FONT_SIZE}px`)
        .style('fill', '#333');

      const lines = dims.lines;
      const totalHeight = lines.length * LINE_HEIGHT;
      const startY = -totalHeight / 2 + LINE_HEIGHT / 2;

      lines.forEach((line, i) => {
        textGroup.append('tspan')
          .attr('x', 0)
          .attr('dy', i === 0 ? `${startY + FONT_SIZE * 0.35}px` : `${LINE_HEIGHT}px`)
          .text(line);
      });

      // Add tooltip
      textGroup.append('title')
        .text(`${d.data.label}\n${d.data.id}`);
    });
  }
}

/**
 * Initialize pan and zoom
 */
export function initializePanZoom(
  svgElement: SVGSVGElement,
  savedState: PanZoomState | null
): ReturnType<typeof svgPanZoom> {
  const panZoom = svgPanZoom(svgElement, {
    zoomEnabled: true,
    controlIconsEnabled: true,
    dblClickZoomEnabled: false,
    contain: false,
    center: !savedState,
    zoomScaleSensitivity: 0.3,
    minZoom: 0.01,
    maxZoom: 100
  });

  // Restore previous pan/zoom state if available
  if (savedState) {
    panZoom.zoom(savedState.zoom);
    panZoom.pan(savedState.pan);
  }

  return panZoom;
}

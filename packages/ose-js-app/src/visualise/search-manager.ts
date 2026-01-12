import * as d3 from 'd3';
import type svgPanZoom from 'svg-pan-zoom';

export interface SearchState {
  query: string;
  matches: string[];
  currentIndex: number;
}

/**
 * Performs search on graph nodes
 */
export function performGraphSearch(
  query: string,
  nodeIdLabelMap: Record<string, string>
): string[] {
  const normalizedQuery = query.trim().toLowerCase();
  
  // Clear previous highlights
  d3.selectAll('.node').classed('search-match', false).classed('search-current', false);
  
  if (!normalizedQuery) {
    return [];
  }
  
  // Find matching nodes by label or ID
  const matches: string[] = [];
  d3.selectAll('.node').each(function() {
    const node = d3.select(this);
    const nodeId = node.attr('data-node-id');
    const label = nodeIdLabelMap[nodeId] || '';
    const id = nodeId?.replace('_', ':') || '';
    
    if (label.toLowerCase().includes(normalizedQuery) || id.toLowerCase().includes(normalizedQuery)) {
      matches.push(nodeId);
      node.classed('search-match', true);
    }
  });
  
  return matches;
}

/**
 * Highlights the current search match
 */
export function highlightSearchMatch(nodeId: string) {
  d3.selectAll('.node').classed('search-current', false);
  d3.select(`.node[data-node-id="${nodeId}"]`).classed('search-current', true);
}

/**
 * Clears all search highlights
 */
export function clearSearchHighlights() {
  d3.selectAll('.node').classed('search-match', false).classed('search-current', false);
}

/**
 * Pans the view to center a specific node
 */
export function panToNode(
  nodeId: string,
  svgContainer: HTMLElement,
  panZoomInstance: ReturnType<typeof svgPanZoom>
): boolean {
  const nodeElement = document.querySelector(`.node[data-node-id="${nodeId}"]`) as SVGGElement;
  
  if (!nodeElement) {
    console.warn('Node element not found:', nodeId);
    return false;
  }
  
  const svgElement = svgContainer.querySelector('svg');
  if (!svgElement) return false;
  
  // Get the graph container (has the actual content)
  const graphContainer = svgElement.querySelector('.graph-container') as SVGGElement;
  if (!graphContainer) return false;
  
  // Get node's position relative to graph container
  const nodeBBox = nodeElement.getBBox();
  
  // Get the node's transform relative to its parent
  let totalX = nodeBBox.x + nodeBBox.width / 2;
  let totalY = nodeBBox.y + nodeBBox.height / 2;
  
  // Walk up the tree to accumulate transforms until we reach graph-container
  let currentElement = nodeElement as SVGGraphicsElement;
  while (currentElement && currentElement !== graphContainer) {
    const transform = currentElement.getAttribute('transform');
    if (transform) {
      const match = transform.match(/translate\(([^,]+),([^)]+)\)/);
      if (match) {
        totalX += parseFloat(match[1]);
        totalY += parseFloat(match[2]);
      }
    }
    currentElement = currentElement.parentElement as unknown as SVGGraphicsElement;
    if (!currentElement || currentElement === svgElement) break;
  }
  
  // Now totalX, totalY are in viewBox coordinates
  // Get current zoom and viewport size
  const currentZoom = panZoomInstance.getSizes().realZoom;
  const sizes = panZoomInstance.getSizes();
  
  // Calculate pan to center the node
  const newPanX = (sizes.width / 2) - (totalX * currentZoom);
  const newPanY = (sizes.height / 2) - (totalY * currentZoom);
  
  panZoomInstance.pan({ x: newPanX, y: newPanY });
  return true;
}

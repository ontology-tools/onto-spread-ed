<script lang="ts" setup>
import { computed, onMounted, ref, toRaw, useTemplateRef, watch, watchEffect, watchPostEffect } from 'vue';
import { SpreadsheetData, VisualisationData, Graph, Row } from '../common/types';
import svgPanZoom from 'svg-pan-zoom';
import { CURATION_STATUS } from '../common/constants';
import * as d3 from 'd3';
import { 
  applyGraphFilters, 
  buildHierarchyTrees,
  type FilterOptions 
} from './graph-filters';
import {
  performGraphSearch,
  highlightSearchMatch,
  clearSearchHighlights,
  panToNode
} from './search-manager';
import {
  calculateNodeDimensions,
  calculateTreeLayouts,
  createArrowMarkers,
  drawHierarchyEdges,
  drawRelationEdges,
  drawNodes,
  initializePanZoom,
  type PanZoomState
} from './graph-renderer';

declare var URLS: { [key: string]: any };
const URL_PREFIX = URLS['prefix'];


const data = ref<VisualisationData | null>(window.ose?.visualise ?? null);

window.oseDataChanged = () => {
  data.value = window.ose?.visualise ?? null;
}

const svgContainer = useTemplateRef("svgContainer")

const sheetData = computed(() => data.value?.sheetData ?? { 
  rows: [], 
  header: [], 
  file_sha: '', 
  repo_name: '', 
  folder: '', 
  spreadsheet_name: '' 
} as SpreadsheetData<Row>);

const visualisationId = ref<string | null>(null);
const loading = ref<boolean>(false);
const error = ref<string | null>(null);

const curationStatuses = computed(() => Object.values(CURATION_STATUS));

const graph = ref<Graph | null>(null);

const nodeIdLabelMap = computed(() => graph.value?.nodes.reduce((map, node) => ({
  [node.id]: node.label,
  ...map
}), {} as Record<string, string>) ?? {});

const curationFilter = ref<string[]>(Object.values(CURATION_STATUS));
const showChildrenFromOtherSheets = ref<boolean>(true);
const showParentsFromOtherSheets = ref<boolean>(true);
const numChildLevels = ref<number | null>(null);
const maxChildLevels = computed(() => graph.value ? Math.max(...graph.value.nodes.map(n => n.visual_depth ?? 0), 1) : 1);

// Store svgPanZoom instance to preserve pan/zoom state across redraws
let panZoomInstance: ReturnType<typeof svgPanZoom> | null = null;

// Search functionality
const searchQuery = ref<string>('');
const searchMatches = ref<string[]>([]);
const currentMatchIndex = ref<number>(-1);

const hasSearchMatches = computed(() => searchMatches.value.length > 0);
const matchInfo = computed(() => {
  if (!searchQuery.value.trim()) return '';
  if (searchMatches.value.length === 0) return 'No matches';
  return `${currentMatchIndex.value + 1} / ${searchMatches.value.length}`;
});

function performSearch() {
  const matches = performGraphSearch(searchQuery.value, nodeIdLabelMap.value);
  searchMatches.value = matches;
  
  if (matches.length > 0) {
    currentMatchIndex.value = 0;
    highlightCurrentMatch();
    setTimeout(() => zoomToCurrentMatch(), 50);
  } else {
    currentMatchIndex.value = -1;
  }
}

function highlightCurrentMatch() {
  if (currentMatchIndex.value >= 0 && currentMatchIndex.value < searchMatches.value.length) {
    const currentNodeId = searchMatches.value[currentMatchIndex.value];
    highlightSearchMatch(currentNodeId);
  }
}

function zoomToCurrentMatch() {
  if (!panZoomInstance || currentMatchIndex.value < 0 || !svgContainer.value) return;
  
  const currentNodeId = searchMatches.value[currentMatchIndex.value];
  panToNode(currentNodeId, svgContainer.value, panZoomInstance);
}

function goToNextMatch() {
  if (searchMatches.value.length === 0) return;
  
  currentMatchIndex.value = (currentMatchIndex.value + 1) % searchMatches.value.length;
  highlightCurrentMatch();
  setTimeout(() => zoomToCurrentMatch(), 0);
}

function goToPreviousMatch() {
  if (searchMatches.value.length === 0) return;
  
  currentMatchIndex.value = (currentMatchIndex.value - 1 + searchMatches.value.length) % searchMatches.value.length;
  highlightCurrentMatch();
  setTimeout(() => zoomToCurrentMatch(), 0);
}

function clearSearch() {
  searchQuery.value = '';
  searchMatches.value = [];
  currentMatchIndex.value = -1;
  clearSearchHighlights();
}


async function fetchGraph() {
  loading.value = true;
  error.value = null;
  try {
    const response = await fetch(`${URL_PREFIX}/api/visualise/generate/${sheetData.value.repo_name}/${sheetData.value.folder}/${sheetData.value.spreadsheet_name}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        header: sheetData.value.header,
        rows: sheetData.value.rows.map(row => sheetData.value.header.map(h => row[h])),
      }),
    });
    
    if (!response.ok) {
      throw new Error(`Server error: ${response.status} ${response.statusText}`);
    }
    
    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.error || 'Failed to generate visualisation');
    }

    visualisationId.value = result.visualisation_id;

    graph.value = result.graphData as Graph;
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'An unexpected error occurred';
    console.error('Failed to fetch graph:', e);
  } finally {
    loading.value = false;
  }
}

function renderGraph() {
  if (!graph.value || !svgContainer.value) return;

  const g = JSON.parse(JSON.stringify(toRaw(graph.value))) as Graph;

  // Apply filters to graph
  const filterOptions: FilterOptions = {
    curationFilter: curationFilter.value,
    showChildrenFromOtherSheets: showChildrenFromOtherSheets.value,
    showParentsFromOtherSheets: showParentsFromOtherSheets.value,
    numChildLevels: numChildLevels.value,
    currentSheet: data?.value?.sheetData?.spreadsheet_name
  };

  const { nodes, hierarchyEdges, relationEdges } = applyGraphFilters(g, filterOptions);

  // Build hierarchical tree structures
  const trees = buildHierarchyTrees(nodes, hierarchyEdges);

  // Save current pan/zoom state before clearing the container
  let savedPanZoom: PanZoomState | null = null;
  if (panZoomInstance) {
    try {
      savedPanZoom = {
        zoom: panZoomInstance.getZoom(),
        pan: panZoomInstance.getPan()
      };
      panZoomInstance.destroy();
      panZoomInstance = null;
    } catch (e) {
      // Ignore errors if the instance is already destroyed
    }
  }

  // Clear the container
  svgContainer.value.innerHTML = '';

  // Create SVG
  const containerRect = svgContainer.value.getBoundingClientRect();
  const width = containerRect.width || 800;
  const height = containerRect.height || 600;

  const svg = d3.select(svgContainer.value)
    .append('svg')
    .attr('width', '100%')
    .attr('height', '100%')
    .attr('viewBox', `0 0 ${width} ${height}`);

  const g_main = svg.append('g').attr('class', 'graph-container');

  // Calculate node dimensions and layout
  const nodeDimensionsMap = calculateNodeDimensions(svg, trees);
  const { treeLayouts, nodePositions } = calculateTreeLayouts(trees, nodeDimensionsMap);

  // Create layer groups for proper z-ordering: edges below, nodes above
  const edgesLayer = g_main.append('g').attr('class', 'edges-layer');
  const nodesLayer = g_main.append('g').attr('class', 'nodes-layer');

  // Define arrowhead markers
  const defs = svg.append('defs');
  createArrowMarkers(defs, relationEdges);

  // Track the currently focused/locked edge
  let focusedEdge: { sourceId: string; targetId: string; element: SVGElement } | null = null;

  // Edge interaction handler
  function handleEdgeInteraction(sourceId: string, targetId: string, element: SVGElement, action: 'enter' | 'leave' | 'click') {
    // Helper to highlight/unhighlight connected nodes
    function highlightNodes(highlight: boolean) {
      svg.selectAll('.node').each(function() {
        const node = d3.select(this);
        const nodeId = node.attr('data-node-id');
        if (nodeId === sourceId || nodeId === targetId) {
          node.classed('edge-connected', highlight);
        }
      });
    }

    if (action === 'click') {
      const isSameEdge = focusedEdge?.sourceId === sourceId && focusedEdge?.targetId === targetId;
      
      if (isSameEdge) {
        // Unfocus
        highlightNodes(false);
        d3.select(focusedEdge!.element).classed('focused', false);
        focusedEdge = null;
      } else {
        // Unfocus previous edge if any
        if (focusedEdge) {
          svg.selectAll('.node').classed('edge-connected', false);
          d3.select(focusedEdge.element).classed('focused', false);
        }
        // Focus new edge
        focusedEdge = { sourceId, targetId, element };
        highlightNodes(true);
        d3.select(element).classed('focused', true);
      }
    } else if (action === 'enter' && !focusedEdge) {
      highlightNodes(true);
      d3.select(element).classed('highlighted', true);
    } else if (action === 'leave' && !focusedEdge) {
      highlightNodes(false);
      d3.select(element).classed('highlighted', false);
    }
  }

  // Draw hierarchy edges
  drawHierarchyEdges(edgesLayer, treeLayouts, nodeDimensionsMap, handleEdgeInteraction);

  // Draw relation edges
  drawRelationEdges(edgesLayer, relationEdges, nodePositions, nodeDimensionsMap, nodeIdLabelMap.value, handleEdgeInteraction);

  // Draw nodes
  drawNodes(nodesLayer, treeLayouts, nodeDimensionsMap);

  // Update viewBox based on actual content
  const bbox = (g_main.node() as SVGGElement)?.getBBox();
  if (bbox) {
    svg.attr('viewBox', `${bbox.x - 20} ${bbox.y - 20} ${bbox.width + 40} ${bbox.height + 40}`);
  }

  // Initialize pan and zoom
  const svgElement = svgContainer.value.querySelector('svg');
  if (svgElement) {
    panZoomInstance = initializePanZoom(svgElement as SVGSVGElement, savedPanZoom);
  }
}
function toggleCurationFilter(status: string) {
  const index = curationFilter.value.indexOf(status);
  if (index >= 0) {
    curationFilter.value.splice(index, 1);
  } else {
    curationFilter.value.push(status);
  }

  renderGraph();
}

// Render graph when graph data changes
watchPostEffect(() => {
  if (graph.value && svgContainer.value) {
    renderGraph();
  }
});

watchEffect(() => {
  if (visualisationId.value) {
    window.history.replaceState({}, '', `${window.location.pathname}?visualisation_id=${visualisationId.value}`);
  }
})

// watchEffect(() => {
//   if (sheetData.value.rows.length > 0) {
//     fetchGraph();
//   }
// });

// watchEffect(() => {
//   if (maxChildLevels.value && (numChildLevels.value === null || numChildLevels.value > maxChildLevels.value)) {
//     numChildLevels.value = maxChildLevels.value;
//   }
// })

watch(numChildLevels, (newValue, oldValue) => {
  if (newValue !== oldValue && newValue !== null && oldValue !== null) {
    renderGraph();
  }
});

watch(showChildrenFromOtherSheets, (newValue, oldValue) => {
  if (newValue !== oldValue) {
    renderGraph();
  }
});

watch(showParentsFromOtherSheets, (newValue, oldValue) => {
  if (newValue !== oldValue) {
    renderGraph();
  }
});

onMounted(async () => {
  if (svgContainer.value) {
    svgContainer.value.style.height = (window.innerHeight - svgContainer.value.offsetTop - 16) + "px";
  }

  loading.value = true;
  error.value = null;
  try {
    const params = new URLSearchParams(window.location.search);
    const visualisation_id = params.get("visualisation_id");
    if (visualisation_id) {
      const response = await fetch(`${URL_PREFIX}/api/visualise/load/${visualisation_id}`);
      
      if (!response.ok) {
        throw new Error(`Server error: ${response.status} ${response.statusText}`);
      }
      
      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.error || 'Failed to load visualisation');
      }

      graph.value = result.graphData as Graph;
      visualisationId.value = visualisation_id;
      
      data.value = {
        selection: [],
        sheetData: {
          repo_name: result.repo,
          folder: result.path.split('/').slice(0, -1).join('/'),
          spreadsheet_name: result.path.split('/').slice(-1)[0],
          header: [],
          rows: [],
          file_sha: "",
        }
      }

      console.log({graph: result.graphData});
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'An unexpected error occurred';
    console.error('Failed to load visualisation:', e);
  } finally {
    loading.value = false;
  }
});

</script>
<template>
  <div class="visualise-container">
    <div class="header d-flex align-items-center justify-content-between">
      <h3>Hierarchy Tree
        <small>
          for {{ data?.sheetData?.spreadsheet_name }}
        </small>
      </h3>

      <div class="search-bar">
        <div class="input-group input-group-sm">
          <input 
            type="text" 
            class="form-control" 
            placeholder="Search classes..." 
            v-model="searchQuery"
            @keyup.enter="performSearch"
          >
          <button class="btn btn-outline-secondary" type="button" @click="performSearch" title="Search">
            <i class="fa-solid fa-search"></i>
          </button>
          <button 
            class="btn btn-outline-secondary" 
            type="button" 
            @click="goToPreviousMatch" 
            :disabled="!hasSearchMatches"
            title="Previous match"
          >
            <i class="fa-solid fa-chevron-up"></i>
          </button>
          <button 
            class="btn btn-outline-secondary" 
            type="button" 
            @click="goToNextMatch" 
            :disabled="!hasSearchMatches"
            title="Next match"
          >
            <i class="fa-solid fa-chevron-down"></i>
          </button>
          <button 
            class="btn btn-outline-secondary" 
            type="button" 
            @click="clearSearch" 
            :disabled="!searchQuery"
            title="Clear search"
          >
            <i class="fa-solid fa-times"></i>
          </button>
        </div>
        <small class="search-info text-muted">{{ matchInfo }}</small>
      </div>

      <div class="form-check">
        <input class="form-check-input" type="checkbox" id="ckb_children_other_sheets"
          v-model="showChildrenFromOtherSheets">
        <label class="form-check-label" for="ckb_children_other_sheets">
          Show children from other sheets
        </label>
      </div>

      <div>
        <label for="range_num_child_levels" class="form-label">Number of child levels ({{ numChildLevels }})</label>
        <input type="range" class="form-range" v-model="numChildLevels" min="1" :max="maxChildLevels" step="1"
          id="range_num_child_levels">
      </div>

      <div class="form-check">
        <input class="form-check-input" type="checkbox" id="ckb_parents_other_sheets"
          v-model="showParentsFromOtherSheets">
        <label class="form-check-label" for="ckb_parents_other_sheets">
          Show parents from other sheets
        </label>
      </div>

      <div class="dropdown">
        <button class="btn btn-primary dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
          Curation Status
        </button>
        <ul class="dropdown-menu">
          <li v-for="s in curationStatuses">
            <a class="dropdown-item" :class="'ose-curation-status-' + s.toLowerCase().replace(' ', '_')" href="#"
              @click="toggleCurationFilter(s)">
              <i class="fa-regular" :class="curationFilter.indexOf(s) >= 0 ? ['fa-circle-check'] : ['fa-circle']"></i>
              {{ s }}
            </a>
          </li>
        </ul>
      </div>


    </div>
    <div ref="svgContainer" class="svg-container">
      <div v-if="loading" class="loading-overlay">
        <div class="spinner"></div>
        <span>Loading visualisation...</span>
      </div>
      <div v-else-if="error" class="error-overlay">
        <i class="fa-solid fa-circle-exclamation"></i>
        <span class="error-title">Failed to load visualisation</span>
        <span class="error-message">{{ error }}</span>
        <button class="btn btn-primary btn-sm" @click="fetchGraph">Try again</button>
      </div>
    </div>
  </div>
</template>
<style lang="scss">
.visualise-container {
  padding: 1rem;

  .search-bar {
    display: flex;
    align-items: center;
    gap: 0.5rem;

    .input-group {
      width: 280px;
    }

    .search-info {
      min-width: 70px;
      text-align: center;
    }
  }

  .loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    background: rgba(250, 250, 250, 0.9);
    z-index: 10;
    border-radius: 4px;

    span {
      color: #666;
      font-size: 0.9rem;
    }

    .spinner {
      width: 40px;
      height: 40px;
      border: 3px solid #e0e0e0;
      border-top-color: #3b82f6;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }
  }

  .error-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    background: rgba(250, 250, 250, 0.95);
    z-index: 10;
    border-radius: 4px;

    .fa-circle-exclamation {
      font-size: 2.5rem;
      color: #dc3545;
    }

    .error-title {
      font-size: 1.1rem;
      font-weight: 600;
      color: #333;
    }

    .error-message {
      font-size: 0.85rem;
      color: #666;
      max-width: 400px;
      text-align: center;
      padding: 0.5rem 1rem;
      background: #f8f8f8;
      border: 1px solid #e0e0e0;
      border-radius: 4px;
    }

    button {
      margin-top: 0.5rem;
    }
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  $curation_status: discussed, proposed, to_be_discussed, in_discussion, published, obsolete, external, pre_proposed;

  @each $status in $curation_status {
    .node.ose-curation-status-#{$status} {
      & > rect {
        fill: var(--ose-curation-status-#{$status}) !important;
      }
    }

    .ose-curation-status-#{$status} {
      background: var(--ose-curation-status-#{$status}) !important;
    }
  }

  // Default/uncurated status
  .node.ose-curation-status-unknown {
    & > rect {
      fill: #fff !important;
    }
  }

  h3 {
    margin: 0 0 0.5rem 0;
    flex-shrink: 0;
  }

  .svg-container {
    position: relative;
    display: block;
    min-width: 100%;
    min-height: 100%;


    width: 100%;
    flex: 1;
    min-height: 0;
    overflow: auto;
    border: 1px solid #ddd;
    border-radius: 4px;
    background: #fafafa;

    transition: all 0.2s ease;

    .link, .relation-link {
      fill: none;
      stroke: #999;
      stroke-opacity: 0.6;
      stroke-width: 1.5px;
      cursor: pointer;
      
      &.highlighted {
        stroke-opacity: 1 !important;
        stroke-width: 3px !important;
      }

      &.focused {
        stroke-opacity: 1 !important;
        stroke-width: 3.5px !important;
        filter: drop-shadow(0 0 3px rgba(0, 0, 0, 0.5));
      }
    }

    .relation-link {
      stroke-opacity: 0.8;
    }

    .node {
      cursor: pointer;

      &:hover, &.edge-connected {
        & > rect {
          stroke: #333 !important;
          stroke-width: 2px !important;
        }
      }

      &.edge-connected > rect {
        filter: drop-shadow(0 0 4px rgba(0, 0, 0, 0.4));
      }

      &.search-match > rect {
        stroke: #f59e0b !important;
        stroke-width: 2px !important;
        filter: drop-shadow(0 0 4px rgba(245, 158, 11, 0.6));
      }

      &.search-current > rect {
        stroke: #dc2626 !important;
        stroke-width: 3px !important;
        filter: drop-shadow(0 0 6px rgba(220, 38, 38, 0.8));
      }
    }
  }
}
</style>
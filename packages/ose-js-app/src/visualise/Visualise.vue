<script lang="ts" setup>
import { computed, onMounted, ref, useTemplateRef, watch, watchEffect, watchPostEffect } from 'vue';
import { SpreadsheetData, VisualisationData, Graph, Row } from "@ose/js-core";
import svgPanZoom from 'svg-pan-zoom';
import { CURATION_STATUS } from "@ose/js-core";
import * as d3 from 'd3';
import {
  applyGraphFilters,
  buildHierarchyTrees,
  HierarchyNode,
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
import { buildGraphFromSpreadsheet, type DependencyData } from './graph-builder';
import { NavigateToTermMessage } from "@ose/js-core";

declare var URLS: { [key: string]: any };
const URL_PREFIX = URLS['prefix'];


const data = ref<VisualisationData | null>(window.ose?.visualise ?? null);

window.oseDataChanged = () => {
  console.debug("Visualisation data updated in window.ose", window.ose?.visualise);
  data.value = window.ose?.visualise ?? null;

  // Debug the computed sheetData
  const sheet = data.value?.sheetData;
  console.debug("Sheet data after update:", {
    hasSheetData: !!sheet,
    repo_name: sheet?.repo_name,
    folder: sheet?.folder,
    spreadsheet_name: sheet?.spreadsheet_name,
    rowCount: sheet?.rows?.length || 0,
    header: sheet?.header
  });
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

const sheetPath = computed(() => `${sheetData.value.folder}/${sheetData.value.spreadsheet_name}`);

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
const maxChildLevels = computed(() => graph.value ? Math.max(...graph.value.nodes.map(n => n.visualDepth ?? 0), 1) : 1);

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
const controlsDisabled = computed(() => !graph.value || loading.value);

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
  // Validate that we have all required data
  if (!sheetData.value.repo_name || !sheetData.value.folder || !sheetData.value.spreadsheet_name) {
    console.warn('Cannot fetch graph: missing repo, folder, or spreadsheet name', {
      repo: sheetData.value.repo_name,
      folder: sheetData.value.folder,
      spreadsheet: sheetData.value.spreadsheet_name
    });
    return;
  }

  if (sheetData.value.rows.length === 0) {
    console.warn('Cannot fetch graph: no rows in spreadsheet');
    return;
  }

  console.debug('Fetching graph dependencies...', {
    repo: sheetData.value.repo_name,
    folder: sheetData.value.folder,
    spreadsheet: sheetData.value.spreadsheet_name,
    rowCount: sheetData.value.rows.length
  });

  loading.value = true;
  error.value = null;
  try {
    const response = await fetch(`${URL_PREFIX}/api/visualise/dependencies/${sheetData.value.repo_name}/${sheetData.value.folder}/${sheetData.value.spreadsheet_name}`);

    if (!response.ok) {
      throw new Error(`Server error: ${response.status} ${response.statusText}`);
    }

    const result = await response.json();

    if (!result.success) {
      throw new Error(result.error || 'Failed to load dependencies');
    }

    console.debug('Dependencies loaded successfully', result.data);

    // Reset view
    panZoomInstance?.destroy();
    panZoomInstance = null;
    clearSearch();

    // Build graph from current spreadsheet data + dependencies on frontend
    const dependencyData = result.data as DependencyData;
    const selection = data.value?.selection && data.value.selection.length > 0 ? data.value.selection : undefined;
    graph.value = buildGraphFromSpreadsheet(
      sheetData.value.rows,
      sheetData.value.header,
      sheetData.value.spreadsheet_name,
      dependencyData,
      selection
    );

    // Set child levels to minimum of 3 and max child depth
    numChildLevels.value = Math.min(3, maxChildLevels.value);

    console.debug('Graph built successfully', {
      nodes: graph.value.nodes.length,
      edges: graph.value.edges.length
    });
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'An unexpected error occurred';
    console.error('Failed to fetch dependencies:', e);
  } finally {
    loading.value = false;
  }
}

function renderGraph() {
  if (!graph.value || !svgContainer.value) {
    console.warn('Cannot render graph:', { hasGraph: !!graph.value, hasContainer: !!svgContainer.value });
    return;
  }

  console.debug('Rendering graph...', {
    nodes: graph.value.nodes.length,
    edges: graph.value.edges.length
  });

  const g = graph.value.clone();

  // Apply filters to graph
  const filterOptions: FilterOptions = {
    curationFilter: curationFilter.value,
    showChildrenFromOtherSheets: showChildrenFromOtherSheets.value,
    showParentsFromOtherSheets: showParentsFromOtherSheets.value,
    numChildLevels: numChildLevels.value,
    currentSheet: data?.value?.sheetData?.spreadsheet_name
  };

  const { nodes, hierarchyEdges, relationEdges } = applyGraphFilters(g, filterOptions);

  console.debug('After filtering:', {
    nodes: nodes.length,
    hierarchyEdges: hierarchyEdges.length,
    relationEdges: relationEdges.length
  });

  // Build hierarchical tree structures
  const trees = buildHierarchyTrees(nodes, hierarchyEdges);

  console.debug('Built trees:', trees.length);

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
  svgContainer.value.querySelector('svg')?.remove();

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

  // Node interaction handler
  function handleNodeInteraction(nodeId: string, element: SVGElement, action: 'enter' | 'leave') {
    if (action === 'enter') {
      // Highlight the node itself
      d3.select(element).classed('node-hovered', true);

      // Find and highlight all connected edges (both hierarchy and relation edges)
      svg.selectAll('.link, .relation-link').each(function () {
        const edge = d3.select(this);
        const sourceId = edge.attr('data-source');
        const targetId = edge.attr('data-target');

        if (sourceId === nodeId || targetId === nodeId) {
          edge.classed('connected', true);

          // Also highlight the connected nodes
          if (sourceId !== nodeId) {
            svg.select(`.node[data-node-id="${sourceId}"]`).classed('node-connected', true);
          }
          if (targetId !== nodeId) {
            svg.select(`.node[data-node-id="${targetId}"]`).classed('node-connected', true);
          }
        }
      });
    } else if (action === 'leave') {
      // Remove highlight from node
      d3.select(element).classed('node-hovered', false);

      // Remove highlight from edges (both hierarchy and relation edges)
      svg.selectAll('.link, .relation-link').classed('connected', false);

      // Remove highlight from connected nodes
      svg.selectAll('.node').classed('node-connected', false);
    }
  }

  // Edge interaction handler
  function handleEdgeInteraction(sourceId: string, targetId: string, element: SVGElement, action: 'enter' | 'leave' | 'click') {
    // Helper to highlight/unhighlight connected nodes
    function highlightNodes(highlight: boolean) {
      svg.selectAll('.node').each(function () {
        const node = d3.select(this);
        const nodeId = node.attr('data-node-id');
        if (nodeId === sourceId || nodeId === targetId) {
          node.classed('edge-connected', highlight);
        }
      });
    }

    // Helper to find and highlight the corresponding edge path and label
    function highlightEdgeElements(highlight: boolean, classToAdd: string) {
      // Find the edge path
      svg.selectAll('.link, .relation-link').each(function () {
        const edge = d3.select(this);
        if (edge.attr('data-source') === sourceId && edge.attr('data-target') === targetId) {
          edge.classed(classToAdd, highlight);
        }
      });

      // Find the edge label
      svg.selectAll('.relation-edge-label').each(function () {
        const label = d3.select(this);
        if (label.attr('data-source') === sourceId && label.attr('data-target') === targetId) {
          label.classed(classToAdd, highlight);
        }
      });
    }

    if (action === 'click') {
      const isSameEdge = focusedEdge?.sourceId === sourceId && focusedEdge?.targetId === targetId;

      if (isSameEdge) {
        // Unfocus
        highlightNodes(false);
        highlightEdgeElements(false, 'focused');
        focusedEdge = null;
      } else {
        // Unfocus previous edge if any
        if (focusedEdge) {
          svg.selectAll('.node').classed('edge-connected', false);
          highlightEdgeElements(false, 'focused');
        }
        // Focus new edge
        focusedEdge = { sourceId, targetId, element };
        highlightNodes(true);
        highlightEdgeElements(true, 'focused');
      }
    } else if (action === 'enter' && !focusedEdge) {
      highlightNodes(true);
      highlightEdgeElements(true, 'highlighted');
    } else if (action === 'leave' && !focusedEdge) {
      highlightNodes(false);
      highlightEdgeElements(false, 'highlighted');
    }
  }

  // Node double-click handler
  function handleNodeDoubleClick(nodeData: HierarchyNode) {
    // Don't navigate for external terms
    if (nodeData.ose_curation?.toLowerCase() === 'external') {
      return;
    }

    // Get the editor window and repo info
    const editorWindow: Window | null = window.opener;
    const repo = sheetData.value.repo_name;
    const originSheet = nodeData.ose_source === "current" ? sheetPath.value : nodeData.ose_origin;
    const nodeId = nodeData.id;

    if (!editorWindow || !repo || !originSheet || !nodeId) {
      console.warn('Cannot navigate to term: missing data', { editorWindow, repo, originSheet, nodeId });
      return;
    }

    const message: NavigateToTermMessage = {
      type: "navigateToTerm",
      repo: repo,
      sheet: originSheet,
      termID: nodeId
    }

    editorWindow.postMessage(message, "*");
  }

  // Draw hierarchy edges
  drawHierarchyEdges(edgesLayer, treeLayouts, nodeDimensionsMap, handleEdgeInteraction);

  // Draw relation edges
  drawRelationEdges(edgesLayer, relationEdges, nodePositions, nodeDimensionsMap, nodeIdLabelMap.value, handleEdgeInteraction);

  // Draw nodes
  drawNodes(nodesLayer, treeLayouts, nodeDimensionsMap, handleNodeInteraction, handleNodeDoubleClick);





  // Initialize pan and zoom
  const svgElement = svgContainer.value?.querySelector('svg');
  if (svgElement) {
    panZoomInstance = initializePanZoom(svgElement as SVGSVGElement, savedPanZoom);


    const bbox = (g_main.node() as SVGGElement)?.getBBox();
    if (bbox && panZoomInstance && !savedPanZoom) {
      const scaleX = containerRect.width / bbox.width;
      const scaleY = containerRect.height / bbox.height;
      const scale = Math.min(scaleX, scaleY, 1);
      panZoomInstance.zoom(scale);

      const panX = (containerRect.width - bbox.width * scale) / 2 - bbox.x * scale;
      const panY = (containerRect.height - bbox.height * scale) / 2 - bbox.y * scale;
      panZoomInstance.pan({ x: panX, y: panY });
    }
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

// Fetch graph when sheet data is available
watchEffect(() => {
  console.debug('watchEffect triggered:', {
    rowsLength: sheetData.value.rows.length,
    repo_name: sheetData.value.repo_name,
    folder: sheetData.value.folder,
    spreadsheet_name: sheetData.value.spreadsheet_name,
    allConditionsMet: sheetData.value.rows.length > 0 &&
      !!sheetData.value.repo_name &&
      !!sheetData.value.folder &&
      !!sheetData.value.spreadsheet_name
  });

  if (sheetData.value.rows.length > 0 &&
    sheetData.value.repo_name &&
    sheetData.value.folder &&
    sheetData.value.spreadsheet_name) {
    fetchGraph();
  }
});

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

watch(loading, (newValue, oldValue) => {
  if (newValue && oldValue === false) {
    svgContainer.value?.querySelector('svg')?.remove();
    clearSearch();
  }
});

onMounted(async () => {
  if (svgContainer.value) {
    svgContainer.value.style.minHeight = (window.innerHeight - svgContainer.value.offsetTop - 16) + "px";
  }
});

</script>
<template>
  <div class="visualise-container">
    <div class="header">
      <div class="header-title-row">
        <div class="title-with-help">
          <h5 class="mb-0">
            Hierarchy Tree <small class="text-muted">{{ data?.sheetData?.spreadsheet_name }}</small>
          </h5>
          <button class="btn btn-sm btn-link text-secondary p-0 ms-2" type="button" data-bs-toggle="modal"
            data-bs-target="#legendModal" title="Help & Legend">
            <i class="fa-solid fa-circle-question"></i>
          </button>
        </div>

        <div class="search-bar">
          <small class="search-info text-muted">{{ matchInfo }}</small>
          <div class="input-group input-group-sm">
            <input type="text" class="form-control" placeholder="Search classes..." v-model="searchQuery"
              @keyup.enter="performSearch" :disabled="controlsDisabled">
            <button class="btn btn-outline-secondary" type="button" @click="performSearch" title="Search"
              :disabled="controlsDisabled">
              <i class="fa-solid fa-search"></i>
            </button>
            <button class="btn btn-outline-secondary" type="button" @click="goToPreviousMatch"
              :disabled="!hasSearchMatches || controlsDisabled" title="Previous match">
              <i class="fa-solid fa-chevron-up"></i>
            </button>
            <button class="btn btn-outline-secondary" type="button" @click="goToNextMatch"
              :disabled="!hasSearchMatches || controlsDisabled" title="Next match">
              <i class="fa-solid fa-chevron-down"></i>
            </button>
            <button class="btn btn-outline-secondary" type="button" @click="clearSearch"
              :disabled="!searchQuery || controlsDisabled" title="Clear search">
              <i class="fa-solid fa-times"></i>
            </button>
          </div>
        </div>
      </div>

      <div class="filters-card">
        <div class="filter-section">
          <span class="filter-section-title">
            <i class="fa-solid fa-filter"></i>
            From other sheets
          </span>
          <div class="filter-controls">
            <div class="form-check form-switch">
              <input class="form-check-input" type="checkbox" role="switch" id="ckb_children_other_sheets"
                v-model="showChildrenFromOtherSheets" :disabled="controlsDisabled">
              <label class="form-check-label" for="ckb_children_other_sheets">
                <i class="fa-solid fa-arrow-down"></i>
                Children
              </label>
            </div>

            <div class="form-check form-switch">
              <input class="form-check-input" type="checkbox" role="switch" id="ckb_parents_other_sheets"
                v-model="showParentsFromOtherSheets" :disabled="controlsDisabled">
              <label class="form-check-label" for="ckb_parents_other_sheets">
                <i class="fa-solid fa-arrow-up"></i>
                Parents
              </label>
            </div>
          </div>
        </div>

        <div class="filter-section">
          <span class="filter-section-title">
            <i class="fa-solid fa-layer-group"></i>
            Child Levels
          </span>
          <div class="filter-controls">
            <div class="range-control">
              <div class="range-header">
                <label for="range_num_child_levels" class="form-label">
                  Depth: <strong>{{ numChildLevels || 'All' }}</strong>
                </label>
                <span class="range-minmax">1–{{ maxChildLevels }}</span>
              </div>
              <input type="range" class="form-range" v-model="numChildLevels" min="1" :max="maxChildLevels" step="1"
                id="range_num_child_levels" :disabled="controlsDisabled">
            </div>
          </div>
        </div>

        <div class="filter-section">
          <span class="filter-section-title">
            <i class="fa-solid fa-tags"></i>
            Curation Status
          </span>
          <div class="filter-controls">
            <div class="dropdown">
              <button class="btn btn-sm btn-outline-primary dropdown-toggle" type="button" data-bs-toggle="dropdown"
                aria-expanded="false" :disabled="controlsDisabled">
                <i class="fa-solid fa-filter"></i>
                {{ curationFilter.length }}/{{ curationStatuses.length }} selected
              </button>
              <ul class="dropdown-menu dropdown-menu-end">
                <li v-for="s in curationStatuses" :key="s">
                  <a class="dropdown-item" :class="'ose-curation-status-' + s.toLowerCase().replace(' ', '_')" href="#"
                    @click="toggleCurationFilter(s)">
                    <i class="fa-solid" :class="curationFilter.indexOf(s) >= 0 ? 'fa-circle-check' : 'fa-circle'"></i>
                    {{ s }}
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>
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
      <div v-else-if="!graph" class="empty-state-overlay">
        <i class="fa-solid fa-diagram-project"></i>
        <span class="empty-state-title">No Visualisation Loaded</span>
        <span class="empty-state-message">To see a visualisation, open a spreadsheet from the editor and click the
          "Visualise" button in the toolbar.</span>
      </div>
    </div>

    <!-- Help & Legend Modal -->
    <div class="modal fade" id="legendModal" tabindex="-1" aria-labelledby="legendModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="legendModalLabel">
              <i class="fa-solid fa-circle-info"></i> Help & Legend
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div class="legend-grid">
              <div class="legend-item">
                <h6><i class="fa-solid fa-circle-question"></i> How to Use</h6>
                <ul>
                  <li><strong>Pan:</strong> Click and drag the background</li>
                  <li><strong>Zoom:</strong> Use mouse wheel or pinch gesture</li>
                  <li><strong>Search:</strong> Find specific classes using the search bar</li>
                  <li><strong>Children/Parents Switches:</strong> Toggle whether to include children or parents from
                    other sheets</li>
                  <li><strong>Child Levels Slider:</strong> Adjust how many levels of child classes to display</li>
                  <li><strong>Curation Status Filter:</strong> Select which curation statuses to display</li>
                  <li><strong>Hover on nodes/edges:</strong> Highlight related nodes and edges</li>
                  <li><strong>Click on edges:</strong> Keep the edge highlighted</li>
                </ul>
              </div>

              <div class="legend-item">
                <h6><i class="fa-solid fa-circle-nodes"></i> Node Types</h6>
                <div class="node-examples">
                  <div class="node-example">
                    <div class="example-node node-current">Current Sheet</div>
                    <div class="example-node node-current node-selected">Selected Term</div>
                    <span class="example-desc">Terms from the current spreadsheet (regular border, selected bold)</span>
                  </div>
                  <div class="node-example">
                    <div class="example-node node-dependencies">Dependencies</div>
                    <span class="example-desc">External terms or terms from other sheets referenced by current terms
                      (dashed border)</span>
                  </div>
                  <div class="node-example">
                    <div class="example-node node-derived">Derived</div>
                    <span class="example-desc">Child terms from other sheets (italic text)</span>
                  </div>
                </div>
              </div>

              <div class="legend-item">
                <h6><i class="fa-solid fa-arrow-right"></i> Edge Types</h6>
                <ul>
                  <li><strong>Subclass Of:</strong> Solid black arrows showing hierarchy (parent → child)</li>
                  <li><strong>Relations:</strong> Colored arrows showing other relationships (e.g., "has part", "part
                    of")</li>
                </ul>
              </div>

              <div class="legend-item full-width">
                <h6><i class="fa-solid fa-palette"></i> Curation Status Colors</h6>
                <div class="status-grid">
                  <span v-for="status in curationStatuses" :key="status" class="status-badge"
                    :class="'ose-curation-status-' + status.toLowerCase().replace(' ', '_')">
                    {{ status }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<style lang="scss">
.visualise-container {
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .header {
    padding: 0.75rem 1rem;
    flex-shrink: 0;
    background: #fff;
  }

  .header-title-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.5rem;

    .title-with-help {
      display: flex;
      align-items: center;
    }

    h5 {
      margin: 0;
      font-weight: 600;

      small {
        font-size: 0.85rem;
        font-weight: 400;
      }
    }

    .btn-link {
      font-size: 1.2rem;
      line-height: 1;
      text-decoration: none;

      &:hover {
        color: #3b82f6 !important;
      }
    }
  }

  .filters-card {
    display: flex;
    gap: 1.5rem;
    padding: 0.5rem 1rem;
    background: #f8f9fa;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    align-items: center;
  }

  .filter-section {
    display: flex;
    align-items: center;
    gap: 0.75rem;

    &:not(:last-child) {
      border-right: 1px solid #e8e8e8;
      padding-right: 1.5rem;
    }
  }

  .filter-section-title {
    font-size: 0.8rem;
    font-weight: 600;
    color: #555;
    display: flex;
    align-items: center;
    gap: 0.4rem;
    white-space: nowrap;

    i {
      color: #999;
      font-size: 0.75rem;
    }
  }

  .filter-controls {
    display: flex;
    gap: 0.75rem;

    .form-check {
      margin-bottom: 0;
    }


    .form-switch {
      display: flex;
      gap: 8px;
    }

    .form-check-label {
      display: flex;
      align-items: center;
      gap: 0.35rem;
      font-size: 0.8rem;
      color: #555;
      cursor: pointer;

      i {
        color: #999;
        font-size: 0.7rem;
      }
    }

    .form-check-input {
      cursor: pointer;
    }

    .dropdown-toggle {
      text-align: left;
      display: flex;
      align-items: center;
      gap: 0.4rem;
      font-size: 0.8rem;
      padding: 0.25rem 0.6rem;

      i {
        font-size: 0.7rem;
      }
    }
  }

  .range-control {
    min-width: 200px;

    .range-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.25rem;
    }

    .form-label {
      font-size: 0.8rem;
      color: #555;
      margin-bottom: 0;

      strong {
        color: #333;
        font-weight: 600;
      }
    }

    .range-minmax {
      font-size: 0.7rem;
      color: #999;
    }

    .form-range {
      height: 0.35rem;
      margin: 0;
    }
  }

  .search-bar {
    display: flex;
    align-items: center;
    gap: 0.5rem;

    .input-group {
      width: 320px;
    }

    .search-info {
      min-width: 70px;
      text-align: center;
      font-size: 0.875rem;
    }
  }

  .legend-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
  }

  .legend-item {
    &.full-width {
      grid-column: 1 / -1;
    }

    h6 {
      font-size: 0.95rem;
      font-weight: 600;
      color: #333;
      margin-bottom: 0.75rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;

      i {
        color: #3b82f6;
        font-size: 0.9rem;
      }
    }

    ul {
      list-style: none;
      padding: 0;
      margin: 0;
      font-size: 0.875rem;
      color: #555;

      li {
        padding: 0.35rem 0;
        line-height: 1.5;
      }
    }
  }

  .node-examples {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .node-example {
    display: grid;
    grid-auto-flow: column;
    gap: 0.5rem;

    .example-desc {
      font-size: 0.8rem;
      color: #666;
      line-height: 1.4;

      grid-row: 2;
      grid-column: 1/3;
    }
  }

  .example-node {
    padding: 0.5rem 0.75rem;
    border: 2px solid #333;
    border-radius: 4px;
    background: white;
    font-size: 0.875rem;
    font-weight: 500;
    text-align: center;
    display: inline-block;
    align-self: flex-start;

    grid-row: 1;

    &.node-selected {
      font-weight: bold;
    }

    &.node-current {
      border-style: solid;
    }

    &.node-dependencies {
      border-style: dashed;
      font-style: italic;
    }

    &.node-derived {
      font-style: italic;
    }
  }

  .status-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 0.5rem;
  }

  .status-badge {
    display: inline-block;
    padding: 0.35rem 0.75rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 500;
    text-align: center;
  }

  .svg-container {
    position: relative;
    flex: 1;
    overflow: hidden;
    border: 1px solid #ddd;
    border-radius: 6px;
    background: #fafafa;

    svg {
      width: 100%;
      height: 100%;
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

  .empty-state-overlay {
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
    background: rgba(250, 250, 250, 0.95);
    z-index: 10;
    border-radius: 4px;

    .fa-diagram-project {
      font-size: 3rem;
      color: #999;
    }

    .empty-state-title {
      font-size: 1.25rem;
      font-weight: 600;
      color: #555;
    }

    .empty-state-message {
      font-size: 0.95rem;
      color: #666;
      max-width: 500px;
      text-align: center;
      line-height: 1.5;
    }
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .node.ose-selected {
    font-weight: bold;
  }

  .node.ose-source-derived {
    font-style: italic;
  }

  .node.ose-source-dependencies {
    font-style: italic;

    &>rect {
      stroke-dasharray: 4 2 !important;
    }
  }

  $curation_status: discussed, proposed, to_be_discussed, in_discussion, published, obsolete, external, pre_proposed;

  @each $status in $curation_status {
    .node.ose-curation-status-#{$status} {
      &>rect {
        fill: var(--ose-curation-status-#{$status}) !important;
      }
    }

    .ose-curation-status-#{$status} {
      background: var(--ose-curation-status-#{$status}) !important;
    }
  }

  // Default/uncurated status
  .node.ose-curation-status-unknown {
    &>rect {
      fill: #fff !important;
    }
  }

  .link,
  .relation-link {
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

    &.connected {
      stroke-opacity: 1 !important;
      stroke-width: 3px !important;
      filter: drop-shadow(0 0 2px rgba(0, 0, 0, 0.3));
    }
  }

  .relation-link {
    stroke-opacity: 0.8;
  }

  .node {
    cursor: pointer;

    &:hover,
    &.edge-connected {
      &>rect {
        stroke: #333 !important;
        stroke-width: 2px !important;
      }
    }

    &.edge-connected>rect {
      filter: drop-shadow(0 0 4px rgba(0, 0, 0, 0.4));
    }

    &.node-hovered>rect {
      stroke: #3b82f6 !important;
      stroke-width: 3px !important;
      filter: drop-shadow(0 0 6px rgba(59, 130, 246, 0.5));
    }

    &.node-connected>rect {
      stroke: #3b82f6 !important;
      stroke-width: 2px !important;
      filter: drop-shadow(0 0 4px rgba(59, 130, 246, 0.3));
    }

    &.search-match>rect {
      stroke: #f59e0b !important;
      stroke-width: 2px !important;
      filter: drop-shadow(0 0 4px rgba(245, 158, 11, 0.6));
    }

    &.search-current>rect {
      stroke: #dc2626 !important;
      stroke-width: 3px !important;
      filter: drop-shadow(0 0 6px rgba(220, 38, 38, 0.8));
    }
  }
}
</style>
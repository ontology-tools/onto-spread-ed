<script lang="ts" setup>
import { computed, h, onMounted, ref, useTemplateRef, watch, watchEffect } from 'vue';
import { SpreadsheetData } from '../common/spreadsheetdata';
import { Graphviz } from "@hpcc-js/wasm/graphviz";
import svgPanZoom from 'svg-pan-zoom';
import { Digraph, fromDot, Node, RootGraphModel, toDot } from 'ts-graphviz';
import { CURATION_STATUS } from '../common/constants';

declare var URLS: { [key: string]: any };
const URL_PREFIX = URLS['prefix'];

interface Row {
  Label: string;
  ID: string;
  Parent: string;

  [key: string]: string;
}

interface VisualisationData {
  sheetData: SpreadsheetData<Row>,
  selection: string[];
}

const data = ref<VisualisationData>(window.ose?.visualise ?? {});

window.oseDataChanged = () => {
  data.value = window.ose?.visualise ?? {};
}

const graphviz = ref<Graphviz | null>(null);

const svgContainer = useTemplateRef("svgContainer")

const sheetData = computed(() => data.value.sheetData ?? { rows: [] });

const visualisationId = ref<string | null>(null);
const loading = ref<boolean>(false);

const dotSource = ref<string | null>(null);
const originalDotSource = ref<string | null>(null);
const curationStatuses = computed(() => Object.values(CURATION_STATUS));

let graph = () => dotSource.value ? fromDot(dotSource.value) : null;
let originalGraph = () => originalDotSource.value ? fromDot(originalDotSource.value) : null;

const curationFilter = ref<string[]>(Object.values(CURATION_STATUS));
const showChildrenFromOtherSheets = ref<boolean>(true);
const showParentsFromOtherSheets = ref<boolean>(true);
const maxChildLevels = computed(() => originalGraph()?.nodes?.map(n => parseInt(n.attributes.get("depth") as string) - 1).reduce((a, b) => Math.max(a, b), 1) ?? 1);
const numChildLevels = ref<number | null>(null);

async function fetchGraph() {
  loading.value = true;
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
    const result = await response.json();

    visualisationId.value = result.visualisation_id;

    originalDotSource.value = result.dot;
    dotSource.value = result.dot;
  } finally {
    loading.value = false;
  }
}

function renderGraph() {
  const g = originalGraph();

  if (g) {
    for (const node of g.nodes) {
      const nodeStatus: string = node.attributes.get('ose_curation') as string ?? "uncurated";
      const nodeOrigin: string = node.attributes.get('ose_origin') as string ?? "<unknown>";
      const nodeDepth: number = parseInt(node.attributes.get('depth') ?? "0");


      const curationStatusFilter = !curationFilter.value.includes(nodeStatus.trim());
      const childSheetFilter = (!showChildrenFromOtherSheets.value && data?.value?.sheetData !== null && !nodeOrigin.endsWith(data.value?.sheetData.spreadsheet_name));
      const parentSheetFilter = (!showParentsFromOtherSheets.value && data?.value?.sheetData !== null && !nodeOrigin.endsWith(data.value?.sheetData.spreadsheet_name));
      const depthFilter = numChildLevels.value !== null && maxChildLevels.value !== null && nodeDepth - 1 > numChildLevels.value;

      if (curationStatusFilter || childSheetFilter || parentSheetFilter || depthFilter) {
        g.edges.filter(e => e.targets.find(t => t.id === node.id)).forEach(e => g.removeEdge(e));
        g.removeNode(node);
      }
    }

    dotSource.value = toDot(g);
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

// Render SVG when dot source or graphviz instance changes
watchEffect(() => {
  if (dotSource.value && graphviz.value && svgContainer.value) {
    const svgString = graphviz.value.layout(dotSource.value, "svg", "dot");
    svgContainer.value.innerHTML = svgString;

    const svg = svgContainer.value.querySelector("svg")!;

    svg.setAttribute("width", "100%");
    svg.setAttribute("height", "100%");

    svgPanZoom(svg, {
      zoomEnabled: true,
      controlIconsEnabled: true,
      dblClickZoomEnabled: false,
      contain: false,
      center: true,
      zoomScaleSensitivity: .3,
      minZoom: 0.01,
      maxZoom: 100
    });


  }
});

watchEffect(() => {
  if (visualisationId.value) {
    window.history.replaceState({}, '', `${window.location.pathname}?visualisation_id=${visualisationId.value}`);
  }
})

watchEffect(() => {
  if (sheetData.value.rows.length > 0) {
    fetchGraph();
  }
});

watchEffect(() => {
  if (maxChildLevels.value && (numChildLevels.value === null || numChildLevels.value > maxChildLevels.value)) {
    numChildLevels.value = maxChildLevels.value;
  }
})

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
  try {
    graphviz.value = await Graphviz.load();

    const params = new URLSearchParams(window.location.search);
    const visualisation_id = params.get("visualisation_id");
    if (visualisation_id) {
      const response = await fetch(`${URL_PREFIX}/api/visualise/load/${visualisation_id}`);
      const result = await response.json();

      dotSource.value = result.dot;
      originalDotSource.value = result.dot;
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

      console.debug(result.dot)
    }
  } finally {
    loading.value = false;
  }
});

</script>
<template>
  <div class="visualise-container" :class="{ loading: loading }">
    <div class="header d-flex align-items-center justify-content-between">
      <h3>Hierarchy Tree
        <small>
          for {{ data?.sheetData?.spreadsheet_name }}
        </small>
      </h3>

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
    <div ref="svgContainer" class="svg-container"></div>
  </div>
</template>
<style lang="scss">
.visualise-container {
  padding: 1rem;

  &.loading::after {
    content: '<i>Loading...</i>';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(255, 255, 255, 0.8);
    padding: 1rem 2rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 1.5rem;
    z-index: 10;
  }

  $curation_status: discussed, proposed, to_be_discussed, in_discussion, published, obsolete, external, pre_proposed;

  @each $status in $curation_status {
    .node.ose-curation-status-#{$status} {
      &>path {
        fill: var(--ose-curation-status-#{$status}) !important;
      }
    }

    .ose-curation-status-#{$status} {
      background: var(--ose-curation-status-#{$status}) !important;
    }
  }

  h3 {
    margin: 0 0 0.5rem 0;
    flex-shrink: 0;
  }

  .svg-container {
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

    .link {
      fill: none;
      stroke: #999;
      stroke-opacity: 0.6;
      stroke-width: 1.5px;
    }

    .node {
      cursor: pointer;

      &:hover {
        &>path {
          fill: #ffffff !important;
        }
      }
    }
  }
}
</style>
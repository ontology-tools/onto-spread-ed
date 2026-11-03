<script lang="ts" setup>
import {computed, ref} from "vue";
import {useRoute, useRouter} from "vue-router";
import {Project} from "@ontospreaded/js-core";

const props = defineProps<{ project: Project }>()

const route = useRoute();
const router = useRouter();

const NODE_WIDTH = 200;
const NODE_HEIGHT = 52;
const GAP_X = 72;
const GAP_Y = 18;
const PADDING = 12;
/** Space taken by an edge passing through a layer */
const WAYPOINT_HEIGHT = 6;
const WAYPOINT = "\u0000";

const layerX = (layer: number) => PADDING + layer * (NODE_WIDTH + GAP_X);

type GraphNode = {
  id: string
  target: string
  sources: number
  publish: boolean
  unknown: boolean
  layer: number
  order: number
  x: number
  y: number
}

type GraphEdge = {
  /** The file that is needed */
  from: string
  /** The file that needs it */
  to: string
  /** Part of a cycle, cannot be built */
  cyclic: boolean
  path: string
}

const graph = computed(() => {
  const files = {external: props.project.external, ...props.project.files};
  const needs = new Map<string, string[]>(Object.entries(files).map(([k, f]) => [k, [...new Set(f.needs)]]));
  // Only the files can be needed, not the external ontology
  const unknown = new Set([...needs.values()].flat().filter(n => !(n in props.project.files)));
  for (const u of unknown) if (!needs.has(u)) needs.set(u, []);

  // Break cycles: edges back to a file that is still being visited are cyclic and ignored for the layout
  const cyclic = new Set<string>();
  const state = new Map<string, "visiting" | "done">();
  const visit = (id: string) => {
    state.set(id, "visiting");
    for (const n of needs.get(id) ?? []) {
      if (state.get(n) === "visiting") cyclic.add(`${n}->${id}`);
      else if (!state.has(n)) visit(n);
    }
    state.set(id, "done");
  };
  for (const id of needs.keys()) if (!state.has(id)) visit(id);

  // Each file is placed one layer after the last file it needs, so files are built from left to right
  const layers = new Map<string, number>();
  const layerOf = (id: string): number => {
    let layer = layers.get(id);
    if (layer === undefined) {
      const acyclic = (needs.get(id) ?? []).filter(n => !cyclic.has(`${n}->${id}`));
      layer = acyclic.length === 0 ? 0 : 1 + Math.max(...acyclic.map(layerOf));
      layers.set(id, layer);
    }
    return layer;
  };

  // Edges spanning several layers pass through a waypoint in each layer in between, so they run between the files
  const waypointsOf = new Map<string, string[]>();
  const columns: string[][] = [];
  for (const id of needs.keys()) (columns[layerOf(id)] ??= []).push(id);
  const neighbours = new Map<string, string[]>();
  const connect = (a: string, b: string) => {
    neighbours.set(a, [...neighbours.get(a) ?? [], b]);
    neighbours.set(b, [...neighbours.get(b) ?? [], a]);
  };
  for (const [id, ns] of needs) {
    for (const n of ns) {
      if (cyclic.has(`${n}->${id}`)) continue;

      const waypoints: string[] = [];
      for (let layer = layerOf(n) + 1; layer < layerOf(id); layer++) {
        const waypoint = `${WAYPOINT}${n}->${id}@${layer}`;
        columns[layer].push(waypoint);
        waypoints.push(waypoint);
      }
      waypointsOf.set(`${n}->${id}`, waypoints);
      [n, ...waypoints, id].reduce((a, b) => (connect(a, b), b));
    }
  }
  for (const column of columns) column.sort();

  // Reduce crossings by ordering each column by the mean position of its neighbours, sweeping back and forth
  const position = new Map<string, number>();
  const updatePositions = () => columns.forEach(c => c.forEach((id, i) => position.set(id, i)));
  updatePositions();
  for (let sweep = 0; sweep < 8; sweep++) {
    const order = sweep % 2 === 0 ? columns : [...columns].reverse();
    for (const column of order) {
      const barycenter = (id: string) => {
        const ps = (neighbours.get(id) ?? []).map(n => position.get(n)!);
        return ps.length === 0 ? position.get(id)! : ps.reduce((a, b) => a + b, 0) / ps.length;
      };
      const keys = new Map(column.map(id => [id, barycenter(id)]));
      column.sort((a, b) => keys.get(a)! - keys.get(b)! || a.localeCompare(b));
      updatePositions();
    }
  }

  const heightOf = (id: string) => id.startsWith(WAYPOINT) ? WAYPOINT_HEIGHT : NODE_HEIGHT;
  const columnHeight = (column: string[]) =>
      column.reduce((sum, id) => sum + heightOf(id), 0) + Math.max(0, column.length - 1) * GAP_Y;
  const height = Math.max(NODE_HEIGHT, ...columns.map(columnHeight));

  const nodes = new Map<string, GraphNode>();
  /** Vertical centre of each node and waypoint */
  const centre = new Map<string, number>();
  columns.forEach((column, layer) => {
    let y = PADDING + (height - columnHeight(column)) / 2;
    column.forEach((id, order) => {
      centre.set(id, y + heightOf(id) / 2);
      if (!id.startsWith(WAYPOINT)) {
        const file = files[id as keyof typeof files];
        nodes.set(id, {
          id,
          target: file?.target.file ?? "",
          sources: file?.sources.length ?? 0,
          publish: file?.target.publish ?? true,
          unknown: !(id in files),
          layer,
          order,
          x: layerX(layer),
          y,
        });
      }
      y += heightOf(id) + GAP_Y;
    });
  });

  const edges: GraphEdge[] = [];
  for (const [id, ns] of needs) {
    for (const n of ns) {
      const key = `${n}->${id}`;
      const from = nodes.get(n)!, to = nodes.get(id)!;
      const x1 = from.x + NODE_WIDTH, y1 = centre.get(n)!;
      const x2 = to.x, y2 = centre.get(id)!;

      let path: string;
      if (cyclic.has(key)) {
        // Cyclic edges point backwards: from the left side of the needed file to the right side of the one needing it
        const [bx1, bx2] = [from.x, to.x + NODE_WIDTH];
        path = `M ${bx1} ${y1} C ${bx1 - GAP_X / 2} ${y1}, ${bx2 + GAP_X / 2} ${y2}, ${bx2} ${y2}`;
      } else {
        path = `M ${x1} ${y1}`;
        let [px, py] = [x1, y1];
        const segment = (x: number, y: number) => {
          path += ` C ${px + GAP_X / 2} ${py}, ${x - GAP_X / 2} ${y}, ${x} ${y}`;
          [px, py] = [x, y];
        };
        for (const waypoint of waypointsOf.get(key) ?? []) {
          const layer = Number(waypoint.slice(waypoint.lastIndexOf("@") + 1));
          const y = centre.get(waypoint)!;
          segment(layerX(layer), y);
          path += ` L ${layerX(layer) + NODE_WIDTH} ${y}`;
          px = layerX(layer) + NODE_WIDTH;
        }
        segment(x2, y2);
      }
      edges.push({from: n, to: id, cyclic: cyclic.has(key), path});
    }
  }

  return {
    nodes: [...nodes.values()],
    edges,
    width: 2 * PADDING + columns.length * NODE_WIDTH + Math.max(0, columns.length - 1) * GAP_X,
    height: 2 * PADDING + height,
    hasCycle: cyclic.size > 0,
    unknown: [...unknown],
  };
});

const hovered = ref<string | null>(null);

/** The hovered file with everything it (transitively) needs and everything that (transitively) needs it */
const highlighted = computed(() => {
  const h = hovered.value;
  if (h === null) return null;

  const follow = (direction: "from" | "to") => {
    const other = direction === "from" ? "to" : "from";
    const seen = new Set([h]);
    const todo = [h];
    while (todo.length > 0) {
      const id = todo.pop()!;
      for (const e of graph.value.edges) {
        if (e[other] === id && !seen.has(e[direction])) {
          seen.add(e[direction]);
          todo.push(e[direction]);
        }
      }
    }
    return seen;
  };
  return {needed: follow("from"), needing: follow("to")};
});

const isDimmed = (id: string) =>
    highlighted.value !== null && !highlighted.value.needed.has(id) && !highlighted.value.needing.has(id);
/** Only edges on a path through the hovered file stay highlighted */
const isEdgeDimmed = (e: GraphEdge) => {
  const h = highlighted.value;
  return h !== null && !(h.needed.has(e.from) && h.needed.has(e.to)) && !(h.needing.has(e.from) && h.needing.has(e.to));
};

function truncate(text: string, length: number) {
  return text.length > length ? "…" + text.slice(text.length - length + 1) : text;
}

function open(node: GraphNode) {
  if (node.unknown) return;
  router.push({name: "project-settings", params: {repo: route.params.repo, tab: "files"}, query: {file: node.id}});
}
</script>

<template>
  <p class="text-body-secondary">
    The files of the project and the files they need. Files are built from left to right; an arrow points from a file
    to the files that need it. Hover a file to highlight what it depends on and what depends on it, click it to edit
    it.
  </p>

  <div v-if="graph.hasCycle" class="alert alert-danger py-2">
    The dependencies contain a cycle (red arrows). The project cannot be built until it is removed.
  </div>
  <div v-if="graph.unknown.length > 0" class="alert alert-warning py-2">
    Some files need files that are not part of the project or cannot be needed: {{ graph.unknown.join(", ") }}.
  </div>

  <div class="graph-container">
    <svg :height="graph.height" :viewBox="`0 0 ${graph.width} ${graph.height}`" :width="graph.width" class="graph"
         role="img" aria-label="Dependency graph of the project files">
      <defs>
        <marker id="dependency-arrow" markerHeight="8" markerWidth="8" orient="auto-start-reverse" refX="9" refY="5"
                viewBox="0 0 10 10">
          <path class="arrow" d="M 0 0 L 10 5 L 0 10 z"/>
        </marker>
        <marker id="dependency-arrow-cyclic" markerHeight="8" markerWidth="8" orient="auto-start-reverse" refX="9"
                refY="5" viewBox="0 0 10 10">
          <path class="arrow cyclic" d="M 0 0 L 10 5 L 0 10 z"/>
        </marker>
      </defs>

      <path v-for="e in graph.edges" :key="`${e.from}->${e.to}`" :class="{cyclic: e.cyclic, dimmed: isEdgeDimmed(e)}"
            :d="e.path" :marker-end="`url(#${e.cyclic ? 'dependency-arrow-cyclic' : 'dependency-arrow'})`" class="edge"/>

      <g v-for="n in graph.nodes" :key="n.id" :class="{unknown: n.unknown, unpublished: !n.publish, dimmed: isDimmed(n.id),
                                                       external: n.id === 'external'}"
         :transform="`translate(${n.x}, ${n.y})`" class="node" @click="open(n)" @mouseenter="hovered = n.id"
         @mouseleave="hovered = null">
        <title>{{ n.unknown ? `${n.id} is not a file of the project` : `${n.id}: ${n.target || "no target file"}` }}</title>
        <rect :height="NODE_HEIGHT" :width="NODE_WIDTH" rx="6"/>
        <text class="name" x="10" y="21">{{ truncate(n.id, 24) }}</text>
        <text class="details" x="10" y="40">
          <template v-if="n.unknown">unknown file</template>
          <template v-else>{{ truncate(n.target || "no target file", 22) }} · {{ n.sources }} src</template>
        </text>
      </g>
    </svg>
  </div>

  <div class="legend small text-body-secondary mt-2">
    <span><span class="swatch"></span> File</span>
    <span><span class="swatch unpublished"></span> Not published</span>
    <span><span class="swatch unknown"></span> Unknown file</span>
  </div>
</template>

<style lang="scss" scoped>
.graph-container {
  overflow-x: auto;
  border: 1px solid var(--bs-border-color);
  border-radius: var(--bs-border-radius);
  background: var(--bs-tertiary-bg);
}

.graph {
  display: block;
  margin: 0 auto;
}

.edge {
  fill: none;
  stroke: var(--bs-secondary-color);
  stroke-width: 1.5;
  transition: opacity .15s;

  &.cyclic {
    stroke: var(--bs-danger);
    stroke-dasharray: 5 3;
  }
}

.arrow {
  fill: var(--bs-secondary-color);

  &.cyclic {
    fill: var(--bs-danger);
  }
}

.node {
  cursor: pointer;
  transition: opacity .15s;

  rect {
    fill: var(--bs-body-bg);
    stroke: var(--bs-primary);
    stroke-width: 1.5;
  }

  &.external rect {
    fill: var(--bs-primary-bg-subtle);
  }

  &.unpublished rect {
    stroke-dasharray: 4 3;
  }

  &.unknown {
    cursor: default;

    rect {
      stroke: var(--bs-danger);
      stroke-dasharray: 4 3;
    }
  }

  &:hover rect {
    stroke-width: 2.5;
  }

  .name {
    font-weight: 600;
    font-size: 14px;
    fill: var(--bs-body-color);
  }

  .details {
    font-size: 12px;
    fill: var(--bs-secondary-color);
  }
}

.dimmed {
  opacity: .25;
}

.legend {
  display: flex;
  gap: 1.5rem;

  .swatch {
    display: inline-block;
    width: 1.2em;
    height: .8em;
    vertical-align: middle;
    border: 1.5px solid var(--bs-primary);
    border-radius: 2px;

    &.unpublished {
      border-style: dashed;
    }

    &.unknown {
      border-style: dashed;
      border-color: var(--bs-danger);
    }
  }
}
</style>

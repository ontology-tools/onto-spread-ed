<script setup lang="ts">
import {computed, nextTick, onBeforeUnmount, ref, watch} from "vue";
import {useRoute, useRouter} from "vue-router";
import type {TabulatorFull as Tabulator} from "tabulator-tables";
import {cachedTree, fetchTree, type RepoTree, api, useMe} from "../api";
import {layout} from "../state";

type SearchHit = { class_id: string, definition: string, label: string, parent: string, repo: string, spreadsheet: string }

const route = useRoute();
const router = useRouter();
const {me} = useMe();

const repo = computed(() => route.params.repo as string);
const folder = computed(() => [route.params.path].flat().filter(Boolean).join("/"));
const branch = computed(() => (route.query.branch as string | undefined) ?? undefined);
const branchQuery = computed(() => branch.value ? {branch: branch.value} : {});

const tree = ref<RepoTree | null>(null);
const error = ref<string | null>(null);
const expanded = ref(new Set<string>());

// The breadcrumb only depends on the route, so it is shown immediately
function setBreadcrumb() {
  const segments = [repo.value, ...folder.value.split("/").filter(Boolean)];
  layout.breadcrumb = segments.map((name, i) => ({
    name,
    to: i < segments.length - 1 ? `/repo/${segments.slice(0, i + 1).join("/")}` : undefined
  }));
}

// Pre-expand the folder from the URL and its ancestors
function expandFolder() {
  const parts = folder.value.split("/").filter(Boolean);
  for (let i = 1; i <= parts.length; i++) expanded.value.add(parts.slice(0, i).join("/"));
}

watch([repo, folder], ([r], [oldRepo]) => {
  if (route.name !== "repo") return;
  if (oldRepo !== undefined && r !== oldRepo) expanded.value = new Set();
  setBreadcrumb();
  expandFolder();
}, {immediate: true});

function applyTree(t: RepoTree) {
  tree.value = t;
  layout.branches = t.branches;
  layout.activeBranch = t.active_branch;
  layout.mainBranch = t.main_branch;
}

watch([repo, branch], async () => {
  if (route.name !== "repo") return;
  error.value = null;
  const [r, b] = [repo.value, branch.value];
  const hit = cachedTree(r, b);
  if (hit) return applyTree(hit);
  tree.value = null;
  layout.branches = [];
  layout.activeBranch = b ?? null;
  try {
    const t = await fetchTree(r, b);
    if (r === repo.value && b === branch.value && route.name === "repo") applyTree(t);
  } catch (e: any) {
    if (r === repo.value && b === branch.value && route.name === "repo") error.value = e.message;
  }
}, {immediate: true});

type Row = { path: string; name: string; type: "dir" | "file"; depth: number }
// Flat list of the visible rows: children of expanded folders, directories first
const rows = computed<Row[]>(() => {
  if (!tree.value) return [];
  const children = new Map<string, Row[]>();
  for (const e of tree.value.entries) {
    const i = e.path.lastIndexOf("/");
    const parent = e.path.slice(0, Math.max(i, 0));
    const list = children.get(parent) ?? [];
    list.push({path: e.path, name: e.path.slice(i + 1), type: e.type, depth: 0});
    children.set(parent, list);
  }
  const out: Row[] = [];
  const walk = (parent: string, depth: number) => {
    const list = (children.get(parent) ?? []).sort((a, b) =>
        a.type === b.type ? a.name.localeCompare(b.name) : a.type === "dir" ? -1 : 1);
    for (const r of list) {
      out.push({...r, depth});
      if (r.type === "dir" && expanded.value.has(r.path)) walk(r.path, depth + 1);
    }
  };
  walk("", 0);
  return out;
});

function toggle(path: string) {
  if (!expanded.value.delete(path)) expanded.value.add(path);
}

// Search
const query = ref("");
const searched = ref(false);
const noResults = ref(false);
const searching = ref(false);
let searchType: "search" | "initials" = "search";
const tableEl = ref<HTMLElement | null>(null);
let table: Tabulator | null = null;

function clearResults() {
  table?.destroy();
  table = null;
  searched.value = false;
  noResults.value = false;
}

watch([repo, branch], clearResults);
onBeforeUnmount(clearResults);

async function createTable(el: HTMLElement, data: SearchHit[]) {
  // loaded on first use to keep tabulator out of the entry chunk
  const [{TabulatorFull}] = await Promise.all([
    import("tabulator-tables"),
    // @ts-expect-error CSS modules have no type declarations
    import("tabulator-tables/dist/css/tabulator.min.css"),
    // @ts-expect-error CSS modules have no type declarations
    import("tabulator-tables/dist/css/tabulator_bootstrap5.min.css"),
  ]);
  if (!el.isConnected) return; // cleared / navigated away while loading
  const textarea = {formatter: "textarea" as const};
  table = new TabulatorFull(el, {
    data,
    columns: [
      {title: "Class ID", field: "class_id", width: 120, ...textarea},
      {title: "Definition", field: "definition", ...textarea},
      {title: "Label", field: "label", ...textarea},
      {title: "Parent", field: "parent", ...textarea},
      {title: "Repo", field: "repo", width: 80, ...textarea},
      {title: "Spreadsheet", field: "spreadsheet", width: 360, ...textarea},
    ],
    layout: "fitColumns",
    pagination: true,
    paginationSize: 5,
    paginationSizeSelector: [5, 10, 25, 50, 100, true],
    paginationCounter: "rows",
  });
  table.on("rowClick", (_, row) => openSheet(row.getData() as SearchHit));
}

function openSheet(hit: SearchHit) {
  const goToRow = searchType === "initials" ? me.value?.initials ?? "" : hit.label ?? "";
  router.push({
    name: "edit",
    params: {repo: hit.repo, path: hit.spreadsheet.split("/")},
    query: {
      filter: JSON.stringify({Label: goToRow}),
      ...branchQuery.value
    }
  });
}

async function search(type: "search" | "initials") {
  searchType = type;
  searching.value = true;
  const [r, b] = [repo.value, branch.value];
  try {
    const body = type === "search" ? {query: query.value} : {initials: me.value?.initials ?? ""};
    const hits = await api<SearchHit[]>(`/api/search/${r}/sheets`, {method: "POST", body: JSON.stringify(body)});
    if (r !== repo.value || b !== branch.value) return; // repo changed meanwhile
    table?.destroy();
    table = null;
    noResults.value = hits.length === 0;
    searched.value = true;
    await nextTick(); // the results area is rendered only now
    if (tableEl.value && hits.length) await createTable(tableEl.value, hits);
  } catch (e) {
    bootbox.alert("Something went wrong");
    console.error(e);
  } finally {
    searching.value = false;
  }
}
</script>

<template>
  <div v-if="error" class="alert alert-danger">{{ error }}</div>
  <template v-else>
    <h2 class="mt-3">{{ repo }}</h2>

    <label class="font-weight-bold form-label" for="inputText">Search across all spreadsheets:</label>
    <form class="d-flex" @submit.prevent="search('search')">
      <input id="inputText" v-model="query" placeholder="search terms" class="form-control me-2 d-inline-block w-auto"/>
      <button type="submit" class="btn btn-outline-success me-2" :disabled="searching">
        <i class="fas fa-search"></i> Search
      </button>
      <button type="button" class="btn btn-outline-warning" :disabled="searching" @click="search('initials')">
        <i class="fas fa-search-plus"></i> Show all assigned to me
      </button>
    </form>

    <div v-if="searched" class="mt-2">
      <button type="button" class="btn btn-sm btn-outline-secondary" @click="clearResults">
        <i class="fas fa-times"></i> Clear results
      </button>
      <p v-if="noResults" class="mt-2">No results</p>
      <div v-else ref="tableEl" class="mt-2" style="font-size: 0.8em; width: 100%;"></div>
    </div>

    <div v-if="!tree" class="spinner-border spinner-border-sm mt-3" role="status"></div>
    <template v-else>
      <p v-if="tree.truncated" class="alert alert-warning mt-3">
        The repository is too large; the file tree is incomplete.
      </p>
      <ul class="list-unstyled mt-3">
        <li class="p-1">
          <i class="fa-solid fa-folder-open me-2" style="color: orange"></i><strong>{{ repo }}</strong>
        </li>
        <li v-for="row in rows" :key="row.path" :style="{marginLeft: `${(row.depth + 1) * 20}px`}" class="p-1">
          <a v-if="row.type === 'dir'" href="#" class="text-reset text-decoration-none"
             @click.prevent="toggle(row.path)">
            <i class="fa-solid me-2" :class="expanded.has(row.path) ? 'fa-folder-open' : 'fa-folder'"
               style="color: orange"></i>{{ row.name }}
          </a>
          <RouterLink v-else :to="{name: 'edit', params: {repo, path: row.path.split('/')}, query: branchQuery}"
                      class="text-reset text-decoration-none">
            <i class="fa-regular fa-file-excel me-2" style="color: green"></i>{{ row.name }}
          </RouterLink>
        </li>
      </ul>
    </template>
  </template>
</template>

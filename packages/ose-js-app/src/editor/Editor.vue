<script lang="ts" setup>
import {computed, ref, watch} from "vue";
import {useRoute} from "vue-router";
import {Project} from "@ontospreaded/js-core";
import {fetchConfig} from "../api";
import {layout} from "../state";
import EditorSheet from "./EditorSheet.vue";
import TableSkeleton from "../common/TableSkeleton.vue";

type RepoConfig = {
  repo_name: string
  repository_config: Project
  branches: string[]
  initials: string
  all_initials: (string | null)[]
}

const route = useRoute();
const repo = computed(() => route.params.repo as string);
const filePath = computed(() => [route.params.path].flat().join("/"));

// Ribbon groups shown while loading
const ribbonSkeleton = [
  {full: [3], small: [3.5, 3.5, 5], title: 2.5},
  {full: [4, 3.5], small: [], title: 2.5},
  {full: [], small: [6.5, 8.5, 8], title: 3},
  {full: [4], small: [], title: 4.5},
];

const config = ref<RepoConfig | null>(null);
const error = ref<string | null>(null);

function setLayout(c?: RepoConfig) {
  const segments = [repo.value, ...filePath.value.split("/")];
  layout.breadcrumb = segments.map((name, i) => ({
    name,
    to: i < segments.length - 1 ? `/repo/${segments.slice(0, i + 1).join("/")}` : undefined
  }));
  layout.branches = c?.branches ?? [];
  layout.activeBranch = (route.query.branch as string | undefined) ?? c?.repository_config.main_branch ?? null;
  layout.mainBranch = c?.repository_config.main_branch ?? null;
}

watch(() => route.fullPath, async () => {
  if (route.name !== "edit") return;
  const r = repo.value;
  error.value = null;
  if (config.value?.repo_name !== r) config.value = null;
  setLayout(config.value ?? undefined);
  if (config.value) return;
  try {
    const c = await fetchConfig<RepoConfig>(r);
    if (r !== repo.value || route.name !== "edit") return; // stale response
    config.value = c;
    setLayout(c);
  } catch (e: any) {
    if (r === repo.value && route.name === "edit") error.value = e.message;
  }
}, {immediate: true});
</script>

<template>
  <div v-if="error" class="alert alert-danger">{{ error }}</div>
  <!-- keyed on the full route so that navigating to another sheet, branch or filter reloads the editor -->
  <EditorSheet v-else-if="config" :key="route.fullPath" :config="config" :file-path="filePath" :repo="repo"/>
  <!-- Mirrors the editor layout (reusing EditorSheet's ribbon styles): ribbon on top, the sheet below -->
  <div v-else class="editor-container" role="status">
    <span class="visually-hidden">Loading the editor…</span>
    <div aria-hidden="true" class="row mb-3">
      <div class="col-md-12">
        <div class="card p-0">
          <div class="card-body ribbon p-0 m-0 placeholder-wave" style="pointer-events: none">
            <template v-for="(group, g) in ribbonSkeleton" :key="g">
              <div v-if="group.full.length" class="ribbon-full">
                <div v-for="(w, i) in group.full" :key="i" class="btn-ribbon">
                  <span class="placeholder" style="width: 1.5rem; height: 1.5rem"></span><br>
                  <span :style="{width: `${w}rem`}" class="placeholder"></span>
                </div>
              </div>
              <!-- As in the real ribbon, the group title follows the group's first block -->
              <span v-if="group.full.length" :style="{gridColumn: `span ${group.small.length ? 2 : 1}`}"
                    class="ribbon-title">
                <span :style="{width: `${group.title}rem`}" class="placeholder"></span>
              </span>
              <div v-if="group.small.length" class="ribbon-small">
                <div v-for="(w, i) in group.small" :key="i" class="btn-ribbon" style="height: 1.6rem">
                  <span class="placeholder" style="width: 1em; height: 1em"></span>
                  <span :style="{width: `${w}rem`}" class="placeholder" style="height: 1em"></span>
                </div>
              </div>
              <span v-if="!group.full.length" class="ribbon-title">
                <span :style="{width: `${group.title}rem`}" class="placeholder"></span>
              </span>
              <div class="ribbon-splitter"></div>
            </template>
            <div class="ribbon-filler"></div>
          </div>
        </div>
      </div>
    </div>
    <TableSkeleton class="flex-fill"/>
  </div>
</template>

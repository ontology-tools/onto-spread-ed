<script lang="ts" setup>
import {computed, ref, watch} from "vue";
import {useRoute} from "vue-router";
import {Project} from "@ontospreaded/js-core";
import {cachedConfig, fetchConfig} from "../api";
import {layout} from "../state";
import EditorSheet from "./EditorSheet.vue";

type RepoConfig = {
  repo_name: string
  repository_config: Project
  main_branch: string
  branches: string[]
  initials: string
  all_initials: (string | null)[]
}

const route = useRoute();
const repo = computed(() => route.params.repo as string);
const filePath = computed(() => [route.params.path].flat().join("/"));

const config = ref<RepoConfig | null>(cachedConfig<RepoConfig>(repo.value) ?? null);
const error = ref<string | null>(null);

function setLayout(c?: RepoConfig) {
  const segments = [repo.value, ...filePath.value.split("/")];
  layout.breadcrumb = segments.map((name, i) => ({
    name,
    to: i < segments.length - 1 ? `/repo/${segments.slice(0, i + 1).join("/")}` : undefined
  }));
  layout.branches = c?.branches ?? [];
  layout.activeBranch = (route.query.branch as string | undefined) ?? c?.main_branch ?? null;
  layout.mainBranch = c?.main_branch ?? null;
}

watch(() => route.fullPath, async () => {
  if (route.name !== "edit") return;
  const r = repo.value;
  error.value = null;
  if (config.value?.repo_name !== r) config.value = cachedConfig<RepoConfig>(r) ?? null;
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
  <div v-else class="spinner-border spinner-border-sm mt-3" role="status"></div>
</template>

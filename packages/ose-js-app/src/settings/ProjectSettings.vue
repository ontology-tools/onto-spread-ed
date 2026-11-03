<script lang="ts" setup>
import {computed, onBeforeUnmount, onMounted, ref, watch} from "vue";
import {onBeforeRouteLeave, onBeforeRouteUpdate, useRoute} from "vue-router";
import {Project} from "@ontospreaded/js-core";
import {api, clearCache, useMe} from "../api";
import {layout} from "../state";
import {confirmDialog} from "../common/bootbox";
import GeneralTab from "./project/GeneralTab.vue";
import FilesTab from "./project/FilesTab.vue";
import DependencyGraphTab from "./project/DependencyGraphTab.vue";
import BuildsTab from "./project/BuildsTab.vue";
import SubontologiesTab from "./project/SubontologiesTab.vue";
import WorkflowsTab from "./project/WorkflowsTab.vue";
import AdvancedTab from "./project/AdvancedTab.vue";

const TABS = [
  {id: "general", name: "General", icon: "fa-sliders"},
  {id: "files", name: "Files", icon: "fa-file"},
  {id: "dependencies", name: "Dependency graph", icon: "fa-diagram-project"},
  {id: "builds", name: "Build configurations", icon: "fa-gears"},
  {id: "subontologies", name: "Subontologies", icon: "fa-sitemap"},
  {id: "workflows", name: "Workflows", icon: "fa-play-circle", permission: "admin"},
  {id: "advanced", name: "Advanced", icon: "fa-code"},
] as const;

const route = useRoute();
const {me} = useMe();

const can = (p: string) => !!me.value?.permissions?.some(x => x === p || x === "admin");
const canEdit = computed(() => can("repository-config-edit"));

const tabs = computed(() => TABS.filter(t => !("permission" in t) || can(t.permission)));
const tab = computed(() => tabs.value.find(t => t.id === route.params.tab)?.id ?? "general");

const repo = computed(() => route.params.repo as string);
const project = ref<Project | null>(null);
const availableStages = ref<string[]>([]);
const saved = ref<string | null>(null);
const revision = ref("");
const loadError = ref<string | null>(null);
const saving = ref<"idle" | "saving" | "error" | "success">("idle");
const saveError = ref<string | null>(null);

const dirty = computed(() => project.value !== null && JSON.stringify(project.value) !== saved.value);

async function load(name: string) {
  project.value = null;
  saved.value = null;
  revision.value = "";
  loadError.value = null;
  saving.value = "idle";
  saveError.value = null;
  layout.breadcrumb = [{name: "Admin", to: "/admin"}, {name: "Settings", to: "/admin/settings"}, {name}];
  try {
    const resp = await api<{ project: Project, revision: string, available_stages: string[] }>(
        `/api/settings/repositories/${encodeURIComponent(name)}/project`);
    if (name !== repo.value) return; // navigated elsewhere meanwhile

    setProject(resp.project);
    revision.value = resp.revision;
    availableStages.value = resp.available_stages;
  } catch (e: any) {
    if (name === repo.value) loadError.value = e.message;
  }
}

function setProject(p: Project) {
  saved.value = JSON.stringify(p);
  project.value = JSON.parse(saved.value);
}

let resetSaveState: ReturnType<typeof setTimeout> | null = null;

async function save() {
  if (!project.value) return;
  const name = repo.value;

  if (resetSaveState !== null) clearTimeout(resetSaveState);
  saving.value = "saving";
  saveError.value = null;
  try {
    const resp = await api<{ project: Project, revision: string }>(`/api/settings/repositories/${encodeURIComponent(name)}/project`, {
      method: "PUT",
      headers: {"If-Match": `"${revision.value}"`},
      body: JSON.stringify(project.value),
    });
    clearCache();
    if (name !== repo.value) return;
    setProject(resp.project);
    revision.value = resp.revision;
    saving.value = "success";
  } catch (e: any) {
    if (name !== repo.value) return;
    saveError.value = e.message;
    saving.value = "error";
  }
  resetSaveState = setTimeout(() => {
    if (saving.value !== "saving") saving.value = "idle";
    resetSaveState = null;
  }, 3000);
}

function discard() {
  if (saved.value !== null) project.value = JSON.parse(saved.value);
  saveError.value = null;
}

function replace(p: Project) {
  project.value = p;
}

async function confirmLeave(): Promise<boolean> {
  return !dirty.value || await confirmDialog({
    title: "Unsaved changes",
    message: `The configuration of ${repo.value} has unsaved changes. Do you want to discard them?`,
    buttons: {
      confirm: {label: "Discard changes", className: "btn-danger"},
      cancel: {label: "Keep editing", className: "btn-primary"},
    },
  });
}

onBeforeRouteLeave(() => confirmLeave());
onBeforeRouteUpdate((to, from) => to.params.repo === from.params.repo || confirmLeave());

function onBeforeUnload(event: BeforeUnloadEvent) {
  if (dirty.value) event.preventDefault();
}

watch(repo, r => load(r));
onMounted(() => {
  window.addEventListener("beforeunload", onBeforeUnload);
  load(repo.value);
});
onBeforeUnmount(() => {
  window.removeEventListener("beforeunload", onBeforeUnload);
  if (resetSaveState !== null) clearTimeout(resetSaveState);
});
</script>

<template>
  <div class="project-settings">
    <div class="d-flex align-items-center gap-2 mb-3">
      <h1 class="flex-grow-1 mb-0">
        {{ project?.full_name ?? repo }}
        <small v-if="project" class="text-body-secondary fs-5">{{ project.full_repository_name }}</small>
      </h1>
      <template v-if="project && canEdit">
        <span v-if="dirty" class="text-body-secondary small">Unsaved changes</span>
        <button :disabled="!dirty || saving === 'saving'" class="btn btn-sm btn-outline-secondary" type="button"
                @click="discard">
          <i class="fa fa-rotate-left"></i> Discard
        </button>
        <button :class="{'btn-primary': saving === 'idle' || saving === 'saving', 'btn-success': saving === 'success',
                         'btn-danger': saving === 'error'}"
                :disabled="!dirty || saving === 'saving'" class="btn btn-sm" type="button" @click="save">
          <i :class="{'fa-save': saving === 'idle', 'fa-spin fa-spinner': saving === 'saving',
                      'fa-check': saving === 'success', 'fa-xmark': saving === 'error'}" class="fa"></i>
          Save
        </button>
      </template>
    </div>

    <div v-if="loadError" class="alert alert-danger">
      Loading the configuration of {{ repo }} failed: {{ loadError }}
      <RouterLink class="alert-link ms-2" to="/admin/settings">Back to the settings</RouterLink>
    </div>
    <div v-else-if="!project" class="text-center py-5">
      <i class="fa fa-spin fa-spinner fa-2x"></i>
    </div>

    <template v-else>
      <div v-if="saveError" class="alert alert-danger">Saving failed: {{ saveError }}</div>
      <div v-if="!canEdit" class="alert alert-info">
        You can view this configuration but you lack the permission to change it.
      </div>

      <ul class="nav nav-tabs mb-3">
        <li v-for="t in tabs" :key="t.id" class="nav-item">
          <RouterLink :class="{active: t.id === tab}" :to="{name: 'project-settings', params: {repo, tab: t.id}}" class="nav-link">
            <i :class="t.icon" class="fa"></i> {{ t.name }}
          </RouterLink>
        </li>
      </ul>

      <WorkflowsTab v-if="tab === 'workflows'" :project="project"/>
      <DependencyGraphTab v-else-if="tab === 'dependencies'" :project="project"/>
      <fieldset v-else :disabled="!canEdit || saving === 'saving'">
        <GeneralTab v-if="tab === 'general'" :project="project"/>
        <FilesTab v-else-if="tab === 'files'" :project="project"/>
        <BuildsTab v-else-if="tab === 'builds'" :available-stages="availableStages" :project="project"/>
        <SubontologiesTab v-else-if="tab === 'subontologies'" :project="project"/>
        <AdvancedTab v-else-if="tab === 'advanced'" :project="project" @replace="replace"/>
      </fieldset>
    </template>
  </div>
</template>

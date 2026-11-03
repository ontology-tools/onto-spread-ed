<script lang="ts" setup>
import {computed, onMounted, Ref, ref, watch} from "vue";
import {BuildConfiguration, Project, Release} from "@ontospreaded/js-core"
import {api, useMe} from "../api";

const props = defineProps<{ repo?: string }>()

defineEmits<{
  (e: 'settingsConfirmed', buildConfiguration: BuildConfiguration): void
}>()

const {me} = useMe();
const canViewSettings = computed(() => !!me.value?.permissions?.some(p => p === "repository-config-view" || p === "admin"));

const project: Ref<Project | null> = ref(null);
const buildConfiguration: Ref<BuildConfiguration | null> = ref(null);
/** Releases of the repository, the latest first */
const lastReleases = ref<Release[] | null>(null)
const error = ref<string | null>(null)

const loading = computed(() => lastReleases.value === null && error.value === null)
const lastSuccessfulRelease = computed(() => lastReleases.value?.find(x => x.state === "completed") ?? null)
const lastRelease = computed(() => lastReleases.value?.[0] ?? null)

watch(() => props.repo, () => update())

async function update() {
  project.value = null
  buildConfiguration.value = null
  lastReleases.value = null
  error.value = null
  if (!props.repo) return

  const repo = props.repo
  try {
    const [p, releases] = await Promise.all([
      api<Project>(`/api/release/${repo}/release_script`),
      api<Release[]>(`/api/release/${repo}`),
    ])
    if (repo !== props.repo) return

    project.value = p
    buildConfiguration.value = p.build_configurations[0] ?? null
    lastReleases.value = releases.sort((a, b) => new Date(b.start).getTime() - new Date(a.start).getTime())
  } catch (e: any) {
    if (repo === props.repo) error.value = e.message
  }
}

onMounted(() => update())
</script>

<template>

  <div class="preparation">

    <h3>Release setup</h3>
    <div v-if="error" class="alert alert-danger">Loading the release setup of {{ repo }} failed: {{ error }}</div>
    <p v-else>
      Currently, there is no release running for {{ repo }}.
      <template v-if="loading">
        <span class="placeholder" style="width: 400px"></span>
      </template>
      <template v-else-if="lastSuccessfulRelease">
        {{ lastSuccessfulRelease.started_by }} started the last successful release on
        {{ $filters.formatDate(lastSuccessfulRelease.start) }}
      </template>
      <template v-else-if="lastRelease">
        {{ lastRelease.started_by }} started the last release on {{ $filters.formatDate(lastRelease.start) }}. But it
        did not complete.
      </template>
      <template v-else>
        There have been no releases in the near past.
      </template>
    </p>

    <p v-if="project && project.build_configurations.length === 0" class="alert alert-warning">
      The project has no build configuration. Add one in the project settings to start a release.
    </p>

    <div class="d-flex gap-2">
      <button :disabled="!buildConfiguration" class="btn btn-success flex-grow-1"
              @click="$emit('settingsConfirmed', buildConfiguration!)">
        <i class="fa fa-play"></i>
        Start a release
      </button>
      <select v-if="(project?.build_configurations.length ?? 0) > 1" v-model="buildConfiguration"
              class="form-select flex-grow-0 w-auto" title="Build configuration">
        <option v-for="bc in project?.build_configurations" :value="bc">{{ bc.name }}</option>
      </select>
      <RouterLink v-if="canViewSettings && repo"
                  :to="{name: 'project-settings', params: {repo, tab: 'builds'}}"
                  class="btn btn-outline-secondary" title="Edit the build configurations in the project settings">
        <i class="fa fa-gear"></i> Configure
      </RouterLink>
    </div>
    <p v-if="buildConfiguration?.description" class="text-body-secondary mt-2 mb-0">
      {{ buildConfiguration.description }}
    </p>

    <ul class="list-group mt-2">
      <li v-for="release in lastReleases" class="list-group-item ">
        <RouterLink class="d-flex justify-content-between align-items-start" style="text-decoration: none; color: inherit" :to="`/admin/release/${release.id}`">
          <div class="ms-2 me-auto">
            <div class="fw-bold">{{ $filters.formatDate(release.start) }}</div>
            {{ release.started_by }}
          </div>
          <span class="badge rounded-pill" :class="{
            'text-bg-primary': ['starting', 'running', 'paused'].indexOf(release.state) >=0,
            'text-bg-success': release.state === 'completed',
            'text-bg-danger': release.state === 'errored',
            'text-bg-secondary': release.state === 'cancelled',
          }">{{ release.state }}</span>
        </RouterLink>
      </li>
    </ul>
  </div>
</template>

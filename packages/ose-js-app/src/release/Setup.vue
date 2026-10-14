<script lang="ts" setup>
import {computed, onBeforeUnmount, onMounted, Ref, ref, watch} from "vue";
import {BuildConfiguration, Project, Release} from "@ontospreaded/js-core"
import ProjectViewer from "./ProjectViewer.vue";

const showAdvanced = ref<boolean>()
const project: Ref<Project | null> = ref(null);
const buildConfiguration: Ref<BuildConfiguration | null> = ref(null);
import { prefix as prefix_url } from "../config";

const saving = ref<"idle" | "saving" | "error" | "success">("idle")

const props = defineProps<{ repo?: string }>()

const lastReleases = ref<Release[] | null>(null)

const loading = computed(() => lastReleases.value === null)
const lastSuccessfulRelease = computed(() => lastReleases.value?.find(x => x.state === "completed") ?? null)
const lastRelease = computed(() => lastReleases.value?.[0] ?? null)

defineEmits<{
  (e: 'settingsConfirmed', buildConfiguration: BuildConfiguration): void
}>()

watch(props, (value, oldValue) => value.repo !== oldValue.repo && update())

async function update() {
  if (props.repo) {
    project.value = null
    project.value = await (await fetch(`${prefix_url}/api/release/${props.repo}/release_script`)).json()
    buildConfiguration.value = project.value?.build_configurations[0] ?? null

    const releases: Release[] = await (await fetch(`${prefix_url}/api/release/${props.repo}`)).json()
    releases.sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime())
    lastReleases.value = releases
  }
}

let _saveFileAnimationTimeout: ReturnType<typeof setTimeout> | null = null;

async function saveFile($event: MouseEvent) {
  $event.preventDefault()

  if (_saveFileAnimationTimeout !== null) {
    clearTimeout(_saveFileAnimationTimeout)
  }

  saving.value = "saving"

  try {
    const response = await fetch(`${prefix_url}/api/release/${props.repo}/release_script`, {
      method: "PUT",
      headers: {
        'Content-Type': "application/json"
      },
      body: JSON.stringify(project.value)
    })

    if (response.ok) {
      saving.value = "success";
    } else {
      saving.value = "error"
    }
  } catch (e) {
    saving.value = "error"
  }

  _saveFileAnimationTimeout = setTimeout(() => {
    saving.value = "idle";
    _saveFileAnimationTimeout = null
  }, 5000)
}

onMounted(() => update())
onBeforeUnmount(() => {
  if (_saveFileAnimationTimeout !== null) clearTimeout(_saveFileAnimationTimeout)
})

</script>

<template>

  <div class="preparation">

    <h3>Release setup</h3>
    <p>
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

    <div class="btn-group  w-100">

      <button :disabled="!buildConfiguration" class="btn btn-success"
              @click="$emit('settingsConfirmed', buildConfiguration!)">
        <i class="fa fa-play"></i>
        Start a release
      </button>
      <select v-if="(project?.build_configurations.length ?? 0) > 1" v-model="buildConfiguration"
              class="form-select flex-grow-0 w-auto" title="Build configuration">
        <option v-for="bc in project?.build_configurations" :value="bc">{{ bc.name }}</option>
      </select>
      <button :disabled="!buildConfiguration" class="btn btn-success dropdown-toggle dropdown-toggle-split flex-grow-0"
              data-bs-toggle="dropdown"
              type="button">
      </button>

      <ul class="dropdown-menu">
        <li><a class="dropdown-item" href="#" @click.prevent="showAdvanced = !showAdvanced">
          <i :class="[showAdvanced ? 'fa-check-square' : 'fa-square']" class="fa-regular"></i> Show advanced
          configuration
        </a></li>
      </ul>
    </div>
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


    <ProjectViewer v-if="!!project && !!buildConfiguration && showAdvanced" :project="project"
                   :build-configuration="buildConfiguration" class="mt-2">
      <template v-slot:buttons>
        <button :class="({
                  'btn-primary': saving === 'idle' || saving === 'saving',
                  'btn-success': saving === 'success',
                  'btn-danger': saving === 'error'
                })"
                class="mb-3 btn btn-sm btn-primary"
                @click="saveFile">
          <i v-if="saving === 'idle'" class="fa fa-save"></i>
          <i v-if="saving === 'saving'" class="fa fa-spin fa-spinner"></i>
          <i v-if="saving === 'success'" class="fa fa-check"></i>
          <i v-if="saving === 'error'" class="fa fa-xmark"></i>
          Save project
        </button>
      </template>
    </ProjectViewer>
  </div>
</template>

<style scoped>

</style>

<script lang="ts" setup>
import {computed, onMounted, Ref, ref, watch} from "vue";
import {Release, ReleaseScript} from "@ose/js-core"
import ReleaseScriptViewer from "./ReleaseScriptViewer.vue";

const showAdvanced = ref<boolean>()
const releaseScript: Ref<ReleaseScript | null> = ref(null);
declare var URLS: { [key: string]: any }
const prefix_url = URLS.prefix

const saving = ref<"idle" | "saving" | "error" | "success">("idle")

const props = defineProps<{ repo?: string }>()

const lastReleases = ref<Release[] | null>(null)

const loading = computed(() => lastReleases.value === null)
const lastSuccessfulRelease = computed(() => lastReleases.value?.find(x => x.state === "completed") ?? null)
const lastRelease = computed(() => lastReleases.value?.[0] ?? null)

defineEmits<{
  (e: 'settingsConfirmed', script: ReleaseScript): void
}>()

watch(props, (value, oldValue) => value.repo !== oldValue.repo && update())

async function update() {
  if (props.repo) {
    releaseScript.value = null
    releaseScript.value = await (await fetch(`${prefix_url}/api/release/${props.repo}/release_script`)).json()

    const releases: Release[] = await (await fetch(`${prefix_url}/api/release/${props.repo}`)).json()
    releases.sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime())
    lastReleases.value = releases
  }
}

let _saveFileAnimationTimeout: number | null = null;

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
      body: JSON.stringify(releaseScript.value)
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

      <button :disabled="!releaseScript" class="btn btn-success"
              @click="$emit('settingsConfirmed', releaseScript)">
        <i class="fa fa-play"></i>
        Start a release
      </button>
      <button :disabled="!releaseScript" class="btn btn-success dropdown-toggle dropdown-toggle-split flex-grow-0"
              data-bs-toggle="dropdown"
              type="button">
      </button>

      <ul class="dropdown-menu">
        <li><a class="dropdown-item" href="#" @click="showAdvanced = !showAdvanced">
          <i :class="[showAdvanced ? 'fa-check-square' : 'fa-square']" class="fa-regular"></i> Show advanced
          configuration
        </a></li>
      </ul>
    </div>
    <ul class="list-group mt-2">
      <li v-for="release in lastReleases" class="list-group-item ">
        <a class=" d-flex justify-content-between align-items-start" style="text-decoration: none; color: inherit" :href="`${release.id}`">
          <div class="ms-2 me-auto">
            <div class="fw-bold">{{ $filters.formatDate(release.start) }}</div>
            {{ release.started_by }}
          </div>
          <span class="badge rounded-pill" :class="{
            'text-bg-primary': ['running', 'waiting-for-user'].indexOf(release.state) >=0,
            'text-bg-success': release.state === 'success',
            'text-bg-error': release.state === 'errored',
            'text-bg-secondary': release.state === 'canceled',
          }">{{ release.state }}</span>
        </a>
      </li>
    </ul>


    <ReleaseScriptViewer v-if="!!releaseScript && showAdvanced" :release-script="releaseScript"
                         class="mt-2">
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
          Save release script
        </button>
      </template>
    </ReleaseScriptViewer>
  </div>
</template>

<style scoped>

</style>

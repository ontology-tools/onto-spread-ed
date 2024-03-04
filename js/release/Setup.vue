<script setup lang="ts">
import {computed, onMounted, Ref, ref, watch} from "vue";
import {Release, ReleaseScript} from "./model.ts"
import ReleaseScriptViewer from "./ReleaseScriptViewer.vue";

const showAdvanced = ref<boolean>()
const releaseScript: Ref<ReleaseScript | null> = ref(null);

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
    releaseScript.value = await (await fetch(`/api/release/${props.repo}/release_script`)).json()

    const releases: Release[] = await (await fetch(`/api/release/${props.repo}`)).json()
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
    const response = await fetch(`/api/release/${props.repo}/release_script`, {
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
        <span style="width: 400px" class="placeholder"></span>
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

    <!--    <RepositorySelector :repositories="repos" v-model="repo" @update:modelValue="setRepo"></RepositorySelector>-->

    <div class="btn-group  w-100">

      <button :disabled="!releaseScript" class="btn btn-success"
              @click="$emit('settingsConfirmed', releaseScript)">
        <i class="fa fa-play"></i>
        Start a release
      </button>
      <button :disabled="!releaseScript" type="button"
              class="btn btn-success dropdown-toggle dropdown-toggle-split flex-grow-0"
              data-bs-toggle="dropdown">
      </button>

      <ul class="dropdown-menu">
        <li><a class="dropdown-item" href="#" @click="showAdvanced = !showAdvanced">
          <i class="fa-regular" :class="[showAdvanced ? 'fa-check-square' : 'fa-square']"></i> Show advanced
          configuration
        </a></li>
      </ul>
    </div>


    <ReleaseScriptViewer :release-script="releaseScript" v-if="!!releaseScript && showAdvanced"
                         class="mt-2">
      <template v-slot:buttons>
        <button class="mb-3 btn btn-sm btn-primary"
                :class="({
                  'btn-primary': saving === 'idle' || saving === 'saving',
                  'btn-success': saving === 'success',
                  'btn-danger': saving === 'error'
                })"
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

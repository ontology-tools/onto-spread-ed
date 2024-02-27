<script setup lang="ts">
import {computed, onMounted, ref, watch} from "vue";
import {Release, ReleaseScript} from "./model.ts";
import Setup from "./Setup.vue";
import Preparation from "./steps/Preparation.vue";
import Validation from "./steps/Validation.vue";
import ImportExternal from "./steps/ImportExternal.vue";
import Build from "./steps/Build.vue";
import Merge from "./steps/Merge.vue";
import HumanVerification from "./steps/HumanVerification.vue";
import GithubPublish from "./steps/GithubPublish.vue";

const release = ref<Release | null>(null);

const loading = ref<boolean>(false)
const error = ref<string | null>(null)

const selected_step = ref<number | null>(null)

const _steps: { [k: string]: any } = {
  "PREPARATION": Preparation,
  "VALIDATION": Validation,
  "IMPORT_EXTERNAL": ImportExternal,
  "BUILD": Build,
  "MERGE": Merge,
  "HUMAN_VERIFICATION": HumanVerification,
  "GITHUB_PUBLISH": GithubPublish
}

const stepComponent = computed(() => {
  const step = selected_step.value ?? release.value?.step
  const currentStep = release.value?.release_script.steps[step]
  return _steps[currentStep?.name ?? ""]
})


async function poll(withLoading: boolean = false) {
  const id = release.value?.id ?? 'running'
  loading.value = withLoading;
  try {
    let response = await fetch(`/api/release/${id}`);
    if (response.ok) {
      release.value = await response.json()
    } else {
      release.value = null
    }
  } catch (e) {
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  const lastPathSegment = window.location.pathname.split("/").slice(-1)[0]
  const releaseId = parseInt(lastPathSegment)

  console.log({lastPathSegment, releaseId})

  if (!isNaN(releaseId)) {
    release.value = await _request(() => fetch(`/api/release/${releaseId}`))
  } else {
    await poll(true)
  }
})

let pollInterval: number | null = null

const stopWaitingForReleaseStart = watch(release, (value, oldValue) => {
  if (oldValue === null && value !== null && pollInterval === null && value.state === "running") {
    pollInterval = setInterval(poll, 2000)
    stopWaitingForReleaseStart()
  }
})

const icon_classes = computed(() => {
  switch (release.value?.state) {
    case undefined:
    case null:
      return ["fa-regular", "fa-file", "text-black-50"]
    case "canceled":
      return ["fa-regular", "fa-circle-xmark", "text-danger"]
    case "waiting-for-user":
      return ["fa-solid", "fa-user-clock", "text-warning"]
    case "errored":
      return ["fa-solid", "fa-triangle-exclamation", "text-danger"]
    case "completed":
      return ["fa-regular", "fa-circle-check", "text-success"]
    default:
      return ["fa-spinner", "fa-spin", "text-black-50"]
  }
})

async function _request<T = any, S = T>(request: () => Promise<Response>): Promise<T>

async function _request<T = any, S = T>(request: () => Promise<Response>, post: ((json: T) => Promise<S>)): Promise<S>
async function _request<T = any, S = T>(request: () => Promise<Response>, post: ((json: T) => Promise<S>) | null = null): Promise<S | T | undefined> {
  try {
    loading.value = true;
    const response = await request()

    if (response.ok) {
      const value = await response.json() as T
      if (post !== null) {
        return await post(value)
      } else {
        return value
      }
    } else {
      const e = await response.json()
      error.value = e.error
    }

    loading.value = false;
  } catch (e) {
    if (e instanceof Error) {
      error.value = e.message
    } else {
      error.value = `An unknown error occurred: ${e}`
    }
  } finally {
    loading.value = false;
  }
}

async function startRelease(releaseScript: ReleaseScript) {
  release.value = await _request(() =>
      fetch("/api/release/start", {
        method: "post",
        body: JSON.stringify(releaseScript),
        headers: {
          "Content-Type": "application/json"
        }
      }))

  window.location.reload()
}

async function cancelRelease() {
  await _request(() => fetch("/api/release/cancel", {
    method: "post"
  }))
}

async function restartRelease() {
  const script = release.value?.release_script
  if (script) {
    await cancelRelease()
    await startRelease(script)
  }
}

function errorsOfStep(step: number) {
  const details = release.value?.details[step.toString()]
  if (details?.hasOwnProperty("errors") && Array.isArray(details["errors"])) {
    return details["errors"].length
  } else if (Array.isArray(details)) {
    return details.map(x => x["errors"]?.length).reduce((p, c) => c + p, 0)
  }
}

function warningsOfStep(step: number) {
  const details = release.value?.details[step.toString()]
  if (details?.hasOwnProperty("warnings") && Array.isArray(details["warnings"])) {
    return details["warnings"].length
  } else if (details) {
    return Object.values(details).map(x => x["warnings"]?.length).reduce((p, c) => c + p, 0)
  }
}

function stepIconClasses(step: number): string[] {
  if ((release.value?.step ?? 0) >= step) {
    if (errorsOfStep(step) > 0) {
      return "fa fa-triangle-exclamation text-danger".split(" ")
    } else if (warningsOfStep(step) > 0) {
      return "fa fa-triangle-exclamation text-warning".split(" ")
    } else if (release.value?.step === step && release.value.state !== 'completed') {
      return "fa-regular fa-circle text-primary".split(" ")
    } else {
      return "fa-regular fa-check-circle text-success".split(" ")
    }
  } else {
    return "fa-regular fa-clock text-warning".split(" ")
  }
}

async function doReleaseControl(type: string) {
  switch (type) {
    case "continue":
      await fetch("/api/release/continue")
      break;
    default:
      console.warn(`No such release control type: '${type}'`)
  }
}

function formatText(str: string): string {
  const s = str.trim().toLowerCase().replace("_", " ")
  return s.charAt(0).toUpperCase() + s.substring(1)
}
</script>

<template>
  <div class="release">
    <div class="alert alert-danger" v-if="error !== null">
      <h6>An error occurred</h6>
      {{ error }}
    </div>
    <div class="d-flex gap-2 align-items-center">
      <h1 id="lbl-release-title">
        <i id="icon-release" class="fa" :class="icon_classes"></i>
        Release
      </h1>
      <span id="release-info" class="align-self-end mb-2 text-muted"></span>
      <span class="flex-fill"></span>

      <template v-if="release && (release.state === 'running' || release.state === 'waiting-for-user')">
        <button class="btn btn-warning" id="btn-release-restart" @click="restartRelease">
          <i class="fa fa-rotate-left"></i> Restart
        </button>
        <button class="btn btn-danger" id="btn-release-cancel" @click="cancelRelease">
          <i class="fa fa-cancel"></i>
          Cancel
        </button>
      </template>
    </div>

    <Setup v-if="!release" style="max-width: 1080px; margin: 0 auto"
           @settingsConfirmed="startRelease($event)"></Setup>

    <template v-if="release !== null">
      <div style="display: grid;grid-template-columns: 240px 1fr;grid-gap: 50px" class="text-start w-100"
           id="release-core">
        <div class="sidebar border" style="grid-column: 1">
          <ul class="list-unstyled ps-2">
            <li class="mb-1 d-flex align-items-center" v-for="(step, i) in release.release_script.steps">
              <i :class="stepIconClasses(i)"></i>
              <a class="btn border-0" href="#" @click="selected_step = i">
                <strong v-if="selected_step !== null ? selected_step == i : release.step == i">{{ formatText(step.name) }}</strong>
                <template v-else>{{ formatText(step.name) }}</template>
              </a>
            </li>
          </ul>
        </div>
        <div class="main" style="grid-column: 2">
          <component :is="stepComponent" :data="release.details[(selected_step ?? release.step).toString()]" :release="release"
                     @release-control="doReleaseControl"></component>
        </div>
      </div>
    </template>
  </div>

  <div class="loading" v-if="loading">
    <div class="inner text-light">
      <div class="spinner-border" style="width: 5rem; height: 5rem;" role="status">
      </div>
      <h5>Loading...</h5>
    </div>
  </div>
</template>


<style scoped lang="scss">
.loading {
  z-index: 1;
  background: rgba(0, 0, 0, .4);
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  display: grid;

  .inner {
    margin: auto;
    justify-self: center;
    align-self: center;
    display: flex;
    flex-direction: column;
    text-align: center;
    gap: 14px;

    .spinner-border {
      border-width: 10px;
    }
  }
}
</style>

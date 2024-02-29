<script setup lang="ts">
import {computed, onMounted, ref, watch} from "vue";
import {Diagnostic, Release, ReleaseScript} from "./model.ts";
import Setup from "./Setup.vue";
import Preparation from "./steps/Preparation.vue";
import Validation from "./steps/Validation.vue";
import ImportExternal from "./steps/ImportExternal.vue";
import Build from "./steps/Build.vue";
import Merge from "./steps/Merge.vue";
import HumanVerification from "./steps/HumanVerification.vue";
import GithubPublish from "./steps/GithubPublish.vue";
import BCIOSearch from "./steps/BCIOSearch.vue";

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
  "GITHUB_PUBLISH": GithubPublish,
  "BCIO_SEARCH": BCIOSearch
}

const stepComponent = computed(() => {
  if (release.value) {
    const step = (selected_step.value ?? release.value.step)
    const currentStep = release.value?.release_script.steps[step]
    return _steps[currentStep?.name ?? ""]
  }
  return null
})

const details = computed(() => release.value?.details[(selected_step.value ?? release.value.step).toString()])

type SubStepContent = { errors: Diagnostic[], warnings: Diagnostic[] };

function subSteps(data?: any): null | { [k: string]: SubStepContent } {
  if (data instanceof Object) {
    const val = data as { [key: string]: Partial<SubStepContent> }
    const steps = Object.entries(val)
        .filter(([k, v]) =>
            !k.startsWith("_") &&
            ["warnings", "errors", "infos"].indexOf(k) < 0 &&
            Array.isArray(v?.warnings) && Array.isArray(v?.errors)
        ) as unknown as [string, SubStepContent][]
    return steps.length > 0 ? Object.fromEntries(steps) : null;
  }

  return null
}

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
    release.value = await _request<Release>(() => fetch(`/api/release/${releaseId}`)) ?? null
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

async function _request<T = any, S = T>(request: () => Promise<Response>): Promise<T | undefined>

async function _request<T = any, S = T>(request: () => Promise<Response>, post: ((json: T) => Promise<S>)): Promise<S | undefined>
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
  const r = await _request<Release>(() =>
      fetch("/api/release/start", {
        method: "post",
        body: JSON.stringify(releaseScript),
        headers: {
          "Content-Type": "application/json"
        }
      }))

  if (r) {
    release.value = r
    window.location.pathname = `/admin/release/${r.id}`
  }
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

function formatDate(d: string | Date): string {
  const date = d instanceof Date ? d : new Date(d)
  return new Intl.DateTimeFormat("default", {dateStyle: "long", timeStyle: "short"}).format(date)
}

function formatText(str: string): string {
  const s = str.trim().toLowerCase().replace("_", " ")
  return s.charAt(0).toUpperCase() + s.substring(1)
}
</script>

<template>
  <div class="release">
    <div class="d-flex gap-2 align-items-center">
      <h1 id="lbl-release-title">
        <i id="icon-release" class="fa" :class="icon_classes"></i>
        Release
      </h1>
      <span id="release-info" class="align-self-end mb-2 text-muted" v-if="release">
          started by {{ release.started_by }} on {{ formatDate(release.start) }}
      </span>
      <span class="flex-fill"></span>

      <template v-if="release && (['running', 'waiting-for-user', 'errored'].indexOf(release.state) >= 0)">
        <button class="btn btn-warning" id="btn-release-restart" @click="restartRelease">
          <i class="fa fa-rotate-left"></i> Restart
        </button>
        <button class="btn btn-danger" id="btn-release-cancel" @click="cancelRelease">
          <i class="fa fa-cancel"></i>
          Cancel
        </button>
      </template>
    </div>

    <template v-if="!release">
      <div class="alert alert-danger" v-if="error !== null">
        <h4>An error occurred</h4>
        {{ error }}
      </div>
      <Setup v-if="!release" style="max-width: 1080px; margin: 0 auto"
             @settingsConfirmed="startRelease($event)"></Setup>
    </template>


    <template v-if="release !== null">
      <div style="display: grid;grid-template-columns: 240px 1fr;grid-gap: 50px" class="text-start w-100"
           id="release-core">
        <div class="sidebar border" style="grid-column: 1">
          <ul class="list-unstyled ps-2">
            <li class="mb-1" v-for="(step, i) in release.release_script.steps">
              <div class="d-flex align-items-center">
                <i :class="stepIconClasses(i)"></i>
                <a class="btn border-0" href="#" @click="selected_step = i">
                  <strong v-if="selected_step !== null ? selected_step == i : release.step == i">
                    {{ formatText(step.name) }}
                  </strong>
                  <template v-else>{{ formatText(step.name) }}</template>
                </a>
              </div>
              <ul class="list-unstyled ms-4" v-if="subSteps">
                <li v-for="(val, key) in subSteps(release.details[i])" style="display: flex; align-items: center">
                  <i v-if="(val.errors?.length ?? 0) > 0" class="fa fa-circle-exclamation text-danger"></i>
                  <i v-else-if="(val.warnings?.length ?? 0) > 0" class="fa fa-triangle-exclamation text-warning"></i>
                  <i v-else class="fa fa-check-circle text-success"></i>
                  <a class="btn border-0 text-truncate">{{ key }}</a>
                </li>
              </ul>
            </li>
          </ul>
        </div>
        <div class="main" style="grid-column: 2">
          <div class="alert alert-danger" v-if="error !== null">
            <h4>An error occurred</h4>
            {{ error }}
          </div>

          <div class="alert alert-danger" v-if="details?.error">
            <h4>An error occurred: {{ details.error.short }}</h4>
            <pre>{{ details.error.long }}</pre>
          </div>

          <component :is="stepComponent" :data="details" :release="release"
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

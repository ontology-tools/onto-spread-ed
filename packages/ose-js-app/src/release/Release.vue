<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, ref, watch, shallowRef, markRaw, type Component, h } from "vue";
import { Diagnostic, Release, ReleaseScript } from "@ontospreaded/js-core";
import Setup from "./Setup.vue";
import Validation from "./steps/Validation.vue";
import HumanVerification from "./steps/HumanVerification.vue";
import GithubPublish from "./steps/GithubPublish.vue";
import Generic from "./steps/Generic.vue";
import { BToast, useToastController } from "bootstrap-vue-next";

declare var SERVER_DATA: { [key: string]: any }
declare var URLS: { [key: string]: any }

interface PluginInfo {
  id: string;
  name: string;
  version: string;
  description: string;
  components: { step_name: string; component_name: string }[];
  has_static: boolean;
  js_module: string | null;
}

const repo = SERVER_DATA.repo
const prefix_url = URLS.prefix
const release = ref<Release | null>(null);

const loading = ref<boolean>(false)
const error = ref<string | null>(null)

const selected_step = ref<number | null>(null)
const selected_sub_step = ref<string | null>(null)

const { show: showToast } = useToastController();

// Built-in step components
const builtInSteps: { [k: string]: Component } = {
  "VALIDATION": Validation,
  "HUMAN_VERIFICATION": HumanVerification,
  "GITHUB_PUBLISH": GithubPublish,
}

// Dynamic plugin components - will be populated from API
const pluginSteps = shallowRef<{ [k: string]: Component }>({})

// Combined steps registry
const _steps = computed(() => ({
  ...builtInSteps,
  ...pluginSteps.value
}))

// Load plugins from API
async function loadPlugins() {
  try {
    const response = await fetch(`${prefix_url}/api/plugins/`);
    if (!response.ok) return;

    const plugins: PluginInfo[] = await response.json();
    const newPluginSteps: { [k: string]: Component } = {};

    for (const plugin of plugins) {
      if (!plugin.has_static || !plugin.js_module || plugin.components.length === 0) continue;

      for (const comp of plugin.components) {
        // Create async component that loads from plugin's static folder
        const pluginId = plugin.id;
        const jsModule = plugin.js_module;
        const componentName = comp.component_name;

        newPluginSteps[comp.step_name] = markRaw(defineAsyncComponent(async () => {
          const moduleUrl = `${prefix_url}/api/plugins/${pluginId}/static/${jsModule}`;
          const module = await import(/* @vite-ignore */ moduleUrl);
          return module[componentName] || module.default;
        }));
      }
    }

    pluginSteps.value = newPluginSteps;
  } catch (e) {
    console.error("Failed to load plugins:", e);
  }
}

const currentStep = computed<{
  args: any,
  name: string
} | null>(() => release.value?.release_script.steps[selected_step.value ?? release.value.step] ?? null)
const stepComponent = computed(() => _steps.value[currentStep.value?.name] ?? Generic)

const stepProps = computed(() => {
  const possibleProps = {
    data: details.value,
    release: release.value,
    selectedSubStep: selected_sub_step.value,
    step: currentStep.value
  }

  const component = stepComponent.value;

  if (component) {
    // For async components, try to get the resolved component's props
    // AsyncComponentWrapper stores the resolved component in __asyncResolved
    const resolvedComponent = component.__asyncResolved || component;
    const componentProps = resolvedComponent.props;

    if (componentProps) {
      const required = Object.keys(componentProps)
      return Object.fromEntries(Object.entries(possibleProps).filter(([k, _]) => required.indexOf(k) >= 0))
    }

    // Fallback: pass all props for unresolved async components
    return possibleProps;
  }

  return null;
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
  const id = release.value?.id ?? `${repo}/running`
  loading.value = withLoading;
  try {
    let response = await fetch(`${prefix_url}/api/release/${id}`);
    if (response.ok) {
      release.value = await response.json()
    } else {
      release.value = null
    }
  } catch (e) {
  } finally {
    loading.value = false;
  }

  if (release.value && ['completed', 'canceled'].includes(release.value.state)) {
    if (pollInterval !== null) {
      clearInterval(pollInterval)
      pollInterval = null
    }
  }
}

onMounted(async () => {
  // Load plugins first
  await loadPlugins();

  const lastPathSegment = window.location.pathname.split("/").slice(-1)[0]
  const releaseId = parseInt(lastPathSegment)

  if (!isNaN(releaseId)) {
    release.value = await _request<Release>(() => fetch(`${prefix_url}/api/release/${releaseId}`)) ?? null
  } else {
    await poll(true)
  }
})

let pollInterval: number | null = null

function startPolling() {
  if (pollInterval === null) {
    pollInterval = setInterval(poll, 2000)
  }
}

const stopWaitingForReleaseStart = watch(release, (value) => {
  if (value !== null && pollInterval === null && !['completed', 'canceled'].includes(value.state)) {
    stopWaitingForReleaseStart()
    startPolling()
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

async function rerunStep() {
  showToast?.({
    props: {
      value: 5000,
      progressProps: {
        variant: 'success',
      }
    },
    component: h(BToast, { variant: "success" }, {
      default: () => h("div", { style: "display: flex; align-items: center; gap: 16px" }, [
        h("i", { class: "fa fa-check" }),
        h("span", null, "Requesting rerun!")
      ])
    })
  })

  await fetch(`${prefix_url}/api/release/${repo}/rerun-step?force=true`, {
    method: "POST"
  })

  startPolling()
}

async function startRelease(releaseScript: ReleaseScript) {
  const r = await _request<Release>(() =>
    fetch(prefix_url + "/api/release/start", {
      method: "post",
      body: JSON.stringify(releaseScript),
      headers: {
        "Content-Type": "application/json"
      }
    }))

  if (r) {
    release.value = r
    window.location.pathname = `${prefix_url}/admin/release/${r.id}`
  }
}

async function cancelRelease() {
  release.value = await _request<Release>(() => fetch(`${prefix_url}/api/release/${repo}/cancel`, {
    method: "post"
  })) ?? null
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
    return Object.values(details).map((x: any) => x["warnings"]?.length).reduce((p, c) => c + p, 0)
  }
}

function stepIconClasses(step: number): string[] {
  if ((release.value?.step ?? 0) >= step) {
    if (errorsOfStep(step) > 0) {
      return "fa fa-triangle-exclamation text-danger".split(" ")
    } else if (warningsOfStep(step) > 0) {
      return "fa fa-triangle-exclamation text-warning".split(" ")
    } else if (release.value?.step === step) {
      switch (release.value?.state) {
        case "canceled":
          return ["fa-regular", "fa-circle-xmark", "text-danger"]
        case "waiting-for-user":
          return ["fa-solid", "fa-user-clock", "text-warning"]
        case "errored":
          return ["fa-solid", "fa-triangle-exclamation", "text-danger"]
        case "completed":
          return ["fa-regular", "fa-circle-check", "text-success"]
        default:
          return ["fa-regular", "fa-circle", "text-primary"]
      }
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
      await fetch(`${prefix_url}/api/release/${repo}/continue`)
      startPolling()
      break;
    default:
      console.warn(`No such release control type: '${type}'`)
  }
}
</script>

<template>
  <BToastOrchestrator />
  <div class="release">
    <div class="d-flex gap-2 align-items-center">
      <h1 id="lbl-release-title">
        <i id="icon-release" class="fa" :class="icon_classes"></i>
        Release {{ repo }}
      </h1>
      <span id="release-info" class="align-self-end mb-2 text-muted" v-if="release">
        started by {{ release.started_by }} on {{ $filters.formatDate(release.start) }}
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

    <template v-if="!release && !loading">
      <div class="alert alert-danger" v-if="error !== null">
        <h4>An error occurred</h4>
        {{ error }}
      </div>
      <Setup v-if="!release" style="max-width: 1080px; margin: 0 auto" :repo="repo"
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
                <a class="btn border-0" @click="selected_step = i; selected_sub_step = null">
                  <strong v-if="selected_step !== null ? selected_step == i : release.step == i">
                    {{ $filters.formatText(step.name) }}
                  </strong>
                  <template v-else>{{ $filters.formatText(step.name) }}</template>
                </a>
              </div>
              <ul class="list-unstyled ms-4" v-if="subSteps">
                <li v-for="(val, key) in subSteps(release.details[i])" style="display: flex; align-items: center">
                  <i v-if="(val.errors?.length ?? 0) > 0" class="fa fa-circle-exclamation text-danger"></i>
                  <i v-else-if="(val.warnings?.length ?? 0) > 0" class="fa fa-triangle-exclamation text-warning"></i>
                  <i v-else class="fa fa-check-circle text-success"></i>
                  <a class="btn border-0 text-truncate"
                    @click="selected_sub_step = selected_sub_step === key ? null : key">
                    <strong v-if="selected_sub_step === key">{{ key }}</strong>
                    <template v-else>{{ key }}</template>
                  </a>
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

          <component :is="stepComponent" v-bind="stepProps" @release-control="doReleaseControl"></component>
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

  <div style="font-size: x-small; position: absolute; bottom: 4px; right: 8px; color: #888;">
    <a href="#" @click.prevent="rerunStep()">Rerun</a>
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

#release-core .sidebar .btn {
  text-align: start !important;
}
</style>

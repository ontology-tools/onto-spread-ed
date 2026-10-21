<script setup lang="ts">
import { computed, defineAsyncComponent, onBeforeUnmount, ref, watch, shallowRef, markRaw, type Component, h } from "vue";
import { useRoute, useRouter } from "vue-router";
import { BuildConfiguration, BuildStep, Diagnostic, Release, currentStage, releaseStages, stageDetails } from "@ontospreaded/js-core";
import Setup from "./Setup.vue";
import Validation from "./steps/Validation.vue";
import HumanVerification from "./steps/HumanVerification.vue";
import GithubPublish from "./steps/GithubPublish.vue";
import Generic from "./steps/Generic.vue";
import { BToast, useToastController } from "bootstrap-vue-next";
import RepositorySelector from "./RepositorySelector.vue";
import { api, prefix } from "../api";
import { layout } from "../state";

interface PluginInfo {
  id: string;
  components: { step_name: string; component_name: string }[];
  has_static: boolean;
  js_module: string | null;
}

const route = useRoute()
const router = useRouter()

const repo = ref<string | null>(null)
const repos = ref<{ short: string, full: string }[] | null>(null)
const chosenRepo = ref<string | null>(null)
const notFound = ref<string | null>(null)
const release = ref<Release | null>(null);

const loading = ref<boolean>(false)
const error = ref<string | null>(null)

const selected_step = ref<number | null>(null)
const selected_sub_step = ref<string | null>(null)

const { show: showToast } = useToastController();

const builtInSteps: { [k: string]: Component } = {
  "VALIDATION": Validation,
  "HUMAN_VERIFICATION": HumanVerification,
  "GITHUB_PUBLISH": GithubPublish,
}

const pluginSteps = shallowRef<{ [k: string]: Component }>({})

const _steps = computed(() => ({
  ...builtInSteps,
  ...pluginSteps.value
}))

async function loadPlugins() {
  try {
    const plugins = await api<PluginInfo[]>("/api/plugins/");
    const newPluginSteps: { [k: string]: Component } = {};

    for (const plugin of plugins) {
      if (!plugin.has_static || !plugin.js_module || plugin.components.length === 0) continue;

      for (const comp of plugin.components) {
        const pluginId = plugin.id;
        const jsModule = plugin.js_module;
        const componentName = comp.component_name;

        newPluginSteps[comp.step_name] = markRaw(defineAsyncComponent(async () => {
          const moduleUrl = `${prefix}/api/plugins/${pluginId}/static/${jsModule}`;
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

const shownStep = computed(() => selected_step.value ?? currentStage(release.value))
const currentStep = computed<BuildStep | null>(() => releaseStages(release.value)[shownStep.value] ?? null)
const stepComponent = computed(() => (currentStep.value ? _steps.value[currentStep.value.name] : undefined) ?? Generic)

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
    const resolvedComponent = (component as any).__asyncResolved || component;
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

const details = computed(() => stageDetails(release.value, shownStep.value))

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

async function poll() {
  const id = release.value?.id
  if (id === undefined) return
  try {
    const r = await api<Release>(`/api/release/${id}`)
    if (release.value?.id === id) release.value = r
  } catch (e: any) {
    if (release.value?.id === id) error.value = e.message
  }

  if (release.value && ['completed', 'cancelled'].includes(release.value.state)) {
    stopPolling()
  }
}

function stopPolling() {
  if (pollInterval !== null) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

let pollInterval: ReturnType<typeof setInterval> | null = null
// Release controls call startPolling() after an await, which may resolve after leaving the page
let unmounted = false

function startPolling() {
  if (pollInterval === null && !unmounted) {
    pollInterval = setInterval(poll, 2000)
  }
}

onBeforeUnmount(() => {
  unmounted = true
  initToken++
  stopPolling()
})

let initToken = 0
async function init() {
  if (!route.path.startsWith("/admin/release")) return // navigating away, the component is about to unmount
  const token = ++initToken
  stopPolling()
  release.value = null
  error.value = null
  notFound.value = null
  selected_step.value = null
  selected_sub_step.value = null
  chosenRepo.value = null

  const idParam = route.params.id as string | undefined
  const repoParam = route.params.repo as string | undefined
  const idOrRepo = idParam ?? repoParam
  const id = idOrRepo !== undefined && /^\d+$/.test(idOrRepo) ? parseInt(idOrRepo) : null
  const stale = () => token !== initToken

  layout.breadcrumb = [{ name: "Admin", to: "/admin/dashboard" }, { name: "Release", to: "/admin/release" }]
  loading.value = true
  try {
    if (id !== null) {
      let r: Release
      try {
        r = await api<Release>(`/api/release/${id}`)
      } catch (e: any) {
        if (stale()) return
        repo.value = null
        notFound.value = e.status === 404 ? `Cannot find release with id '${id}'.` : e.message
        return
      }
      if (stale()) return
      repo.value = r.repo
      layout.breadcrumb.push({ name: r.repo.toUpperCase(), to: `/admin/release/${r.repo}` })
      release.value = r
    } else if (repoParam !== undefined) {
      repo.value = repoParam
      layout.breadcrumb.push({ name: repoParam.toUpperCase(), to: `/admin/release/${repoParam}` })
      let running: Release | null = null
      try {
        running = await api<Release>(`/api/release/${repoParam}/running`)
      } catch (e: any) {
        if (e.status !== 404) error.value = e.message
      }
      if (stale()) return
      if (running) {
        await router.replace(`/admin/release/${running.id}`)
      }
    } else {
      repo.value = null
      const all = await api<{ short: string, full: string }[]>("/api/repo/")
      if (stale()) return
      if (all.length === 1) {
        await router.replace(`/admin/release/${all[0].short}`)
      } else {
        repos.value = all
      }
    }
  } catch (e: any) {
    if (!stale()) error.value = e.message
  } finally {
    if (!stale()) loading.value = false
  }
}

watch(() => [route.params.repo, route.params.id], init, { immediate: true })

watch(chosenRepo, (value) => {
  if (value) router.push(`/admin/release/${value}`)
})

loadPlugins()

watch(release, (value) => {
  if (value !== null && pollInterval === null && !['completed', 'cancelled'].includes(value.state)) {
    startPolling()
  }
})

const icon_classes = computed(() => {
  switch (release.value?.state) {
    case undefined:
    case null:
      return ["fa-regular", "fa-file", "text-black-50"]
    case "cancelled":
      return ["fa-regular", "fa-circle-xmark", "text-danger"]
    case "paused":
      return ["fa-solid", "fa-user-clock", "text-warning"]
    case "errored":
      return ["fa-solid", "fa-triangle-exclamation", "text-danger"]
    case "completed":
      return ["fa-regular", "fa-circle-check", "text-success"]
    default:
      return ["fa-spinner", "fa-spin", "text-black-50"]
  }
})

async function requestRelease(path: string, init: RequestInit = {}): Promise<Release | undefined> {
  const page = route.fullPath
  loading.value = true
  error.value = null
  try {
    const result = await api<Release>(path, init)
    if (!unmounted && route.fullPath === page) return result
  } catch (e: any) {
    if (!unmounted && route.fullPath === page) error.value = e.message
  } finally {
    if (!unmounted && route.fullPath === page) loading.value = false
  }
}

async function rerunStep() {
  const result = await requestRelease(`/api/release/${repo.value}/rerun-step?force=true`, {method: "POST"})
  if (!result) return
  release.value = result
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

  startPolling()
}

async function startRelease(buildConfiguration: BuildConfiguration) {
  const r = await requestRelease("/api/release/start", {
    method: "POST",
    body: JSON.stringify({repo: repo.value, build_configuration: buildConfiguration}),
  })

  if (r) {
    await router.push(`/admin/release/${r.id}`)
  }
}

async function cancelRelease(): Promise<boolean> {
  const cancelled = await requestRelease(`/api/release/${repo.value}/cancel`, {method: "POST"})
  if (cancelled) release.value = cancelled
  return cancelled !== undefined
}

async function restartRelease() {
  const buildConfiguration = release.value?.context?.build_configuration
  // A cancelled release no longer counts as open, the new one can start while the old one still stops
  if (buildConfiguration && await cancelRelease()) {
    await startRelease(buildConfiguration)
  }
}

function errorsOfStep(step: number): number {
  return release.value?.context?.stage_results[step]?.log.errors.length ?? 0
}

function warningsOfStep(step: number): number {
  return release.value?.context?.stage_results[step]?.log.warnings.length ?? 0
}

function stepIconClasses(step: number): string[] {
  if (currentStage(release.value) >= step) {
    if (errorsOfStep(step) > 0) {
      return "fa fa-triangle-exclamation text-danger".split(" ")
    } else if (warningsOfStep(step) > 0) {
      return "fa fa-triangle-exclamation text-warning".split(" ")
    } else if (currentStage(release.value) === step) {
      switch (release.value?.state) {
        case "cancelled":
          return ["fa-regular", "fa-circle-xmark", "text-danger"]
        case "paused":
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
      const continued = await requestRelease(`/api/release/${repo.value}/continue`)
      if (continued) {
        release.value = continued
        startPolling()
      }
      break;
    default:
      console.warn(`No such release control type: '${type}'`)
  }
}
</script>

<template>
  <div class="release">
    <div v-if="notFound" class="alert alert-danger">{{ notFound }}</div>

    <template v-else-if="repo === null">
      <div v-if="error !== null" class="alert alert-danger">{{ error }}</div>
      <div v-else-if="repos" style="max-width: 1080px; margin: 0 auto">
        <h4>Which repository should be released?</h4>
        <RepositorySelector :repositories="repos" v-model="chosenRepo"></RepositorySelector>
      </div>
    </template>

    <template v-else>
    <div class="d-flex gap-2 align-items-center">
      <h1 id="lbl-release-title">
        <i id="icon-release" class="fa" :class="icon_classes"></i>
        Release {{ repo }}
      </h1>
      <span id="release-info" class="align-self-end mb-2 text-muted" v-if="release">
        started by {{ release.started_by }} on {{ $filters.formatDate(release.start) }}
      </span>
      <span class="flex-fill"></span>

      <template v-if="release && (['starting', 'running', 'paused', 'errored'].indexOf(release.state) >= 0)">
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
            <li class="mb-1" v-for="(step, i) in releaseStages(release)">
              <div class="d-flex align-items-center">
                <i :class="stepIconClasses(i)"></i>
                <a class="btn border-0" @click="selected_step = i; selected_sub_step = null">
                  <strong v-if="shownStep == i">
                    {{ $filters.formatText(step.name) }}
                  </strong>
                  <template v-else>{{ $filters.formatText(step.name) }}</template>
                </a>
              </div>
              <ul class="list-unstyled ms-4" v-if="subSteps">
                <li v-for="(val, key) in subSteps(stageDetails(release, i))" style="display: flex; align-items: center">
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

          <div class="alert alert-danger" v-for="exception in details?.errors?.filter(e => e.type === 'exception')">
            <h4>An error occurred: {{ exception.msg }}</h4>
            <pre>{{ exception.traceback }}</pre>
          </div>

          <div class="alert alert-info" v-if="release.state === 'starting' && release.progress?.message">
            <i class="fa fa-spinner fa-spin"></i> {{ release.progress.message }}
          </div>

          <component :is="stepComponent" v-bind="stepProps" @release-control="doReleaseControl"></component>
        </div>
      </div>
    </template>
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

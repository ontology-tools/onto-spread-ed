<script lang="ts" setup>
import {computed, h, onMounted, ref} from "vue";
import {promptDialog} from "../common/bootbox";
import {BToast, useToastController} from "bootstrap-vue-next";
import {api, useMe} from "../api";
import {layout} from "../state";
import {pluginTypeLabel, type PluginInfo} from "../common/plugins";

const {me, ready} = useMe()

const can = (p: string) => !!me.value?.permissions && (me.value.permissions.includes(p) || me.value.permissions.includes("admin"))
const hasAny = computed(() => ["release", "index", "admin", "repository-config-view", "scripts"].some(can))

const {show: showToast} = useToastController()

async function runScript(scriptName: string) {
  const script = scripts.value?.[scriptName]
  const script_args = script?.arguments;

  const args = []
  if (script_args && script_args.length > 0) {

    for (const arg of script_args) {
      const value = await promptDialog({
        title: arg.description,
        value: arg.default,
        inputType: "text"
      })

      if (value === null) {
        return
      }

      args.push(value)
    }
  }

  const dialog = bootbox.dialog({
    message: '<i class="fa fa-spin fa-spinner"></i> Script is being executed',
    closeButton: false
  })
  let dialogShown$ = new Promise<void>((resolve, _) => {
    dialog.on('shown.bs.modal', () => resolve())
  });
  try {

    const response = await api(`/api/scripts/${scriptName}/run`, {
      method: "POST",
      body: JSON.stringify({args})
    })

    await dialogShown$;
    dialog.modal("hide")

    bootbox.dialog({
      title: response.success ? "Success" : "Error",
      message: response.result ?? response.error
    })
  } catch (e) {
    await dialogShown$;
    dialog.modal("hide")

    bootbox.dialog({
      message: `<p>An error occurred</p><p>${e}</p>`,
      title: "Error"
    })
  }
}

async function clearCaches() {
  const dialog = bootbox.dialog({
    message: '<i class="fa fa-spin fa-spinner"></i> Clearing caches',
    closeButton: false
  })
  let dialogShown$ = new Promise<void>((resolve, _) => {
    dialog.on('shown.bs.modal', () => resolve())
  });
  try {

    await api("/api/settings/clear_caches", {method: "POST"})

    await dialogShown$;
    dialog.modal("hide")

    showToast?.({
      props: {
        value: 5000,
        progressProps: {
          variant: 'success',
        }
      },
      component: h(BToast, {variant: "success"}, {
        default: () => h("div", {style: "display: flex; align-items: center; gap: 16px"}, [
          h("i", {class: "fa fa-check"}),
          h("span", null, "Caches cleared!")
        ])
      })
    })
  } catch (e) {
    await dialogShown$;
    dialog.modal("hide")

    bootbox.dialog({
      message: `<p>An error occurred</p><p>${e}</p>`,
      title: "Error"
    })
  }
}

const scripts = ref<null | {
  [key: string]: {
    title: string,
    arguments?: {
      name: string,
      description: string,
      type: string,
      default?: string
    }[]
  }
}>(null)

const plugins = ref<PluginInfo[] | null>(null)
const pluginsError = ref<string | null>(null)

onMounted(async () => {
  layout.breadcrumb = [{name: "Admin"}]
  try {
    await ready
    if (can("admin")) {
      try {
        plugins.value = await api<PluginInfo[]>("/api/plugins/")
      } catch (error) {
        pluginsError.value = error instanceof Error ? error.message : String(error)
      }
    }
    if (can("scripts")) scripts.value = (await api("/api/scripts/")).result
  } catch (e) {
    console.debug("Scripts not available", e)
  }
})

</script>

<template>
  <div v-if="me && !hasAny" class="alert alert-info">You do not have any admin permissions.</div>
  <div class="row align-stretch">
    <div v-if="can('release')" class="col-sm-6 col-md-4 col-lg-3 m-2">
      <RouterLink to="/admin/release" class="card bg-light"
         style="height: 100%; text-decoration: none; border-width: 2px 2px 4px 2px">
        <div class="section p-5 text-center fs-2 bg-light">
          <i class="fas fa-upload"></i>
        </div>

        <div class="card-body">
          <h4>Release</h4>
          <p>
            Start the release process and release a new version of ontologies
          </p>
        </div>
      </RouterLink>
    </div>
    <div v-if="can('index')" class="col-sm-6 col-md-4 col-lg-3 m-2">

      <RouterLink to="/admin/rebuild-index" class="card bg-light"
         style="height: 100%; text-decoration: none; border-width: 2px 2px 4px 2px">
        <div class="section p-5 text-center fs-2 bg-light">
          <i class="fas fa-folder-open"></i>
        </div>

        <div class="card-body">
          <h4>Rebuild index</h4>
          <p>
            Force a complete rebuild of the index to ensure the search finds all entries.
          </p>
        </div>
      </RouterLink>
    </div>
    <div v-if="can('admin')" class="col-sm-6 col-md-4 col-lg-3 m-2">

      <a class="card bg-light" href="#" style="height: 100%; text-decoration: none; border-width: 2px 2px 4px 2px"
         @click.prevent="clearCaches()">
        <div class="section p-5 text-center fs-2 bg-light">
          <i class="fas fa-gauge-high"></i>
        </div>

        <div class="card-body">
          <h4>Clear caches</h4>
          <p>
            Clear cached files loaded from GitHub to ensure the latest version is used.
          </p>
        </div>
      </a>
    </div>
    <div v-if="can('repository-config-view')" class="col-sm-6 col-md-4 col-lg-3 m-2">

      <RouterLink to="/admin/settings" class="card bg-light"
         style="height: 100%; text-decoration: none; border-width: 2px 2px 4px 2px">
        <div class="section p-5 text-center fs-2 bg-light">
          <i class="fa-solid fa-gear"></i>
        </div>

        <div class="card-body">
          <h4>Repositories</h4>
          <p>
            Add, remove, or edit repositories available on the editor.
          </p>
        </div>
      </RouterLink>
    </div>
  </div>
  <div class="row align-stretch">
    <div v-if="can('scripts')" class="dropdown m-2">
      <button aria-expanded="false" class="btn btn-danger dropdown-toggle" data-bs-toggle="dropdown"
              type="button">
        Run a script
      </button>
      <ul class="dropdown-menu">
        <li v-for="(script, key) in scripts"><a class="dropdown-item" href="#" @click.prevent="runScript(key as string)">
          <i class="fa-regular fa-circle-play text-success"></i>
          {{ script.title }}
        </a></li>
      </ul>
    </div>

  </div>

  <section v-if="can('admin')" class="mt-4" aria-labelledby="loaded-plugins-heading">
    <h2 id="loaded-plugins-heading">Loaded plugins</h2>
    <p v-if="pluginsError" class="alert alert-danger" role="alert">Could not load plugins: {{ pluginsError }}</p>
    <p v-else-if="plugins === null" role="status">Loading plugins…</p>
    <p v-else-if="plugins.length === 0">No plugins are loaded.</p>
    <div v-else class="table-responsive">
      <table class="table table-striped align-middle">
        <caption>Each row represents a loaded extension. A package can provide several extension types.</caption>
        <thead>
          <tr><th scope="col">Plugin</th><th scope="col">Type</th><th scope="col">Distribution</th><th scope="col">Version</th></tr>
        </thead>
        <tbody>
          <tr v-for="plugin in plugins" :key="`${plugin.type}:${plugin.id}`">
            <th scope="row">{{ plugin.id }}</th>
            <td>{{ pluginTypeLabel(plugin.type) }}</td>
            <td>{{ plugin.distribution ?? 'Unknown' }}</td>
            <td>{{ plugin.version ?? 'Unknown' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>

</template>

<style lang="scss" scoped>

</style>

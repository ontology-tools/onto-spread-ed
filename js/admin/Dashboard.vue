<script lang="ts" setup>
import {h, onMounted, ref} from "vue";
import {promptDialog} from "../common/bootbox";
import {BToast, BToastOrchestrator, useToastController} from "bootstrap-vue-next";

declare var URLS: { [key: string]: any }
const prefix_url = URLS.prefix

const {show: showToast} = useToastController()

async function runScript(scriptName: string) {
  const script = scripts.value[scriptName]
  const script_args = script.arguments;

  const args = []
  if (script_args?.length > 0) {

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

    const response = await (await fetch(`${prefix_url}/api/scripts/${scriptName}/run`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({args})
    })).json()

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

    await fetch(`${prefix_url}/api/settings/clear_caches`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      }
    })

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

const urls = ref(URLS)

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

onMounted(async () => {
  scripts.value = (await (await fetch(`${prefix_url}/api/scripts`)).json()).result
})

</script>

<template>
  <BToastOrchestrator />

  <div class="row align-stretch">
    <div class="col-sm-6 col-md-4 col-lg-3 m-2">
      <a :href="urls.release" class="card bg-light"
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
      </a>
    </div>
    <div class="col-sm-6 col-md-4 col-lg-3 m-2">

      <a :href="urls.rebuildIndex" class="card bg-light"
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
      </a>
    </div>
    <div class="col-sm-6 col-md-4 col-lg-3 m-2">

      <a class="card bg-light" href="#" style="height: 100%; text-decoration: none; border-width: 2px 2px 4px 2px"
         @click="clearCaches()">
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
    <div v-if="'settings' in urls" class="col-sm-6 col-md-4 col-lg-3 m-2">

      <a :href="urls.settings" class="card bg-light"
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
      </a>
    </div>
    <div v-if="'settings' in urls" class="col-sm-6 col-md-4 col-lg-3 m-2">

      <a :href="urls.settings" class="card bg-light"
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
      </a>
    </div>
  </div>
  <div class="row align-stretch">
    <div class="dropdown m-2">
      <button aria-expanded="false" class="btn btn-danger dropdown-toggle" data-bs-toggle="dropdown"
              type="button">
        Run a script
      </button>
      <ul class="dropdown-menu">
        <li v-for="(script, key) in scripts"><a class="dropdown-item" href="#" @click="runScript(key)">
          <i class="fa-regular fa-circle-play text-success"></i>
          {{ script.title }}
        </a></li>
      </ul>
    </div>

  </div>

</template>

<style lang="scss" scoped>

</style>

<script setup lang="ts">

import CollapsibleCard from "../common/CollapsibleCard.vue";
import {computed, ref} from "vue";
import {alertDialog, promptDialog} from "../common/bootbox.ts";

interface RepositoryConfig {
  short_name: string
  full_name: string

  id_digits: number
  indexed_files: string[]
  main_branch: string
  prefixes: { [K: string]: string }
  release_file: string
  release_script_path: string
  subontologies: {
    [K: string]: {
      release_file: string
      excel_file: string
    }
  }
}

declare var SETTINGS: {
  'repositories': RepositoryConfig[],
  'startup_repositories': string[]
}
declare var URLS: { [key: string]: any }

const prefix_url = URLS.prefix
const settings = ref<typeof SETTINGS>(SETTINGS)

let loading = ref<boolean>(false);
let deleting = ref<string | null>(null);
let startupChanging = ref<string | null>(null);
let blocked = computed(() => loading.value || deleting.value !== null || startupChanging.value !== null)

async function toggleStartup(repo: RepositoryConfig) {
  startupChanging.value = repo.full_name;

  const currentlySet = settings.value.startup_repositories.indexOf(repo.full_name) >= 0;
  const route = currentlySet ? 'remove' : 'add';

  const resp = await (await fetch(`${prefix_url}/api/settings/repositories/${route}_startup`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({"full_name": repo.full_name})
  })).json()

  if (resp.success) {
    settings.value.startup_repositories = currentlySet ?
        settings.value.startup_repositories.filter(x => x !== repo.full_name) :
        [...settings.value.startup_repositories, repo.full_name];
  } else {

    await alertDialog({
      title: currentlySet ? "Unsetting as startup failed" : "Unsetting as startup failed",
      message: "The current configuration probably does not allow setting startup repositories."
    })
  }

  startupChanging.value = null;
}

async function unloadRepository(repo: RepositoryConfig) {
  deleting.value = repo.full_name;

  const resp = await (await fetch(`${prefix_url}/api/settings/repositories/unload`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({"full_name": repo.full_name})
  })).json()

  if (resp.success) {
    settings.value.repositories = settings.value.repositories.filter(x => x !== repo)
  } else {
    await alertDialog({
      title: "Unloading failed",
      message: "The repository was probably already unloaded. Try refreshing the page."
    })
  }

  deleting.value = null;
}

async function loadRepository() {
  loading.value = true;
  let resp = await (await fetch(`${prefix_url}/api/settings/repositories/possibilities`)).json()

  if (resp.success) {
    const suggestions = resp.repositories;
    const index = await promptDialog({
      title: "Found possible external parents",
      message:
          `Chose one of your repositories to load.`,
      inputType: "select",
      inputOptions: suggestions.map(({short_name, full_name}, i) => ({
        value: i,
        text: `${short_name} (${full_name})`
      })),
      buttons: {
        confirm: {
          label: `Load repository`,
          className: "btn-success",
        },
        cancel: {
          label: "Cancel",
          className: "btn-warning"
        }
      }
    })

    if (index !== null) {
      const result = await (await fetch(`${prefix_url}/api/settings/repositories/load`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(suggestions[index])
      })).json()

      if (result.success) {
        settings.value.repositories = [...settings.value.repositories, result.repo]
      } else {
        await alertDialog({
          title: "Loading failed",
          message: result.error
        })
      }
    }
  } else {
    await alertDialog({
      title: "Unloading failed",
      message: "The repository was probably already unloaded. Try refreshing the page."
    })
  }
  loading.value = false;
}
</script>

<template>

  <div class="settings">

    <h1>Settings</h1>
    <h3>Repositories</h3>
    <CollapsibleCard v-for="repo in settings.repositories">
      <template #title>
        {{ repo.short_name }} ({{ repo.full_name }})
      </template>
      <template #buttons>
        <button class="btn btn-primary btn-sm" @click="toggleStartup(repo)">
          <template v-if="settings.startup_repositories.indexOf(repo.full_name) >= 0">
            <i class="fa fa-square-check"></i> Loaded on startup
          </template>
          <template v-else>
            <i class="fa fa-square"></i> Not loaded on startup
          </template>
        </button>

        <button class="btn btn-danger btn-sm btn-circle" @click="$event.stopPropagation(); unloadRepository(repo)"
                :disabled="blocked">
          <i class="fa" :class="deleting === repo.full_name ? ['fa-spinner', 'fa-spin'] : ['fa-trash']"></i>
        </button>
      </template>
      <template #body>
        <h6>Core settings</h6>
        <div class="input-group input-group-sm mb-3">
          <span class="input-group-text">ID Length</span>
          <input v-model="repo.id_digits" type="number" class="form-control">
        </div>

        <div class="input-group input-group-sm mb-3">
          <span class="input-group-text">Main branch</span>
          <input v-model="repo.main_branch" type="text" class="form-control">
        </div>

        <h6>Release</h6>

        <div class="input-group input-group-sm mb-3">
          <span class="input-group-text">Released OWL file</span>
          <input v-model="repo.release_file" type="text" class="form-control">
        </div>

        <div class="input-group input-group-sm mb-3">
          <span class="input-group-text">Released script</span>
          <input v-model="repo.release_script_path" type="text" class="form-control">
        </div>

        <h6>Subontologies</h6>
        <p class="text-body-secondary">
          To generate hierarchical spreadsheets
        </p>

        <template v-for="subontology in repo.subontologies">
          <div class="input-group input-group-sm mb-3">
            <span class="input-group-text">Excel</span>
            <input v-model="subontology.excel_file" type="text" class="form-control">
            <span class="input-group-text">Released</span>
            <input v-model="subontology.release_file" type="text" class="form-control">

            <button class="btn btn-danger" @click="repo.subontology = repo.subontologies.filter(x => x != subontology)"
                    :disabled="blocked">
              <i class="fa fa-trash"></i>
            </button>
          </div>
        </template>
      </template>
    </CollapsibleCard>

    <div class="d-flex gap-2">
      <button class="mb-3 btn btn-sm btn-primary add-file" @click="loadRepository" :disabled="blocked">
        <i class="fa" :class="loading ? ['fa-spinner', 'fa-spin'] : ['fa-add']"></i>
        Load repository
      </button>
      <slot name="buttons"></slot>
    </div>
  </div>
</template>

<style scoped lang="scss">
.settings {
  display: flex;
  flex-direction: column;
  gap: 14px
}
</style>

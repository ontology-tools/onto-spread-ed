<script lang="ts" setup>

import {computed, onMounted, ref} from "vue";
import {api, clearCache, useMe} from "../api";
import {layout} from "../state";
import {alertDialog, promptDialog} from "../common/bootbox";
import {Project} from "@ontospreaded/js-core";

type Settings = {
  repositories: Project[],
  startup_repositories: string[],
  changing_startup_allowed: boolean,
  loading_new_allowed: boolean
}
const settings = ref<Settings>({
  repositories: [],
  startup_repositories: [],
  changing_startup_allowed: false,
  loading_new_allowed: false
})

onMounted(async () => {
  layout.breadcrumb = [{name: "Admin", to: "/admin"}, {name: "Settings"}]
  try {
    settings.value = await api<Settings>("/api/settings")
  } catch (e: any) {
    await alertDialog({
      title: "Loading settings failed",
      message: e.message
    })
  }
})

const {me} = useMe();
const isAdmin = computed(() => !!me.value?.permissions?.includes("admin"));

let loading = ref<boolean>(false);
let deleting = ref<string | null>(null);
let startupChanging = ref<string | null>(null);
let blocked = computed(() => loading.value || deleting.value !== null || startupChanging.value !== null)

let buttonStates = ref<{ reload: string | null }>({
  reload: null,
})

const reloadButtonClass: Record<string, string> = {success: 'btn-success', null: 'btn-primary', error: 'btn-danger'}
const reloadIconClass: Record<string, string[]> = {success: ['fa-check'], error: ['fa-cross'], loading: ['fa-spinner', 'fa-spin']}

let runningTimeouts: { [key: string]: ReturnType<typeof setTimeout> } = {};

async function toggleStartup(repo: Project) {
  startupChanging.value = repo.full_repository_name;

  const currentlySet = settings.value.startup_repositories.indexOf(repo.full_repository_name) >= 0;
  const route = currentlySet ? 'remove' : 'add';

  try {
    const resp = await api<{success: boolean}>(`/api/settings/repositories/${route}_startup`, {
      method: "POST",
      body: JSON.stringify({"full_name": repo.full_repository_name})
    })
    if (!resp.success) {
      throw new Error("The current configuration probably does not allow setting startup repositories.")
    }
    settings.value.startup_repositories = currentlySet ?
        settings.value.startup_repositories.filter(x => x !== repo.full_repository_name) :
        [...settings.value.startup_repositories, repo.full_repository_name];
  } catch (e: any) {
    await alertDialog({
      title: currentlySet ? "Unsetting as startup failed" : "Setting as startup failed",
      message: e.message
    })
  } finally {
    startupChanging.value = null;
  }
}

async function unloadRepository(repo: Project) {
  deleting.value = repo.full_repository_name;

  try {
    const resp = await api<{success: boolean}>("/api/settings/repositories/unload", {
      method: "POST",
      body: JSON.stringify({"full_name": repo.full_repository_name})
    })
    if (!resp.success) {
      throw new Error("The repository was probably already unloaded. Try refreshing the page.")
    }
    clearCache();
    settings.value.repositories = settings.value.repositories.filter(x => x !== repo)
  } catch (e: any) {
    await alertDialog({
      title: "Unloading failed",
      message: e.message
    })
  } finally {
    deleting.value = null;
  }
}

async function loadRepository() {
  loading.value = true;
  try {
    const resp = await api("/api/settings/repositories/possibilities")
    const suggestions = resp.repositories;
    const index = await promptDialog({
      title: "Found possible external parents",
      message:
          `Chose one of your repositories to load.`,
      inputType: "select",
      inputOptions: suggestions.map(({short_name, full_name}: { short_name: string, full_name: string }, i: number) => ({
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
      const result = await api("/api/settings/repositories/load", {
        method: "POST",
        body: JSON.stringify(suggestions[index])
      })
      clearCache();
      settings.value.repositories = [...settings.value.repositories, result.repo]
    }
  } catch (e: any) {
    await alertDialog({
      title: "Loading failed",
      message: e.message
    })
  } finally {
    loading.value = false;
  }
}


async function reload() {
  buttonStates.value.reload = "loading"
  try {
    const resp = await api("/api/settings/repositories/reload", {method: "POST"});
    if (resp.success) {
      clearCache();
      settings.value.repositories = resp.repositories;
      buttonStates.value.reload = "success";
    } else {
      await alertDialog({
        title: "Reloading settings failed",
        message: resp.error
      });
      buttonStates.value.reload = "error";
    }
  } catch (error) {
    await alertDialog({
      title: "Reloading settings failed",
      message: "An error occurred while reloading the settings."
    });
    buttonStates.value.reload = "error";
  }

  if (runningTimeouts["reload"]) {
    clearTimeout(runningTimeouts["reload"]);
  }
  runningTimeouts["reload"] = setTimeout(() => buttonStates.value.reload = null, 2000);
}
</script>

<template>

  <div class="settings">

    <h1>Settings</h1>
    <h3>Repositories</h3>
    <table class="table align-middle">
      <thead>
      <tr>
        <th>Repository</th>
        <th>GitHub</th>
        <th>Loaded on startup</th>
        <th></th>
      </tr>
      </thead>
      <tbody>
      <tr v-for="repo in settings.repositories" :key="repo.full_repository_name">
        <td>
          <RouterLink :to="{name: 'project-settings', params: {repo: repo.short_name}}">
            {{ repo.short_name }}
          </RouterLink>
          <div class="small text-body-secondary">{{ repo.full_name }}</div>
        </td>
        <td>{{ repo.full_repository_name }}</td>
        <td>
          <div class="form-check form-switch">
            <input :checked="settings.startup_repositories.indexOf(repo.full_repository_name) >= 0"
                   :disabled="blocked || !settings.changing_startup_allowed" class="form-check-input" role="switch"
                   title="Load on startup" type="checkbox" @change="toggleStartup(repo)">
            <i v-if="startupChanging === repo.full_repository_name" class="fa fa-spinner fa-spin"></i>
          </div>
        </td>
        <td class="text-end text-nowrap">
          <RouterLink :to="{name: 'project-settings', params: {repo: repo.short_name}}"
                      class="btn btn-sm btn-outline-primary me-1">
            <i class="fa fa-edit"></i> Configuration
          </RouterLink>
          <button v-if="settings.loading_new_allowed" :disabled="blocked" class="btn btn-sm btn-outline-danger"
                  title="Unload repository" @click="unloadRepository(repo)">
            <i :class="deleting === repo.full_repository_name ? ['fa-spinner', 'fa-spin'] : ['fa-trash']" class="fa"></i>
          </button>
        </td>
      </tr>
      </tbody>
    </table>

    <div class="d-flex gap-2">
      <button v-if="settings.loading_new_allowed" :disabled="blocked" class="mb-3 btn btn-sm btn-primary"
              @click="loadRepository">
        <i :class="loading ? ['fa-spinner', 'fa-spin'] : ['fa-add']" class="fa"></i>
        Load repository
      </button>
      <button v-if="isAdmin" :class="[reloadButtonClass[buttonStates.reload ?? 'null']]"
              :disabled="blocked || buttonStates.reload === 'loading'" class="mb-3 btn btn-sm btn-primary"
              @click="reload()">
        <i :class="(reloadIconClass[buttonStates.reload ?? 'null'] ?? ['fa-refresh'])"
           class="fa"></i>
        Reload settings
      </button>
    </div>
  </div>
</template>

<script lang="ts" setup>

import CollapsibleCard from "../common/CollapsibleCard.vue";
import {computed, onMounted, ref} from "vue";
import {api, clearCache} from "../api";
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

let loading = ref<boolean>(false);
let deleting = ref<string | null>(null);
let startupChanging = ref<string | null>(null);
let installingWorkflow = ref<null | "busy" | "error" | "success">(null);
let blocked = computed(() => loading.value || deleting.value !== null || startupChanging.value !== null || installingWorkflow.value === "busy")

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


async function installWorkflow(name: string, repo: Project) {
  installingWorkflow.value = "busy";
  try {
    const resp = await api(`/api/repo/${repo.short_name}/install_workflow/${name}`, {method: "POST"});

    if (!resp.success) {
      await alertDialog({
        title: "Workflow installation failed",
        message: resp.msg
      });
      installingWorkflow.value = "error"
      return;
    }

    installingWorkflow.value = "success"
  } catch (error: any) {
    await alertDialog({
      title: "Workflow installation failed",
      message: error?.message ?? "An error occurred while installing the workflow."
    });

    installingWorkflow.value = "error"
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
    <CollapsibleCard v-for="repo in settings.repositories">
      <template #title>
        {{ repo.short_name }} ({{ repo.full_repository_name }})
      </template>
      <template #buttons>
        <button :disabled="blocked || !settings.changing_startup_allowed" class="btn btn-primary btn-sm"
                @click="toggleStartup(repo)">
          <template v-if="settings.startup_repositories.indexOf(repo.full_repository_name) >= 0">
            <i class="fa fa-square-check"></i> Loaded on startup
          </template>
          <template v-else>
            <i class="fa fa-square"></i> Not loaded on startup
          </template>
        </button>

        <button v-if="settings.loading_new_allowed" :disabled="blocked"
                class="btn btn-danger btn-sm btn-circle" @click="$event.stopPropagation(); unloadRepository(repo)">
          <i :class="deleting === repo.full_repository_name ? ['fa-spinner', 'fa-spin'] : ['fa-trash']" class="fa"></i>
        </button>
      </template>
      <template #body>
        <h6>Core settings</h6>
        <div class="input-group input-group-sm mb-3">
          <span class="input-group-text">ID Length</span>
          <input v-model="repo.id_digits" class="form-control" type="number">
        </div>

        <div class="input-group input-group-sm mb-3">
          <span class="input-group-text">Main branch</span>
          <input v-model="repo.main_branch" class="form-control" type="text">
        </div>

        <h6>Subontologies</h6>
        <p class="text-body-secondary">
          To generate hierarchical spreadsheets
        </p>

        <template v-for="subontology in repo.subontologies">
          <div class="input-group input-group-sm mb-3">
            <span class="input-group-text">Excel</span>
            <input v-model="subontology.excel_file" class="form-control" type="text">
            <span class="input-group-text">Released</span>
            <input v-model="subontology.release_file" class="form-control" type="text">

            <button :disabled="blocked" class="btn btn-danger"
                    @click="repo.subontologies = Object.fromEntries(Object.entries(repo.subontologies).filter(([, x]) => x != subontology))">
              <i class="fa fa-trash"></i>
            </button>
          </div>
        </template>

        <h6>Workflows</h6>
        <p class="text-body-secondary">
          Install github workflows in this repository
        </p>


        <button :class="{'btn-success': installingWorkflow === 'success', 'btn-danger': installingWorkflow === 'error'}"
                :disabled="blocked" class="btn btn-primary btn-sm"
                @click="installWorkflow('externals', repo)">
          <i v-if="installingWorkflow === 'busy'" class="fa fa-spin fa-spinner"></i>
          <i v-if="installingWorkflow === 'success'" class="fa fa-check"></i>
          <i v-if="installingWorkflow === 'error'" class="fa fa-close"></i>
          <i v-else class="fa fa-file-import"></i>
          Automatically build externals owl file
        </button>
      </template>
    </CollapsibleCard>

    <div class="d-flex gap-2">
      <button v-if="settings.loading_new_allowed" :disabled="blocked" class="mb-3 btn btn-sm btn-primary add-file"
              @click="loadRepository">
        <i :class="loading ? ['fa-spinner', 'fa-spin'] : ['fa-add']" class="fa"></i>
        Load repository
      </button>
      <button :class="[reloadButtonClass[buttonStates.reload ?? 'null']]" :disabled="blocked || buttonStates.reload === 'loading'"
              class="mb-3 btn btn-sm btn-primary add-file"
              @click="reload()">
        <i :class="(reloadIconClass[buttonStates.reload ?? 'null'] ?? ['fa-refresh'])"
           class="fa"></i>
        Reload settings
      </button>
      <slot name="buttons"></slot>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.settings {
  display: flex;
  flex-direction: column;
  gap: 14px
}
</style>

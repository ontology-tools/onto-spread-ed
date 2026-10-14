<script lang="ts" setup>
import {ref} from "vue";
import {Project} from "@ontospreaded/js-core";
import {api} from "../../api";

const props = defineProps<{ project: Project }>()

const state = ref<null | "busy" | "error" | "success">(null);
const error = ref<string | null>(null);

async function install(name: string) {
  state.value = "busy";
  error.value = null;
  try {
    const resp = await api(`/api/repo/${props.project.short_name}/install_workflow/${name}`, {method: "POST"});
    if (!resp.success) throw new Error(resp.msg ?? resp.error ?? "The workflow could not be installed.");
    state.value = "success";
  } catch (e: any) {
    error.value = e.message;
    state.value = "error";
  }
}
</script>

<template>
  <p class="text-body-secondary">Install GitHub workflows in {{ project.full_repository_name }}.</p>

  <button :class="{'btn-success': state === 'success', 'btn-danger': state === 'error'}" :disabled="state === 'busy'"
          class="btn btn-primary btn-sm" type="button" @click="install('externals')">
    <i v-if="state === 'busy'" class="fa fa-spin fa-spinner"></i>
    <i v-else-if="state === 'success'" class="fa fa-check"></i>
    <i v-else-if="state === 'error'" class="fa fa-close"></i>
    <i v-else class="fa fa-file-import"></i>
    Automatically build externals owl file
  </button>
  <div v-if="error" class="alert alert-danger py-2 mt-2">{{ error }}</div>
</template>

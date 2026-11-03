<script lang="ts" setup>
import {onMounted, ref} from "vue";
import {api} from "../api";
import {layout} from "../state";
import {alertDialog} from "../common/bootbox";

type IndexStats = {
  number_of_repositories: number
  number_of_sheets: number
  number_of_terms: number
  repositories: string[]
  sheets: string[]
}

const stats = ref<IndexStats | null>(null);
const rebuilding = ref(false);

const error = ref<string | null>(null);

const load = async () => {
  try {
    stats.value = await api<IndexStats>("/api/admin/index");
    error.value = null;
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  }
}
onMounted(() => {
  layout.breadcrumb = [{name: "Admin", to: "/admin"}, {name: "Rebuild index"}];
  load();
});

const esc = (x: string) => x.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

const label = (name: string) => {
  const s = name.replace(/_/g, " ");
  return s.charAt(0).toUpperCase() + s.slice(1);
}

async function rebuild() {
  rebuilding.value = true;
  try {
    const sheets = await api<string[]>("/api/admin/index", {method: "POST"});
    await alertDialog({
      title: "Index rebuild",
      message: `<p>Files included in the index:</p><ul>${sheets.map(x => `<li>${esc(x)}</li>`).join("\n")}</ul>`,
      size: "large"
    });
    await load();
  } catch (e) {
    bootbox.alert(`Something went wrong: ${esc((e as Error)?.message ?? String(e))}`);
    console.error(e);
  } finally {
    rebuilding.value = false;
  }
}
</script>

<template>
  <h1>Rebuild the index</h1>
  <div v-if="error" class="alert alert-danger">{{ error }}</div>
  <p>Currently, the index has the following statistics:</p>

  <table v-if="stats" class="table">
    <thead>
    <tr>
      <th scope="col">Name</th>
      <th scope="col">Value</th>
    </tr>
    </thead>
    <tbody>
    <template v-for="(value, name) in stats" :key="name">
      <template v-if="Array.isArray(value)">
        <tr v-for="(e, i) in (value.length ? value : [''])" :key="i">
          <td>{{ i === 0 ? label(name as string) : "" }}</td>
          <td>{{ e }}</td>
        </tr>
      </template>
      <tr v-else>
        <td>{{ label(name as string) }}</td>
        <td>{{ value }}</td>
      </tr>
    </template>
    </tbody>
  </table>

  <button type="button" class="btn btn-danger" :disabled="rebuilding" @click="rebuild">
    <i v-if="rebuilding" class="fas fa-spin fa-cog"></i>
    Rebuild the index
  </button>
</template>

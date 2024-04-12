<script setup lang="ts">
var URL_PREFIX = '{{config["URL_PREFIX"]}}';
import {onMounted, Ref, ref} from "vue";
import {ReleaseScript} from "./model.ts"
import RepositorySelector from "./RepositorySelector.vue";
import ReleaseScriptViewer from "./ReleaseScriptViewer.vue";

const repos: Ref<{ short: string, full: string }[]> = ref([]);
const releaseScript: Ref<ReleaseScript | null> = ref(null);
const repo: Ref<string | null> = ref(null);

async function fetchData() {
  repos.value = await (await fetch(URL_PREFIX + "/api/repo")).json()
}

onMounted(async () => {
  await fetchData()
})

defineEmits<{
  (e: 'settingsConfirmed', script: ReleaseScript): void
}>()

async function setRepo(repoKey: string) {
  releaseScript.value = await (await fetch(`/api/release/${repoKey}/release_script`)).json()
}
</script>

<template>

  <div class="preparation">

    <h3>Release selection</h3>
    <p>
      Select the repository you want to release.
    </p>

    <RepositorySelector :repositories="repos" v-model="repo" @update:modelValue="setRepo"></RepositorySelector>
    <ReleaseScriptViewer :release-script="releaseScript" v-if="!!releaseScript" class="mt-2"></ReleaseScriptViewer>

    <button v-if="!!releaseScript" class="btn btn-success w-100" @click="$emit('settingsConfirmed', releaseScript)">
      <i class="fa fa-play"></i>
      Start the release
    </button>
  </div>
</template>

<style scoped>

</style>

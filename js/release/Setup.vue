<script setup lang="ts">
import {onMounted, Ref, ref} from "vue";
import {ReleaseScript} from "./model.ts"
import RepositorySelector from "./RepositorySelector.vue";
import ReleaseScriptViewer from "./ReleaseScriptViewer.vue";

const showAdvanced = ref<boolean>()
const repos: Ref<{ short: string, full: string }[]> = ref([]);
const releaseScript: Ref<ReleaseScript | null> = ref(null);
const repo: Ref<string | null> = ref(null);

async function fetchData() {
  repos.value = await (await fetch("/api/repo")).json()
}

onMounted(async () => {
  await fetchData()
})

defineEmits<{
  (e: 'settingsConfirmed', script: ReleaseScript): void
}>()

async function setRepo(repoKey: string) {
  releaseScript.value = null
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

    <div class="btn-group  w-100">

      <button :disabled="!releaseScript" class="btn btn-success"
              @click="$emit('settingsConfirmed', releaseScript)">
        <i class="fa fa-play"></i>
        Start the release
      </button>
      <button :disabled="!releaseScript" type="button"
              class="btn btn-success dropdown-toggle dropdown-toggle-split flex-grow-0"
              data-bs-toggle="dropdown">
      </button>

      <ul class="dropdown-menu">
        <li><a class="dropdown-item" href="#" @click="showAdvanced = !showAdvanced">
          <i class="fa-regular" :class="[showAdvanced ? 'fa-check-square' : 'fa-square']"></i> Show advanced configuration
        </a></li>
      </ul>
    </div>


    <ReleaseScriptViewer :release-script="releaseScript" v-if="!!releaseScript && showAdvanced"
                         class="mt-2"></ReleaseScriptViewer>
  </div>
</template>

<style scoped>

</style>

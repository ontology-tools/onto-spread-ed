<script setup lang="ts">
import {Release} from "../model";
import {computed, ref} from "vue";

const props = defineProps<{
  data?: {
    files: {
      link: string,
      name: string
    }[]
  },
  release: Release,
  selectedSubStep: string | null
}>()

defineEmits<{
  (e: 'release-control', type: string, ...args: any[]): void
}>()

const checkHierarchy = ref<boolean>(props.release.state === "completed")
const checkLabels = ref<boolean>(props.release.state === "completed")
const checkHierarchicalSpreadsheets = ref<boolean>(props.release.state === "completed")

const hasHierarchicalSpreadsheets = computed(() => !!props.data?.files?.find(x => x.name.endsWith(".xlsx")))

const allChecked = computed(() => [
  checkLabels.value,
  checkHierarchy.value,
  !hasHierarchicalSpreadsheets.value || checkHierarchicalSpreadsheets.value
].reduce((p, v) => p && v, true))

</script>

<template>
  <h3>Verify the built ontologies</h3>

  <p>
    Please download the built files and ontologies and open them in Protégé (download
    <a href="https://protege.stanford.edu/software.php#desktop-protege">here</a> or use
    <a href="https://webprotege.stanford.edu/">Web protege</a>).
  </p>
  <ul>
    <li v-for="file in data?.files"><a :href="file.link" :download="file.name">{{ file.name }}</a></li>

  </ul>
  <p>
    Check the following things:
  </p>

  <ul class="list-unstyled">
    <li class="ms-4">
      <div class="form-check">
        <input v-model="checkHierarchy" :disabled="release.state !== 'waiting-for-user'"
               class="form-check-input checklist" type="checkbox" value="" id="chk-inferred">
        <label class="form-check-label" for="chk-inferred">
          Start the reasoner. Does the inferred hierarchy look alright?
        </label>
      </div>
    </li>
    <li class="ms-4">
      <div class="form-check">
        <input v-model="checkLabels" :disabled="release.state !== 'waiting-for-user'"
               class="form-check-input checklist" type="checkbox" value="" id="chk-labels">
        <label class="form-check-label" for="chk-labels">
          Do the labels look alright?
        </label>
      </div>
    </li>
    <li class="ms-4" v-if="hasHierarchicalSpreadsheets">
      <div class="form-check">
        <input v-model="checkHierarchicalSpreadsheets" :disabled="release.state !== 'waiting-for-user'"
               class="form-check-input checklist" type="checkbox" value="" id="chk-hierarchical-spreadsheets">
        <label class="form-check-label" for="chk-hierarchical-spreadsheets">
          Do the hierarchy, labels, and other fields in the hierarchical spreadsheets look alright?
        </label>
      </div>
    </li>
  </ul>

  <button class="btn btn-success w-100" id="btn-publish-release"
          :disabled="!allChecked || release.state !== 'waiting-for-user'" @click="$emit('release-control', 'continue')">
    Everything looks alright. Publish the release!
  </button>


</template>

<style scoped lang="scss">

</style>

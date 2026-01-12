<script setup lang="ts">
import {Release} from "../model";
import TechnicalError from "../TechnicalError.vue";
import ProgressIndicator from "../ProgressIndicator.vue";
import {computed} from "vue";

const STEPS = {
  PREPARATION: {
    title: "Preparation",
    running_text: "Excel files are downloaded to the server and prepared.",
    finished_text: "Excel files were downloaded to the server."
  },
  IMPORT_EXTERNAL: {
    title: "Building external dependencies",
    running_text: "External ontologies are now downloaded and converted. This might take a few minutes.",
    finished_text: "External ontologies were successfully downloaded and converted."
  },
  BUILD: {
    title: "Building OWL files",
    running_text: "OWL files are now build.",
    finished_text: "OWL files were successfully built."
  },
  MERGE: {
    title: "Merging files",
    running_text: "Multiple OWL files are being combined into one.",
    finished_text: "Multiple OWL files were combined into one."
  }
}

const props = defineProps<{
  data: any,
  release: Release
  step: {
    args: any,
    name: string
  }
}>()

defineEmits<{
  (e: 'release-control', type: string, ...args: any[]): void
}>()

function titleCase(str: string): string {
  return str.replace("_", " ").replace(
      /\w\S*/g,
      text => text.charAt(0).toUpperCase() + text.substring(1).toLowerCase()
  );
}

const title = computed(() => STEPS[props.step.name]?.title ?? titleCase(props.step.name ?? "<MISSING>"))
const running_text = computed(() => STEPS[props.step.name]?.running_text ?? "")
const finished_text = computed(() => STEPS[props.step.name]?.finished_text ?? "")
</script>

<template>
  <h3>{{ title }}</h3>

  <TechnicalError v-if="release.state == 'waiting-for-user' && data && (data.errors?.length ?? 0) > 0"
                  :release="release"
                  :details="data"></TechnicalError>

  <ProgressIndicator v-else :details="data" :release="release">
    {{ running_text }}
  </ProgressIndicator>
  <template v-if="release.state === 'completed'">
    <p>
      {{ finished_text }}
    </p>
  </template>
</template>

<style scoped lang="scss">

</style>

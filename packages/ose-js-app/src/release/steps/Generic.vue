<script setup lang="ts">
import { Release, ProgressIndicator, currentStage, releaseStages } from "@ontospreaded/js-core";
import TechnicalError from "../TechnicalError.vue";
import { computed } from "vue";

const STEPS: {[key: string]: {title: string, running_text: string, finished_text: string}} = {
  PREPARATION: {
    title: "Preparation",
    running_text: "The latest version of the repository is checked out on the server.",
    finished_text: "The latest version of the repository was checked out on the server."
  },
  EXTERNAL_IMPORTS: {
    title: "Building external dependencies",
    running_text: "External ontologies are now downloaded and converted. This might take a few minutes.",
    finished_text: "External ontologies were successfully downloaded and converted."
  },
  EXCEL2OWL: {
    title: "Building OWL files",
    running_text: "OWL files are now build.",
    finished_text: "OWL files were successfully built."
  },
  MERGE: {
    title: "Merging files",
    running_text: "Multiple OWL files are being combined into one.",
    finished_text: "Multiple OWL files were combined into one."
  },
  CLEANUP: {
    title: "Cleaning up",
    running_text: "Temporary files and branches of the release are removed.",
    finished_text: "Temporary files and branches of the release were removed."
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
const running_text = computed(() => STEPS[props.step.name]?.running_text ?? `Working on ${title.value.toLowerCase()}...`)
const finished_text = computed(() => STEPS[props.step.name]?.finished_text ?? `Worked on ${title.value.toLowerCase()}`)

const stepNumber = computed(() => releaseStages(props.release).findIndex(s => s.name === props.step.name))
</script>

<template>
  <h3>{{ title }}</h3>

  <TechnicalError v-if="release.state == 'errored' && data && (data.errors?.length ?? 0) > 0"
    :release="release" :details="data"></TechnicalError>

  <ProgressIndicator v-else :details="data" :release="release" :step-number="stepNumber">
    <p
      v-if="release.state === 'completed' || currentStage(release) > stepNumber">

      {{ finished_text }}

    <div class="text-center w-100 text-success" style="font-size: 100px">
      <i class="fa fa-check-double"></i>
    </div>
    </p>
    <p v-else-if="release.state === 'running' || release.state === 'starting'">
      {{ running_text }}
    </p>
    <p v-else>
      {{ running_text }}


      <div class="text-center w-100 text-danger" style="font-size: 100px">
        <i class="fa fa-circle-xmark"></i>
      </div>
    </p>
  </ProgressIndicator>
</template>

<style scoped lang="scss"></style>

<script setup lang="ts">
import { Release, ProgressIndicator } from "@ontospreaded/js-core";
import TechnicalError from "../TechnicalError.vue";
import { computed } from "vue";

const STEPS: {[key: string]: {title: string, running_text: string, finished_text: string}} = {
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
const running_text = computed(() => STEPS[props.step.name]?.running_text ?? `Working on ${title.value.toLowerCase()}...`)
const finished_text = computed(() => STEPS[props.step.name]?.finished_text ?? `Worked on ${title.value.toLowerCase()}`)

const stepNumber = computed(() => props.release.release_script.steps.findIndex(s => s.name === props.step.name))
</script>

<template>
  <h3>{{ title }}</h3>

  <TechnicalError v-if="release.state == 'waiting-for-user' && data && (data.errors?.length ?? 0) > 0"
    :release="release" :details="data"></TechnicalError>

  <ProgressIndicator v-else :details="data" :release="release" :state="release.state === 'running' && release.step > stepNumber ? 'completed' : release.state">
    <p
      v-if="release.state === 'completed' || release.step > stepNumber">

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

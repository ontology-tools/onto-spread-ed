<script setup lang="ts">
import {Release} from "../model.ts";
import TechnicalError from "../TechnicalError.vue";
import ProgressIndicator from "../ProgressIndicator.vue";

defineProps<{
  data: any,
  release: Release
}>()

defineEmits<{
  (e: 'release-control', type: string, ...args: any[]): void
}>()
</script>

<template>
  <h3>Merging files</h3>

  <TechnicalError v-if="release.state == 'waiting-for-user' && data && (data.errors?.length ?? 0) > 0"
                  :release="release"
                  :details="data"></TechnicalError>

  <ProgressIndicator v-else :details="data" :release="release">
    Multiple OWL files are being combined into one.
  </ProgressIndicator>


  <template v-if="release.state === 'completed'">
    <p>
      Multiple OWL files were combined into one.
    </p>
  </template>
</template>

<style scoped lang="scss">

</style>

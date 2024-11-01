<script lang="ts" setup>
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
  <h3>Building OWL files</h3>

  <TechnicalError v-if="release.state == 'waiting-for-user' && data && (data.errors?.length ?? 0) > 0"
                  :details="data"
                  :release="release"></TechnicalError>

  <ProgressIndicator v-else :details="data" :release="release">
    OWL files are now build.
  </ProgressIndicator>


  <template v-if="release.state === 'completed'">
    <p>
      OWL files were successfully built.
    </p>
  </template>
</template>

<style lang="scss" scoped>

</style>

<script setup lang="ts">
import {Release} from "../model.ts";
import ProgressIndicator from "../ProgressIndicator.vue";
import TechnicalError from "../TechnicalError.vue";

defineProps<{
  data: any,
  release: Release
}>()

defineEmits<{
  (e: 'release-control', type: string, ...args: any[]): void
}>()
</script>

<template>
  <h3>Building external dependencies</h3>

  <TechnicalError v-if="release.state == 'waiting-for-user' && data && (data.errors?.length ?? 0) > 0"
                  :release="release"
                  :details="data"></TechnicalError>

  <ProgressIndicator v-else :details="data" :release="release">
    External ontologies are now downloaded and converted. This might take a few minutes.
  </ProgressIndicator>


  <template v-if="release.state === 'completed'">
    <p>
      External ontologies were successfully downloaded and converted.
    </p>
  </template>
</template>

<style scoped lang="scss">

</style>

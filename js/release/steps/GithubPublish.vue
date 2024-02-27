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
  <h3>Publishing the release</h3>

  <TechnicalError v-if="release.state == 'waiting-for-user' && data && (data.errors?.length ?? 0) > 0"
                  :release="release"
                  :details="data"></TechnicalError>
  <template v-else-if="release.state === 'completed'">

    <p>
      The ontologies are now published to github and the release is completed.
    </p>
    <div class="text-center w-100 text-success" style="font-size: 100px">
      <i class="fa fa-check-double"></i>
    </div>
  </template>
  <ProgressIndicator v-else :details="data" :release="release">
    The ontologies are being published to github.
  </ProgressIndicator>
</template>

<style scoped lang="scss">

</style>

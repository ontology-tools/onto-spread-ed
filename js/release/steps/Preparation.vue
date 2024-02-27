<script setup lang="ts">
import {Release} from "../model.ts";
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
  <h3>Preparation</h3>

  <ProgressIndicator>
    <p>
      Excel files are downloaded to the server and prepared.
    </p>
  </ProgressIndicator>

  <template v-if="release.state === 'completed'">
    <p>
      Excel files were downloaded to the server.
    </p>
  </template>
</template>

<style scoped lang="scss">

</style>

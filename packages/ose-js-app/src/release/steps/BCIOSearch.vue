<script setup lang="ts">

import ProgressIndicator from "../ProgressIndicator.vue";

defineProps<{
  data: any,
  release: Release,
  selectedSubStep: string | null
}>()


defineEmits<{
  (e: 'release-control', type: string, ...args: any[]): void
}>()
</script>

<template>
  <h3>Publishing the release</h3>
  <template v-if="release.state === 'waiting-for-user' && data?.errors?.length > 0">
    <div v-for="error in data.errors" class="alert alert-danger">
      <template v-if="error.details && error?.response?.['hydra:description']">
        <h4>{{ error.response['hydra:title'] }}</h4>
        <p>{{ error.details }}</p>
        <p>{{ error.response['hydra:description'] }}</p>
      </template>
      <pre v-else>{{ JSON.stringify(error, undefined, 2) }}</pre>
    </div>
  </template>

  <ProgressIndicator v-else :details="data" :release="release">
    <p>
      The ontologies are being published to BCIOSearch. This will take a while.<br>
    </p>
  </ProgressIndicator>


  <template v-if="release.state === 'completed'">
    <p>
      The ontologies were published to BCIOSearch.
    </p>
  </template>

</template>

<style scoped lang="scss">

</style>

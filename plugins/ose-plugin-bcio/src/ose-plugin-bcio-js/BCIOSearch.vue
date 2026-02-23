<script setup lang="ts">

import { type Release, ProgressIndicator } from "@ontospreaded/js-core";

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
    <div class="alert alert-danger">
      <h4>Errors occurred while publishing to BCIOSearch</h4>
      <p>Some API calls failed. Please review the errors below.</p>
    </div>
    <div v-for="error in data.errors" class="alert alert-danger">
      <template v-if="error.type === 'http-error'">
        <h6 v-if="error.term">Term: {{ error.term }}</h6>
        <p class="mb-1"><strong>HTTP {{ error.status_code }}:</strong> {{ error.response?.['hydra:title'] ?? 'Request failed' }}</p>
        <p v-if="error.response?.['hydra:description']" class="mb-1">{{ error.response['hydra:description'] }}</p>
        <ul v-if="error.response?.violations?.length" class="mb-0">
          <li v-for="v in error.response.violations">
            <strong>{{ v.propertyPath }}</strong>: {{ v.message }}
          </li>
        </ul>
      </template>
      <pre v-else>{{ JSON.stringify(error, undefined, 2) }}</pre>
    </div>
  </template>

  <ProgressIndicator v-else :details="data" :release="release" :state="release.state">
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
